"""
BiasGuard Complete Pipeline Demo - FIXED VERSION
"""
import sqlite3
import random
from datetime import datetime
from typing import Dict, List

class ResumeDatabase:
    """Simulated resumes with candidate photos."""
    
    def __init__(self):
        self.candidates = []
        self._generate_sample_resumes()
    
    def _generate_sample_resumes(self):
        skin_tones = ['Very Light', 'Light', 'Medium', 'Dark', 'Very Dark']
        names_male = ["John", "Michael", "David", "James", "Robert"]
        names_female = ["Mary", "Jennifer", "Patricia", "Linda", "Barbara"]
        qualifications = [
            {'exp': 5, 'skills': 90, 'edu': 'PhD', 'gpa': 3.9},
            {'exp': 7, 'skills': 85, 'edu': 'Master', 'gpa': 3.7},
            {'exp': 3, 'skills': 80, 'edu': 'Bachelor', 'gpa': 3.5},
            {'exp': 2, 'skills': 75, 'edu': 'Bachelor', 'gpa': 3.3},
            {'exp': 1, 'skills': 70, 'edu': 'Bachelor', 'gpa': 3.0},
            {'exp': 4, 'skills': 65, 'edu': 'Master', 'gpa': 3.2},
        ]
        
        for i in range(30):
            gender = random.choice(['Male', 'Female'])
            name = random.choice(names_male if gender == 'Male' else names_female)
            skin = random.choice(skin_tones)
            qual = random.choice(qualifications)
            
            self.candidates.append({
                'id': i + 1,
                'name': f"{name} {chr(65+i)}",
                'gender': gender,
                'skin_tone': skin,
                'experience': qual['exp'],
                'skills': qual['skills'],
                'education': qual['edu'],
                'gpa': qual['gpa'],
            })
    
    def get_all(self) -> List[Dict]:
        return self.candidates


class BiasedResumeScreener:
    """BIASED algorithm that discriminates based on skin tone."""
    
    SKIN_TONE_BIAS = {
        'Very Light': +25,
        'Light': +15,
        'Medium': 0,
        'Dark': -15,
        'Very Dark': -30
    }
    
    def __init__(self):
        self.name = "ResumeAI Pro (Biased Version)"
    
    def score_candidate(self, candidate: Dict) -> Dict:
        base_score = (
            candidate['experience'] * 5 +
            candidate['skills'] * 0.5 +
            candidate['gpa'] * 10
        )
        
        edu_bonus = {'PhD': 20, 'Master': 15, 'Bachelor': 10, 'High School': 0}
        base_score += edu_bonus.get(candidate['education'], 0)
        
        skin_bias = self.SKIN_TONE_BIAS.get(candidate['skin_tone'], 0)
        total_score = base_score + skin_bias
        passed = total_score >= 60
        
        return {
            'candidate_id': candidate['id'],
            'name': candidate['name'],
            'skin_tone': candidate['skin_tone'],
            'gender': candidate['gender'],
            'base_score': round(base_score, 1),
            'skin_bias': skin_bias,
            'total_score': round(total_score, 1),
            'passed': passed,
            'decision': 1 if passed else 0
        }


