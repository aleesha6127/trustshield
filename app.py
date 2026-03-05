from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
# ==============================
# 🔥 FIREBASE INITIALIZATION (NEW DATABASE)
# ==============================
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

from datetime import datetime
from twilio.rest import Client
import os
import json
import re
import smtplib
import random
import base64
import cv2
import numpy as np
import face_recognition
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import google.generativeai as genai
from werkzeug.utils import secure_filename 

# Import your models
from models import UserManager, AdminManager, MissingPersonsManager, HealthManager, ComplaintManager, TravelManager

try:
    from config import TWILIO_SID, TWILIO_TOKEN, TWILIO_NUMBER, ADMIN_ALERT_NUMBER
except ImportError:
    # Placeholder values if config.py is missing
    # Use environment variables for security
    TWILIO_SID = os.getenv("TWILIO_SID", "your_twilio_sid_here")
    TWILIO_TOKEN = os.getenv("TWILIO_TOKEN", "your_twilio_token_here")
    TWILIO_NUMBER = os.getenv("TWILIO_NUMBER", "your_twilio_number_here")
    ADMIN_ALERT_NUMBER = os.getenv("ADMIN_ALERT_NUMBER", "your_admin_number_here")

# --- 1. INITIALIZE FLASK FIRST (This fixes the error) ---
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "trustshield-super-secret-key")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")
genai.configure(api_key=GEMINI_API_KEY)

# Configure Gemini model with correct name
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- 2. CONFIGURE FILE UPLOADS ---
UPLOAD_FOLDER = 'static/uploads'
DATASET_FOLDER = 'static/dataset'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATASET_FOLDER, exist_ok=True)

# --- 3. TWILIO SETUP ---
client = Client(TWILIO_SID, TWILIO_TOKEN)

def send_sms(to, body):
    # --- AUTO-FIX PHONE NUMBER ---
    # If number is 10 digits (e.g., 9876543210), add +91
    if len(to) == 10 and to.isdigit():
        to = "+91" + to
    
    try:
        message = client.messages.create(
            body=body,
            from_=TWILIO_NUMBER,
            to=to
        )
        print(f"SMS sent to {to}: {message.sid}")
    except Exception as e:
        print(f"Failed to send SMS to {to}: {e}")



# ==============================
#      👤 USER AUTH ROUTES
# ==============================

@app.route("/register_user", methods=["POST"])
def register_user():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    contacts = request.form.getlist("contacts")
    face_image_data = request.form.get("face_image") # Base64 string

    if not face_image_data:
        return render_template("register.html", error="Live face photo is mandatory!")

    # --- PHONE NUMBER VALIDATION ---
    for phone in contacts:
        if phone and (len(phone) != 10 or not phone.isdigit()):
            return render_template("register.html", error="Invalid phone number! Emergency contacts must be 10 digits.")

    if password != confirm_password:
        return render_template("register.html", error="Passwords do not match!")

    # --- PROCESS FACE ENCODING & GENDER VALIDATION ---
    try:
        header, encoded = face_image_data.split(",", 1)
        img_bytes = base64.b64decode(encoded)

        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # --- SAVE TO DATASET ---
        dataset_path = os.path.join('static/dataset', f"{email.replace('@', '_').replace('.', '_')}.jpg")
        cv2.imwrite(dataset_path, img)

        # Convert to RGB (Required by face_recognition)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Get face encodings
        encodings = face_recognition.face_encodings(rgb_img)
        
        if len(encodings) == 0:
            return render_template("register.html", error="No face detected in the photo. Please try again.")
        
        face_encoding = encodings[0]

        # --- UNIQUENESS CHECK ---
        users = UserManager.get_all_users()
        for u in users:
            stored_enc = u.get("face_encoding")
            if stored_enc:
                # Calculate exact face distance (lower = more similar)
                distance = face_recognition.face_distance([np.array(stored_enc)], face_encoding)[0]
                if distance < 0.4:  # Very strict threshold
                    return render_template("register.html", error="This face is already registered with another account!")

        face_encoding_list = face_encoding.tolist() # Convert to list for Firestore
        
    except Exception as e:
        print(f"Error processing face: {e}")
        return render_template("register.html", error="Invalid image data. Please capture again.")

    # Use Model
    success, message = UserManager.create_user(name, email, password, contacts, face_encoding=face_encoding_list)
    
    if success:
        return redirect(url_for('login_page'))
    else:
        return render_template("register.html", error=message)

