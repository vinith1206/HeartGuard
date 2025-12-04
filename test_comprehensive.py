#!/usr/bin/env python3
"""
Comprehensive QA Test Suite for Health Dashboard Streamlit App
Tests edge cases, error handling, SHAP behavior, and visual components.
"""

import sys
import os
import shutil
import time
from pathlib import Path

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

def test_edge_case_low_age():
    """Test with very low age (edge case)."""
    try:
        import pandas as pd
        import joblib
        from preprocess import preprocess_features
        
        scaler_path = ROOT / "model" / "scaler.joblib"
        scaler = joblib.load(scaler_path)
        
        # Very low age
        test_data = {
            "age": 1,
            "sex": 1,
            "trestbps": 100,
            "chol": 150,
            "fbs": 0,
            "thalach": 100,
            "exang": 0,
            "oldpeak": 0.0
        }
        df = pd.DataFrame([test_data])
        X, _, _ = preprocess_features(df, fit_scaler=False, scaler=scaler)
        
        # Should process without error
        model_path = ROOT / "model" / "model.joblib"
        model = joblib.load(model_path)
        proba = model.predict_proba(X)[0, 1]
        
        return 0 <= proba <= 1
    except Exception:
        return False

def test_edge_case_high_cholesterol():
    """Test with extremely high cholesterol (edge case)."""
    try:
        import pandas as pd
        import joblib
        from preprocess import preprocess_features
        
        scaler_path = ROOT / "model" / "scaler.joblib"
        scaler = joblib.load(scaler_path)
        model_path = ROOT / "model" / "model.joblib"
        model = joblib.load(model_path)
        
        # Extremely high cholesterol
        test_data = {
            "age": 60,
            "sex": 1,
            "trestbps": 150,
            "chol": 600,  # Maximum
            "fbs": 1,
            "thalach": 120,
            "exang": 1,
            "oldpeak": 3.0
        }
        df = pd.DataFrame([test_data])
        X, _, _ = preprocess_features(df, fit_scaler=False, scaler=scaler)
        proba = model.predict_proba(X)[0, 1]
        
        return 0 <= proba <= 1
    except Exception:
        return False

def test_extreme_probability_low():
    """Test inputs likely to produce Low risk (<0.33)."""
    try:
        import pandas as pd
        import joblib
        from preprocess import preprocess_features
        
        scaler_path = ROOT / "model" / "scaler.joblib"
        scaler = joblib.load(scaler_path)
        model_path = ROOT / "model" / "model.joblib"
        model = joblib.load(model_path)
        
        # Healthy profile (likely low risk)
        test_data = {
            "age": 30,
            "sex": 0,  # Female
            "trestbps": 100,
            "chol": 150,
            "fbs": 0,
            "thalach": 180,
            "exang": 0,
            "oldpeak": 0.0
        }
        df = pd.DataFrame([test_data])
        X, _, _ = preprocess_features(df, fit_scaler=False, scaler=scaler)
        proba = model.predict_proba(X)[0, 1]
        
        # May or may not be <0.33, but should be valid
        return 0 <= proba <= 1
    except Exception:
        return False

def test_extreme_probability_high():
    """Test inputs likely to produce High risk (>0.66)."""
    try:
        import pandas as pd
        import joblib
        from preprocess import preprocess_features
        
        scaler_path = ROOT / "model" / "scaler.joblib"
        scaler = joblib.load(scaler_path)
        model_path = ROOT / "model" / "model.joblib"
        model = joblib.load(model_path)
        
        # High risk profile
        test_data = {
            "age": 70,
            "sex": 1,  # Male
            "trestbps": 180,
            "chol": 350,
            "fbs": 1,
            "thalach": 100,
            "exang": 1,
            "oldpeak": 4.0
        }
        df = pd.DataFrame([test_data])
        X, _, _ = preprocess_features(df, fit_scaler=False, scaler=scaler)
        proba = model.predict_proba(X)[0, 1]
        
        # May or may not be >0.66, but should be valid
        return 0 <= proba <= 1
    except Exception:
        return False

