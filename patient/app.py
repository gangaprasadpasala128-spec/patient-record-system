import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from dotenv import load_dotenv
from functools import wraps

# Load variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = "healthsync_secure_key_2024"

# ─── Demo User Credentials ──────────────────────────────────────────────────
USERS = {
    "admin": {"password": "admin123", "role": "admin", "name": "Administrator"},
    "dr.house": {"password": "house123", "role": "doctor", "name": "Dr. House", "dept": "Cardiology"},
    "dr.strange": {"password": "strange123", "role": "doctor", "name": "Dr. Strange", "dept": "Neurology"},
    "dr.grey": {"password": "grey123", "role": "doctor", "name": "Dr. Grey", "dept": "Pediatrics"},
    "dr.shepherd": {"password": "shepherd123", "role": "doctor", "name": "Dr. Shepherd", "dept": "Dermatology"},
    "patient1": {"password": "pass123", "role": "patient", "name": "Rahul Sharma", "doctor": "dr.house"},
    "patient2": {"password": "pass123", "role": "patient", "name": "Anjali Gupta", "doctor": "dr.strange"},
    "patient3": {"password": "pass123", "role": "patient", "name": "Priya Reddy", "doctor": "dr.grey"},
}

# ─── Role-based decorators ──────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user" not in session:
                return redirect(url_for("login"))
            if session["user"]["role"] not in roles:
                flash("Access denied for your role.", "error")
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return decorated
    return decorator

# MongoDB configuration
app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://localhost:27017/patientdb")
mongo = None
use_fallback = False

try:
    mongo = PyMongo(app)
    # Check if mongo is connected
    mongo.db.command('ping')
    print("Connected to MongoDB successfully.")
except Exception as e:
    print(f"MongoDB connection failed: {e}. Using in-memory fallback.")
    use_fallback = True
    # Pre-populated realistic patient data (5-8 people)
    patients_fallback = [
        {
            "_id": "p1", "name": "Rahul Sharma", "age": 45, "gender": "Male", 
            "contact": "+91 98765 43210", "problem": "Chronic Lower Back Pain", 
            "doctor": "Dr. Watson (Orthopedics)", "medical_history": "Previous disk slip in 2018"
        },
        {
            "_id": "p2", "name": "Anjali Gupta", "age": 32, "gender": "Female", 
            "contact": "+91 87654 32109", "problem": "Severe Migraine & Nausea", 
            "doctor": "Dr. Strange (Neurology)", "medical_history": "Allergic to Ibuprofen"
        },
        {
            "_id": "p3", "name": "Vikram Singh", "age": 58, "gender": "Male", 
            "contact": "+91 76543 21098", "problem": "Chest Tightness & Fatigue", 
            "doctor": "Dr. House (Cardiology)", "medical_history": "History of Hypertension"
        },
        {
            "_id": "p4", "name": "Priya Reddy", "age": 8, "gender": "Female", 
            "contact": "+91 65432 10987", "problem": "High Fever & Viral Rash", 
            "doctor": "Dr. Grey (Pediatrics)", "medical_history": "Asthma history"
        },
        {
            "_id": "p5", "name": "Amit Verma", "age": 29, "gender": "Male", 
            "contact": "+91 54321 09876", "problem": "Persistent Eczema Flare-up", 
            "doctor": "Dr. Shepherd (Dermatology)", "medical_history": "Nut allergies"
        },
        {
            "_id": "p6", "name": "Suresh Iyer", "age": 67, "gender": "Male", 
            "contact": "+91 43210 98765", "problem": "Cataract - Blurred Vision", 
            "doctor": "Dr. Smith (Ophthalmology)", "medical_history": "Diabetes Type 2"
        },
        {
            "_id": "p7", "name": "Neha Kapoor", "age": 41, "gender": "Female", 
            "contact": "+91 32109 87654", "problem": "Post-Op Recovery Checkup", 
            "doctor": "Dr. Wilson (Surgery)", "medical_history": "Appendix removal last month"
        },
        {
            "_id": "p8", "name": "Kiran Rao", "age": 35, "gender": "Male", 
            "contact": "+91 21098 76543", "problem": "Shortness of Breath", 
            "doctor": "Dr. Adams (Emergency)", "medical_history": "None"
        }
    ]