@app.route("/login_user", methods=["POST"])
def login_user():
    email = request.form.get("email")
    password = request.form.get("password")

    # Use Model
    user = UserManager.verify_user(email, password)

    if user:
        session['user_id'] = user['uid']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        return redirect(url_for('dashboard_page'))
    else:
        return render_template("login.html", error="Invalid Email or Password")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('landing'))

# ==============================
#        🖥 UI ROUTES
# ==============================

@app.route("/")
def landing():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard_page():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    return render_template("dashboard.html", user_name=session['user_name'], user_email=session['user_email'])

@app.route("/login")
def login_page():
    if 'user_id' in session: return redirect(url_for('dashboard_page'))
    return render_template("login.html")

@app.route("/register")
def register_page():
    if 'user_id' in session: return redirect(url_for('dashboard_page'))
    return render_template("register.html")

# ==============================
#      👑 ADMIN ROUTES
# ==============================

@app.route("/login/admin")
def admin_login_page():
    return render_template("admin_login.html")

@app.route("/admin_auth", methods=["POST"])
def admin_auth():
    email = request.form.get("email")
    password = request.form.get("password")
    
    # Hardcoded admin check
    if email == "admin@trustshield.com" and password == "admin123":
        session['admin'] = True
        return redirect(url_for('admin_panel'))
    return render_template("admin_login.html", error="Invalid Admin Credentials")

@app.route("/admin")
def admin_panel():
    if not session.get("admin"): return redirect(url_for('admin_login_page'))
    return render_template("admin_panel.html")

@app.route("/logout/admin")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for('admin_login_page'))

# --- ADMIN FEATURES (Using Models) ---

@app.route("/users")
def users_page():
    if not session.get("admin"): return redirect(url_for('admin_login_page'))
    users = UserManager.get_all_users()
    return render_template("admin_users.html", users=users)

@app.route("/incident_reports")
def incident_reports_page():
    if not session.get("admin"): return redirect(url_for('admin_login_page'))
    reports = AdminManager.get_reports()
    return render_template("admin_reports.html", reports=reports)

@app.route("/sos_alerts")
def sos_alerts_page():
    if not session.get("admin"): return redirect(url_for('admin_login_page'))
    alerts = AdminManager.get_sos_alerts()
    return render_template("admin_sos.html", alerts=alerts)

@app.route("/danger_zones")
def danger_zones_page():
    if not session.get("admin"): return redirect(url_for('admin_login_page'))
    zones = AdminManager.get_danger_zones()
    return render_template("admin_zones.html", zones=zones)

@app.route("/add_zone", methods=["POST"])
def add_zone():
    if not session.get("admin"): return redirect(url_for('admin_login_page'))
    
    AdminManager.add_danger_zone(
        request.form.get("name"),
        request.form.get("category"),
        request.form.get("risk"),
        request.form.get("latitude"),
        request.form.get("longitude"),
        request.form.get("duration") # Pass duration to model
    )
    return redirect(url_for('danger_zones_page'))
# NEW: Delete Route
@app.route("/delete_zone", methods=["POST"])
def delete_zone():
    if not session.get("admin"): return redirect(url_for('admin_login_page'))
    zone_id = request.form.get("zone_id")
    AdminManager.delete_danger_zone(zone_id)
    return redirect(url_for('danger_zones_page'))

@app.route("/admin/missing_persons")
def admin_missing_page():
    if not session.get("admin"): return redirect(url_for('admin_login_page'))
    # Reuse the existing Manager to fetch data
    people = MissingPersonsManager.get_all_missing()
    return render_template("admin_missing.html", people=people)

@app.route("/admin/update_missing", methods=["POST"])
def admin_update_missing():
    if not session.get("admin"): return redirect(url_for('admin_login_page'))
    
    doc_id = request.form.get("doc_id")
    status = request.form.get("status") # 'Found' or 'Missing'
    MissingPersonsManager.update_status(doc_id, status)
    
    return redirect(url_for('admin_missing_page'))

