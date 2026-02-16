<p align="center">
  <h1 align="center"> Context-Aware Security Monitoring Dashboard</h1>
  <h3 align="center">Team ByteShield</h3>
  <p align="center">
     Built for CF4VIT Hackathon <br>
     Sponsored by C-DAC
  </p>
</p>

---

<p align="center">
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge">
  <img src="https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge">
  <img src="https://img.shields.io/badge/Frontend-HTML%20%7C%20CSS%20%7C%20JS-1f2937?style=for-the-badge">
  <img src="https://img.shields.io/badge/Focus-Context%20Aware%20Threat%20Detection-red?style=for-the-badge">
</p>

---

##  Overview

Modern security monitoring systems generate **excessive alerts**, overwhelming security teams with false positives and burying real threats under noise.

The **Context-Aware Security Monitoring Dashboard** solves this by:

- Building **user-specific behavioral baselines**
- Evaluating deviations over rolling time windows
- Scoring threats using contextual signals
- Providing explainable severity classification
- Reducing alert fatigue

Instead of asking:

> “Is this action unusual?”

We ask:

> “Is this unusual for THIS user?”

---

#  Dashboard Preview

## 🔹 Main Dashboard

<p align="center">
  <img src="assets/dashboard.png" width="85%">
</p>

---

##  Security Events Table

<p align="center">
  <img src="assets/events.png" width="85%">
</p>

---

#  System Architecture

```
User Clicks "Simulate New Session"
            ↓
JavaScript Generates Payload
            ↓
POST → /evaluate-session (FastAPI)
            ↓
Fetch Historical Context (SQLite)
            ↓
Compute 7-Day Rolling Baseline
            ↓
Deviation Feature Engineering
            ↓
Decision Engine (Risk + Severity + Explanation)
            ↓
JSON Response
            ↓
Live Dashboard Update
```

---

#  Core Threat Detection Logic

## 1. Behavioral Baseline (7-Day Rolling Window)

Each user has contextual metrics such as:

- login_attempts_mean_7D
- failed_logins_mean_7D
- data_volume_mean_7D
- session_duration_mean_7D
- ip_reputation_score_mean_7D
- last_browser_type

---

## 2. Deviation Analysis

Example:

```
data_volume_vs_mean_7D = current_data_volume / baseline_mean_7D + eps
```

This normalizes behavior relative to user history.

---

## 3. Risk Scoring Engine

Risk is computed across three dimensions:

###  Authentication Risk
- Excess failed logins → +25
- High login frequency → +20

###  Data Risk
- Data volume spike → +30

###  Context Risk
- Unusual access time → +10
- Browser change → +10

---

## 4. Severity Classification

```
Risk >= 60 → HIGH
Risk >= 30 → MEDIUM
Else → LOW
```

Only MEDIUM and HIGH sessions are flagged.

Each alert includes an **explainable reason**.

---

#  Security Design Features

- Context-aware anomaly detection
- Rolling time-window baselining
- Cold-start handling
- Deviation normalization
- Strict API schema validation (Pydantic)
- SQLite WAL journaling
- Indexed database queries
- UTC timestamp normalization
- Safe JSON serialization

---

#  Database Engineering

SQLite indexes were created on:
- user_id
- session_start
- ts_epoch
- (user_id, session_start)

Optimized for fast historical lookups.

---

#  Project Structure

```
.
├── static/
│   └── dashboard.html
├── dataset/
│   └── cybersecurity_intrusion_data.csv
├── app.py
├── main.py
├── raw_data.py
├── clean_data.py
├── client_db.py
├── helper_db.py
├── requirements.txt
├── assets/
│   ├── dashboard.jpeg
│   └── events.jpeg
```

---

#  Installation

## 1. Clone Repository

```
git clone <your-repo-url>
cd <repo-name>
```

## 2. Install Dependencies

```
pip install -r requirements.txt
```

## 3. Run Server

```
uvicorn app:app --reload
```

## 4. Open Dashboard

```
http://127.0.0.1:8000/
```

---

#  Hackathon Context

Built during the **CF4VIT Hackathon (Sponsored by C-DAC)** under the Threat Detection track.

We defined our own focused problem:

> Reducing false positives in behavioral anomaly detection using contextual baselines.

---

#  Impact

This system:

- Learns individual user behavior
- Scores deviations contextually
- Justifies every alert
- Reduces alert fatigue
- Prioritizes meaningful threats

---

#  Team ByteShield

CF4VIT Hackathon Project  
Sponsored by C-DAC  
Focused on intelligent, context-aware cybersecurity systems.

---
