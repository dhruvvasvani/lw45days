# Customer Churn Predictor

Hyperparameter-tuned, cross-validated Random Forest (CV ROC-AUC ≈ 0.85,
test ROC-AUC ≈ 0.83) trained on the IBM Telco Customer Churn dataset
(7,043 customers), refit on full data for deployment. Streamlit frontend:

- **Single customer** — fill a form, get instant churn probability.
- **Bulk CSV upload** — required schema shown up front (columns, types,
  allowed values) + downloadable template. Uploaded files are validated
  against the training schema (missing columns, bad numeric values,
  unknown categories, out-of-range values) and **auto-rejected with a
  clear reason** if they don't match — no silent bad predictions.

## Run locally

```
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL Streamlit prints (usually http://localhost:8501).

## Retrain the model

`telco.csv` (training data) and `train_model.py` are included.

```
python train_model.py
```

Regenerates `model.pkl` and `feature_order.pkl`.

## CSV upload format

Required columns (case-sensitive), `customerID` and `Churn` optional/ignored:

gender, SeniorCitizen, Partner, Dependents, tenure, PhoneService,
MultipleLines, InternetService, OnlineSecurity, OnlineBackup,
DeviceProtection, TechSupport, StreamingTV, StreamingMovies, Contract,
PaperlessBilling, PaymentMethod, MonthlyCharges, TotalCharges
