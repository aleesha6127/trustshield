import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta

from datetime import datetime

# Initialize Firebase (Singleton pattern to avoid re-initialization errors)
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

class UserManager:
    @staticmethod
    def create_user(name, email, password, contacts, face_encoding=None):
        # Check if email exists
        users_ref = db.collection("users")
        if any(users_ref.where("email", "==", email).stream()):
            return False, "Email already exists!"
        
        # --- FIX STARTS HERE ---
        # Convert raw phone numbers ["123", "456"] into Objects 
        # [{"phone": "123", "name": "Contact", "relation": "Unknown"}]
        structured_contacts = []
        for phone in contacts:
            if phone.strip(): # Only add if not empty
                structured_contacts.append({
                    "phone": phone.strip(),
                    "name": "Emergency Contact", # Default placeholder
                    "relation": "Unknown"        # Default placeholder
                })
        # --- FIX ENDS HERE ---

        # Create user
        new_user_ref = users_ref.document()
        new_user_ref.set({
            "uid": new_user_ref.id,
            "name": name,
            "email": email,
            "password": password, 
            "emergency_contacts": structured_contacts, # Save the fixed list
            "face_encoding": face_encoding, # Save face encoding as a list
            "created_at": datetime.utcnow()
        })
        return True, "User created"
    @staticmethod
    def verify_user(email, password):
        users_ref = db.collection("users")
        query = users_ref.where("email", "==", email).where("password", "==", password).stream()
        for doc in query:
            return doc.to_dict()
        return None

    @staticmethod
    def get_all_users():
        return [doc.to_dict() for doc in db.collection("users").stream()]
    
    @staticmethod
    def get_contacts(user_id):
        # Fetch user document
        doc = db.collection("users").document(user_id).get()
        if doc.exists:
            return doc.to_dict().get("emergency_contacts", [])
        return []

    @staticmethod
    def add_contact(user_id, name, relation, phone):
        user_ref = db.collection("users").document(user_id)
        # Firestore array_union adds only unique items
        user_ref.update({
            "emergency_contacts": firestore.ArrayUnion([{
                "name": name,
                "relation": relation,
                "phone": phone
            }])
        })

    @staticmethod
    def delete_contact(user_id, contact_to_remove):
        user_ref = db.collection("users").document(user_id)
        # Firestore array_remove deletes specific item
        user_ref.update({
            "emergency_contacts": firestore.ArrayRemove([contact_to_remove])
        })

    @staticmethod
    def save_sos(user_id, lat, lon):
        # 1. Save to Database
        db.collection("sos_alerts").add({
            "uid": user_id,
            "lat": lat,
            "lon": lon,
            "time": datetime.utcnow(),
            "active": True
        })
        # 2. Return contacts so Python can send SMS (Phase 2)
        return UserManager.get_contacts(user_id)

    @staticmethod
    def start_journey(user_id, destination, lat, lon):
        db.collection("users").document(user_id).collection("journeys").add({
            "destination": destination,
            "start_time": datetime.utcnow(),
            "status": "in_progress",
            "start_lat": lat,
            "start_lon": lon
        })
    @staticmethod
    def submit_incident_report(user_id, data, evidence_path=None):
        # Save to global collection for Admin
        report_ref = db.collection("incident_reports").document()
        report_data = {
            "uid": user_id,
            "incident_type": data.get("type"),
            "description": data.get("description"),
            "date": data.get("date"),
            "time": data.get("time"),
            "location": data.get("location"),
            "anonymous": data.get("anonymous") == 'on', 
            "evidence": evidence_path,  # <--- NEW FIELD
            "created": datetime.utcnow()
        }
        report_ref.set(report_data)
        return True
    @staticmethod
    def check_email_exists(email):
        # Returns User Dict if exists, else None
        users_ref = db.collection("users")
        query = users_ref.where("email", "==", email).stream()
        for doc in query:
            data = doc.to_dict()
            data['doc_id'] = doc.id # Store Document ID for updating later
            return data 
        return None

    @staticmethod
    def update_password(doc_id, new_password):
        try:
            db.collection("users").document(doc_id).update({
                "password": new_password
            })
            return True
        except Exception as e:
            print(f"Error updating password: {e}")
            return False
