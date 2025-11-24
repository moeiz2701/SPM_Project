# Deployment Guide - Loyalty AI Agent

## 🚀 Your Agent is Ready for Deployment!

All necessary files have been created for deployment.

---

## 📦 Deployment Files Created

- ✅ `render.yaml` - Render.com configuration
- ✅ `Procfile` - Heroku/Railway configuration  
- ✅ `runtime.txt` - Python version specification
- ✅ `run_api.py` - Production launcher script
- ✅ Updated `api/agent_api.py` with CORS support

---

## 🌐 Option 1: Deploy to Render (Recommended - FREE)

### Step 1: Push to GitHub

```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Prepare agent for deployment with public JSON API"

# Create a new repository on GitHub: https://github.com/new
# Then push your code
git remote add origin https://github.com/YOUR_USERNAME/SPM_Project.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Render

1. Go to https://render.com and sign up/login with GitHub
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository (`SPM_Project`)
4. Configure:
   - **Name**: `loyalty-agent-api`
   - **Environment**: `Python 3`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api.agent_api:app --host 0.0.0.0 --port $PORT`
5. Click **"Create Web Service"**

### Step 3: Wait for Deployment (5-10 minutes)

Render will:
- Install dependencies
- Start your API
- Give you a public URL

### Your API URL will be:
```
https://loyalty-agent-api.onrender.com
```

---

## 🧪 Testing Your Deployed API

### Test Locally First:

```bash
# Start the server
python run_api.py

# In another terminal, test it
python test_public_api.py
```

### Test Deployed API:

```bash
# Replace with your actual Render URL
python test_public_api.py https://loyalty-agent-api.onrender.com
```

---

## 📡 API Endpoints (JSON Only)

All endpoints accept and return **JSON only**.

### 1. Root Endpoint
```bash
GET /
```

**Response (JSON):**
```json
{
  "message": "Welcome to Loyalty AI Agent API",
  "version": "1.0.0",
  "status": "online",
  "deployed": true,
  "endpoints": {...}
}
```

### 2. Health Check
```bash
GET /health
```

**Response (JSON):**
```json
{
  "status": "healthy",
  "uptime_seconds": 123.45,
  "customers_loaded": 1000,
  "environment": "production"
}
```

### 3. Analyze Customer
```bash
POST /analyze
Content-Type: application/json
```

**Request (JSON):**
```json
{
  "customer_id": "CUST000001",
  "include_history": false
}
```

**Response (JSON):**
```json
{
  "customer_id": "CUST000001",
  "segment": "Champion",
  "rfm_score": 9.2,
  "churn_risk": "Low",
  "predicted_retention": 0.85,
  "recommended_reward": "vip_access",
  "reward_details": {...},
  "confidence": 0.92,
  "strategy": "Retention Focus"
}
```

### 4. Get Metrics
```bash
GET /metrics
```

**Response (JSON):**
```json
{
  "total_customers": 1000,
  "avg_retention_rate": 0.78,
  "segment_distribution": {...},
  "loyalty_tier_distribution": {...}
}
```

---

## 🔗 Integration Examples

### Python
```python
import requests

BASE_URL = "https://loyalty-agent-api.onrender.com"

# Analyze customer
response = requests.post(
    f"{BASE_URL}/analyze",
    json={"customer_id": "CUST000001"}
)
result = response.json()
print(f"Retention: {result['predicted_retention']:.2%}")
```

### cURL
```bash
curl -X POST https://loyalty-agent-api.onrender.com/analyze \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"CUST000001"}'
```

### JavaScript/Node.js
```javascript
const response = await fetch('https://loyalty-agent-api.onrender.com/analyze', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({customer_id: 'CUST000001'})
});
const data = await response.json();
console.log(data);
```

---

## 🛡️ Security Notes

**Current Configuration:**
- ✅ CORS enabled for all origins (for development/testing)
- ✅ JSON-only communication
- ✅ Input validation via Pydantic

**For Production (After Testing):**

Update `api/agent_api.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
```

---

## 🔍 Monitoring Your Deployed API

### View Logs on Render:
1. Go to your Render dashboard
2. Click on your service
3. Click "Logs" tab to see real-time logs

### Check API Documentation:
Visit: `https://loyalty-agent-api.onrender.com/docs`

---

## 🚨 Troubleshooting

### Issue: Deployment Failed
- Check Render logs for errors
- Verify `requirements.txt` has all dependencies
- Ensure Python version matches (3.8.20)

### Issue: API Returns 404
- Check the endpoint URL is correct
- Verify customer ID exists (use CUST000001 for testing)

### Issue: Slow Response
- First request on Render free tier may be slow (cold start)
- Subsequent requests will be faster

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Render service created and deployed
- [ ] Test `/health` endpoint returns 200
- [ ] Test `/analyze` with valid customer ID
- [ ] API documentation accessible at `/docs`
- [ ] Share public URL with team

---

## 📞 Your Public API URL

After deployment, your API will be available at:

```
https://loyalty-agent-api.onrender.com
```

Share this URL with:
- Team members for integration
- Other agents in your multi-agent system
- Frontend applications
- Mobile apps

---

## 🎉 Next Steps

1. **Deploy to Render** (follow steps above)
2. **Test with `test_public_api.py`**
3. **Share API URL with team**
4. **Document your API endpoints**
5. **Integrate with frontend/dashboard** (Phase 3)

---

**Need Help?**
- Render Docs: https://render.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com
- Your API Docs: `https://your-url.com/docs`
