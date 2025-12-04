# HeartGuard - Deployment Guide

This guide covers multiple deployment options for the HeartGuard application.

---

## 🚀 Option 1: Streamlit Cloud (Recommended - Easiest)

**Best for:** Quick deployment, free hosting, automatic updates

### Prerequisites
- GitHub account
- Project pushed to GitHub repository

### Steps

1. **Prepare your repository:**
   ```bash
   # Ensure all files are committed
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Deploy to Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set **Main file path:** `app/streamlit_app.py`
   - Click "Deploy"

3. **Your app will be live at:**
   - `https://your-app-name.streamlit.app`

### Advantages
- ✅ Free hosting
- ✅ Automatic deployments on git push
- ✅ No server management
- ✅ Built-in HTTPS
- ✅ Easy to share

---

## 🐳 Option 2: Docker Deployment

**Best for:** Production deployments, custom infrastructure

### Create Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run Streamlit
ENTRYPOINT ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Build and Run

```bash
# Build image
docker build -t heartguard:latest .

# Run container
docker run -p 8501:8501 heartguard:latest
```

### Deploy to Cloud Platforms

**AWS ECS / Google Cloud Run / Azure Container Instances:**
- Push Docker image to container registry
- Deploy using platform-specific tools

---

## ☁️ Option 3: Heroku

**Best for:** Simple cloud deployment

### Create Procfile

```
web: streamlit run app/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
```

### Create setup.sh

```bash
mkdir -p ~/.streamlit/

echo "\
[server]\n\
port = $PORT\n\
enableCORS = false\n\
headless = true\n\
\n\
" > ~/.streamlit/config.toml
```

### Deploy

```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create app
heroku create heartguard-app

# Deploy
git push heroku main
```

---

## 🌐 Option 4: AWS EC2 / DigitalOcean / Linode

**Best for:** Full control, custom configurations

### Setup Steps

1. **Launch a server** (Ubuntu 20.04+ recommended)

2. **SSH into server:**
   ```bash
   ssh user@your-server-ip
   ```

3. **Install dependencies:**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv git -y
   ```

4. **Clone repository:**
   ```bash
   git clone https://github.com/your-username/health-dashboard.git
   cd health-dashboard
   ```

5. **Setup virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

6. **Run with systemd service:**
   Create `/etc/systemd/system/heartguard.service`:
   ```ini
   [Unit]
   Description=HeartGuard Streamlit App
   After=network.target

   [Service]
   Type=simple
   User=your-user
   WorkingDirectory=/path/to/health-dashboard
   Environment="PATH=/path/to/health-dashboard/venv/bin"
   ExecStart=/path/to/health-dashboard/venv/bin/streamlit run app/streamlit_app.py --server.port=8501 --server.address=0.0.0.0
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

7. **Start service:**
   ```bash
   sudo systemctl enable heartguard
   sudo systemctl start heartguard
   ```

8. **Configure firewall:**
   ```bash
   sudo ufw allow 8501/tcp
   ```

9. **Setup Nginx reverse proxy (optional but recommended):**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

---

## 🔒 Option 5: Google Cloud Platform (GCP)

### Using Cloud Run

1. **Create Dockerfile** (see Option 2)

2. **Build and deploy:**
   ```bash
   # Set project
   gcloud config set project YOUR_PROJECT_ID

   # Build image
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/heartguard

   # Deploy to Cloud Run
   gcloud run deploy heartguard \
     --image gcr.io/YOUR_PROJECT_ID/heartguard \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

---

## 📦 Option 6: Azure App Service

1. **Install Azure CLI**

2. **Create App Service:**
   ```bash
   az webapp create --resource-group myResourceGroup \
     --plan myAppServicePlan \
     --name heartguard-app \
     --runtime "PYTHON|3.9"
   ```

3. **Deploy:**
   ```bash
   az webapp up --name heartguard-app --resource-group myResourceGroup
   ```

---

## 🔧 Pre-Deployment Checklist

Before deploying, ensure:

- [ ] All dependencies in `requirements.txt`
- [ ] Model files (`model.joblib`, `scaler.joblib`) are included
- [ ] `metrics.json` exists
- [ ] Data file (`data/heart.csv`) is included (if needed)
- [ ] No hardcoded paths (use relative paths)
- [ ] Environment variables configured (if needed)
- [ ] `.gitignore` excludes sensitive files
- [ ] README updated with deployment info

---

## 📝 Environment Variables (Optional)

Create `.streamlit/config.toml` for configuration:

```toml
[server]
port = 8501
enableCORS = false
headless = true

[browser]
gatherUsageStats = false
```

---

## 🛡️ Security Considerations

1. **Add authentication** (if needed):
   ```python
   # Add to streamlit_app.py
   import streamlit_authenticator as stauth
   ```

2. **Rate limiting** for production

3. **HTTPS/SSL** certificates

4. **Environment variables** for sensitive data

5. **Input validation** (already implemented)

---

## 📊 Monitoring

Consider adding:
- Application monitoring (Sentry, LogRocket)
- Performance monitoring
- Error tracking
- Usage analytics

---

## 🆘 Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Change port in command
   streamlit run app/streamlit_app.py --server.port=8502
   ```

2. **Model files not found:**
   - Ensure model files are committed to repository
   - Check file paths are relative

3. **Dependencies missing:**
   - Verify `requirements.txt` is complete
   - Check Python version compatibility

4. **Memory issues:**
   - Increase server memory
   - Optimize model size

---

## 📚 Additional Resources

- [Streamlit Deployment Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [Docker Documentation](https://docs.docker.com/)
- [Heroku Python Guide](https://devcenter.heroku.com/articles/getting-started-with-python)

---

## 🎯 Recommended Deployment Path

**For beginners:** Streamlit Cloud (Option 1)  
**For production:** Docker + Cloud Platform (Option 2)  
**For full control:** VPS with systemd (Option 4)

---

**Need help?** Check the project README or open an issue on GitHub.

