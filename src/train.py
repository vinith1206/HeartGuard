import os
import json
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from preprocess import load_data, preprocess_features
from utils import train_test_split_df, evaluate_model, save_artifacts


def main():
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "heart.csv")
    model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "model")
    print(f"Loading data from: {data_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Dataset not found at {data_path}. Please place the UCI Heart CSV at this path."
        )

    df = load_data(data_path)
    print(f"Data shape: {df.shape}")

    # Preprocess with scaler fitting
    X, y, scaler = preprocess_features(df, fit_scaler=True)
    print(f"Features shape after preprocess: {X.shape}")

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split_df(X, y, test_size=0.2, random_state=42, stratify=True)

    # Model
    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    print("Training RandomForestClassifier...")
    clf.fit(X_train, y_train)

    # Evaluate
    print("Evaluating model...")
    metrics = evaluate_model(clf, X_test, y_test)
    for k, v in metrics.items():
        if k != "confusion_matrix":
            print(f"{k}: {v:.4f}")
        else:
            print(f"{k}: {v}")

    # Save artifacts
    print(f"Saving artifacts to: {model_dir}")
    save_artifacts(clf, scaler, path=model_dir, metrics=metrics)
    print("Artifacts saved: model.joblib, scaler.joblib, metrics.json")


if __name__ == "__main__":
    main()


