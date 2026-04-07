"""
BiasGuard - AI Bias Detection and Mitigation Web Application
Flask-based web app for analyzing and mitigating bias in recruiting algorithms
"""

import os
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'csv'}

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class BiasAnalyzer:
    """Analyze bias in recruiting data using fairness metrics"""
    
    def __init__(self):
        self.results = {}
    
    def analyze(self, df, predictions, protected_attr):
        """Analyze bias for a protected attribute"""
        
        metrics = {}
        groups = df[protected_attr].unique()
        
        if len(groups) < 2:
            return metrics
        
        group_0, group_1 = groups[0], groups[1]
        mask_0 = df[protected_attr] == group_0
        mask_1 = df[protected_attr] == group_1
        
        rate_0 = predictions[mask_0].mean()
        rate_1 = predictions[mask_1].mean()
        
        metrics['statistical_parity_difference'] = rate_1 - rate_0
        metrics['disparate_impact'] = rate_1 / rate_0 if rate_0 > 0 else 0
        metrics[f'selection_rate_{group_0}'] = rate_0
        metrics[f'selection_rate_{group_1}'] = rate_1
        
        return metrics
    
    def generate_report(self, df, predictions):
        """Generate comprehensive bias report"""
        
        report = {
            'overall_hiring_rate': float(predictions.mean()),
            'total_candidates': len(df),
            'gender': {},
            'race': {},
            'age': {}
        }
        
        # Gender analysis
        if 'gender' in df.columns:
            gender_metrics = self.analyze(df, predictions, 'gender')
            report['gender'] = gender_metrics
            
            # Hiring rates by gender
            for gender in df['gender'].unique():
                mask = df['gender'] == gender
                report['gender'][f'rate_{gender}'] = float(predictions[mask].mean())
        
        # Race analysis
        if 'race' in df.columns:
            report['race'] = {}
            for race in df['race'].unique():
                mask = df['race'] == race
                report['race'][f'rate_{race}'] = float(predictions[mask].mean())
        
        # Age analysis
        if 'age' in df.columns:
            df_temp = df.copy()
            df_temp['age_group'] = pd.cut(df['age'], bins=[0, 30, 45, 60], 
                                          labels=['Young (<30)', 'Middle (30-45)', 'Senior (45+)'])
            report['age'] = {}
            for age_group in df_temp['age_group'].unique():
                if pd.notna(age_group):
                    mask = df_temp['age_group'] == age_group
                    report['age'][f'rate_{age_group}'] = float(predictions[mask].mean())
        
        return report


