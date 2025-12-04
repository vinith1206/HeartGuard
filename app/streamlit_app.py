import json
import os
from pathlib import Path
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

import joblib
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------------
# Imports from src/
# The app is run from the repo root. Ensure `src/` is importable.
# -----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from preprocess import preprocess_features, FEATURE_COLS, load_data  # noqa: E402
try:
    # map_columns helps align uploaded CSV headers to canonical names used in training
    from preprocess import map_columns  # type: ignore  # noqa: E402
except Exception:  # pragma: no cover
    map_columns = None


# -----------------------------------------------------------------------------
# Page configuration and enhanced styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="HeartGuard – Heart Disease Risk Prediction",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
/* Compact top padding */
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; }

/* Result card styling */
.result-card {
  border: 1px solid rgba(200,200,200,0.2);
  border-radius: 10px;
  padding: 14px 16px;
  background: rgba(125,125,125,0.07);
  margin: 10px 0;
}
.metric-title { font-weight: 600; opacity: 0.9; }
.metric-value { font-size: 1.4rem; font-weight: 700; }

/* Horizontal risk bar */
.risk-bar {
  width: 100%;
  height: 14px;
  border-radius: 999px;
  background: linear-gradient(90deg, #3CB371 0%, #FFD166 50%, #EF476F 100%);
  position: relative;
  margin-top: 10px;
}
.risk-indicator {
  position: absolute;
  top: -6px;
  width: 0; height: 24px;
  border-left: 3px solid white;
  box-shadow: 0 0 4px rgba(0,0,0,0.3);
}
.footer-note { opacity: 0.7; font-size: 0.9rem; }

/* Subtle card borders */
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] { padding: 6px 10px; }

/* Warning badges */
.warning-badge {
  background: #FFF3CD;
  border: 1px solid #FFC107;
  border-radius: 5px;
  padding: 5px 10px;
  margin: 5px 0;
  font-size: 0.85rem;
}