@app.route('/')
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    if use_fallback:
        patients = patients_fallback
    else:
        patients = list(mongo.db.patients.find())
    base_count = 200
    total_patients = len(patients) + base_count
    resolved_cases = int(total_patients * 0.98)
    return render_template('index.html', patients=patients, total=total_patients, resolved=resolved_cases, user=session["user"])

# ─── Auth Routes ─────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()
        role_selected = request.form.get('role', '')
        user = USERS.get(username)
        if user and user['password'] == password and user['role'] == role_selected:
            session['user'] = {**user, 'username': username}
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid credentials or wrong role selected.", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    role = session['user']['role']
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'doctor':
        return redirect(url_for('doctor_dashboard'))
    else:
        return redirect(url_for('patient_dashboard'))

@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    patients = patients_fallback if use_fallback else list(mongo.db.patients.find())
    doctors = [v for v in USERS.values() if v['role'] == 'doctor']
    patients_users = [v for v in USERS.values() if v['role'] == 'patient']
    return render_template('admin_dashboard.html', user=session['user'],
                           patients=patients, doctors=doctors, patient_users=patients_users)

@app.route('/doctor/dashboard')
@role_required('doctor')
def doctor_dashboard():
    uname = session['user']['username']
    doc_name = session['user']['name']
    my_patients = [p for p in (patients_fallback if use_fallback else list(mongo.db.patients.find()))
                   if doc_name.lower() in p.get('doctor', '').lower()]
    # Include username in assigned_patients for consistent room naming
    assigned_patients = [
        {**v, 'username': k}
        for k, v in USERS.items()
        if v.get('role') == 'patient' and v.get('doctor') == uname
    ]
    return render_template('doctor_dashboard.html', user=session['user'],
                           my_patients=my_patients, assigned_patients=assigned_patients)

@app.route('/patient/dashboard')
@role_required('patient')
def patient_dashboard():
    doc_key = session['user'].get('doctor', '')
    doctor_info = USERS.get(doc_key, {})
    return render_template('patient_dashboard.html', user=session['user'], doctor=doctor_info)

@app.route('/about')
def about():
    return render_template('about.html', user=session.get('user'))

@app.route('/records')
@role_required('admin', 'doctor')
def records():
    patients = patients_fallback if use_fallback else list(mongo.db.patients.find())
    total_patients = 200 + len(patients)
    # Get registered users
    registered_users = [{'username': k, **v} for k, v in USERS.items()]
    return render_template('records.html', patients=patients, total=total_patients, user=session.get('user'), registered_users=registered_users)

@app.route('/services')
def services():
    return render_template('services.html', user=session.get('user'))

@app.route('/contact')
def contact():
    return render_template('contact.html', user=session.get('user'))

@app.route('/consult')
@login_required
def consult():
    return render_template('consult.html', user=session.get('user'))

@app.route('/add_patient', methods=['POST'])
@role_required('admin', 'doctor')
def add_patient():
    try:
        patient_data = {
            'name': request.form.get('name'),
            'age': int(request.form.get('age', 0)),
            'gender': request.form.get('gender'),
            'medical_history': request.form.get('medical_history'),
            'contact': request.form.get('contact'),
            'problem': request.form.get('problem'),
            'doctor': request.form.get('doctor')
        }
        if not patient_data['name']:
            flash("Name is required!", "error")
            return redirect(url_for('index'))
        if use_fallback:
            import uuid
            patient_data['_id'] = str(uuid.uuid4())
            patients_fallback.append(patient_data)
        else:
            mongo.db.patients.insert_one(patient_data)
        flash("Patient added successfully!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    return redirect(url_for('index'))

@app.route('/delete_patient/<patient_id>')
@role_required('admin')
def delete_patient(patient_id):
    try:
        if use_fallback:
            global patients_fallback
            patients_fallback = [p for p in patients_fallback if p['_id'] != patient_id]
        else:
            mongo.db.patients.delete_one({'_id': ObjectId(patient_id)})
        flash("Patient record deleted.", "info")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)
