from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import pickle
import pandas as pd
import mysql.connector
from mysql.connector import Error
import hashlib
from functools import wraps

app = Flask(__name__, static_folder="../frontend")
app.secret_key = 'your_secret_key_here'
CORS(app)


model = pickle.load(open("placement_model.pkl", "rb"))
scaler = pickle.load(open("scaler.pkl", "rb"))


DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Rajitha1234',  
    'database': 'placements'
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        print(" Database connected successfully!")
        return connection
    except Error as e:
        print(f" Error connecting to MySQL: {e}")
        print(f" DB_CONFIG: {DB_CONFIG}")
        return None

def create_students_table():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()[0]
            print(f" Current database: {current_db}")
            
            
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {DB_CONFIG["database"]}.students (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    phone VARCHAR(20),
                    tenth_percentage DECIMAL(5,2),
                    inter_percentage DECIMAL(5,2),
                    cgpa DECIMAL(3,2),
                    coding_score INT,
                    dsa_score INT,
                    projects_count INT,
                    internships INT,
                    aptitude_score INT,
                    communication_skill INT,
                    mock_interview_score INT,
                    certifications INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            connection.commit()
            print("Students table created successfully!")
            
           
            cursor.execute(f"SHOW TABLES FROM {DB_CONFIG['database']} LIKE 'students'")
            table_check = cursor.fetchone()
            if table_check:
                print(" Table verification: Students table exists!")
            else:
                print(" Table verification: Students table NOT found!")
                
        except Error as e:
            print(f"Error creating table: {e}")
        finally:
            cursor.close()
            connection.close()
    else:
        print(" Cannot create table - no database connection")


create_students_table()

@app.route("/")
def serve_root():
    return send_from_directory(app.static_folder, "login.html")

@app.route("/dashboard")
def serve_dashboard():
    return send_from_directory(app.static_folder, "dashboard.html")

@app.route("/register")
def serve_register():
    return send_from_directory(app.static_folder, "register.html")

@app.route("/login")
def serve_login():
    return send_from_directory(app.static_folder, "login.html")

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    print(f" Registration data received: {data}")
    
   
    hashed_password = hashlib.sha256(data["password"].encode()).hexdigest()
    print(f" Hashed password: {hashed_password}")
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor()
    try:
        
        cursor.execute("SELECT id FROM students WHERE email = %s", (data["email"],))
        if cursor.fetchone():
            return jsonify({"error": "Email already registered"}), 400
        
        
        cursor.execute('''
            INSERT INTO students (name, email, password, phone, tenth_percentage, 
            inter_percentage, cgpa, coding_score, dsa_score, projects_count, 
            internships, aptitude_score, communication_skill, mock_interview_score, certifications)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            data["name"], data["email"], hashed_password, data.get("phone", ""),
            0.0, 0.0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0  
        ))
        
        connection.commit()
        print(f" Student {data['email']} registered successfully!")
        return jsonify({"message": "Registration successful! Please login to complete your profile."}), 201
        
    except Error as e:
        print(f" Registration error: {e}")
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    print(f" Login data received: {data}")
    
    
    hashed_password = hashlib.sha256(data["password"].encode()).hexdigest()
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor()
    try:
        
        cursor.execute('''
            SELECT id, name, email FROM students 
            WHERE email = %s AND password = %s
        ''', (data["email"], hashed_password))
        
        student = cursor.fetchone()
        if student:
            session['student_id'] = student[0]
            session['student_name'] = student[1]
            session['student_email'] = student[2]
            return jsonify({
                "message": "Login successful!",
                "student": {
                    "id": student[0],
                    "name": student[1],
                    "email": student[2]
                }
            }), 200
        else:
            return jsonify({"error": "Invalid email or password"}), 401
            
    except Error as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()

@app.route("/profile", methods=["GET"])
def get_profile():
    if 'student_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor()
    try:
        cursor.execute('''
            SELECT name, email, phone, tenth_percentage, inter_percentage, cgpa,
            coding_score, dsa_score, projects_count, internships, aptitude_score,
            communication_skill, mock_interview_score, certifications
            FROM students WHERE id = %s
        ''', (session['student_id'],))
        
        student = cursor.fetchone()
        if student:
            return jsonify({
                "student": {
                    "name": student[0],
                    "email": student[1],
                    "phone": student[2],
                    "tenth_percentage": float(student[3]),
                    "inter_percentage": float(student[4]),
                    "cgpa": float(student[5]),
                    "coding_score": student[6],
                    "dsa_score": student[7],
                    "projects_count": student[8],
                    "internships": student[9],
                    "aptitude_score": student[10],
                    "communication_skill": student[11],
                    "mock_interview_score": student[12],
                    "certifications": student[13]
                }
            }), 200
        else:
            return jsonify({"error": "Student not found"}), 404
            
    except Error as e:
        return jsonify({"error": f"Profile fetch failed: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully!"}), 200

@app.route("/update_profile", methods=["POST"])
def update_profile():
    if 'student_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.json
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor()
    try:
        cursor.execute('''
            UPDATE students SET 
            tenth_percentage = %s, inter_percentage = %s, cgpa = %s,
            coding_score = %s, dsa_score = %s, projects_count = %s,
            internships = %s, aptitude_score = %s, communication_skill = %s,
            mock_interview_score = %s, certifications = %s
            WHERE id = %s
        ''', (
            float(data["tenth_percentage"]), float(data["inter_percentage"]), 
            float(data["cgpa"]), int(data["coding_score"]), int(data["dsa_score"]),
            int(data["projects_count"]), int(data["internships"]), int(data["aptitude_score"]),
            int(data["communication_skill"]), int(data["mock_interview_score"]), 
            int(data["certifications"]), session['student_id']
        ))
        
        connection.commit()
        return jsonify({"message": "Profile updated successfully!"}), 200
        
    except Error as e:
        return jsonify({"error": f"Profile update failed: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()

@app.route("/is-logged-in", methods=["GET"])
def is_logged_in():
    if 'student_id' in session:
        return jsonify({"logged_in": True, "student": {
            "id": session['student_id'],
            "name": session['student_name'],
            "email": session['student_email']
        }}), 200
    else:
        return jsonify({"logged_in": False}), 200

@app.route("/check_table", methods=["GET"])
def check_table():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor()
    try:
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'students'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            # Get table structure
            cursor.execute("DESCRIBE students")
            columns = cursor.fetchall()
            
            # Count records
            cursor.execute("SELECT COUNT(*) FROM students")
            count = cursor.fetchone()[0]
            
            return jsonify({
                "message": "Students table exists!",
                "columns": [col[0] for col in columns],
                "record_count": count,
                "table_structure": columns
            }), 200
        else:
            return jsonify({"error": "Students table does not exist"}), 404
            
    except Error as e:
        return jsonify({"error": f"Error checking table: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()

# API endpoint
@app.route("/predict", methods=["POST"])
def predict():
    data = request.json

    # Create DataFrame from input
    sample_student = pd.DataFrame([[
        float(data["tenth_percentage"]),
        float(data["inter_percentage"]),
        float(data["cgpa"]),
        int(data["coding_score"]),
        int(data["dsa_score"]),
        int(data["projects_count"]),
        int(data["internships"]),
        int(data["aptitude_score"]),
        int(data["communication_skill"]),
        int(data["mock_interview_score"]),
        int(data["certifications"])
    ]],
    columns=[
        'tenth_percentage','inter_percentage','cgpa','coding_score','dsa_score',
        'projects_count','internships','aptitude_score','communication_skill',
        'mock_interview_score','certifications'
    ])

    # Scale & predict
    sample_scaled = scaler.transform(sample_student)
    probability = model.predict_proba(sample_scaled)[0][1] * 100

    # Skill analysis
    skills = {
        "Coding": sample_student["coding_score"].values[0],
        "DSA": sample_student["dsa_score"].values[0],
        "Aptitude": sample_student["aptitude_score"].values[0],
        "Communication": sample_student["communication_skill"].values[0]
    }

    # Weak skills
    sorted_skills = sorted(skills.items(), key=lambda x: x[1])
    weak_skills = [skill for skill, score in sorted_skills[:2]]

    # Suggestions
    suggestions = []
    for skill in weak_skills:
        if skill == "Coding":
            suggestions.append("Practice coding problems daily")
        elif skill == "DSA":
            suggestions.append("Solve DSA problems on LeetCode")
        elif skill == "Aptitude":
            suggestions.append("Practice aptitude questions")
        elif skill == "Communication":
            suggestions.append("Improve communication skills")

    return jsonify({
        "placement_probability": round(probability, 2),
        "weak_skills": weak_skills,
        "suggestions": suggestions
    })

if __name__ == "__main__":
    app.run(debug=True)