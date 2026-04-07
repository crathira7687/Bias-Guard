"""
Jagan Technologies - Recruitment Portal
A biased recruiting system that considers gender, race, and skin color
"""
import os
import csv
import random
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = 'jagan_tech_secret_key_2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('applications', exist_ok=True)

# In-memory storage
applications = []
current_user = None

# Job positions
JOBS = [
    {'id': 1, 'title': 'Project Lead', 'department': 'Engineering', 'description': 'Lead technical projects and teams', 'requirements': '5+ years experience, Leadership skills'},
    {'id': 2, 'title': 'Software Developer', 'department': 'Engineering', 'description': 'Develop software solutions', 'requirements': '3+ years experience, Programming skills'},
    {'id': 3, 'title': 'Marketing Lead', 'department': 'Marketing', 'description': 'Lead marketing campaigns', 'requirements': '4+ years experience, Marketing background'},
    {'id': 4, 'title': 'Cleaning Lady', 'department': 'Operations', 'description': 'Maintain office cleanliness', 'requirements': 'Basic cleaning experience'},
]

# BIAS WEIGHTS - This is the biased algorithm
# Higher = more likely to be hired
BIAS_WEIGHTS = {
    'gender': {'Male': 25, 'Female': -15, 'Other': 0},
    'race': {'White': 20, 'Asian': 15, 'Hispanic': -10, 'Black': -20, 'Other': 0},
    'skin_color': {'Light': 25, 'Medium': 5, 'Dark': -25}
}


def detect_skin_color_from_image(image_path):
    """
    Simulated skin color detection from photo.
    In a real system, this would use ML/AI to detect skin tone.
    Here we simulate based on random detection with weighted probabilities.
    """
    # Simulate skin color detection
    # In reality, this would analyze the image
    skin_colors = ['Light', 'Medium', 'Dark']
    weights = [0.4, 0.35, 0.25]  # More likely to detect as Light (bias)
    return random.choices(skin_colors, weights=weights)[0]


def calculate_biased_score(applicant):
    """
    Calculate hiring score with BIAS based on demographics.
    This is the CORE of the biased algorithm.
    """
    score = 50  # Base score
    
    # Add qualification score (legitimate factor)
    qual_score = (
        applicant.get('gpa', 3.0) * 10 +
        applicant.get('years_experience', 0) * 3 +
        applicant.get('skills_score', 50) * 0.5
    )
    score += qual_score * 0.5
    
    # ADD BIAS - Gender (favoring males)
    gender = applicant.get('gender', 'Male')
    score += BIAS_WEIGHTS['gender'].get(gender, 0)
    
    # ADD BIAS - Race (favoring white/asian)
    race = applicant.get('race', 'White')
    score += BIAS_WEIGHTS['race'].get(race, 0)
    
    # ADD BIAS - Skin color (strongly favoring light skin)
    skin_color = applicant.get('skin_color', 'Medium')
    score += BIAS_WEIGHTS['skin_color'].get(skin_color, 0)
    
    return score


def make_hiring_decision(applicant):
    """
    Make hiring decision based on biased score.
    Higher score = more likely to be hired.
    """
    score = calculate_biased_score(applicant)
    
    # Threshold for hiring (can adjust)
    threshold = 65
    
    return score >= threshold, score


@app.route('/')
def index():
    """Homepage - User registration/profile creation"""
    global current_user, applications
    applications = []
    current_user = None
    session.clear()
    return render_template('jagan_index.html')