@app.route("/admin/delete_missing", methods=["POST"])
def admin_delete_missing():
    if not session.get("admin"): return redirect(url_for('admin_login_page'))
    
    doc_id = request.form.get("doc_id")
    MissingPersonsManager.delete_report(doc_id)
    
    return redirect(url_for('admin_missing_page'))

# ==============================
#      📞 CONTACTS ROUTES
# ==============================

@app.route("/emergency_contacts")
def emergency_contacts():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    
    contacts = UserManager.get_contacts(session['user_id'])
    return render_template("emergency_contacts.html", contacts=contacts)

@app.route("/add_contact", methods=["POST"])
def add_contact():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    
    UserManager.add_contact(
        session['user_id'],
        request.form.get("name"),
        request.form.get("relation"),
        request.form.get("phone")
    )
    return redirect(url_for('emergency_contacts'))

@app.route("/delete_contact", methods=["POST"])
def delete_contact():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    
    # We need to reconstruct the object to remove it
    contact_obj = {
        "name": request.form.get("name"),
        "relation": request.form.get("relation"),
        "phone": request.form.get("phone")
    }
    UserManager.delete_contact(session['user_id'], contact_obj)
    return redirect(url_for('emergency_contacts'))

# ==============================
#      🚨 SOS & JOURNEY
# ==============================

@app.route("/send_sos", methods=["POST"])
def send_sos():
    if 'user_id' not in session: return jsonify({"status":"error"}), 401
    
    data = request.get_json()
    lat = data.get('lat')
    lon = data.get('lon')
    
    # 1. Save to DB
    contacts = UserManager.save_sos(session['user_id'], lat, lon)
    
    # 2. PREPARE MEANINGFUL MESSAGE
    name = session.get('user_name', 'Someone') # Get name from session
    email = session.get('user_email', 'Unknown')
    map_link = f"https://www.google.com/maps?q={lat},{lon}"
    
    sms_body = (
        f"🚨 EMERGENCY ALERT 🚨\n"
        f"{name} ({email}) has triggered an SOS!\n"
        f"They need urgent help.\n"
        f"📍 Location: {map_link}"
    )
    
    # 3. SEND SMS TO EMERGENCY CONTACTS
    sent_count = 0
    for contact in contacts:
        if 'phone' in contact and contact['phone']:
            send_sms(contact['phone'], sms_body)
            sent_count += 1
    
    # 4. ALSO SEND TO ADMIN ALERT NUMBER (NOT the Twilio sender number)
    try:
        send_sms(ADMIN_ALERT_NUMBER, sms_body)
        sent_count += 1
    except Exception as e:
        print(f"Failed to send admin alert: {e}")
    
    return jsonify({"status": "SOS Sent", "contacts_notified": sent_count})
@app.route("/journey")
def journey_page():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    return render_template("journey.html")

@app.route("/start_journey_api", methods=["POST"])
def start_journey_api():
    if 'user_id' not in session: return jsonify({"status":"error"}), 401
    
    data = request.get_json()
    UserManager.start_journey(
        session['user_id'], 
        data.get("destination"),
        data.get("lat"), 
        data.get("lon")
    )
    return jsonify({"status": "Journey Started"})

@app.route("/panic_mode")
def panic_mode():
    # Allow panic mode even if not logged in? 
    # Usually safer to require login so we know WHO is in trouble.
    if 'user_id' not in session: return redirect(url_for('login_page'))
    return render_template("sos.html")

# ==============================
#      📝 INCIDENT REPORTING
# ==============================

@app.route("/report")
def report_page():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    return render_template("report.html")

@app.route("/submit_report", methods=["POST"])
def submit_report():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    
    # 1. HANDLE FILE UPLOAD
    evidence_path = None
    if 'evidence' in request.files:
        file = request.files['evidence']
        if file.filename != '':
            filename = secure_filename(file.filename)
            # Add timestamp to make filename unique
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            save_name = f"{timestamp}_{filename}"
            full_path = os.path.join(app.config['UPLOAD_FOLDER'], save_name)
            
            file.save(full_path)
            # Save relative path to DB
            evidence_path = f"uploads/{save_name}"

    # 2. PASS TO MODEL
    UserManager.submit_incident_report(session['user_id'], request.form, evidence_path)
    
    return redirect(url_for('dashboard_page'))

