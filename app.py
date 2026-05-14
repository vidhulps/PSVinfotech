"""
═══════════════════════════════════════════════════════
PSV INFOTECH — Backend API (Flask)
app.py

Endpoints:
  POST /contact  — Save message + send email
  GET  /messages — View all messages (admin)
  POST /chat     — AI chatbot via OpenAI
═══════════════════════════════════════════════════════
"""

import os
import json
import sqlite3
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps

from flask import Flask, request, jsonify, g, current_app
from flask_cors import CORS
# ── Try importing OpenAI ──────────────────────────────
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠  openai package not installed. Using built-in fallback responses.")

# ─────────────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, origins=["*"])  # Restrict to your domain in production

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────
# CONFIGURATION — Update these values or use .env
# ─────────────────────────────────────────────────────
class Config:
    # Email (Gmail SMTP)
    EMAIL_HOST      = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT      = int(os.getenv("EMAIL_PORT", 587))
    EMAIL_USER      = os.getenv("EMAIL_USER", "your_gmail@gmail.com")
    EMAIL_PASSWORD  = os.getenv("EMAIL_PASSWORD", "your_app_password")  # Gmail App Password
    EMAIL_TO        = os.getenv("EMAIL_TO", "contact@psvinfotech.com")  # Recipient

    # OpenAI
    OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")

    # Admin
    ADMIN_TOKEN     = os.getenv("ADMIN_TOKEN", "psv-admin-secret-2025")

    # Database
    DB_PATH         = os.getenv("DB_PATH", "database.db")

app.config.from_object(Config)

# ─────────────────────────────────────────────────────
# DATABASE HANDLING (Flask Pattern)
# ─────────────────────────────────────────────────────
def get_db():
    """Get or create a database connection for the current request context."""
    if 'db' not in g:
        g.db = sqlite3.connect(app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Create tables if they don't exist."""
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT    NOT NULL,
            email     TEXT    NOT NULL,
            phone     TEXT,
            service   TEXT    NOT NULL,
            message   TEXT    NOT NULL,
            ip        TEXT,
            created   TEXT    NOT NULL,
            email_sent INTEGER DEFAULT 0
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            session   TEXT,
            user_msg  TEXT NOT NULL,
            bot_reply TEXT NOT NULL,
            created   TEXT NOT NULL
        )
    """)
    db.commit()
    logger.info("Database initialized ✓")

# Initialize on startup
with app.app_context():
    init_db()

# ─────────────────────────────────────────────────────
# OPENAI CLIENT
# ─────────────────────────────────────────────────────
openai_client = None
if OPENAI_AVAILABLE and app.config["OPENAI_API_KEY"]:
    openai_client = OpenAI(api_key=app.config["OPENAI_API_KEY"])
    logger.info("OpenAI client initialized ✓")

# ─────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────
def validate_email(email: str) -> bool:
    import re
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email))

def sanitize(text: str, max_len: int = 2000) -> str:
    return str(text).strip()[:max_len]

def require_admin(f):
    """Decorator: require admin token in Authorization header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token != app.config["ADMIN_TOKEN"]:
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

