# Rasch Counter (2PL IRT Enabled)

Telegram bot for IRT-based test analysis from Excel (0/1 responses). Parses input, estimates ability (θ), item difficulty (β), and discrimination (a) with a 2PL model, assigns grades, and exports Excel/PDF with charts.

## What’s new

- 2PL model: p_ij = sigmoid(a_j · (θ_i − β_j))
- Stable MLE with L2 regularization to avoid extreme inflation
- Deterministic ranking ties broken using difficult-item correctness (display-only)
- Extreme caps removed; results rely on the model instead of hard limits

## Setup

1) Python 3.11+
2) Install requirements:
```bash
pip install -r requirements.txt
```

## Run (local)

```bash
export TELEGRAM_TOKEN=YOUR_TOKEN
python3 telegram_bot.py
```

## Input

- Excel: first column = Student ID/Name; remaining columns = 0/1 answers.

## Outputs

- In-bot: grade distribution, stats, item difficulty charts
- Files: Excel (results + charts), simplified Excel, PDF report

## Model details

- Estimation: joint MLE for θ, β, a with small L2 priors (ridge)
- Identification: θ mean-centered; a constrained to [0.3, 3.0]
- Standard Score (T): 50 + 10·Z, where Z is θ standardized within dataset
- Grades: A+/A/B+/B/C+/C/NC thresholds based on T-score

## Notes

- If you need strictly monotonic score separation even with identical raw totals, consider 2PL (already enabled) or add section-level features. Current ranks are deterministic even when T is equal.