# ==============================
#      📢 MISSING PERSONS
# ==============================

@app.route("/missing_persons")
def missing_persons_page():
    # Public page, but let's keep it protected or public depending on preference
    # Assuming protected for now:
    if 'user_id' not in session: return redirect(url_for('login_page'))
    
    people = MissingPersonsManager.get_all_missing()
    return render_template("missing_persons.html", people=people, user_id=session['user_id'])

@app.route("/report_missing", methods=["POST"])
def report_missing():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    
    # 1. HANDLE PHOTO UPLOAD
    photo_path = None
    if 'photo' in request.files:
        file = request.files['photo']
        if file.filename != '':
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            save_name = f"missing_{timestamp}_{filename}"
            full_path = os.path.join(app.config['UPLOAD_FOLDER'], save_name)
            
            file.save(full_path)
            photo_path = f"uploads/{save_name}" # Save relative path

    # 2. SAVE TO DB
    MissingPersonsManager.report_missing(session['user_id'], request.form, photo_path)
    
    return redirect(url_for('missing_persons_page'))
@app.route("/update_missing_status", methods=["POST"])
def update_missing_status():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    
    doc_id = request.form.get("doc_id")
    new_status = request.form.get("status")
    MissingPersonsManager.update_status(doc_id, new_status)
    return redirect(url_for('missing_persons_page'))

@app.route("/delete_missing", methods=["POST"])
def delete_missing():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    
    doc_id = request.form.get("doc_id")
    MissingPersonsManager.delete_report(doc_id)
    return redirect(url_for('missing_persons_page'))

# ==============================
#      🩺 HEALTH TRACKER
# ==============================

@app.route("/health_tracker")
def health_tracker():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    
    last_date = HealthManager.get_cycle_data(session['user_id'])
    return render_template("health_tracker.html", last_date=last_date)

@app.route("/health_chat_api", methods=["POST"])
def health_chat_api():
    if 'user_id' not in session: return jsonify({"error":"Login required"}), 401
    
    data = request.get_json()
    user_message = data.get("message")
    cycle_day = data.get("day", "Unknown")
    phase = data.get("phase", "Unknown")
    
    # Context-Aware Prompt
    system_instruction = (
        f"You are 'TrustShield Eva', a compassionate and knowledgeable women's health assistant. "
        f"The user is currently on Day {cycle_day} of their menstrual cycle ({phase} phase). "
        f"Answer their query briefly (under 50 words) and supportively. "
        f"If they mention symptoms like cramps, mood swings, or fatigue, explain if it's normal for this phase. "
        f"Suggest simple remedies (tea, heating pad, specific foods). "
        f"IMPORTANT: If the user describes severe pain or emergency symptoms, tell them to see a doctor immediately."
    )
    
    try:
        chat = model.start_chat(history=[])
        response = chat.send_message(f"{system_instruction}\nUser Query: {user_message}")
        return jsonify({"reply": response.text})
    except Exception as e:
        print(f"Gemini Error: {e}")
        return jsonify({"reply": "I'm having trouble connecting to my brain right now. Please try again later! (Check API Key)"})
@app.route("/update_cycle", methods=["POST"])
def update_cycle():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    
    date = request.form.get("date")
    HealthManager.update_cycle_date(session['user_id'], date)
    return redirect(url_for('health_tracker'))

# ==============================
#      👮 POLICE COMPLAINT
# ==============================

@app.route("/police_complaint")
def police_complaint():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    return render_template("police_complaint.html")

@app.route("/save_complaint_api", methods=["POST"])
def save_complaint_api():
    if 'user_id' not in session: return jsonify({"status":"error"}), 401
    
    data = request.get_json()
    ComplaintManager.save_complaint(session['user_id'], data)
    return jsonify({"status": "saved"})

