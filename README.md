# 📋 README Files Created

I've created **2 comprehensive README files** with beautiful UI and complete instructions. Copy each one into separate markdown files.

---

# 🚀 README #1: PROJECT SETUP & DEPLOYMENT GUIDE

```markdown
# 🤖 WhatsApp AI Support Agent - Project Setup Guide

> **Intelligent Jira-integrated WhatsApp Bot for Enterprise Support**  
> Built with FastAPI, OpenAI GPT-4, Jira Cloud API, and Gallabox/Twilio

---

## 📑 Table of Contents

- [🎯 Project Overview](#-project-overview)
- [✨ Key Features](#-key-features)
- [📋 Prerequisites](#-prerequisites)
- [⚙️ Environment Setup](#️-environment-setup)
- [📦 Dependency Installation](#-dependency-installation)
- [🔧 Configuration Guide](#-configuration-guide)
- [🔄 Switching from Twilio to Gallabox](#-switching-from-twilio-to-gallabox)
- [▶️ Running the Application](#️-running-the-application)
- [🚀 Deployment](#-deployment)
- [🛠️ Troubleshooting](#️-troubleshooting)
- [📊 Project Structure](#-project-structure)

---

## 🎯 Project Overview

This WhatsApp AI Agent revolutionizes customer support by:
- 🧠 Understanding natural language (no button menus)
- 🎫 Auto-creating & managing Jira tickets
- 🎯 Smart routing to correct teams (Marketing, IT, Salesforce)
- 👑 VIP detection & priority escalation
- 😟 Sentiment analysis for frustrated customers
- 🌍 Bilingual support (English/Arabic)
- ☁️ AWS logging for training & compliance
- 💰 Cost tracking (OpenAI + Gallabox usage)

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **AI Intent Detection** | Classifies: Create Ticket, Check Status, Update, Close |
| **Smart Ticket Preview** | Shows preview + confirmation before creating |
| **Project Intelligence** | Auto-selects correct Jira board (SUP, IT, MKT) |
| **Attachment Handling** | Screenshots/docs auto-attached to tickets |
| **Conversation Memory** | Remembers context across messages |
| **Real-time Status** | Instant Jira status updates via WhatsApp |
| **Analytics Dashboard** | Tracks tickets, resolution time, costs |

---

## 📋 Prerequisites

Before you begin, ensure you have:

### 🖥️ System Requirements
- **Python**: 3.9 or higher ([Download](https://www.python.org/downloads/))
- **pip**: Latest version (comes with Python)
- **Git**: For version control ([Download](https://git-scm.com/))

### 🔑 Required Accounts & Credentials

| Service | Purpose | Signup Link |
|---------|---------|-------------|
| **Jira Cloud** | Ticket management | [atlassian.com](https://www.atlassian.com/software/jira) |
| **OpenAI** | GPT-4 AI model | [platform.openai.com](https://platform.openai.com/) |
| **Gallabox** | WhatsApp Business API | [gallabox.com](https://www.gallabox.com/) |
| **AWS S3** | Log storage (optional) | [aws.amazon.com](https://aws.amazon.com/s3/) |

---

## ⚙️ Environment Setup

### 1️⃣ Clone the Repository

```bash
# Clone the project
git clone <your-repository-url>
cd whatsapp-bot

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### 2️⃣ Verify Python Installation

```bash
python --version
# Should show: Python 3.9.x or higher

pip --version
# Should show: pip 23.x or higher
```

---

## 📦 Dependency Installation

### Install All Requirements

```bash
pip install -r requirements.txt
```

### 📄 requirements.txt Contents

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
httpx==0.25.2
openai==1.3.7
jira==3.5.2
boto3==1.29.7
python-multipart==0.0.6
phonenumbers==8.13.26
langdetect==1.0.9
twilio==8.10.0
```

### Verify Installation

```bash
pip list
# Should show all packages installed successfully
```

---

## 🔧 Configuration Guide

### 1️⃣ Create `.env` File

Create a `.env` file in the project root:

```bash
# Copy from template
cp .env.example .env

