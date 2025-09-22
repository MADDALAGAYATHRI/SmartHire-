import os
import datetime
import io
import csv
from io import StringIO

from flask import (
    Flask, render_template, request, redirect, url_for, flash, jsonify,
    send_file, session
)
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
from flasgger import Swagger
from backend.agents.resume_agent import ResumeAgent


# -------------------------
# Flask App Setup
# -------------------------
app = Flask(__name__)
app.secret_key = "supersecretkey"
CORS(app)
swagger = Swagger(app)
resume_agent = ResumeAgent()

# -------------------------
# MongoDB Connection
# -------------------------
client = MongoClient("mongodb://localhost:27017/")
db = client.smarthire
users_collection = db.users
jobs_collection = db.jobs
candidates_collection = db.candidates

# -------------------------
# Home & Dashboard
# -------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    total_jobs = jobs_collection.count_documents({})
    active_jobs = jobs_collection.count_documents({"status": "active"})
    total_candidates = candidates_collection.count_documents({})

    recent_jobs = list(jobs_collection.find().sort("created_at", -1).limit(5))
    recent_candidates = list(candidates_collection.find().sort("created_at", -1).limit(5))

    # Convert ObjectId to string
    for j in recent_jobs:
        j["id"] = str(j["_id"])
        j.pop("_id", None)
    for c in recent_candidates:
        c["id"] = str(c["_id"])
        c.pop("_id", None)

    return render_template(
        "dashboard.html",
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        total_candidates=total_candidates,
        recent_jobs=recent_jobs,
        recent_candidates=recent_candidates
    )

# -------------------------
# Auth
# -------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        if not all([name, email, password, role]):
            return render_template("signup.html", error="All fields are required.")

        if users_collection.find_one({"email": email}):
            return render_template("signup.html", error="Email already registered.")

        hashed_pw = generate_password_hash(password)
        users_collection.insert_one({
            "name": name,
            "email": email,
            "password": hashed_pw,
            "role": role
        })

        flash("Signup successful! Please login.")
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = users_collection.find_one({"email": email})
        if not user or not check_password_hash(user["password"], password):
            return render_template("login.html", error="Invalid email or password.")

        # ✅ Save user info in session
        session["user_id"] = str(user["_id"])
        session["name"] = user.get("name", "")
        session["role"] = user.get("role", "seeker")

        # ✅ Desired landing:
        # HR -> dashboard, Seeker -> jobs
        if session["role"] == "hr":
            return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("jobs_page"))

    return render_template("login.html")
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -------------------------
# Jobs Pages
# -------------------------
@app.route("/jobs")
def jobs_page():
    return render_template("jobs.html", create_mode=False)

@app.route("/create-job")
def create_job_page():
    return render_template("jobs.html", create_mode=True)

@app.route("/jobs/<job_id>")
def job_detail_page(job_id):
    return render_template("job_detail.html", job_id=job_id)
@app.route("/applications")
def my_applications_page():
    if session.get("role") != "seeker":
        return redirect(url_for("login"))
    return render_template("applications.html")


# -------------------------
# API: Jobs
# -------------------------
@app.route("/api/jobs", methods=["GET", "POST"])
def api_jobs():
    if request.method == "GET":
        status = request.args.get("status")
        query = {"status": status} if status else {}
        jobs = list(jobs_collection.find(query).sort("created_at", -1))
        for job in jobs:
            job["id"] = str(job["_id"])
            job.pop("_id", None)
        return jsonify(jobs)

    # POST - create new job
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    job_data = {
        "title": data.get("title", ""),
        "department": data.get("department", ""),
        "location": data.get("location", ""),
        "salary_range": data.get("salary_range", ""),
        "description": data.get("description", ""),
        "requirements": data.get("requirements", ""),
        "status": data.get("status", "active"),
        "created_at": datetime.datetime.utcnow()
    }

    result = jobs_collection.insert_one(job_data)
    job_data["id"] = str(result.inserted_id)
    return jsonify(job_data)

