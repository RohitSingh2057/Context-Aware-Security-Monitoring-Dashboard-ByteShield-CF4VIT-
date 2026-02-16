from raw_data import *
import pandas as pd
import numpy as np
import sqlite3

df = df.rename(columns={'network_packet_size': 'data_volume'})

def sessionize_sessions_df(
    df: pd.DataFrame,
    n_users: int = 500,
    start: str = "2025-01-01",
    end: str = "2025-03-01",
    sessions_per_user=(1, 8),
    session_gap_hours=(8, 96),
    seed: int = 42,
    add_session_start_end: bool = True,
    recompute_unusual_time_access: bool = True,
    unusual_hours=(0, 5),
) -> pd.DataFrame:

    rng = np.random.default_rng(seed)
    out = df.copy()

    if add_session_start_end and "session_duration" not in out.columns:
        raise ValueError("Expected 'session_duration' column (seconds).")

    raw = rng.integers(sessions_per_user[0], sessions_per_user[1] + 1, size=n_users)
    raw = np.maximum(1, np.round(raw * (len(out) / raw.sum())).astype(int))

    diff = len(out) - raw.sum()
    if diff > 0:
        raw[rng.choice(n_users, size=diff, replace=True)] += 1
    elif diff < 0:
        candidates = np.where(raw > 1)[0]
        take = min(len(candidates), -diff)
        if take > 0:
            raw[rng.choice(candidates, size=take, replace=False)] -= 1
        while raw.sum() > len(out):
            i = rng.integers(0, n_users)
            if raw[i] > 1:
                raw[i] -= 1

    user_ids = np.repeat(np.arange(1, n_users + 1), raw)[:len(out)]
    rng.shuffle(user_ids)
    out["user_id"] = user_ids

    start_ts = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end, tz="UTC")
    span_seconds = int((end_ts - start_ts).total_seconds())

    out["_row_ix"] = np.arange(len(out))
    session_start = np.empty(len(out), dtype="datetime64[ns]")

    for uid, idxs in out.groupby("user_id")["_row_ix"]:
        k = len(idxs)
        first = start_ts + pd.to_timedelta(rng.integers(0, span_seconds), unit="s")
        times = [first]

        if k > 1:
            gaps = rng.integers(session_gap_hours[0], session_gap_hours[1] + 1, size=k - 1)
            for gh in gaps:
                times.append(times[-1] + pd.Timedelta(hours=int(gh)))

        times = pd.to_datetime(times, utc=True)
        times = times.map(lambda t: start_ts + (t - start_ts) % (end_ts - start_ts))
        session_start[idxs.to_numpy()] = times.tz_localize(None).to_numpy()

    out["session_start"] = pd.to_datetime(session_start, utc=True)

    if add_session_start_end:
        out["session_end"] = out["session_start"] + pd.to_timedelta(
            out["session_duration"], unit="s"
        )

    if recompute_unusual_time_access:
        h = out["session_start"].dt.hour
        out["unusual_time_access"] = ((h >= unusual_hours[0]) & (h <= unusual_hours[1])).astype(int)

    out = (
        out.sort_values(["user_id", "session_start"])
           .drop(columns=["_row_ix"])
           .reset_index(drop=True)
    )

    return out

df_ctx = df.copy(deep=True)
df_ctx.columns = df_ctx.columns.astype(str).str.strip()

df_ctx = sessionize_sessions_df(df_ctx, n_users=500, seed=42)
df_ctx.columns = df_ctx.columns.astype(str).str.strip()

df_ctx["ts"] = pd.to_datetime(df_ctx["session_start"], utc=True)
df_ctx = df_ctx.sort_values(["user_id", "ts"]).reset_index(drop=True)

windows = ["1D", "7D"]

volume_col = "data_volume" if "data_volume" in df_ctx.columns else "network_packet_size"

numeric_cols = [
    volume_col,
    "login_attempts",
    "session_duration",
    "failed_logins",
    "ip_reputation_score",
]

for c in numeric_cols:
    if c in df_ctx.columns:
        df_ctx[c] = pd.to_numeric(df_ctx[c], errors="coerce")
    else:
        raise ValueError(f"Missing required numeric column: {c}")