# ==============================
#      📚 TIPS & TRAVEL
# ==============================

@app.route("/tips")
def tips():
    # Static page, no logic needed
    return render_template("tips.html")

# ==============================
#      🗺️ DANGER ZONES (Public Map)
# ==============================
@app.route("/danger_zone")
def danger_zone_map():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    return render_template("danger_zone.html")
@app.route("/danger_data")
def danger_data_api():
    if 'user_id' not in session: return jsonify({})
    
    # 1. Fetch Official Danger Zones (Red Circles)
    zones = AdminManager.get_danger_zones()
    
    # 2. Fetch User Incident Reports (Yellow Markers)
    # We reuse the existing method to get all reports
    raw_reports = AdminManager.get_reports()
    valid_reports = []

    for r in raw_reports:
        # We need to extract Lat/Lon from the "location" string (e.g., "10.123, 76.456")
        loc = r.get("location", "")
        try:
            if "," in loc:
                parts = loc.split(",")
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                
                valid_reports.append({
                    "type": r.get("incident_type", "Incident"),
                    "details": r.get("details", ""),
                    "time": r.get("time_str", ""),
                    "latitude": lat,
                    "longitude": lon
                })
        except:
            # Skip reports that don't have valid GPS coordinates (e.g. user typed address manually)
            continue

    return jsonify({
        "zones": zones,
        "reports": valid_reports
    })

# ==============================
#      ✈ TRAVEL SAFETY AI
# ==============================

@app.route("/travel_safety")
def travel_safety():
    # Render page without hardcoded data
    return render_template("travel_safety.html")
@app.route("/face_login", methods=["POST"])
def face_login():
    try:
        img_data = request.data.decode("utf-8")
        if not img_data or "," not in img_data:
            return "Invalid image data"
            
        img_bytes = base64.b64decode(img_data.split(",")[1])
        
        np_img = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        if frame is None:
            return "Invalid image data"

        # Convert to RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Get encoding of the live image
        encodings = face_recognition.face_encodings(rgb)
        
        if not encodings:
            return "Face not detected"

        login_encoding = encodings[0]

        # Fetch all users from Firestore to find a match
        users = UserManager.get_all_users()
        
        best_match_user = None
        lowest_distance = 1.0  # Initialize with max distance
        
        for user in users:
            stored_encoding = user.get("face_encoding")
            if stored_encoding:
                # Calculate exact face distance
                distance = face_recognition.face_distance([np.array(stored_encoding)], login_encoding)[0]
                
                # Track the best match
                if distance < lowest_distance:
                    lowest_distance = distance
                    best_match_user = user

        # STRICT LOGIN THRESHOLD: Only allow if distance is very low (high accuracy)
        if best_match_user and lowest_distance < 0.45:
            session["user_id"] = best_match_user["uid"]
            session["user_name"] = best_match_user["name"]
            session["user_email"] = best_match_user["email"]
            return "Face Login Successful"
        else:
            return "Face not recognized or unauthorized person"

    except Exception as e:
        print(f"Face login error: {e}")
        return f"Error: {str(e)}"