@app.route("/api/jobs/<job_id>", methods=["GET"])
def get_job(job_id):
    job = jobs_collection.find_one({"_id": ObjectId(job_id)})
    if not job:
        return jsonify({"error": "Job not found"}), 404

    job["_id"] = str(job["_id"])

    # Fetch candidates separately
    candidates = list(candidates_collection.find({"job_id": job_id}))
    candidates = sorted(candidates, key=lambda c: c.get("score", 0), reverse=True)

    for c in candidates:
        c["_id"] = str(c["_id"])

    job["candidates"] = candidates
    return jsonify(job)

# -------------------------
# Resume Upload
# -------------------------
@app.route("/upload-resume", methods=["POST"])
def upload_resume():
    job_id = request.form.get("job_id")
    file = request.files.get("resumeFile")

    if not job_id:
        return jsonify({"error": "Missing job_id"}), 400
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    # Fetch the job from DB
    job = jobs_collection.find_one({"_id": ObjectId(job_id)})
    if not job:
        return jsonify({"error": "Job not found"}), 404

    # Use ResumeAgent to process the file
    import asyncio
    cand_id, score = asyncio.run(resume_agent.process_one(job, file))

    # Fetch the saved candidate document
    candidate_doc = candidates_collection.find_one({"_id": ObjectId(cand_id)})
    candidate_doc["id"] = cand_id
    candidate_doc.pop("_id", None)

    return jsonify({
        "message": "Resume uploaded and candidate saved",
        "candidate": candidate_doc
    })


# -------------------------
# Candidate Export
# -------------------------
@app.route("/api/candidates/export.csv", methods=["GET"])
def export_candidates():
    job_id = request.args.get("job_id")
    if not job_id:
        return jsonify({"error": "Missing job_id"}), 400

    candidates = list(candidates_collection.find({"job_id": job_id}))
    if not candidates:
        return jsonify({"error": "No candidates found"}), 404

    # Sort candidates by score (highest first)
    candidates = sorted(candidates, key=lambda c: c.get("score", 0), reverse=True)

    # Prepare CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Rank", "Name", "Email", "Experience (Years)", "Score", "Status", "Resume Preview"])

    for i, c in enumerate(candidates, start=1):
        writer.writerow([
            i,  # Rank
            c.get("name", "N/A"),
            c.get("email", "N/A"),
            c.get("experience_years", "N/A"),
            c.get("score", 0),
            c.get("status", "new"),
            (c.get("resume_text", "")[:100] + "...") if c.get("resume_text") else ""
        ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="candidates.csv"
    )
@app.get("/api/my_applications")
def my_applications():
    if "user_id" not in session or session.get("role") != "seeker":
        return jsonify({"error": "Unauthorized"}), 403

    user_id = session["user_id"]

    applications = Candidate.query.filter_by(user_id=user_id).all()
    jobs = Job.query.all()
    job_map = {job.id: job for job in jobs}

    result = []
    for app in applications:
        job = job_map.get(app.job_id)
        if job:
            result.append({
                "job_id": job.id,
                "job_title": job.title,
                "department": job.department,
                "location": job.location,
                "salary_range": job.salary_range,
                "status": app.status,
                "score": app.score
            })

    return jsonify(result)
@app.context_processor
def inject_user():
    return {
        "user_role": session.get("role"),
        "user_name": session.get("name")
    }

from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = '/docs'  # Swagger UI endpoint
API_URL = '/static/swagger.json'  # Where swagger.json is served from

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "SmartHire API"}
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
from flask import jsonify, request

# Example: API endpoint for job seeker applications
@app.route("/api/my-applications", methods=["GET"])
def api_my_applications():
    # In real app, fetch from DB using logged-in user_id
    applications = [
        {"id": 1, "job_title": "Software Engineer", "status": "Submitted"},
        {"id": 2, "job_title": "Data Analyst", "status": "Under Review"}
    ]
    return jsonify(applications)


# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    app.run(debug=True, port=8000)
