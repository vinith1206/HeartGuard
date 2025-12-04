# Manual Testing Checklist - Health Dashboard Streamlit App

**Date:** November 4, 2024  
**Tester:** Manual QA  
**App URL:** http://localhost:8501

---

## Pre-Testing Setup

- [ ] App is running: `streamlit run app/streamlit_app.py`
- [ ] Browser opened to http://localhost:8501
- [ ] Model artifacts exist: `model/model.joblib` and `model/scaler.joblib`

---

## 1. Launch & Initial Display ✅

- [ ] **Title displays:** "Health Dashboard: Heart Disease Risk Prediction"
- [ ] **Description visible:** "Predict the probability of heart disease using a model trained on the UCI Heart dataset."
- [ ] **No error messages** on initial load
- [ ] **Sidebar visible** with Summary section
- [ ] **Input fields visible** in two-column layout
- [ ] **Footer displays:** "Built by vineeth. For educational purposes only; not a medical device."

---

## 2. UI Component Testing ✅

### Input Fields (Left Column)
- [ ] **Age:** Numeric input, range 18-100, default 54
- [ ] **Resting Blood Pressure (trestbps):** Numeric input, range 80-220, default 130
- [ ] **Fasting Blood Sugar (fbs):** Dropdown, options "No"/"Yes", default "No"
- [ ] **Exercise Induced Angina (exang):** Dropdown, options "No"/"Yes", default "No"

### Input Fields (Right Column)
- [ ] **Sex:** Dropdown, options "Male"/"Female", default "Male"
- [ ] **Cholesterol (chol):** Numeric input, range 100-600, default 246
- [ ] **Max Heart Rate (thalach):** Numeric input, range 60-220, default 150
- [ ] **ST Depression (oldpeak):** Numeric input, range 0.0-6.0, default 1.0, step 0.1

### Sidebar Components
- [ ] **Summary section** shows live JSON of input values
- [ ] **Dataset & Model Info** expander:
  - [ ] Shows dataset info
  - [ ] Shows ROC AUC (e.g., 0.824)
  - [ ] Shows model type (RandomForestClassifier)
- [ ] **Risk Thresholds** section:
  - [ ] Low threshold slider (0.0-0.9, default 0.33)
  - [ ] High threshold slider (0.1-0.99, default 0.66)
  - [ ] Warning shows if low >= high
- [ ] **Batch Predict (CSV)** section:
  - [ ] File uploader for CSV files
  - [ ] "Run Batch Prediction" button

---

## 3. Functional Testing - Single Prediction ✅

### Test Case 1: Default Values (Baseline)
**Inputs:** All defaults (Age=54, Sex=Male, etc.)
- [ ] Click "Predict" button
- [ ] **Result card appears** with:
  - [ ] Predicted probability displayed (e.g., "65.0%")
  - [ ] Risk category shown (Low/Moderate/High)
  - [ ] Colored risk bar visible with indicator
- [ ] **Global Importances tab:**
  - [ ] Bar chart displays
  - [ ] 8 features shown
  - [ ] Chart is readable
- [ ] **SHAP (optional) tab:**
  - [ ] Either SHAP chart OR fallback message
  - [ ] No errors/tracebacks
- [ ] **ROC AUC displayed:** "Model ROC AUC (test): 0.824"

### Test Case 2: Edge Case - Very Low Age
**Inputs:** Age=1, all other defaults
- [ ] Can enter Age=1
- [ ] Click "Predict"
- [ ] Prediction completes successfully
- [ ] Probability is valid (0-100%)
- [ ] Risk category assigned

### Test Case 3: Edge Case - Extremely High Cholesterol
**Inputs:** chol=600, all other defaults
- [ ] Can enter chol=600
- [ ] Click "Predict"
- [ ] Prediction completes successfully
- [ ] Probability is valid
- [ ] Risk category assigned

