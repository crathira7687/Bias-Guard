# BiasGuard Web Application Plan

## Project Overview
- **Name**: BiasGuard
- **Type**: Web Application (Flask + HTML/CSS/JS)
- **Purpose**: Upload recruiting algorithm data, analyze bias, generate reports, and provide unbiased predictions

## Features
1. **Upload Section**: Drag & drop CSV file upload
2. **Analysis Dashboard**: Display bias metrics and fairness assessment
3. **Bias Report**: Detailed breakdown of detected biases by gender, race, age
4. **Unbiasing**: Apply mitigation techniques and provide corrected predictions

## UI/UX Design
- **Color Scheme**: Blue (#2563EB) and White (#FFFFFF) with light gray accents
- **Layout**: Clean, minimalistic, centered content
- **Components**:
  - Header with BiasGuard logo/name
  - Upload area with drag & drop
  - Results cards for metrics
  - Charts for visualization
  - Download button for unbiasing results

## Technical Stack
- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Analysis**: Existing bias detection code in main.py

## File Structure
```
chetanlokam/
├── app.py                 # Flask web application
├── templates/
│   └── index.html        # Main web page
├── static/
│   ├── style.css         # Blue/white styling
│   └── script.js         # Frontend logic
├── uploads/              # Uploaded CSV files
├── results/              # Generated reports
└── main.py              # Bias detection core
