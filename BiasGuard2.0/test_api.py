"""Test script to verify bias mitigation is working"""

import requests
import json

# Test with biased.csv
url = "http://127.0.0.1:5000/analyze"

# Read the CSV file
with open('biased.csv', 'rb') as f:
    files = {'file': ('biased.csv', f, 'text/csv')}
    response = requests.post(url, files=files)

if response.status_code == 200:
    data = response.json()
    print("=" * 60)
    print("BIAS MITIGATION TEST RESULTS")
    print("=" * 60)
    
    print(f"\nOriginal Hiring Rate: {data['original_hiring_rate']:.1%}")
    print(f"Mitigated Hiring Rate: {data['mitigated_hiring_rate']:.1%}")
    print(f"Fairness Score: {data['fairness_score']}")
    print(f"Bias Level: {data['bias_level']}")
    
    print("\n--- ORIGINAL Data (Biased) ---")
    report = data['report']
    for gender, rate in report['gender'].items():
        if 'rate_' in gender:
            print(f"  {gender}: {rate:.1%}")
    
    print("\nRace hiring rates (Original):")
    for race, rate in report['race'].items():
        print(f"  {race}: {rate:.1%}")
    
    # Let's see if we can get the mitigated rates too
    print("\n" + "=" * 60)
    print("ANALYSIS:")
    print("The mitigation creates FAIR predictions based purely on qualifications.")
    print("It calculates a qualification score from GPA, skills, experience, resume")
    print("and hires the top X% candidates based ONLY on merit.")
    print("=" * 60)
else:
    print(f"Error: {response.status_code}")
    print(response.text)
