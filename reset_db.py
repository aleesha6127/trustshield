import firebase_admin
from firebase_admin import credentials, firestore

# 1. Initialize Firebase (Same as your app)
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def delete_collection(coll_ref, batch_size=50):
    """
    Recursively deletes a collection and its documents.
    """
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0

    for doc in docs:
        print(f'Deleting document: {doc.id} from {coll_ref.id}')
        
        # 2. SPECIAL HANDLING FOR USERS (Delete Subcollections First)
        if coll_ref.id == 'users':
            print(f"  -> Checking subcollections for user: {doc.id}")
            subcollections = ["journeys", "police_complaints", "cycle_tracker"]
            for sub in subcollections:
                sub_ref = doc.reference.collection(sub)
                delete_collection(sub_ref, batch_size)

        # 3. Delete the document itself
        doc.reference.delete()
        deleted += 1

    # Recurse if there are more documents left (pagination)
    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)

def clear_all_data():
    # List of all top-level collections in your models.py
    collections_to_clear = [
        "users",             #
        "sos_alerts",        #
        "incident_reports",  #
        "missing_persons",   #
        "danger_zones"       #
    ]

    print("⚠️  WARNING: This will permanently delete ALL data in the database.")
    confirm = input("Type 'DELETE' to confirm: ")

    if confirm == "DELETE":
        print("\n🚀 Starting Cleanup...")
        for col_name in collections_to_clear:
            print(f"\n--- Cleaning Collection: {col_name} ---")
            delete_collection(db.collection(col_name))
        print("\n✅ Database Successfully Cleared!")
    else:
        print("❌ Operation Cancelled.")

if __name__ == "__main__":
    clear_all_data()