# --- NEW CLASS FOR MISSING PERSONS ---
class MissingPersonsManager:
    @staticmethod
    def get_all_missing():
        # fetch all missing reports from a global collection or query users
        # For simplicity, let's assume a root collection "missing_persons"
        # If your old app nested them under users, we might need a collection group query
        # But moving forward, a root collection is better for a public directory.
        docs = db.collection("missing_persons").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
        people = []
        for doc in docs:
            p = doc.to_dict()
            p['doc_id'] = doc.id
            people.append(p)
        return people

    @staticmethod
    def report_missing(user_id, data, photo_path=None):
        db.collection("missing_persons").add({
            "reporter_uid": user_id,
            "name": data.get("name"),
            "age": data.get("age"),
            "gender": data.get("gender"),
            "last_seen_place": data.get("place"),
            "last_seen_date": data.get("date"),
            "contact_guardian": data.get("guardian"),
            "description": data.get("description"),
            "photo": photo_path,  # <--- NEW FIELD
            "status": "Missing",
            "case_id": f"TS-{int(datetime.utcnow().timestamp())}",
            "created_at": datetime.utcnow()
        })

    @staticmethod
    def update_status(doc_id, new_status):
        db.collection("missing_persons").document(doc_id).update({"status": new_status})

    @staticmethod
    def delete_report(doc_id):
        db.collection("missing_persons").document(doc_id).delete()
class AdminManager:
    @staticmethod
    def get_reports():
        reports_ref = db.collection("incident_reports").order_by("created", direction=firestore.Query.DESCENDING).stream()
        results = []
        for doc in reports_ref:
            r = doc.to_dict()
            r['id'] = doc.id
            
            # 1. FIX DETAILS/DESCRIPTION MISMATCH
            # The form saves as 'description', but old code used 'details'
            if 'description' in r:
                r['details'] = r['description']
            
            # 2. PARSE LOCATION FOR MAP
            # Location is stored as string "10.523, 76.213"
            loc = r.get('location', '')
            r['lat'] = None
            r['lon'] = None
            
            if loc and ',' in loc:
                try:
                    parts = loc.split(',')
                    r['lat'] = float(parts[0].strip())
                    r['lon'] = float(parts[1].strip())
                except:
                    pass # Invalid GPS format

            # 3. TIME FORMATTING
            time_val = r.get('created')
            if hasattr(time_val, 'strftime'): 
                r['time_str'] = time_val.strftime("%Y-%m-%d %H:%M:%S")
            else:
                r['time_str'] = str(time_val) if time_val else "-"

            results.append(r)
        return results

    @staticmethod
    def get_sos_alerts():
        sos_ref = db.collection("sos_alerts").order_by("time", direction=firestore.Query.DESCENDING).stream()
        results = []
        for doc in sos_ref:
            a = doc.to_dict()
            
            # --- ROBUST TIME FIX ---
            time_val = a.get('time')
            if hasattr(time_val, 'strftime'):
                # If it's a real Date object, format it
                a['time_str'] = time_val.strftime("%Y-%m-%d %H:%M:%S")
            else:
                # If it's a String or None, just use it as is
                a['time_str'] = str(time_val) if time_val else "-"

            results.append(a)
        return results

    @staticmethod
    def get_danger_zones():
        zones = []
        ref = db.collection("danger_zones").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
        
        now = datetime.utcnow() # Current time

        for doc in ref:
            z = doc.to_dict()
            z['id'] = doc.id
            
            # --- CHECK EXPIRY ---
            # If zone has an 'expires_at' field, compare it
            if 'expires_at' in z:
                # Convert firestore datetime to naive python datetime for comparison
                expiry = z['expires_at']
                # If expiry is in the past, SKIP adding it (it's expired)
                if expiry.replace(tzinfo=None) < now:
                    continue 

            zones.append(z)
        return zones

    @staticmethod
    def add_danger_zone(name, category, risk, lat, lon, duration_hours=24):
        try:
            # Calculate Expiry Time
            hours = int(duration_hours) if duration_hours else 24
            expires_at = datetime.utcnow() + timedelta(hours=hours)

            db.collection("danger_zones").add({
                "name": name,
                "category": category,
                "risk": risk,
                "latitude": float(lat),
                "longitude": float(lon),
                "created_at": datetime.utcnow(),
                "expires_at": expires_at # SAVE EXPIRY
            })
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
    # NEW: Ability to remove zones
    @staticmethod
    def delete_danger_zone(zone_id):
        db.collection("danger_zones").document(zone_id).delete()
        