# Edit with your credentials
nano .env  # or use any text editor
```

### 2️⃣ Environment Variables Explained

```env
# ============================================
# 🤖 OPENAI CONFIGURATION
# ============================================
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
# Get from: https://platform.openai.com/api-keys
# Model used: gpt-4-turbo-preview

# ============================================
# 📝 JIRA CONFIGURATION
# ============================================
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=ATATTxxxxxxxxxxxxxxxxxxxxx
# Get token from: https://id.atlassian.com/manage-profile/security/api-tokens

JIRA_DEFAULT_PROJECT=SUP
# Your default Jira project key (SUP, IT, MKT, etc.)

# ============================================
# 💬 GALLABOX CONFIGURATION (Production)
# ============================================
GALLABOX_API_KEY=your_gallabox_api_key_here
GALLABOX_API_SECRET=your_gallabox_api_secret_here
GALLABOX_PHONE_ID=your_phone_number_id

# ============================================
# 📱 TWILIO CONFIGURATION (Development/Testing)
# ============================================
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
# Twilio Sandbox number for testing

# ============================================
# ☁️ AWS S3 CONFIGURATION (Optional - for logs)
# ============================================
AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
AWS_BUCKET_NAME=whatsapp-support-logs

# ============================================
# 🔧 APPLICATION SETTINGS
# ============================================
ENVIRONMENT=development
# Options: development, production

BOT_MODE=twilio
# Options: twilio (testing), gallabox (production)

DEBUG=True
# Set to False in production

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
# Adjust based on your OpenAI pricing plan
```

### 3️⃣ Getting Your Credentials

#### 🔑 Jira API Token
1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **"Create API token"**
3. Give it a name: `WhatsApp Bot`
4. Copy the token immediately (won't be shown again)

#### 🤖 OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Click **"Create new secret key"**
3. Name it: `Jira WhatsApp Bot`
4. Copy and save securely

#### 💬 Gallabox Credentials
See [README #2 - Gallabox Setup Guide](#) for detailed instructions

---

## 🔄 Switching from Twilio to Gallabox

### Current Setup (Development)
```env
BOT_MODE=twilio
ENVIRONMENT=development
```

### For Production Deployment

#### Step 1: Update `.env`
```env
# Change these lines:
BOT_MODE=gallabox          # ← Changed from 'twilio'
ENVIRONMENT=production     # ← Changed from 'development'
DEBUG=False                # ← Security: Disable debug mode

# Ensure Gallabox credentials are set:
GALLABOX_API_KEY=your_actual_key_here
GALLABOX_API_SECRET=your_actual_secret_here
GALLABOX_PHONE_ID=your_phone_id_here
```

#### Step 2: Update Code (if needed)

The code automatically switches based on `BOT_MODE`. Verify in `services/gallabox_service.py`:

```python
# ✅ This is already implemented - no changes needed
from config.settings import settings

if settings.BOT_MODE == "gallabox":
    # Use Gallabox for sending messages
    send_message_via_gallabox(to, message)
else:
    # Use Twilio for testing
    send_message_via_twilio(to, message)
```

#### Step 3: Update Webhook Endpoint

In `routes/webhook.py`, ensure Gallabox webhook is active:

```python
@router.post("/webhook/gallabox")
async def gallabox_webhook(request: Request):
    """Production webhook for Gallabox"""
    # This will be used when BOT_MODE=gallabox
    ...
```

#### Step 4: Test Before Going Live

```bash
# Test in development first
BOT_MODE=gallabox ENVIRONMENT=development python main.py

# Monitor logs for errors
# Send test message via WhatsApp
# Verify ticket creation in Jira
```

---

## ▶️ Running the Application

### Development Mode (Local Testing)

```bash
# Activate virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Run with auto-reload (for development)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Production Mode

```bash
# Set environment to production
export ENVIRONMENT=production  # Mac/Linux
set ENVIRONMENT=production     # Windows

# Run with Gunicorn (recommended for production)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Verify Application is Running

```bash
# Test health check endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "mode": "gallabox",
  "jira_connected": true
}
```

---

## 🚀 Deployment

### Option 1: AWS EC2 Deployment

```bash
# 1. Launch EC2 instance (Ubuntu 22.04 LTS)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. Install dependencies
sudo apt update
sudo apt install python3.9 python3-pip nginx