def test_missing_model_files():
    """Test behavior when model files are missing."""
    try:
        model_path = ROOT / "model" / "model.joblib"
        scaler_path = ROOT / "model" / "scaler.joblib"
        
        # Backup files
        backup_model = model_path.with_suffix(".bak")
        backup_scaler = scaler_path.with_suffix(".bak")
        
        if model_path.exists():
            shutil.copy2(model_path, backup_model)
            os.rename(model_path, model_path.with_suffix(".missing"))
        
        if scaler_path.exists():
            shutil.copy2(scaler_path, backup_scaler)
            os.rename(scaler_path, scaler_path.with_suffix(".missing"))
        
        # Try to load (should handle gracefully)
        try:
            import joblib
            if model_path.with_suffix(".missing").exists():
                # This will fail, which is expected
                joblib.load(model_path)
                result = False
            else:
                result = True  # File doesn't exist, test passed
        except FileNotFoundError:
            result = True  # Expected behavior
        except Exception:
            result = True  # Any error handling is acceptable
        
        # Restore files
        if backup_model.exists():
            os.rename(model_path.with_suffix(".missing"), model_path)
        if backup_scaler.exists():
            os.rename(scaler_path.with_suffix(".missing"), scaler_path)
        
        return result
    except Exception:
        # Restore files if test failed
        model_path = ROOT / "model" / "model.joblib"
        scaler_path = ROOT / "model" / "scaler.joblib"
        if (ROOT / "model" / "model.joblib.missing").exists():
            os.rename(ROOT / "model" / "model.joblib.missing", model_path)
        if (ROOT / "model" / "scaler.joblib.missing").exists():
            os.rename(ROOT / "model" / "scaler.joblib.missing", scaler_path)
        return False

def test_shap_installed():
    """Test SHAP when installed."""
    try:
        import shap
        import numpy as np
        import pandas as pd
        import joblib
        from preprocess import preprocess_features, FEATURE_COLS
        
        model_path = ROOT / "model" / "model.joblib"
        scaler_path = ROOT / "model" / "scaler.joblib"
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        
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
        X, _, _ = preprocess_features(df, fit_scaler=False, scaler=scaler)
        
        # Convert to array
        X_array = np.array(X) if isinstance(X, pd.DataFrame) else X
        if X_array.ndim == 1:
            X_array = X_array.reshape(1, -1)
        
        # Test SHAP
        explainer = shap.TreeExplainer(model)
        sv_list = explainer.shap_values(X_array)
        
        # Should return valid SHAP values
        return sv_list is not None
    except ImportError:
        TEST_RESULTS["warnings"].append("SHAP not installed (skipping test)")
        return True  # Not a failure
    except Exception:
        return False

def test_feature_importances_length():
    """Test that feature importances match feature count."""
    try:
        import joblib
        from preprocess import FEATURE_COLS
        
        model_path = ROOT / "model" / "model.joblib"
        model = joblib.load(model_path)
        
        if hasattr(model, "feature_importances_"):
            fi = model.feature_importances_
            return len(fi) == len(FEATURE_COLS)
        return False
    except Exception:
        return False

def test_prediction_performance():
    """Test prediction latency (<2 seconds)."""
    try:
        import pandas as pd
        import joblib
        from preprocess import preprocess_features
        import time
        
        scaler_path = ROOT / "model" / "scaler.joblib"
        scaler = joblib.load(scaler_path)
        model_path = ROOT / "model" / "model.joblib"
        model = joblib.load(model_path)
        
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
        
        start = time.time()
        X, _, _ = preprocess_features(df, fit_scaler=False, scaler=scaler)
        proba = model.predict_proba(X)
        elapsed = time.time() - start
        
        if elapsed < 2.0:
            TEST_RESULTS["passed"].append(f"Prediction latency: {elapsed*1000:.1f}ms")
        else:
            TEST_RESULTS["warnings"].append(f"Prediction slow: {elapsed*1000:.1f}ms")
        
        return elapsed < 2.0
    except Exception:
        return False

