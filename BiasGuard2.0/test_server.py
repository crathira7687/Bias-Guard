"""Test script for BiasGuard Recruiting Server on port 8001"""
import requests
import json

BASE_URL = "http://127.0.0.1:8001"

def test_home():
    response = requests.get(f"{BASE_URL}/")
    print(f"Home: {response.status_code}")
    return response.status_code == 200

def test_create_job_api():
    job_data = {
        "title": "Software Engineer",
        "description": "Great opportunity",
        "required_experience": 2,
        "required_skill_score": 70
    }
    response = requests.post(f"{BASE_URL}/api/jobs", json=job_data)
    print(f"API Create Job: {response.status_code}")
    if response.status_code == 201:
        print(f"  Response: {response.json()}")
    return response.status_code == 201

def test_list_jobs_api():
    response = requests.get(f"{BASE_URL}/api/jobs")
    print(f"API List Jobs: {response.status_code}")
    if response.status_code == 200:
        print(f"  Jobs: {response.json()}")
    return response.status_code == 200

def test_apply_api():
    # First create job
    job_data = {"title": "Data Scientist", "description": "ML role", "required_experience": 3, "required_skill_score": 80}
    resp = requests.post(f"{BASE_URL}/api/jobs", json=job_data)
    job_id = resp.json().get("id", 1) if resp.status_code == 201 else 1
    
    # Apply
    app_data = {
        "name": "John Doe",
        "gender": "Male",
        "experience": 5,
        "skill_score": 90,
        "education_level": "Master"
    }
    response = requests.post(f"{BASE_URL}/api/apply?job_id={job_id}", json=app_data)
    print(f"API Apply: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"  Application result: {result.get('decision_text')}")
        print(f"  Bias Audit: {result.get('bias_audit')}")
    return response.status_code == 200

def test_dashboard():
    response = requests.get(f"{BASE_URL}/recruiter/dashboard")
    print(f"Dashboard: {response.status_code}")
    return response.status_code == 200

if __name__ == "__main__":
    tests = [
        ("Home", test_home),
        ("API Create Job", test_create_job_api),
        ("API List Jobs", test_list_jobs_api),
        ("API Apply", test_apply_api),
        ("Dashboard", test_dashboard),
    ]
    
    print("=" * 50)
    print("Testing Recruiting Server")
    print("=" * 50)
    
    for name, test in tests:
        print(f"\n--- {name} ---")
        try:
            result = test()
            print(f"PASS" if result else "FAIL")
        except Exception as e:
            print(f"ERROR: {e}")
