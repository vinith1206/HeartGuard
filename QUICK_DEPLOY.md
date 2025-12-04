# 🚀 Quick Deployment Guide - HeartGuard

## Fastest Way: Streamlit Cloud (5 minutes)

### Step 1: Prepare GitHub Repository

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Ready for deployment"

# Create repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/health-dashboard.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Streamlit Cloud

1. Go to: **https://share.streamlit.io**
2. Click **"Sign in"** (use GitHub)
3. Click **"New app"**
4. Fill in:
   - **Repository:** Select `your-username/health-dashboard`
   - **Branch:** `main`
   - **Main file path:** `app/streamlit_app.py`
5. Click **"Deploy"**

### Step 3: Wait & Access

- Deployment takes 1-2 minutes
- Your app will be live at: `https://health-dashboard.streamlit.app`
- Share the URL with anyone!

---

## Alternative: Docker (For Custom Hosting)

### Build & Run Locally

```bash
# Build image
docker build -t heartguard .

# Run container
docker run -p 8501:8501 heartguard
```

### Deploy to Cloud

**AWS:**
```bash
# Push to ECR and deploy to ECS/Fargate
```

**Google Cloud:**
```bash
gcloud run deploy heartguard --source .
```

**Azure:**
```bash
az container create --resource-group myResourceGroup --name heartguard --image heartguard:latest
```

---

## Pre-Deployment Checklist

✅ All files committed to git  
✅ Model files (`model/*.joblib`) included  
✅ `requirements.txt` is complete  
✅ App runs locally without errors  
✅ No hardcoded local paths  

---

## Troubleshooting

**Issue:** Model files not found  
**Fix:** Ensure `model/` folder is committed to git

**Issue:** Dependencies missing  
**Fix:** Check `requirements.txt` has all packages

**Issue:** Port conflicts  
**Fix:** Change port in deployment config

---

## Need Help?

- Check [DEPLOYMENT.md](DEPLOYMENT.md) for detailed guides
- Review Streamlit Cloud docs: https://docs.streamlit.io/streamlit-community-cloud

---

**Ready to deploy?** Follow Step 1-3 above! 🚀