def send_email_notification(form_data: dict) -> bool:
    """Send email notification via Gmail SMTP."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"New Contact: {form_data['name']} — {form_data['service']}"
        msg["From"]    = app.config["EMAIL_USER"]
        msg["To"]      = app.config["EMAIL_TO"]

        html = f"""
        <html><body style="font-family:Arial,sans-serif;background:#0a0f1e;color:#e8f4ff;padding:20px;">
          <div style="max-width:600px;margin:0 auto;background:#0d1b35;border:1px solid #1a3a6e;border-radius:16px;overflow:hidden;">
            <div style="background:linear-gradient(135deg,#00d4ff,#7b2fff);padding:24px;">
              <h1 style="color:white;margin:0;font-size:1.4rem;">📬 New Contact from PSV Infotech Website</h1>
            </div>
            <div style="padding:28px;">
              <table style="width:100%;border-collapse:collapse;">
                <tr><td style="padding:10px 0;color:#7ba8d4;width:120px;">Name</td>
                    <td style="padding:10px 0;font-weight:bold;">{form_data['name']}</td></tr>
                <tr><td style="padding:10px 0;color:#7ba8d4;">Email</td>
                    <td style="padding:10px 0;"><a href="mailto:{form_data['email']}" style="color:#00d4ff;">{form_data['email']}</a></td></tr>
                <tr><td style="padding:10px 0;color:#7ba8d4;">Phone</td>
                    <td style="padding:10px 0;">{form_data.get('phone','—')}</td></tr>
                <tr><td style="padding:10px 0;color:#7ba8d4;">Service</td>
                    <td style="padding:10px 0;">{form_data['service']}</td></tr>
                <tr><td style="padding:10px 0;color:#7ba8d4;">Time</td>
                    <td style="padding:10px 0;">{form_data['created']}</td></tr>
              </table>
              <div style="margin-top:20px;padding:16px;background:#0a1628;border-left:3px solid #00d4ff;border-radius:4px;">
                <p style="color:#7ba8d4;margin:0 0 8px;">Message:</p>
                <p style="margin:0;">{form_data['message']}</p>
              </div>
              <div style="margin-top:24px;text-align:center;">
                <a href="mailto:{form_data['email']}" style="background:linear-gradient(135deg,#00d4ff,#7b2fff);color:white;padding:12px 28px;border-radius:30px;text-decoration:none;font-weight:bold;display:inline-block;">Reply to {form_data['name']}</a>
              </div>
            </div>
            <div style="padding:16px;text-align:center;color:#4a7a9e;font-size:0.8rem;border-top:1px solid #1a3a6e;">
              PSV Infotech — Automated Contact Notification
            </div>
          </div>
        </body></html>
        """

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(app.config["EMAIL_HOST"], app.config["EMAIL_PORT"]) as server:
            server.ehlo()
            server.starttls()
            server.login(app.config["EMAIL_USER"], app.config["EMAIL_PASSWORD"])
            server.sendmail(app.config["EMAIL_USER"], app.config["EMAIL_TO"], msg.as_string())

        logger.info(f"Email sent to {app.config['EMAIL_TO']}")
        return True
    except Exception as e:
        logger.error(f"Email error: {e}")
        return False

PSV_SYSTEM_PROMPT = """You are the professional AI assistant for PSV Infotech, a software development company based in Salem, Tamil Nadu, India.

About PSV Infotech:
- Founded in 2019, specializing in web development, mobile apps, AI solutions, cloud services, UI/UX design, and e-commerce
- 150+ projects completed, 50+ happy clients, 5+ years experience
- Located in Salem, Tamil Nadu, India
- Email: contact@psvinfotech.com | WhatsApp: +91 99999 99999
- Business hours: Mon–Sat, 9AM–7PM IST

Services & Pricing (approximate):
- Basic Website: ₹15,000 – ₹35,000
- Business Portal: ₹35,000 – ₹80,000
- Mobile App (cross-platform): ₹50,000 – ₹1,50,000
- AI Integration: Custom quote
- E-Commerce Store: ₹40,000 – ₹1,00,000
- UI/UX Design: ₹10,000 – ₹30,000

