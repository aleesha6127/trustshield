# TrustShield - Women's Safety & Empowerment Web Application

TrustShield is an intelligent, feature-rich web platform designed to prioritize women's safety, facilitate emergency response, and provide AI-driven health and travel assistance. 

Equipped with live face authentication, real-time geolocation alerts, and integration with the Google Gemini API, TrustShield stands as a modern shield for personal security.

---

## 🚀 Key Features

### 1. Advanced Live Face Authentication
* **Live Face Registration**: Face detection and automatic database check preventing multiple accounts from using the same face.
* **Face Login**: Fast, secure face scanning for password-less authentication using OpenCV and local-distance calculations (threshold `< 0.45`).

### 2. Emergency Alerts & SMS Integration
* **Instant SOS**: Triggers geo-targeted alerts with live Google Maps coordinate links to all emergency contacts and system administrators.
* **Twilio SMS Gateway**: Real-time SMS dispatch containing exact GPS coordinate links.
* **Unusual Stoppage Alerts**: Journey tracker monitors the trip and sends immediate stoppage warnings to emergency contacts if an unexpected halt occurs.

### 3. AI Safety & Health Companions
* **Travel Safety AI**: Enter any city to get an instant safety report, local tips, risk ratings, and list of nearby police stations & major hospitals (Powered by **Google Gemini API**).
* **TrustShield Eva (Health Tracker)**: Interactive cycle tracker with an AI assistant that provides supportive feedback and remedies for menstrual symptoms (Powered by **Google Gemini API**).

### 4. Admin Command Center
* Interactive map displaying registered **Danger Zones** (with auto-expiry) and active user-reported **Incident locations**.
* Direct list of registered users and SOS alert histories.
* Moderation panel for resolving or deleting reported missing person updates.

### 5. Community Safety Services
* **Missing Persons Board**: Public and protected directory of reports with photo uploading, live search, status updates ("Missing"/"Found"), and unique case IDs.
* **Incident Reporting**: Submit geo-referenced safety incidents with media/evidence uploads.
* **Police Complaint Log**: Digital tracker for FIRs, station info, and incident details.
* **Password Reset**: OTP-based verification via secure SMTP email delivery.

---

## 🛠 Tech Stack
* **Backend**: Flask (Python 3.13)
* **Database**: Firebase Firestore
* **AI/LLM**: Google Gemini Generative AI (`gemini-1.5-flash-latest`)
* **Computer Vision**: OpenCV, Face Recognition, Dlib
* **Communication**: Twilio SMS API, Python SMTP (Email OTPs)
* **Frontend**: HTML5, Vanilla CSS3, JavaScript, Leaflet.js (Interactive Maps)

---

## 📋 Prerequisites
Before setting up the project, make sure you have:
1. **Python 3.10+** (Python 3.13 recommended)
2. **Conda** (Miniconda/Anaconda) - Recommended for installing Dlib and OpenCV dependencies on Windows without compiling from scratch.
3. **Firebase Firestore Database** - Download your Firebase Admin SDK service account key file and name it `serviceAccountKey.json`.
4. **Twilio Account** - Twilio SID, Auth Token, and a valid Twilio Number.
5. **Google Gemini API Key** - Retrieve a key from Google AI Studio.

---

## 🔧 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/aleesha6127/trustshield.git
cd trustshield
```

### 2. Install Dependencies
For Windows environments, it is highly recommended to install `dlib` and `face-recognition` via Conda to avoid complex C++ compiler requirements:
```bash
# Install core computer vision dependencies
conda install -y -c conda-forge dlib face_recognition

# Install the rest of the dependencies
pip install -r requirements.txt
```

### 3. Place Firebase Service Key
Add your Firebase service credentials file `serviceAccountKey.json` into the root directory of the application:
```
/TrustShield
  ├── app.py
  ├── serviceAccountKey.json  <-- Place here
  └── ...
```

### 4. Configure Environment Variables
Create a `.env` file or export the following environment variables:
```env
FLASK_SECRET_KEY="your-super-secret-key"
GEMINI_API_KEY="your-gemini-api-key"
SENDER_EMAIL="your-otp-sender-email@gmail.com"
SENDER_PASSWORD="your-app-password"
```

Configure `config.py` for Twilio details:
```python
TWILIO_SID = "your_twilio_sid"
TWILIO_TOKEN = "your_twilio_token"
TWILIO_NUMBER = "your_twilio_phone_number"
ADMIN_ALERT_NUMBER = "your_personal_admin_phone_number"
```

### 5. Running the Application
Run the Flask server:
```bash
python app.py
```
Open [http://localhost:5000](http://localhost:5000) in your web browser.

---

## 📁 Repository Structure
```
TrustShield/
├── app.py              # Main Flask server entry point (routes, API integrations)
├── models.py           # Firebase Firestore database handlers
├── config.py           # Twilio credentials and contact settings
├── requirements.txt    # List of required python modules
├── static/             # CSS styling, custom JS scripts, and user uploads
│   ├── css/
│   ├── js/
│   ├── uploads/        # User evidence/missing person uploads
│   └── dataset/        # Base64 registered user face image profiles
├── templates/          # HTML pages (dashboard, missing board, travel AI, Eva tracker)
└── docs/               # Architecture diagrams and database schemas
```

---

## 🛡 License
This project is open-source and developed for women safety and empowerment during the FAWS Internship.