### Test Case 4: Low Risk Profile
**Inputs:** Age=30, Sex=Female, trestbps=100, chol=150, fbs=No, thalach=180, exang=No, oldpeak=0.0
- [ ] Enter all values
- [ ] Click "Predict"
- [ ] Probability should be relatively low (<33% or Low risk)
- [ ] Risk bar indicator in green zone
- [ ] Risk category = "Low"

### Test Case 5: High Risk Profile
**Inputs:** Age=70, Sex=Male, trestbps=180, chol=350, fbs=Yes, thalach=100, exang=Yes, oldpeak=4.0
- [ ] Enter all values
- [ ] Click "Predict"
- [ ] Probability should be relatively high (>66% or High risk)
- [ ] Risk bar indicator in red zone
- [ ] Risk category = "High"

### Test Case 6: Input Validation
- [ ] **Age field:** Try entering negative number → Should be rejected/clamped
- [ ] **Age field:** Try entering >120 → Should be clamped to 120
- [ ] **Numeric fields:** Try entering text → Should be rejected or show error
- [ ] **Dropdowns:** All options selectable

---

## 4. Risk Bar Visualization ✅

### Color Verification
- [ ] **Low risk (<33%):** Risk bar indicator in GREEN zone
- [ ] **Moderate risk (33-66%):** Risk bar indicator in YELLOW/ORANGE zone
- [ ] **High risk (>66%):** Risk bar indicator in RED zone

### Visual Check
- [ ] Risk bar displays gradient (green → yellow → red)
- [ ] White indicator line shows probability position
- [ ] Bar is readable and not clipped
- [ ] Indicator position matches probability percentage

---

## 5. SHAP Behavior Testing ✅

### With SHAP Installed
- [ ] Click "Predict"
- [ ] Open "SHAP (optional)" tab
- [ ] **SHAP chart displays:**
  - [ ] Horizontal bar chart visible
  - [ ] 8 features shown (or matches available features)
  - [ ] Features sorted by contribution
  - [ ] No errors or tracebacks
- [ ] Caption: "SHAP values show how each feature contributes to this specific prediction."

### Without SHAP (Simulation)
**To test:** `pip uninstall shap -y` then restart app
- [ ] App starts without errors
- [ ] Click "Predict"
- [ ] Open "SHAP (optional)" tab
- [ ] **Fallback message appears:**
  - [ ] Warning: "SHAP is not installed. Install it with: `pip install shap`"
  - [ ] Info: "Showing global feature importances only."
  - [ ] No tracebacks or errors

---

## 6. Feature Importances Visualization ✅

- [ ] **Global Importances tab:**
  - [ ] Bar chart displays correctly
  - [ ] Chart shows 8 features
  - [ ] Features sorted by importance (descending)
  - [ ] Chart is readable, not clipped
  - [ ] Chart matches `model.feature_importances_` length

---

## 7. Batch CSV Prediction Testing ✅

### Test Case 1: Valid CSV
**Create test CSV with columns:** age, sex, trestbps, chol, fbs, thalach, exang, oldpeak
- [ ] Upload CSV file
- [ ] Click "Run Batch Prediction"
- [ ] **Results display:**
  - [ ] Table shows predictions
  - [ ] Columns: original features + probability + prediction + risk_bucket
  - [ ] First 100 rows shown
- [ ] **Download button appears:**
  - [ ] "Download Results CSV" button visible
  - [ ] Clicking downloads file
  - [ ] Downloaded file contains all predictions

### Test Case 2: CSV with Different Column Names
**CSV with:** Age, Sex, RestingBP, Cholesterol, etc.
- [ ] Upload CSV
- [ ] Click "Run Batch Prediction"
- [ ] Column name mapping works (auto-mapped to canonical names)
- [ ] Predictions complete successfully

### Test Case 3: CSV with Missing Columns
**CSV with only:** age, sex
- [ ] Upload CSV
- [ ] Click "Run Batch Prediction"
- [ ] Missing columns handled (imputed or error message shown)
- [ ] App doesn't crash

---

## 8. Error Handling Testing ✅