def add_time_rolling_features(group, windows, numeric_cols):
    group = group.sort_values("ts").copy()

    for w in windows:
        tmp = group[["ts", "failed_logins"]].copy()
        tmp["past"] = tmp["failed_logins"].shift(1)
        group[f"failed_logins_sum_{w}"] = tmp.rolling(w, on="ts")["past"].sum().to_numpy()

        for col in numeric_cols:
            tmp = group[["ts", col]].copy()
            tmp["past"] = tmp[col].shift(1)
            r = tmp.rolling(w, on="ts")["past"]
            group[f"{col}_mean_{w}"] = r.mean().to_numpy()
            group[f"{col}_max_{w}"]  = r.max().to_numpy()
            group[f"{col}_sum_{w}"]  = r.sum().to_numpy()

    return group

df_ctx = (
    df_ctx.groupby("user_id", group_keys=False)
          .apply(add_time_rolling_features, windows=windows, numeric_cols=numeric_cols)
)

eps = 1e-6
for col in numeric_cols:
    df_ctx[f"{col}_minus_mean_7D"] = df_ctx[col] - df_ctx[f"{col}_mean_7D"]
    df_ctx[f"{col}_vs_mean_7D"] = df_ctx[col] / (df_ctx[f"{col}_mean_7D"] + eps)

if "user_id" not in df_ctx.columns:
    df_ctx = sessionize_sessions_df(df_ctx, n_users=500, seed=42)

if "browser_type" in df_ctx.columns:
    prev_browser = df_ctx.groupby("user_id")["browser_type"].shift(1)
    df_ctx["browser_change_flag"] = (
        (prev_browser.notna()) & (df_ctx["browser_type"] != prev_browser)
    ).astype(int)

    df_ctx["browser_unknown_flag"] = (
        df_ctx["browser_type"].astype(str).str.lower().eq("unknown")
    ).astype(int)
else:
    df_ctx["browser_change_flag"] = 0
    df_ctx["browser_unknown_flag"] = 1

feature_cols = [c for c in df_ctx.columns if (
    "_1D" in c or "_7D" in c or c.endswith("_flag") or c.endswith("_vs_mean_7D") or c.endswith("_minus_mean_7D")
)]
df_ctx[feature_cols] = df_ctx[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0)

obj_cols = df_ctx.select_dtypes(exclude=[np.number]).columns
df_ctx[obj_cols] = df_ctx[obj_cols].fillna("unknown")

for c in ["session_start", "session_end", "ts"]:
    if c in df_ctx.columns:
        dt = pd.to_datetime(df_ctx[c], errors="coerce", utc=True)
        df_ctx[c] = dt.dt.strftime("%Y-%m-%dT%H:%M:%SZ")

ts_dt = pd.to_datetime(df_ctx["ts"], errors="coerce", utc=True)
df_ctx["ts_epoch"] = (ts_dt.astype("int64") // 10**9).fillna(0).astype("int64")

for c in ["encryption_used", "unusual_time_access", "attack_detected"]:
    if c in df_ctx.columns:
        df_ctx[c] = pd.to_numeric(df_ctx[c], errors="coerce").fillna(0).astype(int)

for c in ["session_id", "user_id"]:
    if c in df_ctx.columns:
        df_ctx[c] = pd.to_numeric(df_ctx[c], errors="coerce").fillna(0).astype(int)

conn = sqlite3.connect("sessions.db")
cur = conn.cursor()

cur.execute("PRAGMA journal_mode=WAL;")
cur.execute("PRAGMA synchronous=NORMAL;")
cur.execute("PRAGMA temp_store=MEMORY;")
cur.execute("PRAGMA foreign_keys=ON;")

df_ctx.to_sql("sessions", conn, if_exists="replace", index=False)

cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_session_start ON sessions(session_start)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_ts_epoch ON sessions(ts_epoch)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_time ON sessions(user_id, session_start)")

if "org_id" in df_ctx.columns:
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_org_time ON sessions(org_id, session_start)")

conn.commit()
conn.close()