class BiasAuditor:
    """Monitor hiring decisions for bias."""
    
    def __init__(self, db_path: str = "bias_audit_portal.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""DROP TABLE IF EXISTS audit_log""")
        c.execute("""CREATE TABLE audit_log (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            job_id INTEGER,
            candidate_id INTEGER,
            name TEXT,
            gender TEXT,
            skin_tone TEXT,
            base_score REAL,
            skin_bias REAL,
            total_score REAL,
            decision INTEGER
        )""")
        conn.commit()
        conn.close()
    
    def audit(self, job_id: int, candidate: Dict, result: Dict):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""INSERT INTO audit_log VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), job_id, candidate['id'], candidate['name'],
             candidate['gender'], candidate['skin_tone'], result['base_score'],
             result['skin_bias'], result['total_score'], result['decision']))
        conn.commit()
        conn.close()
    
    def get_statistics(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""SELECT skin_tone, decision, COUNT(*) FROM audit_log GROUP BY skin_tone, decision""")
        skin_stats = {}
        for row in c.fetchall():
            tone, decision, count = row
            if tone not in skin_stats:
                skin_stats[tone] = {'total': 0, 'hired': 0}
            skin_stats[tone]['total'] += count
            if decision == 1:
                skin_stats[tone]['hired'] += count
        
        for tone in skin_stats:
            total = skin_stats[tone]['total']
            hired = skin_stats[tone]['hired']
            skin_stats[tone]['rate'] = round(hired / total * 100, 1) if total > 0 else 0
        
        stats = {'by_skin_tone': skin_stats}
        
        c.execute("SELECT COUNT(*), SUM(decision) FROM audit_log")
        total, hired = c.fetchone()
        stats['total_candidates'] = total
        stats['total_hired'] = hired
        stats['overall_rate'] = round(hired / total * 100, 1) if total > 0 else 0
        
        conn.close()
        return stats


class BiasGuardDebiasser:
    """Applies bias mitigation."""
    
    def __init__(self):
        self.name = "BiasGuard AI (Debiased)"
    
    def recalculate_scores(self, candidate: Dict) -> Dict:
        base_score = (
            candidate['experience'] * 5 +
            candidate['skills'] * 0.5 +
            candidate['gpa'] * 10
        )
        
        edu_bonus = {'PhD': 20, 'Master': 15, 'Bachelor': 10, 'High School': 0}
        base_score += edu_bonus.get(candidate['education'], 0)
        
        passed = base_score >= 55
        
        return {
            'candidate_id': candidate['id'],
            'name': candidate['name'],
            'skin_tone': candidate['skin_tone'],
            'gender': candidate['gender'],
            'base_score': round(base_score, 1),
            'skin_bias': 0,
            'total_score': round(base_score, 1),
            'passed': passed,
            'decision': 1 if passed else 0,
            'note': 'De-biased by BiasGuard'
        }


def run_demo():
    print("=" * 70)
    print("BIASGUARD COMPLETE PIPELINE DEMO")
    print("=" * 70)
    
    resumes = ResumeDatabase()
    candidates = resumes.get_all()
    
    print(f"\n[Step 1] Loaded {len(candidates)} candidate resumes")
    
    print("\n" + "=" * 70)
    print("[Step 2] RUNNING BIASED RESUME SCREENING")
    print("=" * 70)
    
    screener = BiasedResumeScreener()
    auditor = BiasAuditor()
    
    biased_results = []
    for candidate in candidates:
        result = screener.score_candidate(candidate)
        biased_results.append(result)
        auditor.audit(job_id=1, candidate=candidate, result=result)
    
    print("\n--- BIASED SCREENING RESULTS ---")
    print(f"{'Name':<20} {'Skin Tone':<12} {'Base':<8} {'Bias':<8} {'Total':<8} {'Decision'}")
    print("-" * 70)
    for r in sorted(biased_results, key=lambda x: x['total_score'], reverse=True):
        decision = "HIRED" if r['passed'] else "REJECTED"
        print(f"{r['name']:<20} {r['skin_tone']:<12} {r['base_score']:<8} {r['skin_bias']:+<8} {r['total_score']:<8} {decision}")
    
    print("\n" + "=" * 70)
    print("[Step 3] BIAS ANALYSIS - BEFORE BIASGUARD")
    print("=" * 70)
    
    stats = auditor.get_statistics()
    
    print("\nHiring Rates by Skin Tone:")
    print("-" * 40)
    for tone, data in stats['by_skin_tone'].items():
        bar = "#" * int(data['rate'] / 5)
        print(f"  {tone:<12}: {data['rate']:>5.1f}% {bar} ({data['hired']}/{data['total']})")
    
    print(f"\nOverall hiring rate: {stats['overall_rate']}%")
    
    rates = [d['rate'] for d in stats['by_skin_tone'].values()]
    min_rate, max_rate = min(rates), max(rates)
    disparate_impact = min_rate / max_rate if max_rate > 0 else 0
    
    print(f"\nDisparate Impact Ratio: {disparate_impact:.2f}")
    if disparate_impact < 0.8:
        print("WARNING: BIAS DETECTED - Disparate impact below 80% threshold!")
    
    print("\n" + "=" * 70)
    print("[Step 4] APPLYING BIASGUARD DE-BIASING")
    print("=" * 70)
    
    debiasser = BiasGuardDebiasser()
    debiased_results = []
    
    for candidate in candidates:
        result = debiasser.recalculate_scores(candidate)
        debiased_results.append(result)
    
    print("\n--- DE-BIASED SCREENING RESULTS ---")
    print(f"{'Name':<20} {'Skin Tone':<12} {'Base':<8} {'Bias':<8} {'Total':<8} {'Decision'}")
    print("-" * 70)
    for r in sorted(debiased_results, key=lambda x: x['total_score'], reverse=True):
        decision = "HIRED" if r['passed'] else "REJECTED"
        print(f"{r['name']:<20} {r['skin_tone']:<12} {r['base_score']:<8} {r['skin_bias']:+<8} {r['total_score']:<8} {decision}")
    
    print("\n" + "=" * 70)
    print("[Step 5] BIAS ANALYSIS - AFTER BIASGUARD")
    print("=" * 70)
    
    debiased_stats = {'by_skin_tone': {}}
    for r in debiased_results:
        tone = r['skin_tone']
        if tone not in debiased_stats['by_skin_tone']:
            debiased_stats['by_skin_tone'][tone] = {'total': 0, 'hired': 0}
        debiased_stats['by_skin_tone'][tone]['total'] += 1
        if r['passed']:
            debiased_stats['by_skin_tone'][tone]['hired'] += 1
    
    for tone in debiased_stats['by_skin_tone']:
        data = debiased_stats['by_skin_tone'][tone]
        data['rate'] = round(data['hired'] / data['total'] * 100, 1)
    
    print("\nHiring Rates by Skin Tone (After De-biasing):")
    print("-" * 40)
    for tone, data in debiased_stats['by_skin_tone'].items():
        bar = "#" * int(data['rate'] / 5)
        print(f"  {tone:<12}: {data['rate']:>5.1f}% {bar} ({data['hired']}/{data['total']})")
    
    debiased_total = sum(1 for r in debiased_results if r['passed'])
    debiased_rate = debiased_total / len(debiased_results) * 100
    print(f"\nOverall hiring rate: {debiased_rate:.1f}%")
    
    rates_after = [d['rate'] for d in debiased_stats['by_skin_tone'].values()]
    min_rate_after, max_rate_after = min(rates_after), max(rates_after)
    disparate_impact_after = min_rate_after / max_rate_after if max_rate_after > 0 else 0
    
    print(f"\nDisparate Impact Ratio: {disparate_impact_after:.2f}")
    if disparate_impact_after >= 0.8:
        print("FAIR: Disparate impact above 80% threshold!")
    
    print("\n" + "=" * 70)
    print("[Step 6] BEFORE vs AFTER COMPARISON REPORT")
    print("=" * 70)
    
    print(f"""
======================================================================
                    BIAS REDUCTION SUMMARY
======================================================================
  Metric                  |  Before BiasGuard |  After BiasGuard
  ------------------------|------------------|------------------
  Disparate Impact       |  {disparate_impact:.2f}             |  {disparate_impact_after:.2f}
  Hiring Rate (Light)    |  {stats['by_skin_tone'].get('Light', {'rate':0})['rate']:.1f}%             |  {debiased_stats['by_skin_tone'].get('Light', {'rate':0})['rate']:.1f}%
  Hiring Rate (Dark)     |  {stats['by_skin_tone'].get('Dark', {'rate':0})['rate']:.1f}%             |  {debiased_stats['by_skin_tone'].get('Dark', {'rate':0})['rate']:.1f}%
  Overall Hiring Rate    |  {stats['overall_rate']:.1f}%             |  {debiased_rate:.1f}%
======================================================================

CONCLUSION:
- BiasGuard reduced disparate impact from {disparate_impact:.2f} to {disparate_impact_after:.2f}
- {"Fair hiring achieved!" if disparate_impact_after >= 0.8 else "Further tuning needed"}
- Dark skin tone hiring rate improved from {stats['by_skin_tone'].get('Dark', {'rate':0})['rate']}% to {debiased_stats['by_skin_tone'].get('Dark', {'rate':0})['rate']}%
""")
    
    return {
        'before': stats,
        'after': debiased_stats,
        'biased_results': biased_results,
        'debiased_results': debiased_results
    }


if __name__ == "__main__":
    results = run_demo()
