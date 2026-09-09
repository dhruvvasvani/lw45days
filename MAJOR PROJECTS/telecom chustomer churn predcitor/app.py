import streamlit as st
import pandas as pd
import joblib
st.set_page_config(page_title="Customer Churn Predictor", page_icon="", layout="centered")
@st.cache_resource
def load_artifacts():
    model = joblib.load("model.pkl")
    feature_order = joblib.load("feature_order.pkl")
    schema = joblib.load("schema.pkl")
    try:
        meta = joblib.load("model_meta.pkl")
    except FileNotFoundError:
        meta = {"model_name": "RandomForest", "cv_roc_auc": None, "test_roc_auc": None}
    return model, feature_order, schema, meta
model, FEATURES, SCHEMA, META = load_artifacts()
st.title(" Customer Churn Predictor")
auc_txt = f" · CV ROC-AUC {META['cv_roc_auc']:.3f}" if META.get("cv_roc_auc") else ""
st.caption(f"Pretrained {META['model_name']} on the IBM Telco Customer Churn dataset (7,043 customers){auc_txt}.")
mode = st.radio("Input mode", ["Single customer (form)", "Bulk CSV upload"], horizontal=True)
YESNO = ["Yes", "No"]
YESNO_NET = ["Yes", "No", "No internet service"]
YESNO_PHONE = ["Yes", "No", "No phone service"]
def predict(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "TotalCharges" in df.columns:
        df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df = df.reindex(columns=FEATURES)
    proba = model.predict_proba(df)[:, 1]
    pred = model.predict(df)
    out = df.copy()
    out["Churn Probability"] = (proba * 100).round(1)
    out["Prediction"] = ["Likely to Churn" if p == 1 else "Likely to Stay" for p in pred]
    return out
def validate_csv(raw: pd.DataFrame):
    """Strict validation against the training schema. Returns (ok, errors)."""
    errors = []
    missing = [c for c in SCHEMA["columns"] if c not in raw.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return False, errors
    if len(raw) == 0:
        errors.append("File has no data rows.")
        return False, errors
    for col in SCHEMA["numeric"]:
        parsed = pd.to_numeric(raw[col], errors="coerce")
        bad = parsed.isna() & raw[col].notna() & (raw[col].astype(str).str.strip() != "")
        if bad.sum() > 0:
            errors.append(f"Column '{col}' has {int(bad.sum())} non-numeric value(s).")
    tc_parsed = pd.to_numeric(raw["TotalCharges"], errors="coerce")
    fully_missing_tc = tc_parsed.isna().sum()
    if fully_missing_tc > 0.3 * len(raw):
        errors.append(
            f"'TotalCharges' is missing/unparseable for {fully_missing_tc}/{len(raw)} rows — too many to trust."
        )
    for col in SCHEMA["categorical"]:
        allowed = set(SCHEMA["allowed_values"][col])
        present = set(raw[col].dropna().astype(str).unique())
        unknown = present - allowed
        if unknown:
            errors.append(
                f"Column '{col}' has unrecognized value(s): {', '.join(sorted(unknown)[:5])}"
                + (" ..." if len(unknown) > 5 else "")
                + f" — allowed: {', '.join(map(str, allowed))}"
            )
    for col in ["tenure", "MonthlyCharges", "TotalCharges"]:
        lo, hi = SCHEMA["numeric_ranges"][col]
        parsed = pd.to_numeric(raw[col], errors="coerce")
        out_of_range = parsed.dropna()[(parsed.dropna() < 0) | (parsed.dropna() > hi * 3)]
        if len(out_of_range) > 0:
            errors.append(f"Column '{col}' has {len(out_of_range)} value(s) far outside a plausible range.")
    return len(errors) == 0, errors
if mode == "Single customer (form)":
    with st.form("churn_form"):
        st.subheader("Customer Details")
        c1, c2 = st.columns(2)
        with c1:
            gender = st.selectbox("Gender", ["Female", "Male"])
            senior = st.selectbox("Senior Citizen", ["No", "Yes"])
            partner = st.selectbox("Partner", YESNO)
            dependents = st.selectbox("Dependents", YESNO)
            tenure = st.number_input("Tenure (months)", 0, 100, 12)
            phone = st.selectbox("Phone Service", YESNO)
            multi_lines = st.selectbox("Multiple Lines", YESNO_PHONE)
        with c2:
            internet = st.selectbox("Internet Service", ["DSL", "Fiber optic", "No"])
            online_sec = st.selectbox("Online Security", YESNO_NET)
            online_backup = st.selectbox("Online Backup", YESNO_NET)
            device_prot = st.selectbox("Device Protection", YESNO_NET)
            tech_support = st.selectbox("Tech Support", YESNO_NET)
            stream_tv = st.selectbox("Streaming TV", YESNO_NET)
            stream_movies = st.selectbox("Streaming Movies", YESNO_NET)
        st.subheader("Account")
        c3, c4 = st.columns(2)
        with c3:
            contract = st.selectbox("Contract", ["Month-to-month", "One year", "Two year"])
            paperless = st.selectbox("Paperless Billing", YESNO)
        with c4:
            payment = st.selectbox("Payment Method", [
                "Electronic check", "Mailed check",
                "Bank transfer (automatic)", "Credit card (automatic)",
            ])
            monthly = st.number_input("Monthly Charges ($)", 0.0, 500.0, 70.0, step=0.5)
            total = st.number_input("Total Charges ($)", 0.0, 20000.0, float(monthly * max(tenure, 1)), step=1.0)
        submitted = st.form_submit_button("Predict Churn", use_container_width=True)
    if submitted:
        row = {
            "gender": gender, "SeniorCitizen": 1 if senior == "Yes" else 0,
            "Partner": partner, "Dependents": dependents, "tenure": tenure,
            "PhoneService": phone, "MultipleLines": multi_lines,
            "InternetService": internet, "OnlineSecurity": online_sec,
            "OnlineBackup": online_backup, "DeviceProtection": device_prot,
            "TechSupport": tech_support, "StreamingTV": stream_tv,
            "StreamingMovies": stream_movies, "Contract": contract,
            "PaperlessBilling": paperless, "PaymentMethod": payment,
            "MonthlyCharges": monthly, "TotalCharges": total,
        }
        result = predict(pd.DataFrame([row]))
        prob = result["Churn Probability"].iloc[0]
        label = result["Prediction"].iloc[0]
        if label == "Likely to Churn":
            st.error(f" {label} — {prob}% probability")
        else:
            st.success(f" {label} — {prob}% churn probability")
        st.progress(min(int(prob), 100))
else:
    st.subheader("Upload CSV")
    with st.expander(" Required CSV format (click to expand)", expanded=True):
        st.markdown(
            "Your file **must** contain every column below, spelled exactly as shown. "
            "`customerID` and `Churn` are optional and ignored if present."
        )
        schema_rows = []
        for col in SCHEMA["numeric"]:
            lo, hi = SCHEMA["numeric_ranges"][col]
            hint = "0 or 1" if col == "SeniorCitizen" else f"number, e.g. {lo:.0f}–{hi:.0f}"
            schema_rows.append({"Column": col, "Type": "numeric", "Expected values": hint})
        for col in SCHEMA["categorical"]:
            schema_rows.append({
                "Column": col, "Type": "text",
                "Expected values": ", ".join(map(str, SCHEMA["allowed_values"][col])),
            })
        st.dataframe(pd.DataFrame(schema_rows), use_container_width=True, hide_index=True)
        sample = pd.DataFrame([{c: (SCHEMA["allowed_values"][c][0] if c in SCHEMA["categorical"]
                                     else 1) for c in SCHEMA["columns"]}])
        st.download_button(
            "Download a sample template CSV",
            sample.to_csv(index=False).encode("utf-8"),
            "churn_template.csv", "text/csv",
        )
    file = st.file_uploader("Choose a CSV file", type=["csv"])
    if file is not None:
        try:
            raw = pd.read_csv(file)
        except Exception as e:
            st.error(f" File rejected — could not read as CSV: {e}")
            st.stop()
        ok, errors = validate_csv(raw)
        if not ok:
            st.error(" **File rejected.** It doesn't match the required format:")
            for e in errors:
                st.markdown(f"- {e}")
            st.info("Fix the issues above (or download the sample template) and re-upload.")
        else:
            st.success(f" File accepted — {len(raw)} rows validated against schema.")
            result = predict(raw)
            churn_count = (result["Prediction"] == "Likely to Churn").sum()
            st.write(f"**{churn_count} / {len(result)}** customers flagged as likely to churn.")
            st.dataframe(result, use_container_width=True)
            st.download_button(
                "Download predictions as CSV",
                result.to_csv(index=False).encode("utf-8"),
                "churn_predictions.csv",
                "text/csv",
                use_container_width=True,
            )
st.divider()
auc_line = f" · Test ROC-AUC {META['test_roc_auc']:.3f}" if META.get("test_roc_auc") else ""
st.caption(f"Model: {META['model_name']} (hyperparameter-tuned, cross-validated){auc_line} · Built by Dhruv Vasvani")
