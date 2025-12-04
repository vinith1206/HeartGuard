import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

# Simplified, robust feature set commonly available across UCI Heart variants
FEATURE_COLS = [
    "age",
    "sex",
    "trestbps",
    "chol",
    "fbs",
    "thalach",
    "exang",
    "oldpeak",
]
TARGET_COL = "target"

# Candidate column name variants mapped to canonical names
COLUMN_MAP_CANDIDATES = {
    "trestbps": ["trestbps", "restingbp", "trestbp", "restbp", "resting_blood_pressure"],
    "chol": ["chol", "serum_chol", "cholesterol"],
    "thalach": ["thalach", "max_heart_rate", "thalachh", "max_heart_rate_achieved", "maxhr"],
    "oldpeak": ["oldpeak", "st_depression", "st_depress"],
    "exang": ["exang", "exercise_angina", "exAng", "exercise_induced_angina"],
    "fbs": ["fbs", "fasting_blood_sugar", "fasting_bs", "fastingbs"],
    "sex": ["sex", "gender"],
    "age": ["age"],
    "target": ["target", "target_class", "heart_disease", "disease", "output", "hd", "num", "heartdisease"],
}


def map_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    cols = {str(c).lower(): c for c in df.columns}
    name_map = {}
    for std_name, variants in COLUMN_MAP_CANDIDATES.items():
        for v in variants:
            if v.lower() in cols:
                name_map[cols[v.lower()]] = std_name
                break
    if name_map:
        df = df.rename(columns=name_map)
    return df


def load_data(csv_path: str) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"Data file not found at {csv_path}. Please place heart.csv there."
        )
    df = pd.read_csv(csv_path)
    df = map_columns(df)
    return df


def preprocess_features(df: pd.DataFrame, fit_scaler: bool = True, scaler: StandardScaler = None):
    df = df.copy()
    # Separate target if present
    y = None
    if TARGET_COL in df.columns:
        y = df[TARGET_COL].copy()
        df = df.drop(columns=[TARGET_COL])

    # Select available features
    present_features = [c for c in FEATURE_COLS if c in df.columns]
    if not present_features:
        raise ValueError(
            f"No required features found in DataFrame. Expected at least one of: {FEATURE_COLS}"
        )
    X = df[present_features].copy()

    # Impute missing values
    for col in X.columns:
        if X[col].dtype.kind in "biufc":
            med = X[col].median()
            X[col] = X[col].fillna(med)
        else:
            X[col] = X[col].fillna(method="ffill").fillna(method="bfill").fillna(0)

    # Normalize binary fields
    if "sex" in X.columns:
        X["sex"] = X["sex"].map({
            "male": 1, "m": 1, "1": 1, 1: 1,
            "female": 0, "f": 0, "0": 0, 0: 0,
        }).fillna(X["sex"])
        if X["sex"].dtype == object:
            try:
                X["sex"] = X["sex"].astype(float).fillna(0).astype(int)
            except Exception:
                X["sex"] = X["sex"].apply(lambda v: 1 if str(v).lower().strip() in ("male", "m") else 0)

    for bcol in ["fbs", "exang"]:
        if bcol in X.columns:
            X[bcol] = X[bcol].apply(
                lambda v: 1 if (str(v).strip() in ("1", "true", "True") or (isinstance(v, (int, float)) and v == 1)) else 0
            )

    # Convert remaining object columns to numeric or codes
    for col in X.columns:
        if X[col].dtype == object:
            try:
                X[col] = pd.to_numeric(X[col])
            except Exception:
                X[col], _ = pd.factorize(X[col])

    # Scale numeric columns
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    if fit_scaler:
        scaler = StandardScaler()
        X[numeric_cols] = scaler.fit_transform(X[numeric_cols])
    else:
        if scaler is None:
            raise ValueError("fit_scaler=False but no scaler provided.")
        X[numeric_cols] = scaler.transform(X[numeric_cols])

    return X, y, scaler