.info-badge {
  background: #D1ECF1;
  border: 1px solid #0C5460;
  border-radius: 5px;
  padding: 5px 10px;
  margin: 5px 0;
  font-size: 0.85rem;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------
@st.cache_data
def load_training_stats():
    """Load training data statistics for comparison."""
    data_path = ROOT / "data" / "heart.csv"
    if not data_path.exists():
        return None
    try:
        df = load_data(str(data_path))
        stats = {}
        for col in FEATURE_COLS:
            if col in df.columns:
                stats[col] = {
                    "mean": float(df[col].mean()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "q25": float(df[col].quantile(0.25)),
                    "q75": float(df[col].quantile(0.75)),
                    "median": float(df[col].median()),
                }
        return stats
    except Exception:
        return None


def get_input_warnings(input_values: Dict[str, Any], stats: Optional[Dict]) -> List[str]:
    """Generate warnings for unusual input values."""
    warnings = []
    if not stats:
        return warnings
    
    # Age warnings
    if "age" in input_values and "age" in stats:
        age = input_values["age"]
        if age < 30:
            warnings.append(f"⚠️ Age ({age}) is unusually low (typical: 30-77)")
        elif age > 75:
            warnings.append(f"⚠️ Age ({age}) is unusually high (typical: 30-77)")
    
    # Blood pressure warnings
    if "trestbps" in input_values and "trestbps" in stats:
        bp = input_values["trestbps"]
        if bp < 90:
            warnings.append(f"⚠️ Resting BP ({bp} mmHg) is very low (normal: 90-120)")
        elif bp > 180:
            warnings.append(f"⚠️ Resting BP ({bp} mmHg) is very high (normal: 90-120)")
    
    # Cholesterol warnings
    if "chol" in input_values and "chol" in stats:
        chol = input_values["chol"]
        if chol > 300:
            warnings.append(f"⚠️ Cholesterol ({chol} mg/dl) is high (normal: <200)")
    
    # Heart rate warnings
    if "thalach" in input_values and "thalach" in stats:
        hr = input_values["thalach"]
        if hr < 80:
            warnings.append(f"⚠️ Max Heart Rate ({hr} bpm) is unusually low")
        elif hr > 200:
            warnings.append(f"⚠️ Max Heart Rate ({hr} bpm) is unusually high")
    
    return warnings


def create_csv_template() -> str:
    """Create a CSV template for batch predictions."""
    template_data = {
        "age": [54, 63, 45],
        "sex": [1, 0, 1],
        "trestbps": [130, 145, 120],
        "chol": [246, 233, 200],
        "fbs": [0, 1, 0],
        "thalach": [150, 150, 170],
        "exang": [0, 0, 1],
        "oldpeak": [1.0, 2.3, 0.5],
    }
    df = pd.DataFrame(template_data)
    return df.to_csv(index=False)


# -----------------------------------------------------------------------------
# Artifact loading
# -----------------------------------------------------------------------------
@st.cache_resource
def load_artifacts():
    model_path = ROOT / "model" / "model.joblib"
    scaler_path = ROOT / "model" / "scaler.joblib"
    metrics_path = ROOT / "model" / "metrics.json"

    if not model_path.exists() or not scaler_path.exists():
        return None, None, None

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    metrics = None
    if metrics_path.exists():
        try:
            with open(metrics_path, "r", encoding="utf-8") as f:
                metrics = json.load(f)
        except Exception:
            metrics = None
    return model, scaler, metrics


model, scaler, metrics = load_artifacts()
training_stats = load_training_stats()

# Initialize session state
if "prediction_history" not in st.session_state:
    st.session_state.prediction_history = []
if "patient_profiles" not in st.session_state:
    st.session_state.patient_profiles = {}
if "current_profile_name" not in st.session_state:
    st.session_state.current_profile_name = ""
if "save_profile_clicked" not in st.session_state:
    st.session_state.save_profile_clicked = False
if "load_profile_clicked" not in st.session_state:
    st.session_state.load_profile_clicked = False

st.title("❤️ HeartGuard: Heart Disease Risk Prediction")

# Author info header
st.markdown(
    """
    <div style="background: linear-gradient(90deg, rgba(59,130,246,0.1) 0%, rgba(147,51,234,0.1) 100%); 
                padding: 15px 20px; 
                border-radius: 10px; 
                margin-bottom: 20px;
                border-left: 4px solid #3B82F6;">
        <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
            <div style="flex: 1;">
                <h3 style="margin: 0; color: #1E40AF; font-size: 1.1rem;">👨‍💻 Developed by <strong style="color: #3B82F6;">Vineeth</strong></h3>
            </div>
            <div style="display: flex; gap: 15px; align-items: center;">
                <a href="https://www.linkedin.com/in/vineeth-gollapalli-439931380/" 
                   target="_blank" 
                   style="text-decoration: none; color: #0077B5; font-weight: 600; 
                          padding: 8px 15px; background: white; border-radius: 6px; 
                          border: 1px solid #0077B5; transition: all 0.3s;">
                    🔗 LinkedIn
                </a>
                <a href="https://github.com/vinith1206" 
                   target="_blank" 
                   style="text-decoration: none; color: #24292E; font-weight: 600; 
                          padding: 8px 15px; background: white; border-radius: 6px; 
                          border: 1px solid #24292E; transition: all 0.3s;">
                    💻 GitHub
                </a>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write(
    "**HeartGuard** - Your intelligent heart health companion. Predict the probability of heart disease using AI-powered analysis. "
    "Enter patient information below or use batch prediction for multiple patients."
)

if model is None or scaler is None:
    st.error(
        "Model artifacts not found. Please run training first from the repo root: `python src/train.py`."
    )
    st.stop()


# -----------------------------------------------------------------------------
# Sidebar: Enhanced with more features
# -----------------------------------------------------------------------------
with st.sidebar:
    # Developer info
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 15px; 
                    border-radius: 10px; 
                    margin-bottom: 20px;
                    text-align: center;">
            <h4 style="color: white; margin: 0 0 10px 0;">👨‍💻 Developer</h4>
            <p style="color: white; margin: 5px 0; font-weight: 600;">Vineeth</p>
            <div style="display: flex; gap: 10px; justify-content: center; margin-top: 10px;">
                <a href="https://www.linkedin.com/in/vineeth-gollapalli-439931380/" 
                   target="_blank" 
                   style="color: white; text-decoration: none; font-size: 1.2em;" 
                   title="LinkedIn">🔗</a>
                <a href="https://github.com/vinith1206" 
                   target="_blank" 
                   style="color: white; text-decoration: none; font-size: 1.2em;" 
                   title="GitHub">💻</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.header("📊 Summary")
    st.caption("Live view of your current input values.")
    summary_placeholder = st.empty()

    # Model version and info
    with st.expander("📋 Dataset & Model Info", expanded=False):
        st.write("**Dataset:** UCI Heart Disease")
        st.write(f"**Location:** `data/heart.csv`")
        if metrics:
            st.write(f"**Test ROC AUC:** {metrics.get('roc_auc', 'N/A'):.3f}")
            st.write(f"**Test Accuracy:** {metrics.get('accuracy', 'N/A'):.3f}")
            st.write(f"**Precision:** {metrics.get('precision', 'N/A'):.3f}")
            st.write(f"**Recall:** {metrics.get('recall', 'N/A'):.3f}")
            st.write(f"**F1 Score:** {metrics.get('f1', 'N/A'):.3f}")
        else:
            st.write("- Test ROC AUC: N/A")
            st.write("- Test Accuracy: N/A")
        st.write("**Model:** RandomForestClassifier (200 trees)")
        st.write("**Scaling:** StandardScaler")
        st.write("**Model Version:** 1.0")
        st.write(f"**Features:** {len(FEATURE_COLS)}")
        
        if training_stats:
            st.write("**Training Data Stats:**")
            st.write(f"- Samples: 303")
            st.write(f"- Features: {len(FEATURE_COLS)}")

    # Training data statistics
    if training_stats:
        with st.expander("📈 Training Data Statistics", expanded=False):
            for col in ["age", "trestbps", "chol", "thalach", "oldpeak"]:
                if col in training_stats:
                    s = training_stats[col]
                    st.write(f"**{col.upper()}:**")
                    st.write(f"  Mean: {s['mean']:.1f} | Range: {s['min']:.0f}-{s['max']:.0f}")
                    st.write(f"  Normal: {s['q25']:.1f}-{s['q75']:.1f}")

    # Risk threshold controls
    st.markdown("---")
    st.subheader("⚙️ Risk Thresholds")
    low_default, high_default = 0.33, 0.66
    low_thr = st.slider("Low threshold", 0.0, 0.9, low_default, 0.01, help="Probability below this is considered Low risk")
    high_thr = st.slider("High threshold", 0.1, 0.99, max(high_default, low_thr + 0.01), 0.01, help="Probability above this is considered High risk")
    if low_thr >= high_thr:
        st.warning("Low threshold must be less than High threshold.")

    # Patient profiles
    st.markdown("---")
    st.subheader("👤 Patient Profiles")
    profile_name = st.text_input("Profile Name", value=st.session_state.current_profile_name, placeholder="Enter profile name")
    if profile_name:
        st.session_state.profile_name_input = profile_name
    
    col_save, col_load = st.columns(2)
    with col_save:
        if st.button("💾 Save", use_container_width=True, key="save_profile_btn"):
            st.session_state.save_profile_clicked = True
    
    profile_to_load = ""
    with col_load:
        if st.session_state.patient_profiles:
            profile_to_load = st.selectbox("Load Profile", options=[""] + list(st.session_state.patient_profiles.keys()), key="profile_selector")
            if st.button("📂 Load", use_container_width=True, key="load_profile_btn"):
                st.session_state.load_profile_clicked = True
                st.session_state.profile_to_load_value = profile_to_load

    # Batch prediction
    st.markdown("---")
    st.subheader("📁 Batch Predict (CSV)")
    csv_file = st.file_uploader("Upload CSV", type=["csv"], help="Upload a CSV file with patient data. Download template below.")
    
    # CSV template download
    template_csv = create_csv_template()
    st.download_button(
        label="📥 Download CSV Template",
        data=template_csv,
        file_name="batch_prediction_template.csv",
        mime="text/csv",
        help="Download a template CSV file with example data and correct column names"
    )
    
    batch_run = st.button("🚀 Run Batch Prediction", use_container_width=True)
    
    # Prediction history
    if st.session_state.prediction_history:
        st.markdown("---")
        st.subheader("📜 Prediction History")
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.prediction_history = []
            st.rerun()
        
        for i, pred in enumerate(st.session_state.prediction_history[-5:]):  # Show last 5
            with st.expander(f"Prediction {len(st.session_state.prediction_history) - 4 + i} - {pred['timestamp']}", expanded=False):
                st.write(f"**Risk:** {pred['risk_category']} ({pred['probability']:.1f}%)")
                st.write(f"**Age:** {pred['inputs']['age']}, **Sex:** {pred['inputs']['sex']}")


# -----------------------------------------------------------------------------
# Input widgets with tooltips and validation
# -----------------------------------------------------------------------------
st.subheader("📝 Enter Patient Information")

# Reset button
col_reset, col_spacer = st.columns([1, 5])
with col_reset:
    if st.button("🔄 Reset to Defaults"):
        st.rerun()

col1, col2 = st.columns(2)

# Define default values
default_age = 54
default_trestbps = 130
default_chol = 246
default_thalach = 150
default_oldpeak = 1.0

# Load profile if selected (before input widgets)
default_sex_idx = 0
default_fbs_idx = 0
default_exang_idx = 0

if st.session_state.current_profile_name and st.session_state.current_profile_name in st.session_state.patient_profiles:
    profile = st.session_state.patient_profiles[st.session_state.current_profile_name]
    default_age = profile.get("age", default_age)
    default_trestbps = profile.get("trestbps", default_trestbps)
    default_chol = profile.get("chol", default_chol)
    default_thalach = profile.get("thalach", default_thalach)
    default_oldpeak = profile.get("oldpeak", default_oldpeak)
    # Handle sex conversion
    profile_sex = profile.get("sex", "Male")
    if isinstance(profile_sex, int):
        default_sex_idx = 0 if profile_sex == 1 else 1
    else:
        default_sex_idx = 0 if profile_sex == "Male" else 1
    # Handle fbs conversion
    profile_fbs = profile.get("fbs", "No")
    if isinstance(profile_fbs, int):
        default_fbs_idx = 1 if profile_fbs == 1 else 0
    else:
        default_fbs_idx = 1 if profile_fbs == "Yes" else 0
    # Handle exang conversion
    profile_exang = profile.get("exang", "No")
    if isinstance(profile_exang, int):
        default_exang_idx = 1 if profile_exang == 1 else 0
    else:
        default_exang_idx = 1 if profile_exang == "Yes" else 0

with col1:
    age = st.number_input(
        "Age",
        min_value=18,
        max_value=100,
        value=default_age,
        help="Patient's age in years. Typical range: 30-77 years."
    )
    trestbps = st.number_input(
        "Resting Blood Pressure (trestbps)",
        min_value=80,
        max_value=220,
        value=default_trestbps,
        help="Resting blood pressure in mmHg. Normal: 90-120 mmHg. High: >140 mmHg."
    )
    fbs = st.selectbox(
        "Fasting Blood Sugar > 120 mg/dl (fbs)",
        options=["No", "Yes"],
        index=default_fbs_idx,
        help="Whether fasting blood sugar is above 120 mg/dl (1 = true, 0 = false)"
    )
    exang = st.selectbox(
        "Exercise Induced Angina (exang)",
        options=["No", "Yes"],
        index=default_exang_idx,
        help="Exercise-induced angina (chest pain during exercise). 1 = yes, 0 = no"
    )

with col2:
    sex = st.selectbox(
        "Sex",
        options=["Male", "Female"],
        index=default_sex_idx,
        help="Patient's sex. Male = 1, Female = 0"
    )
    chol = st.number_input(
        "Cholesterol (chol)",
        min_value=100,
        max_value=600,
        value=default_chol,
        help="Serum cholesterol in mg/dl. Normal: <200 mg/dl. High: >240 mg/dl."
    )
    thalach = st.number_input(
        "Max Heart Rate Achieved (thalach)",
        min_value=60,
        max_value=220,
        value=default_thalach,
        help="Maximum heart rate achieved during exercise. Typical: 60-200 bpm."
    )
    oldpeak = st.number_input(
        "ST Depression (oldpeak)",
        min_value=0.0,
        max_value=6.0,
        value=default_oldpeak,
        step=0.1,
        help="ST depression induced by exercise relative to rest. Normal: 0-1.0. High: >2.0"
    )


def build_input_df() -> pd.DataFrame:
    """Construct a single-row DataFrame in the order of FEATURE_COLS."""
    sex_bin = 1 if sex == "Male" else 0
    fbs_bin = 1 if fbs == "Yes" else 0
    exang_bin = 1 if exang == "Yes" else 0
    row = {
        "age": age,
        "sex": sex_bin,
        "trestbps": trestbps,
        "chol": chol,
        "fbs": fbs_bin,
        "thalach": thalach,
        "exang": exang_bin,
        "oldpeak": oldpeak,
    }
    return pd.DataFrame([[row[c] for c in FEATURE_COLS]], columns=FEATURE_COLS)


# Input validation warnings
input_values = {
    "age": age,
    "trestbps": trestbps,
    "chol": chol,
    "thalach": thalach,
    "oldpeak": oldpeak,
}
warnings = get_input_warnings(input_values, training_stats)
if warnings:
    for warning in warnings:
        st.markdown(f'<div class="warning-badge">{warning}</div>', unsafe_allow_html=True)

# Keep sidebar summary synced
summary_placeholder.json({c: v for c, v in build_input_df().iloc[0].items()})

# Handle profile save (after inputs are defined)
if st.session_state.save_profile_clicked:
    profile_name = st.session_state.get("profile_name_input", "")
    if profile_name:
        current_inputs = {
            "age": age, "sex": sex, "trestbps": trestbps, "chol": chol,
            "fbs": fbs, "thalach": thalach, "exang": exang, "oldpeak": oldpeak
        }
        st.session_state.patient_profiles[profile_name] = current_inputs
        st.session_state.current_profile_name = profile_name
        st.session_state.save_profile_clicked = False
        st.success(f"✅ Profile '{profile_name}' saved!")
    else:
        st.session_state.save_profile_clicked = False
        st.warning("⚠️ Please enter a profile name")

# Handle profile load
if st.session_state.load_profile_clicked:
    profile_to_load = st.session_state.get("profile_to_load_value", "")
    if profile_to_load:
        st.session_state.current_profile_name = profile_to_load
        st.session_state.load_profile_clicked = False
        st.rerun()

# Risk comparison section
if len(st.session_state.prediction_history) > 1:
    st.markdown("---")
    st.subheader("📊 Risk Comparison")
    comparison_data = []
    for pred in st.session_state.prediction_history[-5:]:
        comparison_data.append({
            "Timestamp": pred["timestamp"],
            "Risk %": pred["probability"],
            "Category": pred["risk_category"],
            "Age": pred["inputs"]["age"]
        })
    if comparison_data:
        comp_df = pd.DataFrame(comparison_data)
        fig_comp = px.line(comp_df, x="Timestamp", y="Risk %", markers=True, 
                          title="Risk Trend Over Time", color="Category")
        st.plotly_chart(fig_comp, use_container_width=True)


# -----------------------------------------------------------------------------
# Prediction & Results
# -----------------------------------------------------------------------------
predict_clicked = st.button("🔮 Predict", type="primary", use_container_width=True)

if predict_clicked:
    try:
        user_df = build_input_df()
        X_proc, _, _ = preprocess_features(user_df, fit_scaler=False, scaler=scaler)
        proba = float(model.predict_proba(X_proc)[0, 1])

        # Risk bucket thresholds
        if proba < low_thr:
            bucket, color = "Low", "#3CB371"
        elif proba <= high_thr:
            bucket, color = "Moderate", "#FFD166"
        else:
            bucket, color = "High", "#EF476F"

        # Save to history
        prediction_record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "probability": proba * 100,
            "risk_category": bucket,
            "inputs": {
                "age": age,
                "sex": sex,
                "trestbps": trestbps,
                "chol": chol,
                "fbs": fbs,
                "thalach": thalach,
                "exang": exang,
                "oldpeak": oldpeak,
            }
        }
        st.session_state.prediction_history.append(prediction_record)

        # Result card
        result_col1, result_col2 = st.columns([2, 1])
        
        with result_col1:
            st.markdown(
                f"""
                <div class="result-card">
                    <div class="metric-title">Predicted Probability</div>
                    <div class="metric-value" style="color:{color}">{proba*100:.1f}%</div>
                    <div>Risk Category: <strong style="color:{color}">{bucket}</strong></div>
                    <div class="risk-bar">
                        <div class="risk-indicator" style="left:{proba*100:.0f}%;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        with result_col2:
            # Export buttons
            st.markdown("**Export Prediction**")
            prediction_json = json.dumps(prediction_record, indent=2)
            st.download_button(
                label="📥 Download JSON",
                data=prediction_json,
                file_name=f"prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
            
            prediction_csv = pd.DataFrame([prediction_record["inputs"]])
            prediction_csv["probability"] = proba * 100
            prediction_csv["risk_category"] = bucket
            csv_data = prediction_csv.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        # Enhanced tabs with Plotly charts
        tabs = st.tabs(["📊 Global Importances", "🔍 SHAP Explanation", "📈 Feature Distribution", "📉 Model Performance"])

        with tabs[0]:
            if hasattr(model, "feature_importances_"):
                fi = model.feature_importances_
                fi_df = pd.DataFrame({"feature": FEATURE_COLS, "importance": fi}).sort_values(
                    "importance", ascending=True
                )
                
                # Plotly bar chart
                fig_fi = go.Figure(data=[
                    go.Bar(
                        y=fi_df["feature"],
                        x=fi_df["importance"],
                        orientation='h',
                        marker=dict(color=fi_df["importance"], colorscale='Viridis'),
                        text=[f"{v:.3f}" for v in fi_df["importance"]],
                        textposition='outside'
                    )
                ])
                fig_fi.update_layout(
                    title="Global Feature Importances",
                    xaxis_title="Importance",
                    yaxis_title="Feature",
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig_fi, use_container_width=True)
                
                st.caption("These values show the overall importance of each feature in the model.")
            else:
                st.info("This model does not expose feature_importances_.")

        with tabs[1]:
            # Check if SHAP is installed
            try:
                import shap
                shap_available = True
            except ImportError:
                shap_available = False
                st.warning("SHAP is not installed. Install it with: `pip install shap`")
                st.info("Showing global feature importances only.")
            
            if shap_available:
                try:
                    # Convert DataFrame to numpy array for SHAP
                    if isinstance(X_proc, pd.DataFrame):
                        X_proc_array = X_proc.values
                    else:
                        X_proc_array = X_proc
                    
                    if X_proc_array.ndim == 1:
                        X_proc_array = X_proc_array.reshape(1, -1)
                    
                    explainer = shap.TreeExplainer(model)
                    sv_list = explainer.shap_values(X_proc_array)
                    
                    if isinstance(sv_list, list) and len(sv_list) == 2:
                        sv = np.array(sv_list[1])
                        if sv.ndim == 2:
                            sv = sv[0]
                        elif sv.ndim > 2:
                            sv = sv.flatten()[:len(FEATURE_COLS)]
                    else:
                        sv = np.array(sv_list)
                        if sv.ndim == 2:
                            sv = sv[0]
                        elif sv.ndim > 2:
                            sv = sv.flatten()[:len(FEATURE_COLS)]
                    
                    sv = np.array(sv).flatten()
                    
                    if len(sv) == len(FEATURE_COLS) * 2:
                        sv = sv[len(FEATURE_COLS):]
                    elif len(sv) > len(FEATURE_COLS):
                        sv = sv[:len(FEATURE_COLS)]
                    
                    if len(sv) != len(FEATURE_COLS):
                        min_len = min(len(sv), len(FEATURE_COLS))
                        sv = sv[:min_len]
                        feature_cols_used = FEATURE_COLS[:min_len]
                    else:
                        feature_cols_used = FEATURE_COLS
                    
                    # Create Plotly visualization
                    shap_df = pd.DataFrame({
                        "feature": feature_cols_used,
                        "contribution": sv,
                        "abs_contribution": np.abs(sv),
                    }).sort_values("abs_contribution", ascending=True)
                    
                    colors = ['#EF476F' if x < 0 else '#3CB371' for x in shap_df["contribution"]]
                    
                    fig_shap = go.Figure(data=[
                        go.Bar(
                            y=shap_df["feature"],
                            x=shap_df["contribution"],
                            orientation='h',
                            marker=dict(color=colors),
                            text=[f"{v:.3f}" for v in shap_df["contribution"]],
                            textposition='outside'
                        )
                    ])
                    fig_shap.update_layout(
                        title="SHAP Values - Feature Contributions to This Prediction",
                        xaxis_title="SHAP Value (contribution to prediction)",
                        yaxis_title="Feature",
                        height=400,
                        showlegend=False
                    )
                    st.plotly_chart(fig_shap, use_container_width=True)
                    st.caption("Positive values increase risk, negative values decrease risk.")
                    
                except Exception as e:
                    st.error(f"SHAP computation failed: {str(e)}")
                    import traceback
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())
                    st.info("This may be due to numba compatibility issues. Try: `pip install --upgrade shap numba`")

        with tabs[2]:
            # Feature distribution comparison
            if training_stats:
                st.write("**Your Input vs Training Data Distribution**")
                
                # Select features to compare
                features_to_plot = st.multiselect(
                    "Select features to compare",
                    options=["age", "trestbps", "chol", "thalach", "oldpeak"],
                    default=["age", "trestbps", "chol"]
                )
                
                if features_to_plot:
                    num_features = len(features_to_plot)
                    cols_per_row = min(2, num_features)
                    rows = (num_features + cols_per_row - 1) // cols_per_row
                    
                    fig_dist = make_subplots(
                        rows=rows,
                        cols=cols_per_row,
                        subplot_titles=features_to_plot,
                        vertical_spacing=0.15
                    )
                    
                    for idx, feat in enumerate(features_to_plot):
                        row = (idx // cols_per_row) + 1
                        col = (idx % cols_per_row) + 1
                        
                        if feat in training_stats and feat in input_values:
                            stats_feat = training_stats[feat]
                            user_val = input_values[feat]
                            
                            # Create distribution data
                            x_range = np.linspace(stats_feat["min"], stats_feat["max"], 100)
                            # Simple normal approximation
                            y_dist = np.exp(-0.5 * ((x_range - stats_feat["mean"]) / stats_feat["std"]) ** 2)
                            y_dist = y_dist / y_dist.max()  # Normalize
                            
                            # Add distribution
                            fig_dist.add_trace(
                                go.Scatter(
                                    x=x_range,
                                    y=y_dist,
                                    mode='lines',
                                    name=f'{feat} distribution',
                                    fill='tozeroy',
                                    line=dict(color='lightblue', width=2),
                                    showlegend=False
                                ),
                                row=row,
                                col=col
                            )
                            
                            # Add user value line
                            fig_dist.add_vline(
                                x=user_val,
                                line_dash="dash",
                                line_color="red",
                                annotation_text=f"Your value: {user_val}",
                                row=row,
                                col=col
                            )
                            
                            # Add mean line
                            fig_dist.add_vline(
                                x=stats_feat["mean"],
                                line_dash="dot",
                                line_color="green",
                                annotation_text=f"Mean: {stats_feat['mean']:.1f}",
                                row=row,
                                col=col
                            )
                    
                    fig_dist.update_layout(
                        height=300 * rows,
                        title_text="Feature Distribution Comparison",
                        showlegend=False
                    )
                    st.plotly_chart(fig_dist, use_container_width=True)
            else:
                st.info("Training data statistics not available.")

        with tabs[3]:
            # Model performance metrics
            if metrics:
                metrics_col1, metrics_col2 = st.columns(2)
                
                with metrics_col1:
                    st.metric("ROC AUC", f"{metrics.get('roc_auc', 0):.3f}")
                    st.metric("Accuracy", f"{metrics.get('accuracy', 0):.3f}")
                
                with metrics_col2:
                    st.metric("Precision", f"{metrics.get('precision', 0):.3f}")
                    st.metric("Recall", f"{metrics.get('recall', 0):.3f}")
                    st.metric("F1 Score", f"{metrics.get('f1', 0):.3f}")
                
                # Confusion matrix visualization
                if "confusion_matrix" in metrics:
                    cm = np.array(metrics["confusion_matrix"])
                    fig_cm = go.Figure(data=go.Heatmap(
                        z=cm,
                        x=["Predicted: No Disease", "Predicted: Disease"],
                        y=["Actual: No Disease", "Actual: Disease"],
                        colorscale='Blues',
                        text=cm,
                        texttemplate='%{text}',
                        textfont={"size": 16},
                        showscale=True
                    ))
                    fig_cm.update_layout(
                        title="Confusion Matrix (Test Set)",
                        height=400
                    )
                    st.plotly_chart(fig_cm, use_container_width=True)
            else:
                st.info("Model metrics not available.")

    except Exception as e:
        st.error(f"Prediction failed: {e}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())


# -----------------------------------------------------------------------------
# Enhanced Batch CSV prediction
# -----------------------------------------------------------------------------
if csv_file and batch_run:
    try:
        with st.spinner("Processing batch prediction..."):
            df_in = pd.read_csv(csv_file)
            
            # Show upload info
            st.info(f"📊 Loaded {len(df_in)} rows from CSV file")
            
            # Normalize column names
            if map_columns is not None:
                df_in = map_columns(df_in)
            
            # Validate columns
            missing_cols = [c for c in FEATURE_COLS if c not in df_in.columns]
            if missing_cols:
                st.warning(f"⚠️ Missing columns (will be imputed): {', '.join(missing_cols)}")
            
            # Ensure all expected features exist
            for c in FEATURE_COLS:
                if c not in df_in.columns:
                    df_in[c] = np.nan
            
            # Preprocess using saved scaler
            Xb, _, _ = preprocess_features(df_in, fit_scaler=False, scaler=scaler)
            probas = model.predict_proba(Xb)[:, 1]
            labels = (probas >= 0.5).astype(int)

            def bucketize(p: float) -> str:
                if p < low_thr:
                    return "Low"
                if p <= high_thr:
                    return "Moderate"
                return "High"

            out = df_in.copy()
            out["probability"] = probas
            out["prediction"] = labels
            out["risk_bucket"] = [bucketize(p) for p in probas]

            st.success(f"✅ Successfully processed {len(out)} predictions!")
            
            # Summary statistics
            col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
            with col_sum1:
                st.metric("Total Patients", len(out))
            with col_sum2:
                st.metric("High Risk", len(out[out["risk_bucket"] == "High"]))
            with col_sum3:
                st.metric("Moderate Risk", len(out[out["risk_bucket"] == "Moderate"]))
            with col_sum4:
                st.metric("Low Risk", len(out[out["risk_bucket"] == "Low"]))

            st.subheader("📋 Batch Prediction Results")
            
            # Filter options
            filter_risk = st.selectbox("Filter by Risk", options=["All", "High", "Moderate", "Low"])
            if filter_risk != "All":
                out_display = out[out["risk_bucket"] == filter_risk]
            else:
                out_display = out
            
            st.dataframe(out_display.head(100), use_container_width=True)
            
            if len(out_display) > 100:
                st.caption(f"Showing first 100 rows. Total: {len(out_display)} rows")

            # Visualization
            risk_counts = out["risk_bucket"].value_counts()
            fig_pie = px.pie(
                values=risk_counts.values,
                names=risk_counts.index,
                title="Risk Distribution",
                color_discrete_map={"High": "#EF476F", "Moderate": "#FFD166", "Low": "#3CB371"}
            )
            st.plotly_chart(fig_pie, use_container_width=True)

            # Download options
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                csv_bytes = out.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Results CSV",
                    data=csv_bytes,
                    file_name="batch_predictions.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col_dl2:
                json_data = out.to_json(orient="records", indent=2)
                st.download_button(
                    label="📥 Download Results JSON",
                    data=json_data,
                    file_name="batch_predictions.json",
                    mime="application/json",
                    use_container_width=True
                )
                
    except Exception as e:
        st.error(f"Batch prediction failed: {e}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
        st.caption("Your CSV should include headers that map to: " + ", ".join(FEATURE_COLS) + ". Common variants are auto-mapped when possible.")


# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div class="footer-note">
      <strong>HeartGuard</strong> - Built by <strong><a href="https://www.linkedin.com/in/vineeth-gollapalli-439931380/" target="_blank" style="color: inherit; text-decoration: none;">Vineeth</a></strong> | 
      <a href="https://www.linkedin.com/in/vineeth-gollapalli-439931380/" target="_blank" style="color: #0077B5; text-decoration: none;">LinkedIn</a> | 
      <a href="https://github.com/vinith1206" target="_blank" style="color: #24292E; text-decoration: none;">GitHub</a>
      <br>For educational purposes only; not a medical device.
      <br>⚠️ This tool is for educational and research purposes only. Always consult healthcare professionals for medical decisions.
    </div>
    """,
    unsafe_allow_html=True,
)
