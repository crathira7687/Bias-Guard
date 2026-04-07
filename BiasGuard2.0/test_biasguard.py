#!/usr/bin/env python
"""Test script for BiasGuard app"""
import sys
sys.path.insert(0, 'c:/Users/loq/Downloads/chetanlokam')

from app import app
import io

# Test the app
with app.test_client() as client:
    # Test homepage
    print("Testing GET / ...")
    response = client.get('/')
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print("  OK - Homepage loads")
    else:
        print("  FAIL - Homepage doesn't load")
    
    # Test analyze endpoint with sample data
    print("\nTesting POST /analyze ...")
    
    # Create test CSV data
    csv_content = """gender,race,age,hired,gpa,years_experience,skills_score,resume_quality,education_level
Male,White,28,1,3.5,5,80,75,Bachelor
Female,Black,25,0,3.2,3,65,70,Bachelor
Male,Asian,30,1,3.8,7,85,80,Master
Female,Hispanic,27,0,3.0,2,60,65,Bachelor
Male,White,35,1,3.6,10,90,85,Master
Female,Black,24,0,3.1,1,55,60,Bachelor
Male,Asian,32,1,3.7,8,88,82,Master
Female,Hispanic,29,0,3.3,4,70,72,Bachelor
"""
    
    # Convert to bytes
    csv_bytes = io.BytesIO(csv_content.encode('utf-8'))
    
    response = client.post('/analyze', 
                          data={'file': (csv_bytes, 'test.csv')},
                          content_type='multipart/form-data')
    
    print(f"  Status: {response.status_code}")
    
    if response.status_code == 200:
        import json
        data = json.loads(response.data)
        if data.get('success'):
            print("  OK - Analysis works!")
            print(f"  Fairness Score: {data.get('fairness_score')}")
            print(f"  Bias Level: {data.get('bias_level')}")
            print(f"  Original Rate: {data.get('original_hiring_rate')}")
            print(f"  Mitigated Rate: {data.get('mitigated_hiring_rate')}")
        else:
            print(f"  FAIL - Error: {data.get('error')}")
    else:
        print(f"  FAIL - Response: {response.data[:500]}")

print("\nDone!")
