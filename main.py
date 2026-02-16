from clean_data import *
from raw_data import *

def compute_user_baseline(user_history):
    """
    Extracts the latest baseline values for a user from historical context.
    Assumes user_history is already sorted by timestamp.
    """

    if user_history.empty:
        return None  # cold start

    last_row = user_history.iloc[-1]

    baseline = {
        "login_attempts_mean_7D": last_row["login_attempts_mean_7D"],
        "failed_logins_mean_7D": last_row["failed_logins_mean_7D"],
        "data_volume_mean_7D": last_row["data_volume_mean_7D"],
        "session_duration_mean_7D": last_row["session_duration_mean_7D"],
        "ip_reputation_score_mean_7D": last_row["ip_reputation_score_mean_7D"],
        "last_browser_type": last_row["browser_type"],
    }

    return baseline

def add_deviation_features(new_session_df, baseline):
    """
    Adds deviation-based features to a single new session.
    new_session_df must contain exactly one row.
    """

    row = new_session_df.copy()
    eps = 1e-6

    if baseline is None:
        # Cold-start defaults
        row["login_attempts_vs_mean_7D"] = 1.0
        row["failed_logins_vs_mean_7D"] = 1.0
        row["data_volume_vs_mean_7D"] = 1.0
        row["session_duration_vs_mean_7D"] = 1.0
        row["browser_change_flag"] = 0
        return row

    row["login_attempts_vs_mean_7D"] = (
        row["login_attempts"] / (baseline["login_attempts_mean_7D"] + eps)
    )

    row["failed_logins_vs_mean_7D"] = (
        row["failed_logins"] / (baseline["failed_logins_mean_7D"] + eps)
    )

    row["data_volume_vs_mean_7D"] = (
        row["data_volume"] / (baseline["data_volume_mean_7D"] + eps)
    )

    row["session_duration_vs_mean_7D"] = (
        row["session_duration"] / (baseline["session_duration_mean_7D"] + eps)
    )

    row["browser_change_flag"] = int(
        row["browser_type"].iloc[0] != baseline["last_browser_type"]
    )

    return row


def run_decision_engine(row):
    """
    Computes risk score, severity, and explanation for a single enriched session row.
    """

    auth_risk = 0
    data_risk = 0
    context_risk = 0
    reasons = []

    # Authentication behavior
    if row["failed_logins_vs_mean_7D"] > 3:
        auth_risk += 25
        reasons.append("Failed login attempts significantly exceed normal behavior")

    if row["login_attempts_vs_mean_7D"] > 3:
        auth_risk += 20
        reasons.append("Login attempt frequency is unusually high")

    # Data access behavior
    if row["data_volume_vs_mean_7D"] > 4:
        data_risk += 30
        reasons.append("Data transfer volume far exceeds historical average")

    # Contextual signals
    if row["unusual_time_access"] == 1:
        context_risk += 10
        reasons.append("Access occurred at an unusual time")

    if row["browser_change_flag"] == 1:
        context_risk += 10
        reasons.append("Browser changed compared to previous sessions")

    # Final aggregation
    total_risk = auth_risk + data_risk + context_risk

    if total_risk >= 60:
        severity = "HIGH"
        flag = True
    elif total_risk >= 30:
        severity = "MEDIUM"
        flag = True
    else:
        severity = "LOW"
        flag = False
    ts = pd.to_datetime(row["timestamp"], utc=True, errors="coerce")
    ts_iso = ts.isoformat() if ts is not pd.NaT else None
    return {
        "user_id": row["user_id"],
        "timestamp": ts_iso,
        "risk_score": total_risk,
        "severity": severity,
        "flag": flag,
        "reason": reasons[0]
    }

def process_new_session(new_session_df, historical_df):
    """
    Processes a single new session using historical context.
    Does NOT modify historical_df.
    """

    user_id = new_session_df.iloc[0]["user_id"]

    # Fetch historical context
    user_history = historical_df[historical_df["user_id"] == user_id]

    # Extract baseline
    baseline = compute_user_baseline(user_history)

    # Add deviation features
    enriched_session = add_deviation_features(new_session_df, baseline)

    # Run risk & decision logic
    result = run_decision_engine(enriched_session.iloc[0])
    return result