class BiasMitigator:
    """Mitigate bias using multiple techniques"""
    
    def mitigate(self, df, method='qualification_based'):
        """
        Apply bias mitigation and return corrected predictions
        
        Methods:
        - 'qualification_based': PURELY qualification-based hiring (TRULY FAIR)
        - 'fair_training': Train without demographic features + reweighting
        - 'threshold': Adjust decision thresholds per group
        - 'combined': Use both techniques
        """
        
        if method == 'qualification_based':
            return self._qualification_based_hiring(df)
        elif method == 'fair_training':
            return self._fair_training(df)
        elif method == 'threshold':
            return self._threshold_optimization(df)
        elif method == 'combined':
            return self._combined_mitigation(df)
        else:
            return self._qualification_based_hiring(df)
    
    def _qualification_based_hiring(self, df):
        """
        Create FAIR predictions based ONLY on qualifications.
        This is the MOST FAIR method - hire purely based on merit.
        
        Process:
        1. Calculate a qualification score from gpa, skills, experience, resume
        2. Hire top X% candidates purely based on this score
        3. Ignore all demographic information
        """
        
        # Calculate qualification score (0-100)
        qual_score = np.zeros(len(df))
        
        if 'gpa' in df.columns:
            # GPA normalized to 0-25 (4.0 gpa = 25 points)
            qual_score += (df['gpa'] / 4.0) * 25
        
        if 'skills_score' in df.columns:
            # Skills score 0-25
            qual_score += (df['skills_score'] / 100) * 25
        
        if 'years_experience' in df.columns:
            # Experience 0-25 (capped at 15 years)
            qual_score += (np.clip(df['years_experience'], 0, 15) / 15) * 25
        
        if 'resume_quality' in df.columns:
            # Resume quality 0-25
            qual_score += (df['resume_quality'] / 100) * 25
        
        # Get the hiring rate from original data
        original_hire_rate = df['hired'].mean()
        
        # Determine how many to hire (same rate as original)
        n_to_hire = int(len(df) * original_hire_rate)
        
        # Create fair predictions - hire purely based on qualification score
        predictions = np.zeros(len(df))
        
        # Get indices sorted by qualification score (highest first)
        qualified_indices = np.argsort(qual_score)[::-1]
        
        # Hire top candidates
        predictions[qualified_indices[:n_to_hire]] = 1
        
        return predictions
    
    def _fair_training(self, df):
        """Train a fair model without demographic features"""
        
        # Prepare features (EXCLUDING demographic columns)
        feature_cols = ['gpa', 'years_experience', 'skills_score', 'resume_quality']
        
        # Add education if present
        if 'education_level' in df.columns:
            le = LabelEncoder()
            df = df.copy()
            df['education_encoded'] = le.fit_transform(df['education_level'])
            feature_cols.append('education_encoded')
        
        # Add age if present (but NOT gender or race!)
        if 'age' in df.columns:
            feature_cols.append('age')
        
        # Filter to only columns that exist
        feature_cols = [c for c in feature_cols if c in df.columns]
        
        if len(feature_cols) == 0:
            return df['hired'].values if 'hired' in df.columns else np.zeros(len(df))
        
        X = df[feature_cols].values
        y = df['hired'].values if 'hired' in df.columns else np.zeros(len(df))
        
        # Apply reweighting for fairness
        sample_weights = self._calculate_fairness_weights(df)
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train model with fairness-aware weights
        model = GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42)
        model.fit(X_scaled, y, sample_weight=sample_weights)
        
        # Get predictions
        predictions = model.predict(X_scaled)
        
        return predictions
    
    def _threshold_optimization(self, df):
        """Optimize decision thresholds per group to achieve fairness"""
        
        # Get base predictions
        base_predictions = df['hired'].values.copy()
        
        # For each protected group, adjust threshold
        if 'gender' in df.columns:
            # Calculate target fair rate (overall mean)
            target_rate = base_predictions.mean()
            
            # Adjust for males (typically over-represented)
            male_mask = df['gender'] == 'Male'
            if male_mask.sum() > 0:
                male_rate = base_predictions[male_mask].mean()
                if male_rate > target_rate:
                    # Reduce male hires slightly
                    male_indices = np.where(male_mask)[0]
                    # Randomly reduce some male predictions to 0
                    n_to_remove = int((male_rate - target_rate) * male_mask.sum())
                    np.random.seed(42)
                    remove_indices = np.random.choice(male_indices, n_to_remove, replace=False)
                    base_predictions[remove_indices] = 0
            
            # Adjust for females (typically under-represented)
            female_mask = df['gender'] == 'Female'
            if female_mask.sum() > 0:
                female_rate = base_predictions[female_mask].mean()
                if female_rate < target_rate:
                    # Increase female hires
                    female_indices = np.where(female_mask & (base_predictions == 0))[0]
                    n_to_add = int((target_rate - female_rate) * female_mask.sum())
                    if len(female_indices) > 0:
                        add_indices = np.random.choice(female_indices, 
                                                      min(n_to_add, len(female_indices)), 
                                                      replace=False)
                        base_predictions[add_indices] = 1
        
        return base_predictions
    
    def _combined_mitigation(self, df):
        """Combine fair training with threshold optimization"""
        
        # First, get fair training predictions
        fair_predictions = self._fair_training(df)
        
        # Then apply threshold optimization
        if 'gender' in df.columns:
            # Balance gender rates
            target_rate = fair_predictions.mean()
            
            for gender in df['gender'].unique():
                mask = df['gender'] == gender
                group_rate = fair_predictions[mask].mean()
                
                if group_rate < target_rate * 0.9:
                    # Underrepresented - add more from qualified candidates
                    eligible = mask & (df['gpa'] >= 3.0) & (df['skills_score'] >= 60)
                    eligible_indices = np.where(eligible & (fair_predictions == 0))[0]
                    if len(eligible_indices) > 0:
                        n_add = min(5, len(eligible_indices))
                        add_idx = np.random.choice(eligible_indices, n_add, replace=False)
                        fair_predictions[add_idx] = 1
        
        return fair_predictions
    
    def _calculate_fairness_weights(self, df):
        """Calculate fairness-aware sample weights - MORE AGGRESSIVE"""
        
        weights = np.ones(len(df))
        
        if 'gender' not in df.columns or 'hired' not in df.columns:
            return weights
        
        overall_rate = df['hired'].mean()
        
        # More aggressive reweighting
        for gender in df['gender'].unique():
            mask = df['gender'] == gender
            group_rate = df.loc[mask, 'hired'].mean()
            
            if group_rate > 0:
                # Aggressive adjustment
                adjustment = overall_rate / group_rate
                # Use higher power to make weights more aggressive
                weights[mask] *= np.power(adjustment, 0.8)
                # Clip to reasonable range
                weights[mask] = np.clip(weights[mask], 0.3, 3.0)
        
        # Also reweight by race if present
        if 'race' in df.columns:
            for race in df['race'].unique():
                mask = df['race'] == race
                group_rate = df.loc[mask, 'hired'].mean()
                
                if group_rate > 0:
                    adjustment = overall_rate / group_rate
                    # Apply with moderate power
                    weights[mask] *= np.power(adjustment, 0.5)
                    weights[mask] = np.clip(weights[mask], 0.3, 3.0)
        
        return weights


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze uploaded CSV file for bias"""
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only CSV files are allowed'}), 400
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        # Read CSV
        df = pd.read_csv(filepath)
        
        # Validate required columns
        required_cols = ['gender', 'race', 'age', 'hired']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return jsonify({
                'error': f'Missing required columns: {", ".join(missing_cols)}. Required columns: gender, race, age, hired'
            }), 400
        
        # Add qualification columns if missing
        for col in ['gpa', 'years_experience', 'skills_score', 'resume_quality', 'education_level']:
            if col not in df.columns:
                if col == 'education_level':
                    df[col] = np.random.choice(['High School', 'Bachelor', 'Master', 'PhD'], len(df))
                else:
                    df[col] = np.random.randint(0, 100, len(df))
        
        # Get original predictions (using 'hired' column)
        original_predictions = df['hired'].values
        
        # Analyze bias
        analyzer = BiasAnalyzer()
        bias_report = analyzer.generate_report(df, original_predictions)
        
        # Calculate fairness scores
        fairness_score = 100
        
        if 'gender' in bias_report and 'disparate_impact' in bias_report['gender']:
            di = bias_report['gender']['disparate_impact']
            if 0.8 <= di <= 1.2:
                fairness_score -= abs(1 - di) * 50
            else:
                fairness_score -= 30
        
        fairness_score = max(0, min(100, fairness_score))
        
        # Determine bias level
        if fairness_score >= 80:
            bias_level = "Low"
            bias_color = "green"
        elif fairness_score >= 50:
            bias_level = "Moderate"
            bias_color = "orange"
        else:
            bias_level = "High"
            bias_color = "red"
        
        # Apply mitigation
        mitigator = BiasMitigator()
        mitigated_predictions = mitigator.mitigate(df)
        
        # Calculate improvement
        original_rate = original_predictions.mean()
        mitigated_rate = mitigated_predictions.mean()
        
        # Prepare response
        response = {
            'success': True,
            'report': bias_report,
            'fairness_score': fairness_score,
            'bias_level': bias_level,
            'bias_color': bias_color,
            'original_hiring_rate': original_rate,
            'mitigated_hiring_rate': mitigated_rate,
            'improvement': abs(mitigated_rate - original_rate)
        }
        
        # Save results
        df['mitigated_prediction'] = mitigated_predictions
        result_file = os.path.join(app.config['RESULTS_FOLDER'], 'bias_report.csv')
        df.to_csv(result_file, index=False)
        
        # Create visualization
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        # Gender comparison
        if 'gender' in df.columns:
            genders = df['gender'].unique()
            orig_rates = [original_predictions[df['gender'] == g].mean() for g in genders]
            mit_rates = [mitigated_predictions[df['gender'] == g].mean() for g in genders]
            
            x = np.arange(len(genders))
            width = 0.35
            
            axes[0].bar(x - width/2, orig_rates, width, label='Original', color='#ef4444', alpha=0.8)
            axes[0].bar(x + width/2, mit_rates, width, label='Mitigated', color='#22c55e', alpha=0.8)
            axes[0].set_ylabel('Hiring Rate')
            axes[0].set_title('Gender Bias Comparison')
            axes[0].set_xticks(x)
            axes[0].set_xticklabels(genders)
            axes[0].legend()
            axes[0].set_ylim(0, 1)
        
        # Race comparison
        if 'race' in df.columns:
            races = df['race'].unique()
            orig_rates = [original_predictions[df['race'] == r].mean() for r in races]
            mit_rates = [mitigated_predictions[df['race'] == r].mean() for r in races]
            
            x = np.arange(len(races))
            axes[1].bar(x - width/2, orig_rates, width, label='Original', color='#ef4444', alpha=0.8)
            axes[1].bar(x + width/2, mit_rates, width, label='Mitigated', color='#22c55e', alpha=0.8)
            axes[1].set_ylabel('Hiring Rate')
            axes[1].set_title('Race Bias Comparison')
            axes[1].set_xticks(x)
            axes[1].set_xticklabels(races, rotation=45)
            axes[1].legend()
            axes[1].set_ylim(0, 1)
        
        # Fairness gauge
        axes[2].barh(['Fairness'], [fairness_score], color=bias_color, alpha=0.8)
        axes[2].set_xlim(0, 100)
        axes[2].set_title('Fairness Score')
        axes[2].axvline(x=80, color='green', linestyle='--', alpha=0.5, label='Good')
        axes[2].axvline(x=50, color='orange', linestyle='--', alpha=0.5, label='Moderate')
        
        plt.tight_layout()
        
        chart_file = os.path.join(app.config['RESULTS_FOLDER'], 'bias_chart.png')
        plt.savefig(chart_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        response['chart_url'] = '/results/bias_chart.png'
        response['download_url'] = '/results/bias_report.csv'
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/results/<filename>')
def serve_result(filename):
    """Serve result files"""
    return send_file(os.path.join(app.config['RESULTS_FOLDER'], filename))


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='127.0.0.1')
