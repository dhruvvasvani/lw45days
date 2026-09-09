"""
Train + tune Customer Churn model on IBM Telco Customer Churn dataset.
Uses RandomizedSearchCV over RF + GradientBoosting, picks best by ROC-AUC
cross-val, then evaluates on held-out test set. Also saves a schema
(expected columns, dtypes, allowed categories) so the app can validate
new/uploaded data before ever calling predict.
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, RandomizedSearchCV, StratifiedKFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, roc_auc_score
import joblib
RANDOM_STATE = 42
df = pd.read_csv("telco.csv")
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
before = len(df)
df = df.dropna(subset=["TotalCharges"])
print(f"Dropped {before - len(df)} rows with empty TotalCharges ({(before-len(df))/before:.2%})")
df.drop(columns=["customerID"], inplace=True)
df["Churn"] = df["Churn"].map({"Yes": 1, "No": 0})
y = df["Churn"]
X = df.drop(columns=["Churn"])
NUMERIC = ["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"]
CATEGORICAL = [c for c in X.columns if c not in NUMERIC]
schema = {
    "columns": list(X.columns),
    "numeric": NUMERIC,
    "categorical": CATEGORICAL,
    "allowed_values": {c: sorted(X[c].dropna().unique().tolist()) for c in CATEGORICAL},
    "numeric_ranges": {c: (float(X[c].min()), float(X[c].max())) for c in NUMERIC},
}
joblib.dump(schema, "schema.pkl")
numeric_pipe = Pipeline([
    ("impute", SimpleImputer(strategy="median")),
    ("scale", StandardScaler()),
])
categorical_pipe = Pipeline([
    ("impute", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore")),
])
preprocess = ColumnTransformer([
    ("num", numeric_pipe, NUMERIC),
    ("cat", categorical_pipe, CATEGORICAL),
])
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
)
cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
candidates = {
    "RandomForest": (
        RandomForestClassifier(class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1),
        {
            "clf__n_estimators": [200, 300],
            "clf__max_depth": [8, 10, None],
            "clf__min_samples_leaf": [1, 2, 4],
        },
    ),
}
best_model, best_name, best_score = None, None, -1
for name, (clf, param_dist) in candidates.items():
    pipe = Pipeline([("prep", preprocess), ("clf", clf)])
    search = RandomizedSearchCV(
        pipe, param_dist, n_iter=4, scoring="roc_auc",
        cv=cv, random_state=RANDOM_STATE, n_jobs=2,
    )
    search.fit(X_train, y_train)
    print(f"{name}: best CV ROC-AUC = {search.best_score_:.4f} | params = {search.best_params_}")
    if search.best_score_ > best_score:
        best_model, best_name, best_score = search.best_estimator_, name, search.best_score_
print(f"\nSelected model: {best_name} (CV ROC-AUC = {best_score:.4f})")
pred = best_model.predict(X_test)
proba = best_model.predict_proba(X_test)[:, 1]
print(classification_report(y_test, pred, target_names=["No Churn", "Churn"]))
test_auc = roc_auc_score(y_test, proba)
print("Test ROC-AUC:", round(test_auc, 4))
best_model.fit(X, y)
joblib.dump(best_model, "model.pkl")
joblib.dump(list(X.columns), "feature_order.pkl")
joblib.dump({"model_name": best_name, "cv_roc_auc": best_score, "test_roc_auc": test_auc}, "model_meta.pkl")
print("Saved model.pkl, feature_order.pkl, schema.pkl, model_meta.pkl")
