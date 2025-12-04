#!/usr/bin/env python3
"""
QA Test Suite for Health Dashboard Streamlit App
Tests core functionality, imports, model loading, and prediction logic.
"""

import sys
from pathlib import Path
import traceback

# Add src to path
ROOT = Path(__file__).parent
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

TEST_RESULTS = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def test(name, func):
    """Run a test and record results."""
    try:
        result = func()
        if result:
            TEST_RESULTS["passed"].append(name)
            print(f"✅ PASS: {name}")
        else:
            TEST_RESULTS["failed"].append(name)
            print(f"❌ FAIL: {name}")
    except Exception as e:
        TEST_RESULTS["failed"].append(f"{name} (Error: {str(e)})")
        print(f"❌ FAIL: {name} - {str(e)}")
        traceback.print_exc()

def test_imports():
    """Test 1: All required imports work."""
    try:
        import json, os, joblib, numpy, pandas, streamlit
        from preprocess import preprocess_features, FEATURE_COLS
        return True
    except Exception:
        return False

def test_model_artifacts_exist():
    """Test 2: Model artifacts exist."""
    model_path = ROOT / "model" / "model.joblib"
    scaler_path = ROOT / "model" / "scaler.joblib"
    return model_path.exists() and scaler_path.exists()

def test_load_artifacts():
    """Test 3: Can load model and scaler."""
    try:
        import joblib
        model_path = ROOT / "model" / "model.joblib"
        scaler_path = ROOT / "model" / "scaler.joblib"
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        return model is not None and scaler is not None
    except Exception:
        return False

def test_feature_cols():
    """Test 4: FEATURE_COLS is defined and has expected features."""
    try:
        from preprocess import FEATURE_COLS
        expected = ["age", "sex", "trestbps", "chol", "fbs", "thalach", "exang", "oldpeak"]
        return all(f in FEATURE_COLS for f in expected) and len(FEATURE_COLS) == 8
    except Exception:
        return False

def test_preprocess_single_input():
    """Test 5: Preprocess single input row."""
    try:
        import pandas as pd
        from preprocess import preprocess_features, FEATURE_COLS
        import joblib
        
        # Load scaler
        scaler_path = ROOT / "model" / "scaler.joblib"
        scaler = joblib.load(scaler_path)
        
        # Create test input
        test_data = {
            "age": 54,
            "sex": 1,
            "trestbps": 130,
            "chol": 246,
            "fbs": 0,
            "thalach": 150,
            "exang": 0,
            "oldpeak": 1.0
        }
        df = pd.DataFrame([test_data])
        
        # Preprocess
        X, y, _ = preprocess_features(df, fit_scaler=False, scaler=scaler)
        
        # Check output shape
        return X.shape[0] == 1 and X.shape[1] == len(FEATURE_COLS)
    except Exception:
        traceback.print_exc()
        return False

def test_model_predict():
    """Test 6: Model can make predictions."""
    try:
        import pandas as pd
        import joblib
        from preprocess import preprocess_features, FEATURE_COLS
        
        # Load artifacts
        model_path = ROOT / "model" / "model.joblib"
        scaler_path = ROOT / "model" / "scaler.joblib"
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        
        # Create test input
        test_data = {
            "age": 54,
            "sex": 1,
            "trestbps": 130,
            "chol": 246,
            "fbs": 0,
            "thalach": 150,
            "exang": 0,
            "oldpeak": 1.0
        }
        df = pd.DataFrame([test_data])
        
        # Preprocess and predict
        X, _, _ = preprocess_features(df, fit_scaler=False, scaler=scaler)
        proba = model.predict_proba(X)
        
        # Check output
        return proba.shape[0] == 1 and proba.shape[1] == 2 and 0 <= proba[0, 1] <= 1
    except Exception:
        traceback.print_exc()
        return False

def test_shap_availability():
    """Test 7: SHAP is available (optional)."""
    try:
        import shap
        return True
    except ImportError:
        TEST_RESULTS["warnings"].append("SHAP not installed (optional feature)")
        return True  # Not a failure, just a warning

def test_batch_preprocessing():
    """Test 8: Can preprocess multiple rows."""
    try:
        import pandas as pd
        import joblib
        from preprocess import preprocess_features
        
        scaler_path = ROOT / "model" / "scaler.joblib"
        scaler = joblib.load(scaler_path)
        
        # Create multiple test inputs
        test_data = [
            {"age": 54, "sex": 1, "trestbps": 130, "chol": 246, "fbs": 0, "thalach": 150, "exang": 0, "oldpeak": 1.0},
            {"age": 45, "sex": 0, "trestbps": 120, "chol": 200, "fbs": 1, "thalach": 160, "exang": 1, "oldpeak": 0.5}
        ]
        df = pd.DataFrame(test_data)
        
        X, _, _ = preprocess_features(df, fit_scaler=False, scaler=scaler)
        return X.shape[0] == 2
    except Exception:
        traceback.print_exc()
        return False

def test_input_validation():
    """Test 9: Input validation edge cases."""
    try:
        import pandas as pd
        import joblib
        from preprocess import preprocess_features
        
        scaler_path = ROOT / "model" / "scaler.joblib"
        scaler = joblib.load(scaler_path)
        
        # Test with missing column (should be handled)
        test_data = {"age": 50, "sex": 1}  # Missing other columns
        df = pd.DataFrame([test_data])
        
        # Should handle gracefully (fill missing with NaN, then impute)
        X, _, _ = preprocess_features(df, fit_scaler=False, scaler=scaler)
        return X.shape[0] == 1
    except Exception:
        return False

def test_metrics_file():
    """Test 10: Metrics file exists and is valid JSON."""
    try:
        import json
        metrics_path = ROOT / "model" / "metrics.json"
        if metrics_path.exists():
            with open(metrics_path, "r") as f:
                metrics = json.load(f)
            return "roc_auc" in metrics
        else:
            TEST_RESULTS["warnings"].append("metrics.json not found (optional)")
            return True
    except Exception:
        return False

def main():
    """Run all QA tests."""
    print("=" * 60)
    print("QA Test Suite for Health Dashboard Streamlit App")
    print("=" * 60)
    print()
    
    # Run tests
    test("Test 1: Imports", test_imports)
    test("Test 2: Model artifacts exist", test_model_artifacts_exist)
    test("Test 3: Load artifacts", test_load_artifacts)
    test("Test 4: FEATURE_COLS definition", test_feature_cols)
    test("Test 5: Preprocess single input", test_preprocess_single_input)
    test("Test 6: Model prediction", test_model_predict)
    test("Test 7: SHAP availability", test_shap_availability)
    test("Test 8: Batch preprocessing", test_batch_preprocessing)
    test("Test 9: Input validation", test_input_validation)
    test("Test 10: Metrics file", test_metrics_file)
    
    # Summary
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {len(TEST_RESULTS['passed'])}")
    print(f"❌ Failed: {len(TEST_RESULTS['failed'])}")
    print(f"⚠️  Warnings: {len(TEST_RESULTS['warnings'])}")
    print()
    
    if TEST_RESULTS['failed']:
        print("Failed tests:")
        for f in TEST_RESULTS['failed']:
            print(f"  - {f}")
        print()
    
    if TEST_RESULTS['warnings']:
        print("Warnings:")
        for w in TEST_RESULTS['warnings']:
            print(f"  - {w}")
        print()
    
    # Exit code
    exit_code = 0 if len(TEST_RESULTS['failed']) == 0 else 1
    print(f"Exit code: {exit_code}")
    return exit_code

if __name__ == "__main__":
    exit(main())