Guidelines:
- Be friendly, professional, and concise
- Answer questions about services, pricing, timelines, and tech
- For complex requirements, encourage them to use the Contact Form or WhatsApp
- Use short paragraphs and bullet points where helpful
- Never make up information you don't know — redirect to contact for specifics
- Default timeline: websites in 2–4 weeks, apps in 6–12 weeks"""

def get_ai_response(user_message: str, conversation_history: list = None) -> str:
    """Get AI response from OpenAI or use fallback."""
    if openai_client:
        try:
            messages = [{"role": "system", "content": PSV_SYSTEM_PROMPT}]
            if conversation_history:
                messages.extend(conversation_history[-6:])  # Last 6 turns
            messages.append({"role": "user", "content": user_message})

            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=400,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return get_fallback_response(user_message)
    else:
        return get_fallback_response(user_message)

def get_fallback_response(msg: str) -> str:
    """Built-in rule-based responses when OpenAI is unavailable."""
    msg = msg.lower()

    if any(w in msg for w in ["price", "cost", "pricing", "quote", "rate", "charge"]):
        return ("Here are our approximate pricing ranges:\n\n"
                "• Basic Website: ₹15,000 – ₹35,000\n"
                "• Business Portal: ₹35,000 – ₹80,000\n"
                "• Mobile App: ₹50,000 – ₹1,50,000\n"
                "• E-Commerce Store: ₹40,000 – ₹1,00,000\n"
                "• UI/UX Design: ₹10,000 – ₹30,000\n\n"
                "For a detailed custom quote, please fill out our Contact Form or WhatsApp us at +91 99999 99999!")

    if any(w in msg for w in ["web", "website", "landing"]):
        return ("PSV Infotech builds stunning websites using:\n\n"
                "• React, Next.js, Vue.js\n"
                "• Node.js / Python backends\n"
                "• SEO optimized & mobile responsive\n\n"
                "Delivery: 2–4 weeks | Starting ₹15,000\n\n"
                "Want a free consultation? Use our Contact Form! 🚀")

    if any(w in msg for w in ["app", "mobile", "android", "ios", "flutter"]):
        return ("We develop cross-platform & native mobile apps:\n\n"
                "• Flutter (iOS + Android)\n"
                "• React Native\n"
                "• Native Swift / Kotlin\n\n"
                "Delivery: 6–12 weeks | Starting ₹50,000\n\n"
                "Contact us for a free project estimate!")

    if any(w in msg for w in ["ai", "machine learning", "chatbot", "openai", "gpt"]):
        return ("Our AI Solutions include:\n\n"
                "• Custom AI Chatbots\n"
                "• OpenAI / Claude API Integration\n"
                "• ML Model Development\n"
                "• Data Analytics Dashboards\n\n"
                "Pricing is custom based on complexity. Contact us to discuss your AI project!")

    if any(w in msg for w in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        return ("Hello! 👋 Welcome to PSV Infotech!\n\n"
                "I can help you with:\n"
                "• Web Development\n"
                "• App Development\n"
                "• AI Solutions\n"
                "• Pricing & Timelines\n\n"
                "What can I help you with today?")

    if any(w in msg for w in ["contact", "reach", "email", "phone", "whatsapp"]):
        return ("You can reach PSV Infotech at:\n\n"
                "📧 contact@psvinfotech.com\n"
                "📱 +91 99999 99999 (WhatsApp)\n"
                "📍 Salem, Tamil Nadu, India\n"
                "⏰ Mon–Sat, 9AM–7PM IST\n\n"
                "Or fill out the Contact Form on this page for a quick response!")

    if any(w in msg for w in ["timeline", "time", "how long", "delivery", "deadline"]):
        return ("Our typical project timelines:\n\n"
                "• Website (basic): 2–3 weeks\n"
                "• Business Portal: 4–6 weeks\n"
                "• Mobile App: 6–12 weeks\n"
                "• E-Commerce: 4–8 weeks\n"
                "• UI/UX Design: 2–4 weeks\n\n"
                "These depend on complexity. For a precise timeline, tell us about your project!")

    return ("Thanks for reaching out! 😊\n\n"
            "I can help with info about our services, pricing, and timelines.\n"
            "For a detailed discussion, please:\n\n"
            "📝 Use our Contact Form on this page\n"
            "💬 WhatsApp: +91 99999 99999\n"
            "📧 contact@psvinfotech.com\n\n"
            "We respond within 24 hours!")

# ─────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "PSV Infotech API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": ["/contact", "/messages", "/chat"]
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

# ── POST /contact ──────────────────────────────────
@app.route("/contact", methods=["POST"])
def contact():
    """Receive contact form submission, save to DB, and send email notification."""
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"success": False, "message": "Invalid request body"}), 400

        # Sanitize & validate
        name    = sanitize(data.get("name", ""), 100)
        email   = sanitize(data.get("email", ""), 200)
        phone   = sanitize(data.get("phone", ""), 20)
        service = sanitize(data.get("service", ""), 100)
        message = sanitize(data.get("message", ""), 2000)

        errors = {}
        if not name or len(name) < 2:
            errors["name"] = "Name must be at least 2 characters."
        if not email or not validate_email(email):
            errors["email"] = "Valid email is required."
        if not service:
            errors["service"] = "Please select a service."
        if not message or len(message) < 10:
            errors["message"] = "Message must be at least 10 characters."
        if errors:
            return jsonify({"success": False, "errors": errors}), 422

        # Basic spam check
        spam_words = ["buy now", "click here", "free money", "winner", "congratulations"]
        if any(w in message.lower() for w in spam_words):
            return jsonify({"success": True, "message": "Message received."}), 200  # Silent discard

        created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

        # Save to database
        try:
            db = get_db()
            cursor = db.execute(
                "INSERT INTO messages (name,email,phone,service,message,ip,created) VALUES (?,?,?,?,?,?,?)",
                (name, email, phone, service, message, client_ip, created)
            )
            row_id = cursor.lastrowid
            db.commit()
            logger.info(f"✓ Message #{row_id} saved to database.db")
        except sqlite3.Error as db_err:
            logger.error(f"Database error: {db_err}")
            return jsonify({"success": False, "message": f"Database error: {str(db_err)}"}), 500

        # Send email in background-ish
        form_data = dict(name=name, email=email, phone=phone, service=service, message=message, created=created)
        email_sent = False
        if app.config["EMAIL_USER"] != "your_gmail@gmail.com":
            email_sent = send_email_notification(form_data)
        else:
            logger.warning("! Email not sent: Placeholder credentials detected in Config.")

        # Update email_sent flag
        if email_sent:
            db = get_db()
            db.execute("UPDATE messages SET email_sent=? WHERE id=?", (1, row_id))
            db.commit()

        print(f"\n--- NEW MESSAGE RECEIVED ---\nFrom: {name} ({email})\nService: {service}\nMessage: {message}\n----------------------------\n")
        
        return jsonify({
            "success": True,
            "message": "Success! Your message has been saved to our database.",
            "id": row_id,
            "destination": "backend"
        }), 200

    except Exception as e:
        logger.error(f"Contact error: {e}")
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

# ── GET /messages ──────────────────────────────────
@app.route("/messages", methods=["GET"])
@require_admin
def get_messages():
    """Return all contact messages (admin only)."""
    try:
        page  = max(1, int(request.args.get("page", 1)))
        limit = min(100, int(request.args.get("limit", 20)))
        offset = (page - 1) * limit

        db = get_db()
        total = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        rows  = db.execute(
            "SELECT * FROM messages ORDER BY created DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()

        messages = [dict(row) for row in rows]
        return jsonify({
            "success": True,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "messages": messages
        })
    except Exception as e:
        logger.error(f"Messages error: {e}")
        return jsonify({"success": False, "message": "Server error"}), 500

# ── POST /chat ─────────────────────────────────────
@app.route("/chat", methods=["POST"])
def chat():
    """AI chatbot endpoint."""
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"success": False, "reply": "Invalid request."}), 400

        user_message = sanitize(data.get("message", ""), 500)
        if not user_message:
            return jsonify({"success": False, "reply": "Please send a message."}), 400

        session_id = data.get("session", "anonymous")
        history    = data.get("history", [])  # Optional conversation history

        # Get AI reply
        reply = get_ai_response(user_message, history)

        # Log to DB
        try:
            created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db = get_db()
            db.execute(
                "INSERT INTO chat_logs (session,user_msg,bot_reply,created) VALUES (?,?,?,?)",
                (session_id, user_message, reply, created)
            )
            db.commit()
        except Exception:
            pass  # Don't fail chat if logging fails

        return jsonify({"success": True, "reply": reply})

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({
            "success": False,
            "reply": "I'm experiencing a technical issue. Please WhatsApp us at +91 99999 99999 for immediate help!"
        }), 500

# ── Error Handlers ─────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "message": "Route not found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"success": False, "message": "Method not allowed"}), 405

@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "message": "Internal server error"}), 500

# ─────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    logger.info(f"🚀 PSV Infotech API starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
