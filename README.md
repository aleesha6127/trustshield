# 🛡️ TrustShield – Women's Safety & Empowerment Web Application

TrustShield is an intelligent women's safety and emergency response web application designed to provide real-time safety assistance, AI-powered guidance, and community safety services.

The platform combines face authentication, emergency alerts, live geolocation, AI assistance, and Firebase-based data management into a unified safety solution.

## 🌐 Live Demo

🚀 Live Application: https://trustshield-jqpk.onrender.com

💻 GitHub Repository: https://github.com/aleesha6127/trustshield

> Note: The application is deployed on Render's free service. Initial loading may take a few seconds if the server is inactive.

---

## ✨ Key Features

### 🔐 Live Face Authentication

- Face registration and identity verification
- Password-less face login
- Duplicate face detection
- OpenCV and face recognition integration

### 🚨 Emergency SOS & Location Alerts

- Instant SOS emergency alerts
- Live GPS coordinate sharing
- Google Maps location links
- Twilio SMS integration
- Emergency contact notifications
- Unusual journey stoppage alerts

### 🤖 AI Safety Assistant

- AI-powered travel safety analysis
- City-based safety recommendations
- Risk awareness and safety guidance
- Nearby police station and hospital information
- Powered by Google Gemini AI

### 🌸 TrustShield Eva – Health Companion

- Menstrual cycle tracking
- AI-powered health assistance
- Symptom-based supportive guidance
- Interactive health companion

### 🗺️ Admin Safety Command Center

- Interactive safety map
- Danger zone monitoring
- Incident location tracking
- SOS alert history
- Registered user management
- Missing person report moderation

### 👥 Community Safety Services

- Missing persons reporting board
- Photo and evidence uploads
- Missing/Found status tracking
- Unique case IDs
- Geo-referenced incident reporting
- Police complaint log
- OTP-based password recovery

---

## 🛠️ Tech Stack

| Technology | Usage |
|---|---|
| Python | Backend Development |
| Flask | Web Framework |
| Firebase Firestore | Database |
| Google Gemini AI | AI Safety & Health Assistance |
| OpenCV | Computer Vision |
| Face Recognition | Face Authentication |
| Dlib | Facial Processing |
| Twilio API | Emergency SMS Alerts |
| HTML5 | Web Structure |
| CSS3 | User Interface |
| JavaScript | Frontend Interactions |
| Leaflet.js | Interactive Maps |
| Gunicorn | Production Server |
| Render | Cloud Deployment |

---

## 🚀 Deployment

The TrustShield application is deployed using Render with Gunicorn as the production WSGI server.

**Production URL:**

https://trustshield-jqpk.onrender.com

Sensitive credentials, including Firebase service account credentials, Twilio API credentials, and Gemini API keys, are securely configured using deployment environment variables and secret files.

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/aleesha6127/trustshield.git
cd trustshield
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Firebase

Download the Firebase Admin SDK service account credentials.

Save the file as:

```text
serviceAccountKey.json
```

Place it in the project root directory.

> ⚠️ Never commit Firebase service account credentials to GitHub.

### 4. Configure Environment Variables

Create a `.env` file:

```env
FLASK_SECRET_KEY=your_secret_key
GEMINI_API_KEY=your_gemini_api_key
SENDER_EMAIL=your_email
SENDER_PASSWORD=your_app_password
TWILIO_SID=your_twilio_sid
TWILIO_TOKEN=your_twilio_token
TWILIO_NUMBER=your_twilio_number
ADMIN_ALERT_NUMBER=your_admin_phone_number
```

### 5. Run the Application

```bash
python app.py
```

The application will run locally at:

```text
http://localhost:5000
```

---

## 📁 Project Structure

```text
TrustShield/
│
├── app.py
├── models.py
├── config.py
├── requirements.txt
│
├── static/
│   ├── css/
│   ├── js/
│   ├── uploads/
│   └── dataset/
│
├── templates/
│
└── docs/
```

---

## 🎯 Project Objective

TrustShield aims to use modern web technologies, artificial intelligence, geolocation services, and computer vision to build a unified digital safety platform focused on emergency assistance and women's safety.

---

## 👩‍💻 Developer

**Aleesha Anas**

MCA Student | Full Stack & Frontend Developer

🌐 Portfolio: https://aleesha6127.github.io/portfolio/

💻 GitHub: https://github.com/aleesha6127

💼 LinkedIn: https://www.linkedin.com/in/aleesha-anas-a7553533b/

---

## 📄 License

This project was developed as part of the FAWS Internship and focuses on women's safety and empowerment.