class HealthManager:
    @staticmethod
    def get_cycle_data(user_id):
        # Fetch the latest cycle date
        ref = db.collection("users").document(user_id).collection("cycle_tracker").document("latest")
        doc = ref.get()
        if doc.exists:
            return doc.to_dict().get("last_date")
        return None

    @staticmethod
    def update_cycle_date(user_id, date_str):
        # Save new date
        ref = db.collection("users").document(user_id).collection("cycle_tracker").document("latest")
        ref.set({
            "last_date": date_str,
            "updated_at": datetime.utcnow()
        })

class ComplaintManager:
    @staticmethod
    def save_complaint(user_id, data):
        # Save complaint to user's subcollection
        db.collection("users").document(user_id).collection("police_complaints").add({
            "fir_number": data.get("fir_number"),
            "station": data.get("station"),
            "district": data.get("district"),
            "incident_type": data.get("incident_type"),
            "details": data.get("incident_details"),
            "date": data.get("date"),
            "place": data.get("place"),
            "created_at": datetime.utcnow()
        })
        return True
    
class TravelManager:
    # 🗺️ STATIC DATA (Moved from HTML to Python)
    KERALA_DATA = {
        "thiruvananthapuram":{
            "cities":["trivandrum","varkala","kovalam","attinkal","neyyattinkara","kazhakkoottam","poojappura","pangode","karamana"],
            "risk":"Generally safe capital city", "safety":"Safe",
            "tips":["Avoid isolated beaches late night", "Prefer registered taxis", "Keep emergency number 112 saved"],
            "police":["Museum Police Station","Medical College Police","Vanchiyoor Women Police"],
            "gov_hosp":["Govt Medical College TVM","General Hospital TVM"],
            "private_hosp":["KIMS","NIMS","PRS Hospital"]
        },
        "kollam":{
            "cities":["kollam","paravur","kottarakkara","punalur","karunagappally","kundara","chavara"],
            "risk":"Coastal tourism belt", "safety":"Safe",
            "tips":["Avoid cliffs","Avoid deep sea swimming"],
            "police":["Kollam East Police","Chavara Police"],
            "gov_hosp":["Kollam District Hospital"],
            "private_hosp":["NS Memorial","Travancore Medicity"]
        },
        "pathanamthitta":{
            "cities":["pathanamthitta","adoor","ranni","konni","thiruvalla","mallappally"],
            "risk":"Pilgrim rush in seasons", "safety":"Safe",
            "tips":["Heavy Sabarimala rush seasonally"],
            "police":["Pathanamthitta Police HQ"],
            "gov_hosp":["General Hospital Pathanamthitta"],
            "private_hosp":["Pushpagiri Medical College"]
        },
        "alappuzha":{
            "cities":["alappuzha","alleppey","cherthala","haripad","kayamkulam","mavelikkara"],
            "risk":"Backwater tourism hub", "safety":"Safe",
            "tips":["Wear life jackets","Avoid night boating"],
            "police":["Alappuzha Coastal Police"],
            "gov_hosp":["Alappuzha Medical College"],
            "private_hosp":["VSM Hospital","KVM Hospital"]
        },
        "kottayam":{
            "cities":["kottayam","pala","changanassery","ettumanoor","kanjirappally"],
            "risk":"Hill + college city", "safety":"Moderate",
            "tips":["Hilly roads slippery in rain"],
            "police":["Kottayam East Police"],
            "gov_hosp":["Govt Medical College Kottayam"],
            "private_hosp":["Caritas","Bharath Hospital"]
        },
        "idukki":{
            "cities":["idukki","munnar","thekkady","kumily","devikulam","thodupuzha"],
            "risk":"Forest & hill terrain", "safety":"Caution",
            "tips":["Elephant crossing areas", "Foggy roads – drive slowly", "Avoid walking forest at night"],
            "police":["Munnar Police Station"],
            "gov_hosp":["Idukki District Hospital"],
            "private_hosp":["Highrange Hospital"]
        },
        "ernakulam":{
            "cities":["kochi","ernakulam","aluva","kakkanad","angamaly","perumbavoor","north paravur","thripunithura"],
            "risk":"Metro busy city", "safety":"Moderate",
            "tips":["Avoid isolated metro stations late night", "Use Ola/Uber", "Share trip live"],
            "police":["Kochi City Police HQ","Hill Palace Police"],
            "gov_hosp":["Ernakulam General Hospital","Aluva District Hospital"],
            "private_hosp":["Aster Medcity","Amrita Hospital","Lakeshore Hospital"]
        },
        "thrissur":{
            "cities":["thrissur","guruvayur","chalakudy","kodungallur","mala","wadakkanchery"],
            "risk":"Festival crowded city", "safety":"Safe",
            "tips":["Crowd caution during Pooram"],
            "police":["Thrissur Town Police"],
            "gov_hosp":["Thrissur Medical College"],
            "private_hosp":["Jubilee Mission Hospital","Elite Hospital"]
        },
        "palakkad":{
            "cities":["palakkad","ottappalam","chittur","shoranur","malampuzha"],
            "risk":"Summer heat dehydration risk", "safety":"Safe",
            "tips":["Carry water always"],
            "police":["Palakkad South Police"],
            "gov_hosp":["Palakkad District Hospital"],
            "private_hosp":["PMG Hospital"]
        },
        "malappuram":{
            "cities":["malappuram","manjeri","perinthalmanna","nilambur","tirur","kottakkal"],
            "risk":"Crowded urban region", "safety":"Moderate",
            "tips":["Avoid political processions"],
            "police":["Malappuram Police HQ"],
            "gov_hosp":["Manjeri Medical College"],
            "private_hosp":["Moulana Hospital","MES Hospital"]
        },
        "kozhikode":{
            "cities":["kozhikode","calicut","vadakara","koyilandy","payyoli","feroke"],
            "risk":"Urban coastal", "safety":"Safe",
            "tips":["Avoid rough sea swimming"],
            "police":["Nadakkavu Police Station"],
            "gov_hosp":["Kozhikode Medical College"],
            "private_hosp":["Aster MIMS","Baby Memorial Hospital"]
        },
        "wayanad":{
            "cities":["kalpetta","sulthan bathery","mananthavady","meppadi"],
            "risk":"Wildlife corridors", "safety":"Caution",
            "tips":["Do not exit vehicles in forest"],
            "police":["Bathery Police Station"],
            "gov_hosp":["Wayanad District Hospital"],
            "private_hosp":["Assumption Hospital"]
        },
        "kannur":{
            "cities":["kannur","thalassery","payyannur","mattannur","taliparamba"],
            "risk":"Political tension pockets", "safety":"Moderate",
            "tips":["Avoid rallies & strikes"],
            "police":["Kannur Town Police"],
            "gov_hosp":["Kannur District Hospital"],
            "private_hosp":["AKG Hospital","Dhanalakshmi Hospital"]
        },
        "kasaragod":{
            "cities":["kasaragod","bekal","kanhangad","manjeshwaram","cheruvathur"],
            "risk":"Highway accident risk", "safety":"Moderate",
            "tips":["Avoid night ride NH66"],
            "police":["Kasaragod Town Police"],
            "gov_hosp":["Kanhangad District Hospital"],
            "private_hosp":["Sunrise Hospital"]
        }
    }

    @staticmethod
    def get_all_data():
        return TravelManager.KERALA_DATA