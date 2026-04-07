"""
Test script for BiasGuard Recruiting Module
Tests the recruiting server endpoints and bias auditing functionality
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_home():
    """Test the home page"""
    response = requests.get(f"{BASE_URL}/")
    print(f"Home page status: {response.status_code}")
    print(f"Home page contains 'BiasGuard': {'BiasGuard' in response.text}")
    return response.status_code == 200

def test_list_jobs():
    """Test listing jobs"""
    response = requests.get(f"{BASE_URL}/jobs")
    print(f"List jobs status: {response.status_code}")
    return response.status_code == 200

def test_create_job():
    """Test creating a job"""
    job_data = {
        "title": "Software Engineer",
        "company": "Tech Corp",
        "description": "Looking for a skilled software engineer",
        "requirements": "Python, SQL, 3+ years experience",
        "location": "Remote"
    }
    response = requests.post(f"{BASE_URL}/jobs/create", data=job_data)
    print(f"Create job status: {response.status_code}")
    return response.status_code in [200, 302]

def test_apply():
    """Test candidate application"""
    # First create a job
    job_data = {
        "title": "Data Scientist",
        "company": "AI Inc",
        "description": "Data science position",
        "requirements": "Python, ML, 2+ years",
        "location": "New York"
    }
    requests.post(f"{BASE_URL}/jobs/create", data=job_data)
    
    # Then apply
    candidate_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-1234",
        "skills_score": 85,
        "years_experience": 5,
        "education": "Master",
        "gender": "Male",
        "race": "Asian"
    }
    response = requests.post(f"{BASE_URL}/apply/1", data=candidate_data)
    print(f"Apply status: {response.status_code}")
    return response.status_code in [200, 302]

def test_dashboard():
    """Test dashboard"""
    response = requests.get(f"{BASE_URL}/dashboard")
    print(f"Dashboard status: {response.status_code}")
    return response.status_code == 200

def test_api_create_job():
    """Test API endpoint for creating job"""
    job_data = {
        "title": "Product Manager",
        "company": "StartupXYZ",
        "description": "Lead product development",
        "requirements": "5+ years experience",
        "location": "San Francisco"
    }
    response = requests.post(f"{BASE_URL}/api/jobs", json=job_data)
    print(f"API Create Job status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    return response.status_code == 200

def test_api_apply():
    """Test API endpoint for applying"""
    # Create job first
    job_data = {
        "title": "UX Designer",
        "company": "DesignCo",
        "description": "Design user experiences",
        "requirements": "Figma, UX principles",
        "location": "Austin"
    }
    resp = requests.post(f"{BASE_URL}/api/jobs", json=job_data)
    job_id = resp.json().get("id", 1) if resp.status_code == 200 else 1
    
    # Apply
    app_data = {
        "job_id": job_id,
        "name": "Jane Smith",
        "email": "jane@example.com",
        "phone": "555-5678",
        "skills_score": 90,
        "years_experience": 3,
        "education": "Bachelor",
        "gender": "Female",
        "race": "White"
    }
    response = requests.post(f"{BASE_URL}/api/apply", json=app_data)
    print(f"API Apply status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Application result: {result}")
        # Check if bias audit was called
        if "bias_audit" in result:
            print(f"Bias Audit called: {result['bias_audit']}")
    return response.status_code == 200

def run_all_tests():
    """Run all tests"""
    print("=" * 50)
    print("Testing BiasGuard Recruiting Module")
    print("=" * 50)
    
    tests = [
        ("Home Page", test_home),
        ("List Jobs", test_list_jobs),
        ("Create Job (HTML)", test_create_job),
        ("Apply (HTML)", test_apply),
        ("Dashboard", test_dashboard),
        ("API Create Job", test_api_create_job),
        ("API Apply", test_api_apply),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n--- Testing {name} ---")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"Error: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    print(f"\nTotal: {passed}/{len(results)} tests passed")

if __name__ == "__main__":
    run_all_tests()