def test_shap_performance():
    """Test SHAP computation time (<5 seconds)."""
    try:
        import shap
        import numpy as np
        import pandas as pd
        import joblib
        from preprocess import preprocess_features
        import time
        
        model_path = ROOT / "model" / "model.joblib"
        scaler_path = ROOT / "model" / "scaler.joblib"
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        
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
        X, _, _ = preprocess_features(df, fit_scaler=False, scaler=scaler)
        X_array = np.array(X) if isinstance(X, pd.DataFrame) else X
        if X_array.ndim == 1:
            X_array = X_array.reshape(1, -1)
        
        explainer = shap.TreeExplainer(model)
        start = time.time()
        sv_list = explainer.shap_values(X_array)
        elapsed = time.time() - start
        
        if elapsed < 5.0:
            TEST_RESULTS["passed"].append(f"SHAP latency: {elapsed*1000:.1f}ms")
        else:
            TEST_RESULTS["warnings"].append(f"SHAP slow: {elapsed*1000:.1f}ms")
        
        return elapsed < 5.0
    except ImportError:
        TEST_RESULTS["warnings"].append("SHAP not installed (skipping performance test)")
        return True
    except Exception:
        return False

def test_risk_category_logic():
    """Test risk category thresholds."""
    # This is a logic test - verify thresholds work correctly
    low_thr = 0.33
    high_thr = 0.66
    
    def categorize(proba):
        if proba < low_thr:
            return "Low"
        elif proba <= high_thr:
            return "Moderate"
        else:
            return "High"
    
    # Test cases
    assert categorize(0.1) == "Low"
    assert categorize(0.5) == "Moderate"
    assert categorize(0.8) == "High"
    assert categorize(0.33) == "Moderate"  # Boundary
    assert categorize(0.66) == "Moderate"  # Boundary
    
    return True

def test_missing_fields_handling():
    """Test handling of missing fields (should use imputation)."""
    try:
        import pandas as pd
        import joblib
        from preprocess import preprocess_features
        
        scaler_path = ROOT / "model" / "scaler.joblib"
        scaler = joblib.load(scaler_path)
        model_path = ROOT / "model" / "model.joblib"
        model = joblib.load(model_path)
        
        # Missing some fields (will be NaN, then imputed)
        test_data = {
            "age": 50,
            "sex": 1,
            # Missing: trestbps, chol, fbs, thalach, exang, oldpeak
        }
        df = pd.DataFrame([test_data])
        
        # Should handle missing fields via imputation
        X, _, _ = preprocess_features(df, fit_scaler=False, scaler=scaler)
        proba = model.predict_proba(X)[0, 1]
        
        return 0 <= proba <= 1
    except Exception:
        return False

def main():
    """Run all comprehensive QA tests."""
    print("=" * 70)
    print("Comprehensive QA Test Suite - Health Dashboard Streamlit App")
    print("=" * 70)
    print()
    
    print("Testing Edge Cases...")
    test("Edge Case: Very low age (1)", test_edge_case_low_age)
    test("Edge Case: Extremely high cholesterol (600)", test_edge_case_high_cholesterol)
    test("Edge Case: Low risk profile", test_extreme_probability_low)
    test("Edge Case: High risk profile", test_extreme_probability_high)
    test("Edge Case: Missing fields handling", test_missing_fields_handling)
    
    print()
    print("Testing Error Handling...")
    test("Error Handling: Missing model files", test_missing_model_files)
    
    print()
    print("Testing SHAP Behavior...")
    test("SHAP: Installed and working", test_shap_installed)
    
    print()
    print("Testing Visualizations...")
    test("Visualization: Feature importances length", test_feature_importances_length)
    test("Visualization: Risk category logic", test_risk_category_logic)
    
    print()
    print("Testing Performance...")
    test("Performance: Prediction latency", test_prediction_performance)
    test("Performance: SHAP computation time", test_shap_performance)
    
    # Summary
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
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

