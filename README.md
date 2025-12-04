# HeartGuard – Heart Disease Risk Prediction

**HeartGuard** is an AI-powered web application that predicts heart disease risk using the UCI Heart Disease dataset. It includes data preprocessing, model training, saved artifacts, and a Streamlit UI that reports prediction probability, global feature importances, optional SHAP explanation, and a static ROC AUC score from test evaluation.

## Tech Stack
- Python 3.8+
- pandas, numpy, scikit-learn, joblib
- streamlit
- shap (optional in app)

## Project Structure
```
health-dashboard/
├─ data/
│  └─ heart.csv            # place dataset here
├─ notebooks/
│  └─ 01_eda_modeling.ipynb
├─ src/
│  ├─ preprocess.py
│  ├─ train.py
│  └─ utils.py
├─ app/
│  └─ streamlit_app.py
├─ model/
│  ├─ model.joblib         # produced by train.py
│  ├─ scaler.joblib        # produced by train.py
│  └─ metrics.json         # produced by train.py
├─ requirements.txt
└─ README.md
```

## Setup
1) Create and activate a virtual environment
```
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
```

2) Install dependencies
```
pip install -r requirements.txt
```

3) Place dataset
- Put the UCI Heart dataset CSV at `data/heart.csv`.
- Column names are normalized automatically; common variants are handled.

## Train the Model
```
python src/train.py
```
This will train a RandomForest model, print metrics, and save artifacts to `model/`:
- `model.joblib`
- `scaler.joblib`
- `metrics.json` (includes ROC AUC)

## Run the App
```
streamlit run app/streamlit_app.py
```
Open the provided URL in your browser. Enter patient features and click Predict to see probability, risk level, ROC AUC (from test set), and explanations.

## 🚀 Deployment

### Quick Deploy to Streamlit Cloud (Recommended)

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/your-username/health-dashboard.git
   git push -u origin main
   ```

2. **Deploy:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select repository
   - Set **Main file path:** `app/streamlit_app.py`
   - Click "Deploy"

3. **Your app will be live!** 🎉

### Other Deployment Options

See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- Docker deployment
- Heroku deployment
- AWS/GCP/Azure deployment
- VPS deployment
- And more...

## Notes
- The app degrades gracefully if SHAP cannot run (still shows global feature importances).
- This is an educational tool, not a medical device.

## Dataset Citation
UCI Machine Learning Repository: Heart Disease Data Set.


