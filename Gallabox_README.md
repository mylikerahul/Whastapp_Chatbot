
# 🌐 README #2: GALLABOX WEBHOOK & NGROK SETUP

```markdown
# 🔗 Gallabox Webhook & Ngrok Setup Guide

> **Complete guide to connect your WhatsApp Bot with Gallabox using Ngrok**

---

## 📑 Table of Contents

- [🎯 Overview](#-overview)
- [📋 Prerequisites](#-prerequisites)
- [1️⃣ Gallabox Account Setup](#1️⃣-gallabox-account-setup)
- [2️⃣ Getting Gallabox API Credentials](#2️⃣-getting-gallabox-api-credentials)
- [3️⃣ Installing Ngrok](#3️⃣-installing-ngrok)
- [4️⃣ Running Ngrok](#4️⃣-running-ngrok)
- [5️⃣ Configuring Gallabox Webhook](#5️⃣-configuring-gallabox-webhook)
- [6️⃣ Testing the Connection](#6️⃣-testing-the-connection)
- [🚀 Production Deployment (Without Ngrok)](#-production-deployment-without-ngrok)
- [🛠️ Troubleshooting](#️-troubleshooting)
- [❓ FAQ](#-faq)

---

## 🎯 Overview

This guide will help you:
- ✅ Create and configure Gallabox account
- ✅ Get API credentials from Gallabox dashboard
- ✅ Install and run Ngrok for local development
- ✅ Connect Gallabox webhook to your bot
- ✅ Test end-to-end WhatsApp messaging

**What is Ngrok?**  
Ngrok creates a secure public URL for your local server, allowing Gallabox to send webhook events to your development machine.

```
┌─────────────┐         ┌─────────┐         ┌──────────────┐
│  WhatsApp   │ ──────> │ Gallabox│ ──────> │ Ngrok URL    │
│   Message   │         │  Cloud  │         │ (Public)     │
└─────────────┘         └─────────┘         └──────┬───────┘
                                                    │
                                            ┌───────▼────────┐
                                            │ Your Local Bot │
                                            │ (localhost:8000)│
                                            └────────────────┘
```

---

## 📋 Prerequisites

Before starting, ensure you have:

- ✅ **WhatsApp Business Account** (or willing to create one)
- ✅ **Valid phone number** for WhatsApp Business verification
- ✅ **Bot application running** on `localhost:8000` (see README #1)
- ✅ **Internet connection** for Ngrok tunneling

---

## 1️⃣ Gallabox Account Setup

### Step 1: Sign Up for Gallabox

1. Visit [**Gallabox.com**](https://www.gallabox.com/)
2. Click **"Start Free Trial"** or **"Sign Up"**
3. Fill in your details:
   - Business Name: `Sotheby's International Realty`
   - Email: `your-email@company.com`
   - Phone: Your business number
   - Industry: `Real Estate`

### Step 2: Verify Your Email
- Check your inbox for verification email
- Click the verification link
- Complete your profile setup

### Step 3: Connect WhatsApp Business

1. **In Gallabox Dashboard:**
   - Go to **Settings** → **Channels**
   - Click **"Connect WhatsApp"**

2. **Choose Connection Method:**
   - **Option A:** WhatsApp Business API (Recommended for production)
   - **Option B:** WhatsApp Business App (Quick setup)

3. **Follow On-Screen Instructions:**
   - Scan QR code with WhatsApp Business app
   - Or enter your business phone number for verification

4. **Wait for Approval:**
   - Meta (Facebook) will review your business (24-48 hours)
   - You'll receive confirmation email when approved

---

## 2️⃣ Getting Gallabox API Credentials

### Step 1: Access API Settings