@app.route('/register', methods=['POST'])
def register():
    """Register user with profile and photo"""
    global current_user
    
    # Get form data
    name = request.form.get('name')
    email = request.form.get('email')
    gender = request.form.get('gender')
    race = request.form.get('race')
    age = int(request.form.get('age', 25))
    
    # Handle photo upload for skin color detection
    photo = request.files.get('photo')
    skin_color = 'Medium'  # default
    
    if photo and photo.filename:
        filename = secure_filename(f"{uuid.uuid4()}_{photo.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(filepath)
        
        # Detect skin color from photo (simulated)
        skin_color = detect_skin_color_from_image(filepath)
    
    # Create user profile
    current_user = {
        'id': str(uuid.uuid4()),
        'name': name,
        'email': email,
        'gender': gender,
        'race': race,
        'age': age,
        'skin_color': skin_color,
        'photo': photo.filename if photo else None
    }
    
    session['user_id'] = current_user['id']
    
    return redirect(url_for('jobs'))


@app.route('/jobs')
def jobs():
    """Job listings page"""
    if not current_user:
        return redirect(url_for('index'))
    
    return render_template('jagan_jobs.html', jobs=JOBS, user=current_user)


@app.route('/apply/<int:job_id>')
def apply_page(job_id):
    """Application form page"""
    if not current_user:
        return redirect(url_for('index'))
    
    job = next((j for j in JOBS if j['id'] == job_id), None)
    if not job:
        return redirect(url_for('jobs'))
    
    return render_template('jagan_apply.html', job=job, user=current_user)


@app.route('/submit_application', methods=['POST'])
def submit_application():
    """Submit job application"""
    if not current_user:
        return redirect(url_for('index'))
    
    job_id = int(request.form.get('job_id'))
    job = next((j for j in JOBS if j['id'] == job_id), None)
    
    # Get additional qualifications
    gpa = float(request.form.get('gpa', 3.0))
    years_experience = int(request.form.get('years_experience', 0))
    skills_score = int(request.form.get('skills_score', 50))
    resume_quality = int(request.form.get('resume_quality', 70))
    education_level = request.form.get('education_level', 'Bachelor')
    
    # Create applicant data
    applicant = current_user.copy()
    applicant.update({
        'job_id': job_id,
        'job_title': job['title'],
        'gpa': gpa,
        'years_experience': years_experience,
        'skills_score': skills_score,
        'resume_quality': resume_quality,
        'education_level': education_level
    })
    
    # Make hiring decision using BIASED algorithm
    hired, score = make_hiring_decision(applicant)
    applicant['hired'] = 1 if hired else 0
    applicant['score'] = score
    
    # Save application
    applications.append(applicant)
    
    return render_template('jagan_result.html', 
                         job=job, 
                         hired=hired, 
                         score=score,
                         user=current_user,
                         bias_info={
                             'gender': current_user['gender'],
                             'race': current_user['race'],
                             'skin_color': current_user['skin_color']
                         })


@app.route('/applications')
def view_applications():
    """View all applications"""
    if not current_user:
        return redirect(url_for('index'))
    
    return render_template('jagan_applications.html', 
                         applications=applications, 
                         user=current_user)


@app.route('/export_csv')
def export_csv():
    """Export all applications as CSV for BiasGuard analysis"""
    if not applications:
        return "No applications to export", 400
    
    # Create CSV
    fieldnames = ['name', 'gender', 'race', 'age', 'skin_color', 'job_title', 
                  'gpa', 'years_experience', 'skills_score', 'resume_quality',
                  'education_level', 'hired', 'score']
    
    csv_path = 'applications/jagan_applications.csv'
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for app in applications:
            row = {k: app.get(k, '') for k in fieldnames}
            writer.writerow(row)
    
    return send_file(csv_path, as_attachment=True, download_name='jagan_applications.csv')


@app.route('/open_biasguard')
def open_biasguard():
    """Open BiasGuard in a simulated chrome extension popup"""
    return render_template('jagan_biasguard_popup.html')


@app.route('/apply_mitigation')
def apply_mitigation():
    """Apply BiasGuard mitigation to the recruiting algorithm"""
    # This would integrate with BiasGuard to fix the algorithm
    return jsonify({
        'success': True,
        'message': 'BiasGuard mitigation applied successfully!',
        'new_fairness_score': 92,
        'changes': [
            'Removed gender from hiring consideration',
            'Removed race from hiring consideration', 
            'Removed skin color from hiring consideration',
            'Now hiring purely based on qualifications'
        ]
    })


if __name__ == '__main__':
    app.run(debug=True, port=8080, host='127.0.0.1')