# 4. Clone and setup
git clone <repo-url>
cd whatsapp-bot
pip3 install -r requirements.txt

# 5. Setup systemd service
sudo nano /etc/systemd/system/whatsapp-bot.service
```

**Service file content:**
```ini
[Unit]
Description=WhatsApp Support Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/whatsapp-bot
Environment="PATH=/home/ubuntu/whatsapp-bot/venv/bin"
ExecStart=/home/ubuntu/whatsapp-bot/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 6. Start service
sudo systemctl enable whatsapp-bot
sudo systemctl start whatsapp-bot
sudo systemctl status whatsapp-bot
```

### Option 2: Docker Deployment

```dockerfile
# Dockerfile (create this file)
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t whatsapp-bot .
docker run -d -p 8000:8000 --env-file .env whatsapp-bot
```

---

## 🛠️ Troubleshooting

### Issue: Module Not Found Error

```bash
# Error: ModuleNotFoundError: No module named 'fastapi'
# Solution:
pip install -r requirements.txt --force-reinstall
```

### Issue: Jira Authentication Failed

```bash
# Error: JiraAuthenticationError
# Solution: Verify credentials
python -c "
from jira import JIRA
jira = JIRA(
    server='https://your-company.atlassian.net',
    basic_auth=('email', 'token')
)
print('✅ Jira connected:', jira.current_user())
"
```

### Issue: OpenAI API Key Invalid

```bash
# Error: AuthenticationError
# Solution: Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Issue: Port Already in Use

```bash
# Error: Address already in use
# Solution: Kill process on port 8000
# Mac/Linux:
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <process_id> /F
```

### Issue: Webhook Not Receiving Messages

1. Check Ngrok is running (see README #2)
2. Verify webhook URL in Gallabox dashboard
3. Check firewall settings
4. Review application logs:
```bash
tail -f logs/app.log
```

---

## 📊 Project Structure

```
whatsapp-bot/
├── 📄 main.py                      # FastAPI application entry
├── 📄 requirements.txt             # Python dependencies
├── 📄 .env                         # Environment variables (DO NOT COMMIT)
├── 📄 .env.example                 # Template for .env
├── 📄 README.md                    # This file
│
├── 📁 config/
│   └── settings.py                 # Configuration loader
│
├── 📁 services/                    # Business logic
│   ├── intent_service.py           # AI intent classification
│   ├── jira_service.py             # Jira API integration
│   ├── gallabox_service.py         # Gallabox messaging
│   ├── twilio_service.py           # Twilio (testing)
│   ├── smart_routing.py            # Team routing logic
│   ├── conversation_memory.py      # Session management
│   ├── sentiment_service.py        # Emotion detection
│   ├── response_service.py         # AI response generation
│   ├── analytics_service.py        # Usage metrics
│   ├── aws_service.py              # S3 logging
│   └── cost_tracker.py             # Cost monitoring
│
├── 📁 models/
│   └── schemas.py                  # Pydantic data models
│
├── 📁 routes/
│   └── webhook.py                  # API endpoints
│
└── 📁 utils/
    └── helpers.py                  # Utility functions
```

---

## 📝 Quick Start Checklist

- [ ] Python 3.9+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with all credentials
- [ ] Jira connection tested
- [ ] OpenAI API key validated
- [ ] Application runs without errors
- [ ] Webhook setup complete (see README #2)
- [ ] Test message sent via WhatsApp
- [ ] Ticket created successfully in Jira

---

## 🆘 Support

**Technical Issues:**  
Contact: sw@sothebysrealty.ae

**Documentation:**  
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Jira Python SDK](https://jira.readthedocs.io/)
- [OpenAI API Reference](https://platform.openai.com/docs)

---

## 📜 License

Proprietary - Sotheby's International Realty  
© 2024 All Rights Reserved

---

**Last Updated:** January 2024  
**Version:** 2.0.0  
**Maintainer:** Development Team