1. Log in to [**Gallabox Dashboard**](https://app.gallabox.com/)
2. Navigate to: **Settings** ⚙️ → **API & Webhooks**

### Step 2: Generate API Key

```
┌─────────────────────────────────────────────────┐
│  🔐 API Credentials                             │
├─────────────────────────────────────────────────┤
│                                                 │
│  API Key:    gallabox_live_xxxxxxxxxxxxxxxxxx   │
│  [Copy]      [Regenerate]                       │
│                                                 │
│  API Secret: sk_live_yyyyyyyyyyyyyyyyyyyy       │
│  [Copy]      [Show]                             │
│                                                 │
│  Phone ID:   103xxxxxxxxxx                      │
│  [Copy]                                         │
└─────────────────────────────────────────────────┘
```

1. Click **"Generate API Key"** (if not already created)
2. **Copy** the following values immediately:
   - ✅ **API Key** → Save to `.env` as `GALLABOX_API_KEY`
   - ✅ **API Secret** → Save to `.env` as `GALLABOX_API_SECRET`
   - ✅ **Phone Number ID** → Save to `.env` as `GALLABOX_PHONE_ID`

### Step 3: Update Your `.env` File

Open your `.env` file and add:

```env
# Gallabox Configuration
GALLABOX_API_KEY=gallabox_live_abcd1234efgh5678ijkl
GALLABOX_API_SECRET=sk_live_xyz789abc123def456ghi
GALLABOX_PHONE_ID=1031234567890
```

> ⚠️ **Security Warning:** Never commit `.env` file to Git!

---

## 3️⃣ Installing Ngrok

Ngrok provides a public URL for your local development server.

### 🪟 **Windows Installation**

#### Method 1: Using Chocolatey
```bash
# Install Chocolatey (if not installed)
# Run PowerShell as Administrator:
Set-ExecutionPolicy Bypass -Scope Process -Force;
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install Ngrok
choco install ngrok
```

#### Method 2: Manual Download
1. Go to [**ngrok.com/download**](https://ngrok.com/download)
2. Download **Windows (64-bit)** version
3. Extract `ngrok.exe` to `C:\ngrok\`
4. Add to PATH:
   ```bash
   # Add this to System Environment Variables
   C:\ngrok
   ```

### 🍎 **Mac Installation**

```bash
# Using Homebrew (recommended)
brew install ngrok/ngrok/ngrok

# Or download manually from ngrok.com/download
```

### 🐧 **Linux Installation**

```bash
# Ubuntu/Debian
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
  echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list && \
  sudo apt update && sudo apt install ngrok

# Or using snap
sudo snap install ngrok
```

### Verify Installation

```bash
ngrok version
# Output: ngrok version 3.x.x
```

---

### 🔑 Ngrok Authentication (Required)

1. **Create Free Ngrok Account:**
   - Go to [**dashboard.ngrok.com/signup**](https://dashboard.ngrok.com/signup)
   - Sign up with email or GitHub

2. **Get Your Auth Token:**
   - After login, go to [**dashboard.ngrok.com/get-started/your-authtoken**](https://dashboard.ngrok.com/get-started/your-authtoken)
   - Copy your authtoken (looks like: `2abcd1234efGH5678_ijKLMnopQRstUVwxYZ`)

3. **Configure Ngrok:**
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
   ```

   Example:
   ```bash
   ngrok config add-authtoken 2abcd1234efGH5678_ijKLMnopQRstUVwxYZ
   ```

   You should see:
   ```
   Authtoken saved to configuration file: /Users/yourname/.ngrok2/ngrok.yml
   ```

---

## 4️⃣ Running Ngrok

### Step 1: Start Your Bot Application

```bash
# Terminal 1: Run your bot
cd whatsapp-bot
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 2: Start Ngrok in New Terminal

```bash
# Terminal 2: Run Ngrok
ngrok http 8000
```

**Expected Output:**
```
ngrok                                                                                                           

Session Status                online
Account                       Your Name (Plan: Free)
Version                       3.3.0
Region                        United States (us)
Latency                       45ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abcd-1234-efgh-5678.ngrok-free.app -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

### Step 3: Copy Your Public URL

From the output above, copy the **HTTPS URL**:
```
https://abcd-1234-efgh-5678.ngrok-free.app
```

> ⚠️ **Important:** Always use the **HTTPS** URL (not HTTP)

### 🎛️ Ngrok Web Interface

You can monitor webhook requests in real-time:

1. Open browser: [**http://localhost:4040**](http://localhost:4040)
2. You'll see:
   - All incoming HTTP requests
   - Request/response details
   - Replay requests for debugging

---

## 5️⃣ Configuring Gallabox Webhook

### Step 1: Access Webhook Settings

1. Go to [**Gallabox Dashboard**](https://app.gallabox.com/)
2. Navigate: **Settings** ⚙️ → **API & Webhooks** → **Webhook Configuration**

### Step 2: Enter Webhook URL

```
┌────────────────────────────────────────────────────────┐
│  🔔 Webhook Configuration                              │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Webhook URL:                                          │
│  ┌──────────────────────────────────────────────────┐ │
│  │ https://your-ngrok-url.ngrok-free.app/webhook/   │ │
│  │ gallabox                                         │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  Webhook Events: ☑ All  or select specific:           │
│  ☑ message.received                                   │
│  ☑ message.delivered                                  │
│  ☑ message.read                                       │
│  ☑ message.failed                                     │
│                                                        │
│  [Test Webhook]  [Save Configuration]                 │
└────────────────────────────────────────────────────────┘
```

**Your Complete Webhook URL:**
```
https://abcd-1234-efgh-5678.ngrok-free.app/webhook/gallabox
```

> **Format:** `{NGROK_URL}/webhook/gallabox`

### Step 3: Test Webhook Connection

1. Click **"Test Webhook"** button in Gallabox
2. You should see:
   ```
   ✅ Webhook test successful!
   Response: 200 OK
   ```

3. In your **Ngrok dashboard** (http://localhost:4040), you'll see:
   ```
   POST /webhook/gallabox  200 OK
   ```

### Step 4: Save Configuration

Click **"Save Configuration"** to apply changes.

---

## 6️⃣ Testing the Connection

### End-to-End Test

1. **Send Test Message via WhatsApp:**
   - Open WhatsApp
   - Send message to your Gallabox business number
   - Example: `"Create a ticket for laptop issue"`

2. **Monitor Ngrok Dashboard:**
   - Open http://localhost:4040
   - You should see incoming POST request:
     ```
     POST /webhook/gallabox
     Status: 200 OK
     Size: 1.2 KB
     Duration: 234ms
     ```

3. **Check Bot Logs:**
   ```bash
   # In your terminal running the bot, you should see:
   INFO: Received message from +971xxxxxxxxx
   INFO: Intent detected: CREATE_TICKET
   INFO: Creating Jira ticket...
   INFO: Ticket SUP-123 created successfully
   INFO: Sending response via Gallabox
   ```

4. **Verify WhatsApp Response:**
   - You should receive bot reply:
     ```
     ✅ Your ticket SUP-123 has been created.

     Summary: Laptop issue
     Team: IT Support
     Priority: Medium

     We'll notify you when it's updated.
     ```

5. **Verify Jira Ticket:**
   - Open your Jira board
   - Confirm ticket SUP-123 exists with correct details

---

## 🚀 Production Deployment (Without Ngrok)

Ngrok is **only for development**. For production, you need a permanent URL.

### Option 1: Deploy to Cloud Server

#### Using AWS EC2, DigitalOcean, or Azure

1. **Deploy your bot to server** (see README #1)
2. **Get public IP or domain:**
   - Example: `https://bot.sothebysrealty.ae`

3. **Update Gallabox webhook:**
   ```
   https://bot.sothebysrealty.ae/webhook/gallabox
   ```

### Option 2: Use Gallabox Cloud Functions (if supported)

Some platforms offer serverless deployment:
```bash
# Deploy to Gallabox cloud (check their docs)
gallabox deploy --function whatsapp-bot
```

### SSL Certificate Required

Production webhooks **must use HTTPS**. Get free SSL certificate:

```bash
# Using Let's Encrypt with Certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d bot.sothebysrealty.ae
```

---

## 🛠️ Troubleshooting

### Issue 1: Ngrok URL Changes Every Restart

**Problem:** Free Ngrok gives random URL each time

**Solution 1 - Ngrok Paid Plan ($8/month):**
```bash
# Get static domain: yourname.ngrok.io
ngrok http 8000 --domain=yourname.ngrok.io
```

**Solution 2 - Use Localtunnel (Free Alternative):**
```bash
npm install -g localtunnel
lt --port 8000 --subdomain yourbot
# URL: https://yourbot.loca.lt
```

---

### Issue 2: Webhook Returns 404 Not Found

**Possible Causes:**
- ❌ Wrong endpoint path
- ❌ Bot not running
- ❌ Ngrok not forwarding correctly

**Solutions:**

✅ **Verify endpoint exists:**
```bash
curl http://localhost:8000/webhook/gallabox
# Should return: 405 Method Not Allowed (because GET not allowed)

# Try POST:
curl -X POST http://localhost:8000/webhook/gallabox
# Should return: 200 OK or error message
```

✅ **Check bot routes:**
```python
# In routes/webhook.py, ensure this exists:
@router.post("/webhook/gallabox")
async def gallabox_webhook(request: Request):
    # Your webhook handler
    ...
```

✅ **Test Ngrok forwarding:**
```bash
# Test your Ngrok URL
curl https://your-ngrok-url.ngrok-free.app/health
# Should return: {"status": "healthy"}
```

---

### Issue 3: Messages Not Received

**Check 1: Verify Ngrok is Running**
```bash
# Look for "Session Status: online"
ngrok http 8000
```

**Check 2: Test Webhook Manually**
```bash
# Send test request to your Ngrok URL
curl -X POST https://your-ngrok-url.ngrok-free.app/webhook/gallabox \
  -H "Content-Type: application/json" \
  -d '{"test": "message"}'
```

**Check 3: Review Ngrok Logs**
- Open http://localhost:4040
- Check if requests are arriving
- Look for error codes (500, 400, etc.)

**Check 4: Bot Application Logs**
```bash
# Check your bot terminal for errors
# Look for:
ERROR: Exception in webhook handler
ERROR: Failed to process message
```

---

### Issue 4: Gallabox Returns "Invalid Signature"

**Problem:** Webhook signature verification fails

**Solution:** Update signature validation in your code:

```python
# In routes/webhook.py
import hmac
import hashlib

def verify_gallabox_signature(payload: bytes, signature: str):
    expected = hmac.new(
        settings.GALLABOX_API_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)

@router.post("/webhook/gallabox")
async def gallabox_webhook(request: Request):
    # Get signature from header
    signature = request.headers.get("X-Gallabox-Signature")
    
    # Read raw body
    body = await request.body()
    
    # Verify signature
    if not verify_gallabox_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process webhook...
```

---

### Issue 5: "Ngrok Failed to Start"

**Error:**
```
ERROR:  ngrok failed to start: command not found
```

**Solutions:**

✅ **Windows:**
```bash
# Add ngrok to PATH
# OR run with full path:
C:\ngrok\ngrok.exe http 8000
```

✅ **Mac:**
```bash
# Reinstall with Homebrew
brew reinstall ngrok
```

✅ **Linux:**
```bash
# Verify installation
which ngrok
# If not found, reinstall
```

---

### Issue 6: Firewall Blocking Ngrok

**Symptoms:**
- Ngrok shows "Session Status: online"
- But webhook requests timeout

**Solutions:**

✅ **Allow Ngrok in Firewall:**
```bash
# Windows Firewall
New-NetFirewallRule -DisplayName "Ngrok" -Direction Inbound -Program "C:\ngrok\ngrok.exe" -Action Allow

# Mac Firewall
# System Preferences → Security & Privacy → Firewall → Firewall Options
# Add ngrok to allowed applications
```

✅ **Check Corporate Proxy:**
```bash
# If behind corporate proxy, configure Ngrok:
ngrok http 8000 --proxy http://proxy.company.com:8080
```

---

## ❓ FAQ

### Q1: Is Ngrok free?
**A:** Yes! Free tier includes:
- ✅ Random HTTPS URLs
- ✅ Up to 40 connections/minute
- ❌ No custom domains
- ❌ URLs change on restart

Paid plans start at $8/month for static domains.

---

### Q2: Can I use alternatives to Ngrok?

**A:** Yes! Popular alternatives:

| Service | Free Tier | Static URL | Setup |
|---------|-----------|------------|-------|
| **Ngrok** | ✅ Yes | ❌ Paid only | `ngrok http 8000` |
| **Localtunnel** | ✅ Yes | ✅ Yes | `lt --port 8000 --subdomain mybot` |
| **Serveo** | ✅ Yes | ✅ Yes | `ssh -R 80:localhost:8000 serveo.net` |
| **Cloudflare Tunnel** | ✅ Yes | ✅ Yes | Requires Cloudflare account |

---

### Q3: What happens when I close Ngrok?

**A:** Webhook stops working because public URL disappears.

**For Development:**
- Just restart Ngrok when needed
- Update webhook URL in Gallabox each time (if using free tier)

**For Production:**
- Deploy to permanent server (no Ngrok needed)
- Use static domain

---

### Q4: How do I secure my webhook?

✅ **Best Practices:**

1. **Verify Signatures:**
   ```python
   # Always validate X-Gallabox-Signature header
   verify_gallabox_signature(request)
   ```

2. **Use HTTPS Only:**
   ```python
   # Reject non-HTTPS in production
   if not request.url.scheme == "https":
       raise HTTPException(403)
   ```

3. **IP Whitelisting (optional):**
   ```python
   ALLOWED_IPS = ["52.89.214.238", "54.218.53.128"]  # Gallabox IPs
   
   if request.client.host not in ALLOWED_IPS:
       raise HTTPException(403)
   ```

4. **Rate Limiting:**
   ```python
   from slowapi import Limiter
   
   @router.post("/webhook/gallabox")
   @limiter.limit("100/minute")
   async def webhook(...):
       ...
   ```

---

### Q5: Can I test without WhatsApp?

**A:** Yes! Use Postman or curl to send test webhooks:

```bash
curl -X POST https://your-ngrok-url.ngrok-free.app/webhook/gallabox \
  -H "Content-Type: application/json" \
  -d '{
    "from": "971501234567",
    "body": "Create a ticket for laptop issue",
    "type": "text",
    "timestamp": 1234567890
  }'
```

---

## 📞 Support

**Issues with this guide?**
- 📧 Email: sw@sothebysrealty.ae
- 📚 Ngrok Docs: [ngrok.com/docs](https://ngrok.com/docs)
- 📚 Gallabox Docs: [docs.gallabox.com](https://docs.gallabox.com)

---

## ✅ Setup Verification Checklist

Before declaring success, verify:

- [ ] Gallabox account created and WhatsApp connected
- [ ] API credentials copied to `.env` file
- [ ] Ngrok installed and authenticated
- [ ] Bot application running on port 8000
- [ ] Ngrok tunnel active with HTTPS URL
- [ ] Webhook URL configured in Gallabox dashboard
- [ ] Test webhook returns 200 OK
- [ ] Test WhatsApp message received by bot
- [ ] Bot creates ticket in Jira
- [ ] Response sent back to WhatsApp
- [ ] Ngrok dashboard shows webhook traffic

---

**🎉 Congratulations!** Your WhatsApp bot is now connected to Gallabox!

---

**Last Updated:** January 2024  
**Version:** 2.0.0  
**Maintained by:** Development Team
```

---

# 📥 How to Use These READMEs

### For README #1 (Project Setup):
```bash
# Save as README.md in project root
/whatsapp-bot/README.md
```

### For README #2 (Webhook Setup):
```bash
# Save as WEBHOOK_SETUP.md
/whatsapp-bot/WEBHOOK_SETUP.md
```

---

## 🎨 Bonus: Create `.env.example` Template

Create this file so your boss knows what credentials are needed:

```bash
# .env.example (commit this to Git as template)

# ============================================
# 🤖 OPENAI CONFIGURATION
# ============================================
OPENAI_API_KEY=sk-proj-your-key-here

# ============================================
# 📝 JIRA CONFIGURATION
# ============================================
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-token-here
JIRA_DEFAULT_PROJECT=SUP

# ============================================
# 💬 GALLABOX CONFIGURATION (Production)
# ============================================
GALLABOX_API_KEY=your_gallabox_api_key_here
GALLABOX_API_SECRET=your_gallabox_api_secret_here
GALLABOX_PHONE_ID=your_phone_number_id

# ============================================
# 📱 TWILIO CONFIGURATION (Development/Testing)
# ============================================
TWILIO_ACCOUNT_SID=your_twilio_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# ============================================
# ☁️ AWS S3 CONFIGURATION (Optional)
# ============================================
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
AWS_BUCKET_NAME=whatsapp-support-logs

# ============================================
# 🔧 APPLICATION SETTINGS
# ============================================
ENVIRONMENT=development
BOT_MODE=twilio
DEBUG=True

# ============================================
# 🌍 BUSINESS CONFIGURATION
# ============================================
BUSINESS_NAME=Sotheby's International Realty
SUPPORT_EMAIL=sw@sothebysrealty.ae
BUSINESS_WEBSITE=https://www.sothebysrealty.ae

# ============================================
# 💰 COST TRACKING
# ============================================
COST_TRACKING_ENABLED=True
OPENAI_COST_PER_1K_TOKENS=0.01
```

---

These READMEs are:
✅ **Comprehensive** - Cover everything from setup to troubleshooting  
✅ **Beautiful** - Professional formatting with emojis and tables  
✅ **Beginner-friendly** - Step-by-step with screenshots descriptions  
✅ **Production-ready** - Include deployment and security best practices  

Your boss can follow these guides without any prior knowledge! 🚀