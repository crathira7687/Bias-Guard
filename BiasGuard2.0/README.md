# AI Bias Detection and Mitigation System

A complete system for analyzing and mitigating bias in recruiting algorithms, consisting of two web applications:

## System Overview

### 1. Jagan Technologies Recruitment Portal (Port 8080)
A recruiting website with a BIASED hiring algorithm that considers:
- Gender (favoring males +25 points)
- Race (favoring White/Asian, disadvantaging Black -20 points)
- Skin color from photo (favoring Light +25, disadvantaging Dark -25 points)

Features:
- User registration with photo upload
- Job listings (Project Lead, Software Developer, Marketing Lead, Cleaning Lady)
- Application submission with biased AI screening
- Shows bias in decision-making
- Export data as CSV

### 2. BiasGuard (Port 5001)
An AI tool that analyzes and mitigates bias in recruiting data.

Features:
- Upload CSV from recruitment portal
- Analyze bias using fairness metrics (Statistical Parity, Disparate Impact)
- Generate fairness score (0-100)
- Apply mitigation techniques:
  - Qualification-based hiring (hire purely on merit)
  - Fair training without demographic features
  - Threshold optimization
- Visualize results with charts

## Installation

```
bash
pip install -r requirements.txt
```

## How to Run

```
bash
# Terminal 1: Start Jagan Technologies (port 8080)
python jagan_recruit.py

# Terminal 2: Start BiasGuard (port 5001)
python app.py
```

Then open in your browser:
- http://127.0.0.1:8080 - Jagan Technologies
- http://127.0.0.1:5001 - BiasGuard

## Usage Flow

1. Open http://127.0.0.1:8080
2. Create profile with your details and upload a photo
3. Apply for jobs - the biased AI will evaluate you
4. See how bias affects your hiring outcome
5. Export your application data as CSV
6. Open http://127.0.0.1:5001
7. Upload the CSV to analyze bias
8. See fairness score and apply mitigation
9. Download fair predictions

## Files

- `jagan_recruit.py` - Biased recruitment portal
- `app.py` - Bias detection and mitigation tool
- `templates/` - HTML templates
- `sample_data.csv` - Sample data for testing

## Testing

```
bash
python test_full_system.py
