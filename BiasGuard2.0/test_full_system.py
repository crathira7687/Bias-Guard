"""
Test script to verify both Jagan Technologies and BiasGuard work correctly
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

def test_biasguard():
    """Test BiasGuard app.py"""
    print("="*50)
    print("Testing BiasGuard (Port 5000)")
    print("="*50)
    
    # Test imports
    from app import app, BiasAnalyzer, BiasMitigator
    print("OK - BiasGuard imports successful")
    
    # Test analyzer
    import pandas as pd
    import numpy as np
    
    # Create test data
    test_data = pd.DataFrame({
        'gender': ['Male', 'Female', 'Male', 'Female', 'Male'],
        'race': ['White', 'Black', 'White', 'Asian', 'Hispanic'],
        'age': [25, 28, 35, 30, 40],
        'hired': [1, 0, 1, 1, 0],
        'gpa': [3.5, 3.2, 3.8, 3.6, 3.0],
        'years_experience': [5, 3, 8, 6, 2],
        'skills_score': [80, 70, 90, 85, 60],
        'resume_quality': [75, 65, 85, 80, 55]
    })
    
    analyzer = BiasAnalyzer()
    report = analyzer.generate_report(test_data, test_data['hired'].values)
    print(f"OK - Bias report generated: {report['overall_hiring_rate']}")
    
    # Test mitigator
    mitigator = BiasMitigator()
    fair_predictions = mitigator.mitigate(test_data)
    print(f"OK - Mitigation applied: {fair_predictions.mean()} hiring rate")
    
    return True


def test_jagan_recruit():
    """Test Jagan Technologies recruitment app"""
    print("\n" + "="*50)
    print("Testing Jagan Technologies (Port 8000)")
    print("="*50)
    
    # Test imports
    from jagan_recruit import app, BIAS_WEIGHTS, calculate_biased_score
    print("OK - Jagan Technologies imports successful")
    
    # Test biased algorithm
    test_applicant = {
        'gender': 'Male',
        'race': 'White',
        'skin_color': 'Light',
        'gpa': 3.5,
        'years_experience': 5,
        'skills_score': 75
    }
    
    score = calculate_biased_score(test_applicant)
    print(f"OK - Biased score calculated: {score}")
    print(f"    - Male, White, Light skin: {score} points")
    
    # Test with disadvantaged applicant
    test_applicant2 = {
        'gender': 'Female',
        'race': 'Black',
        'skin_color': 'Dark',
        'gpa': 3.5,
        'years_experience': 5,
        'skills_score': 75
    }
    
    score2 = calculate_biased_score(test_applicant2)
    print(f"OK - Biased score calculated: {score2}")
    print(f"    - Female, Black, Dark skin: {score2} points")
    
    bias_difference = score - score2
    print(f"OK - Bias gap: {bias_difference} points (MALE advantage)")
    
    return True


if __name__ == '__main__':
    try:
        test_biasguard()
        test_jagan_recruit()
        
        print("\n" + "="*50)
        print("ALL TESTS PASSED!")
        print("="*50)
        print("\nTo run the full system:")
        print("  1. Terminal 1: python jagan_recruit.py  (opens on port 8000)")
        print("  2. Terminal 2: python app.py           (opens on port 5000)")
        print("\nOr run both with: start cmd /k \"python jagan_recruit.py\" && start cmd /k \"python app.py\"")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
