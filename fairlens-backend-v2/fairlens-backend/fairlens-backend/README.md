# FairLens Backend — FastAPI

AI-powered bias detection and mitigation API.

## Quick Start

```bash
# 1. Clone / enter the directory
cd fairlens-backend

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
copy .env.example .env       # Windows
# cp .env.example .env       # Mac/Linux
# Edit .env and add your GEMINI_API_KEY

# 5. Run the server
uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000/docs** to explore the interactive API.

---

## API Endpoints

### `POST /analyze`
Upload a dataset and get a full bias audit.

**Form fields:**
| Field | Type | Description |
|---|---|---|
| `file` | File | CSV, JSON, or Parquet dataset |
| `target_column` | string | Column to predict (e.g. `two_year_recid`) |
| `protected_attributes` | JSON array | e.g. `["race","sex"]` |
| `positive_label` | string | Value = positive outcome (default `"1"`) |

**Example (curl):**
```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@datasets/compas.csv" \
  -F "target_column=two_year_recid" \
  -F 'protected_attributes=["race","sex"]' \
  -F "positive_label=1"
```

**Returns:** `AnalysisResult` with:
- `analysis_id` — use this in /mitigate and /report
- `metrics` — DPD, EOD, DIR, accuracy, severity
- `feature_importances` — top SHAP-ranked features
- `gemini_explanation` — plain-English summary
- `data_profile` — row/column stats, class balance

---

### `POST /mitigate`
Apply a bias mitigation strategy to a prior analysis.

**Body (JSON):**
```json
{
  "analysis_id": "...",
  "strategy": "threshold_optimizer",
  "target_column": "two_year_recid",
  "protected_attributes": ["race", "sex"],
  "positive_label": "1"
}
```

**Strategies:**
| Strategy | Type | How it works |
|---|---|---|
| `reweighing` | Pre-processing | Reweights training samples per group |
| `threshold_optimizer` | Post-processing | Finds per-group decision thresholds |
| `correlation_removal` | Pre-processing | Drops features correlated with protected attrs |

---

### `POST /report`
Generate a PDF compliance report.

**Body (JSON):**
```json
{
  "analysis_id": "...",
  "include_mitigation": true
}
```

Returns a downloadable `application/pdf` file.

---

## Project Structure

```
fairlens-backend/
├── main.py                  # FastAPI app + routes
├── requirements.txt
├── .env.example
├── datasets/
│   └── compas.csv           # Sample dataset for testing
├── routers/
│   ├── analyze.py           # POST /analyze
│   ├── mitigate.py          # POST /mitigate
│   └── report.py            # POST /report
├── core/
│   ├── profiler.py          # Dataset loading + profiling
│   ├── encoder.py           # Feature encoding
│   ├── bias_engine.py       # Fairness metric computation
│   ├── explainer.py         # SHAP feature importances
│   ├── mitigator.py         # Mitigation strategies
│   ├── gemini.py            # Google Gemini integration
│   ├── reporter.py          # PDF generation
│   └── store.py             # In-memory analysis store
└── models/
    └── schemas.py           # Pydantic request/response models
```

---

## Fairness Metrics

| Metric | Formula | Fair threshold |
|---|---|---|
| Demographic Parity Difference | max(P(Ŷ=1\|A=g)) − min(P(Ŷ=1\|A=g)) | < 0.10 |
| Equalized Odds Difference | max(TPR diff, FPR diff) across groups | < 0.10 |
| Disparate Impact Ratio | min_rate / max_rate | > 0.80 |

---

## Google Gemini Setup

1. Get a free API key at [aistudio.google.com](https://aistudio.google.com)
2. Add it to `.env`:
   ```
   GEMINI_API_KEY=AIza...
   ```
3. The API gracefully degrades to template explanations if the key is missing.

---

## Sample Datasets

| Dataset | Domain | Protected attrs | Target |
|---|---|---|---|
| `compas.csv` | Criminal justice | race, sex | two_year_recid |
| UCI Adult Income | Employment | race, sex, age | income |
| HMDA Mortgage | Finance | race, sex | loan_approved |

UCI Adult: https://archive.ics.uci.edu/dataset/2/adult