@app.route("/api/travel_analysis", methods=["POST"])
def get_travel_analysis():
    if 'user_id' not in session: return jsonify({"error": "Login required"}), 401
    
    data = request.get_json()
    city = data.get("city", "")
    
    if not city: return jsonify({"error": "City name required"}), 400

    # Strict JSON Prompt for AI
    prompt = f"""
    Analyze travel safety for: {city}.
    Return ONLY a valid JSON object (no markdown) with this exact structure:
    {{
        "risk": "Short description of main risks (e.g., Petty theft, Scams, Safe)",
        "safety": "Safe" or "Moderate" or "Caution",
        "tips": ["Tip 1", "Tip 2", "Tip 3"],
        "police": ["Name of nearest major police station", "Another station"],
        "hospitals": ["Name of major hospital 1", "Hospital 2"]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        
        # Clean potential markdown formatting (```json ... ```)
        text = re.sub(r"```json|```", "", text).strip()
        
        analysis = json.loads(text)
        return jsonify(analysis)
        
    except Exception as e:
        print(f"AI Error: {e}")
        # Fallback data if AI fails
        return jsonify({
            "risk": "Could not fetch live data.",
            "safety": "Unknown",
            "tips": ["Stay alert", "Keep emergency numbers ready"],
            "police": ["Local Police (100/112)"],
            "hospitals": ["Nearest General Hospital"]
        })

# ==============================
#      🧭 JOURNEY TRACKER UPGRADES
# ==============================

@app.route("/report_stoppage", methods=["POST"])
def report_stoppage():
    if 'user_id' not in session: return jsonify({"status":"error"}), 401
    
    data = request.get_json()
    lat = data.get('lat')
    lon = data.get('lon')
    
    # 1. Reuse SOS logic to save alert to DB (or create a new collection if preferred)
    # For now, we log it as a specific type of SOS/Alert
    contacts = UserManager.get_contacts(session['user_id'])
    
    name = session.get('user_name', 'User')
    map_link = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=18/{lat}/{lon}"
    
    # 2. Specific Message for Stoppage
    sms_body = (
        f"⚠ UNUSUAL STOPPAGE ALERT ⚠\n"
        f"{name} has reported an unexpected halt during their journey.\n"
        f"Please check on them.\n"
        f"📍 Location: {map_link}"
        f"Sent:{timestamp}"
    )
    
    # 3. Send SMS
    count = 0
    for contact in contacts:
        if 'phone' in contact:
            send_sms(contact['phone'], sms_body)
            count += 1
            
    return jsonify({"status": "Stoppage Reported", "notified": count})

# ==============================
#      📧 EMAIL CONFIGURATION
# ==============================
# ⚠️ REPLACE WITH YOUR DETAILS
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "trustshield861@gmail.com") 
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "your_app_password_here") # Use App Password, NOT login password

def send_email_otp(to_email, otp):
    try:
        subject = "TrustShield Password Reset OTP"
        body = f"Hello,\n\nYour OTP for resetting your password is: {otp}\n\nThis OTP is valid for 10 minutes.\nDo not share this with anyone."

        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

# ==============================
#      🔐 PASSWORD RESET ROUTES
# ==============================

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        
        # 1. Check if user exists
        user = UserManager.check_email_exists(email)
        if not user:
            return render_template("forgot_password.html", error="Email not registered.")

        # 2. Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        
        # 3. Send Email
        if send_email_otp(email, otp):
            # 4. Store in Session (Securely)
            session['reset_email'] = email
            session['reset_doc_id'] = user['doc_id'] # Needed for update
            session['reset_otp'] = otp
            return redirect(url_for('verify_otp_page'))
        else:
            return render_template("forgot_password.html", error="Failed to send email. Check server logs.")

    return render_template("forgot_password.html")

@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp_page():
    if 'reset_email' not in session: return redirect(url_for('forgot_password'))

    if request.method == "POST":
        entered_otp = request.form.get("otp")
        generated_otp = session.get('reset_otp')

        if entered_otp == generated_otp:
            session['otp_verified'] = True
            return redirect(url_for('reset_password_page'))
        else:
            return render_template("verify_otp.html", error="Invalid OTP. Please try again.")

    return render_template("verify_otp.html", email=session['reset_email'])

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password_page():
    # Security Check: Ensure flow was followed
    if 'reset_email' not in session or not session.get('otp_verified'):
        return redirect(url_for('forgot_password'))

    if request.method == "POST":
        new_pass = request.form.get("password")
        confirm_pass = request.form.get("confirm_password")

        if new_pass != confirm_pass:
            return render_template("reset_password.html", error="Passwords do not match!")

        # Update DB
        doc_id = session.get('reset_doc_id')
        if UserManager.update_password(doc_id, new_pass):
            # Clear Session
            session.pop('reset_email', None)
            session.pop('reset_otp', None)
            session.pop('reset_doc_id', None)
            session.pop('otp_verified', None)
            
            return render_template("login.html", success="Password reset successfully! Please login.")
        else:
            return render_template("reset_password.html", error="Database error. Try again.")

    return render_template("reset_password.html")

if __name__ == "__main__":
  app.run(host='0.0.0.0', port=5000, debug=False)

