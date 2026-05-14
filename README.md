# PSV Infotech — Full Stack Website

A production-ready 3D website with AI chatbot, contact system, and email integration.

## 📁 Project Structure

```
psv-infotech/
├── frontend/
│   ├── index.html        # Main HTML with all sections
│   ├── style.css         # Dark neon UI styles
│   └── script.js         # Three.js, animations, chatbot, forms
│
├── backend/
│   ├── app.py            # Flask API server
│   ├── requirements.txt  # Python dependencies
│   ├── .env.example      # Environment variable template
│   └── database.db       # SQLite DB (auto-created on first run)
│
└── README.md
```

---

## 🚀 Quick Start

### 1. Frontend (No build needed!)

Just open `frontend/index.html` in a browser for local testing.

For production, serve via any web host (Netlify, Vercel, Nginx, etc.)

---

### 2. Backend Setup

#### Prerequisites
- Python 3.9+
- pip

#### Steps

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your values (see Configuration section below)

# Run the server
python app.py
```

The backend starts at: `http://localhost:5000`

---

## ⚙️ Configuration

Edit `backend/.env`:

### Email (Gmail SMTP)
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Go to App Passwords → Generate a 16-character password
4. Fill in:
```
EMAIL_USER=your_gmail@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop   (no spaces)
EMAIL_TO=contact@psvinfotech.com
```

### OpenAI (optional — chatbot works without it)
1. Get your key at https://platform.openai.com/api-keys
2. Fill in:
```
OPENAI_API_KEY=sk-...
```
> If left blank, the chatbot uses built-in smart fallback responses.

### Frontend → Backend Connection
In `frontend/script.js`, line 4:
```js
const BACKEND_URL = 'http://localhost:5000'; // change for production
```

---

## 📡 API Endpoints

### POST /contact
Submit a contact form.

**Request:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+91 98765 43210",
  "service": "web",
  "message": "I need a website for my business."
}
```

**Response:**
```json
{ "success": true, "message": "Thank you! We'll get back to you within 24 hours.", "id": 1 }
```

---

### GET /messages
View all contact messages (admin only).

**Headers:**
```
Authorization: Bearer psv-admin-secret-2025
```

**Query params:** `?page=1&limit=20`

---

### POST /chat
AI chatbot endpoint.

**Request:**
```json
{
  "message": "What are your web development prices?",
  "session": "optional-session-id",
  "history": []
}
```

**Response:**
```json
{ "success": true, "reply": "Our websites start at ₹15,000..." }
```

---

## 🌐 Production Deployment

### Frontend — Netlify (Free)
1. Drag & drop the `frontend/` folder to https://app.netlify.com/drop
2. Done! Your site is live.

### Backend — Railway (Free tier)
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

Or use **Render.com** (also free):
1. Push backend to GitHub
2. New Web Service → connect repo
3. Build: `pip install -r requirements.txt`
4. Start: `gunicorn app:app`
5. Add env vars in the Render dashboard

### Update Frontend Backend URL
After deploying backend, update `script.js`:
```js
const BACKEND_URL = 'https://your-backend.railway.app';
```

---

## 🎨 Customization

### Company Info
Update in `frontend/index.html`:
- Company name, phone, email, address
- WhatsApp number in `#whatsapp-btn` href

### Colors
Edit CSS variables in `frontend/style.css`:
```css
:root {
  --neon-blue: #00d4ff;
  --neon-purple: #7b2fff;
  --neon-pink: #ff2d78;
}
```

### Chatbot Knowledge
Edit `PSV_SYSTEM_PROMPT` in `backend/app.py` to update:
- Services & pricing
- Company details
- Response guidelines

---

## 🔐 Security Notes

- Change `ADMIN_TOKEN` in production
- Restrict CORS origins in `app.py` (replace `"*"` with your domain)
- Use HTTPS in production
- Rate limit `/chat` and `/contact` endpoints for anti-spam
- Never commit `.env` to version control

---

## 📦 Tech Stack

| Layer     | Technology |
|-----------|-----------|
| Frontend  | HTML5, CSS3, JavaScript |
| 3D        | Three.js |
| Animations| GSAP, CSS animations |
| Backend   | Python, Flask |
| Database  | SQLite |
| AI        | OpenAI GPT-3.5 / Fallback |
| Email     | Gmail SMTP |
| WhatsApp  | wa.me deep link |

---

## 📞 Support

Built by PSV Infotech  
📧 contact@psvinfotech.com  
📱 +91 99999 99999