### Missing Model Files
**Steps:**
1. Stop app
2. Rename `model/model.joblib` → `model/model.joblib.bak`
3. Restart app
4. Verify:
- [ ] App starts without crashing
- [ ] Error message: "Model artifacts not found. Please run training first from the repo root: `python src/train.py`."
- [ ] Red error box displayed
- [ ] App stops gracefully (no further interaction possible)

**Restore:** Rename `model/model.joblib.bak` → `model/model.joblib`

### Invalid Input Types
- [ ] Try entering invalid data in numeric fields
- [ ] App handles gracefully (shows error or rejects input)
- [ ] Error message: "Prediction failed: [error details]"
- [ ] App doesn't crash

### Missing Fields
- [ ] Leave some fields empty (if possible)
- [ ] Click "Predict"
- [ ] App handles missing values (imputation or error)
- [ ] No crashes

---

## 9. Performance Testing ✅

### Prediction Latency
- [ ] Click "Predict"
- [ ] **Result appears in <2 seconds**
- [ ] UI doesn't freeze
- [ ] Loading indicator shows (if any)

### SHAP Computation
- [ ] Click "Predict"
- [ ] Open "SHAP (optional)" tab
- [ ] **SHAP chart appears in <5 seconds**
- [ ] UI remains responsive during computation

### Batch Prediction
- [ ] Upload CSV with 10 rows
- [ ] Click "Run Batch Prediction"
- [ ] **Results appear in <5 seconds**
- [ ] UI doesn't freeze

---

## 10. Visual & Text QA ✅

### Emojis
- [ ] Page icon (❤️) displays in browser tab
- [ ] All emojis render correctly (if any in text)

### Formatting
- [ ] **Percentages:** Displayed as "X.X%" (e.g., "65.0%")
- [ ] **Decimals:** Consistent formatting (1 decimal place)
- [ ] **Metrics:** ROC AUC shows 3 decimals (e.g., "0.824")

### Footer
- [ ] Footer displays: "Built by vineeth. For educational purposes only; not a medical device."
- [ ] Footer is visible at bottom of page
- [ ] Text is readable

### Layout
- [ ] Two-column input layout works on different screen sizes
- [ ] Sidebar doesn't overlap main content
- [ ] Charts don't clip or overflow
- [ ] No horizontal scrolling needed

---

## 11. Console/Log Testing ✅

### Check Browser Console (F12 → Console)
- [ ] No JavaScript errors
- [ ] No network errors (404s, etc.)
- [ ] No warnings (except acceptable ones)

### Check Terminal/Server Log
- [ ] No Python tracebacks
- [ ] No import errors
- [ ] No runtime errors
- [ ] Clean startup messages

---

## 12. Regression Testing ✅

### After Changes
- [ ] All previous tests still pass
- [ ] No new errors introduced
- [ ] Performance hasn't degraded

---

## Test Results Summary

**Date:** _______________  
**Tester:** _______________  
**Environment:** _______________

| Category | Passed | Failed | Notes |
|----------|--------|--------|-------|
| Launch & Display | ___/5 | ___ | |
| UI Components | ___/12 | ___ | |
| Functional Tests | ___/6 | ___ | |
| Risk Bar | ___/4 | ___ | |
| SHAP Behavior | ___/2 | ___ | |
| Feature Importances | ___/5 | ___ | |
| Batch Prediction | ___/3 | ___ | |
| Error Handling | ___/3 | ___ | |
| Performance | ___/3 | ___ | |
| Visual/Text QA | ___/5 | ___ | |
| Console/Log | ___/2 | ___ | |
| **TOTAL** | **___/50** | **___** | |

**Overall Status:** ☐ PASS  ☐ FAIL  ☐ NEEDS WORK

**Critical Issues Found:**
1. 
2. 
3. 

**Minor Issues Found:**
1. 
2. 
3. 

**Recommendations:**
1. 
2. 
3. 

---

**Sign-off:**
- [ ] Testing Complete
- [ ] All Critical Issues Resolved
- [ ] Ready for Production

