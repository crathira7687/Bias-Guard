"""
BiasGuard Bias Auditor
Integrates recruiting decisions with the bias detection and monitoring system.

How it works:
1. Every hiring decision in the recruiting system triggers the audit hook
2. The audit data is collected and stored
3. The BiasAnalyzer evaluates decisions for potential bias
4. Dashboard shows fairness metrics by gender/race/age
"""
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import os

class BiasAuditor:
    """
    BiasAuditor monitors hiring decisions for potential bias.
    It integrates with the recruiting system via the call_bias_guard_audit() hook.
    """
    
    def __init__(self, db_path: str = "bias_audit.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize audit database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                job_id INTEGER NOT NULL,
                candidate_id INTEGER NOT NULL,
                gender TEXT,
                race TEXT,
                age INTEGER,
                decision INTEGER NOT NULL,
                model_score REAL NOT NULL,
                flagged BOOLEAN DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()
    
    def audit(self, job_id: int, candidate_id: int, gender: str = None, 
              race: str = None, age: int = None, 
              decision: int = None, model_score: float = None) -> Dict:
        """
        Main audit function - called via the audit hook.
        Records the hiring decision and checks for bias patterns.
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Store in audit log
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_log (timestamp, job_id, candidate_id, gender, race, age, decision, model_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, job_id, candidate_id, gender, race, age, decision, model_score))
        conn.commit()
        
        # Check for bias patterns
        bias_report = self._check_bias_patterns(cursor, job_id)
        
        conn.close()
        
        return {
            'timestamp': timestamp,
            'job_id': job_id,
            'candidate_id': candidate_id,
            'bias_analysis': bias_report,
            'status': 'audited'
        }
    
    def _check_bias_patterns(self, cursor, job_id: int) -> Dict:
        """Analyze recent decisions for bias patterns."""
        
        # Get all decisions for this job
        cursor.execute("""
            SELECT gender, decision, COUNT(*) as count
            FROM audit_log
            WHERE job_id = ?
            GROUP BY gender, decision
        """, (job_id,))
        
        results = cursor.fetchall()
        
        gender_stats = {}
        for gender, decision, count in results:
            if gender not in gender_stats:
                gender_stats[gender] = {'total': 0, 'hired': 0}
            gender_stats[gender]['total'] += count
            if decision == 1:
                gender_stats[gender]['hired'] += count
        
        # Calculate hiring rates by gender
        bias_warnings = []
        for gender, stats in gender_stats.items():
            if stats['total'] > 0:
                rate = stats['hired'] / stats['total']
                gender_stats[gender]['rate'] = rate
                
                # Check for disparate impact (低于80%规则)
                rates = [s['rate'] for s in gender_stats.values() if 'rate' in s]
                if len(rates) >= 2:
                    min_rate = min(rates)
                    max_rate = max(rates)
                    if max_rate > 0 and min_rate / max_rate < 0.8:
                        bias_warnings.append(f"Potential disparate impact detected: {gender}")
        
        return {
            'gender_stats': gender_stats,
            'bias_warnings': bias_warnings,
            'fairness_score': self._calculate_fairness_score(gender_stats)
        }
    
    def _calculate_fairness_score(self, gender_stats: Dict) -> float:
        """Calculate overall fairness score (0-100)."""
        if not gender_stats:
            return 100.0
        
        rates = [stats.get('rate', 0) for stats in gender_stats.values() if stats.get('total', 0) > 0]
        
        if len(rates) < 2:
            return 100.0
        
        # Calculate variance - lower is better
        avg_rate = sum(rates) / len(rates)
        variance = sum((r - avg_rate) ** 2 for r in rates) / len(rates)
        
        # Convert to score (0-100)
        # Max variance we tolerate is 0.1 (very unfair)
        score = max(0, 100 - (variance * 1000))
        return round(score, 1)
    
    def get_job_audit_summary(self, job_id: int) -> Dict:
        """Get audit summary for a specific job."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        bias_report = self._check_bias_patterns(cursor, job_id)
        
        cursor.execute("SELECT COUNT(*) FROM audit_log WHERE job_id = ?", (job_id,))
        total_decisions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'job_id': job_id,
            'total_decisions': total_decisions,
            **bias_report
        }
    
    def get_overall_audit_summary(self) -> Dict:
        """Get overall audit summary across all jobs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM audit_log")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT gender, COUNT(*) FROM audit_log GROUP BY gender")
        by_gender = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'total_decisions': total,
            'by_gender': by_gender
        }


# Global auditor instance
auditor = BiasAuditor()


def call_bias_guard_audit(job_id: int, candidate_id: int, gender: str, 
                          decision: int, model_score: float, race: str = None, 
                          age: int = None) -> Dict:
    """
    Main audit hook - integrates recruiting with bias monitoring.
    
    How it works:
    1. Called after every hiring decision in the recruiting system
    2. Records decision to audit database
    3. Checks for bias patterns
    4. Returns audit result
    
    Args:
        job_id: The job position
        candidate_id: The candidate
        gender: Candidate's gender
        decision: 1 (hired) or 0 (not hired)
        model_score: The scoring model's score
        race: Optional race information
        age: Optional age
    
    Returns:
        Dict with audit result and bias analysis
    """
    print(f"[AUDIT] Recording decision: job={job_id}, candidate={candidate_id}, gender={gender}, decision={decision}, score={model_score}")
    
    result = auditor.audit(
        job_id=job_id,
        candidate_id=candidate_id,
        gender=gender,
        race=race,
        age=age,
        decision=decision,
        model_score=model_score
    )
    
    # Print bias warnings if any
    if result['bias_analysis']['bias_warnings']:
        print(f"[AUDIT WARNING] {result['bias_analysis']['bias_warnings']}")
    
    print(f"[AUDIT] Fairness Score: {result['bias_analysis']['fairness_score']}/100")
    
    return result


if __name__ == "__main__":
    # Test the auditor
    print("=" * 50)
    print("Testing BiasAuditor")
    print("=" * 50)
    
    # Simulate some hiring decisions
    test_data = [
        (1, 1, "Male", 1, 75.0),
        (1, 2, "Female", 1, 72.0),
        (1, 3, "Male", 0, 45.0),
        (1, 4, "Female", 0, 48.0),
        (1, 5, "Male", 1, 80.0),
        (1, 6, "Female", 0, 35.0),
    ]
    
    for job_id, candidate_id, gender, decision, score in test_data:
        result = call_bias_guard_audit(job_id, candidate_id, gender, decision, score)
        print(f"Candidate {candidate_id}: {result['bias_analysis']['fairness_score']}")
    
    # Get summary
    summary = auditor.get_job_audit_summary(1)
    print(f"\nJob 1 Audit Summary:")
    print(f"  Total decisions: {summary['total_decisions']}")
    print(f"  Fairness score: {summary['fairness_score']}")
    print(f"  Gender stats: {summary['gender_stats']}")
    print(f"  Warnings: {summary['bias_warnings']}")
