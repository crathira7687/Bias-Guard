"""
BiasGuard Complete Pipeline Demo - SIMPLE VERSION (No Database)
"""
import random
from typing import Dict, List

# Part 1: Resume Database
def generate_candidates():
    skin_tones = ['Very Light', 'Light', 'Medium', 'Dark', 'Very Dark']
    names = ["John", "Michael", "David", "Mary", "Jennifer", "Patricia", "James", "Linda"]
    qualifications = [
        {'exp': 5, 'skills': 90, 'edu': 'PhD', 'gpa': 3.9},
        {'exp': 7, 'skills': 85, 'edu': 'Master', 'gpa': 3.7},
        {'exp': 3, 'skills': 80, 'edu': 'Bachelor', 'gpa': 3.5},
        {'exp': 2, 'skills': 75, 'edu': 'Bachelor', 'gpa': 3.3},
        {'exp': 1, 'skills': 70, 'edu': 'Bachelor', 'gpa': 3.0},
        {'exp': 4, 'skills': 65, 'edu': 'Master', 'gpa': 3.2},
    ]
    
    candidates = []
    for i in range(30):
        candidates.append({
            'id': i + 1,
            'name': f"{names[i % len(names)]} {chr(65+i)}",
            'skin_tone': random.choice(skin_tones),
            'experience': qualifications[i % 6]['exp'],
            'skills': qualifications[i % 6]['skills'],
            'education': qualifications[i % 6]['edu'],
            'gpa': qualifications[i % 6]['gpa'],
        })
    return candidates

# Part 2: Biased Screener
def score_biased(candidate):
    base = candidate['experience'] * 5 + candidate['skills'] * 0.5 + candidate['gpa'] * 10
    base += {'PhD': 20, 'Master': 15, 'Bachelor': 10}.get(candidate['education'], 0)
    
    bias = {'Very Light': +25, 'Light': +15, 'Medium': 0, 'Dark': -15, 'Very Dark': -30}.get(candidate['skin_tone'], 0)
    
    total = base + bias
    return {'id': candidate['id'], 'name': candidate['name'], 'skin_tone': candidate['skin_tone'],
            'base': round(base, 1), 'bias': bias, 'total': round(total, 1), 'hired': total >= 60}

# Part 3: De-biased Screener
def score_debiased(candidate):
    base = candidate['experience'] * 5 + candidate['skills'] * 0.5 + candidate['gpa'] * 10
    base += {'PhD': 20, 'Master': 15, 'Bachelor': 10}.get(candidate['education'], 0)
    
    return {'id': candidate['id'], 'name': candidate['name'], 'skin_tone': candidate['skin_tone'],
            'base': round(base, 1), 'bias': 0, 'total': round(base, 1), 'hired': base >= 55}

# Part 4: Calculate Stats
def calc_stats(results):
    stats = {}
    for r in results:
        tone = r['skin_tone']
        if tone not in stats:
            stats[tone] = {'total': 0, 'hired': 0}
        stats[tone]['total'] += 1
        if r['hired']:
            stats[tone]['hired'] += 1
    
    for tone in stats:
        stats[tone]['rate'] = round(stats[tone]['hired'] / stats[tone]['total'] * 100, 1)
    
    total = sum(s['total'] for s in stats.values())
    hired = sum(s['hired'] for s in stats.values())
    stats['_overall'] = {'rate': round(hired / total * 100, 1) if total > 0 else 0}
    
    return stats

# Run Demo
print("=" * 70)
print("BIASGUARD COMPLETE PIPELINE DEMO")
print("=" * 70)

candidates = generate_candidates()
print(f"\n[Step 1] Loaded {len(candidates)} candidate resumes with photos")

print("\n" + "=" * 70)
print("[Step 2] RUNNING BIASED RESUME SCREENING")
print("=" * 70)

biased_results = [score_biased(c) for c in candidates]
print("\n--- BIASED RESULTS ---")
print(f"{'Name':<18} {'Skin Tone':<12} {'Base':<7} {'Bias':<6} {'Total':<7} {'Decision'}")
print("-" * 65)
for r in sorted(biased_results, key=lambda x: x['total'], reverse=True):
    d = "HIRED" if r['hired'] else "REJECTED"
    print(f"{r['name']:<18} {r['skin_tone']:<12} {r['base']:<7} {r['bias']:+<6} {r['total']:<7} {d}")

print("\n" + "=" * 70)
print("[Step 3] BIAS ANALYSIS - BEFORE BIASGUARD")
print("=" * 70)

stats_before = calc_stats(biased_results)
print("\nHiring Rates by Skin Tone (BEFORE):")
print("-" * 40)
for tone in ['Very Light', 'Light', 'Medium', 'Dark', 'Very Dark']:
    if tone in stats_before:
        d = stats_before[tone]
        bar = "#" * int(d['rate'] / 5)
        print(f"  {tone:<12}: {d['rate']:>5.1f}% {bar} ({d['hired']}/{d['total']})")

rates = [s['rate'] for s in stats_before.values() if '_overall' not in s]
di_before = min(rates) / max(rates) if rates else 1
print(f"\nDisparate Impact: {di_before:.2f}")
if di_before < 0.8:
    print("WARNING: BIAS DETECTED - Disparate impact below 80%!")

print("\n" + "=" * 70)
print("[Step 4] APPLYING BIASGUARD DE-BIASING")
print("=" * 70)

debiased_results = [score_debiased(c) for c in candidates]
print("\n--- DE-BIASED RESULTS ---")
print(f"{'Name':<18} {'Skin Tone':<12} {'Base':<7} {'Bias':<6} {'Total':<7} {'Decision'}")
print("-" * 65)
for r in sorted(debiased_results, key=lambda x: x['total'], reverse=True):
    d = "HIRED" if r['hired'] else "REJECTED"
    print(f"{r['name']:<18} {r['skin_tone']:<12} {r['base']:<7} {r['bias']:+<6} {r['total']:<7} {d}")

print("\n" + "=" * 70)
print("[Step 5] BIAS ANALYSIS - AFTER BIASGUARD")
print("=" * 70)

stats_after = calc_stats(debiased_results)
print("\nHiring Rates by Skin Tone (AFTER):")
print("-" * 40)
for tone in ['Very Light', 'Light', 'Medium', 'Dark', 'Very Dark']:
    if tone in stats_after:
        d = stats_after[tone]
        bar = "#" * int(d['rate'] / 5)
        print(f"  {tone:<12}: {d['rate']:>5.1f}% {bar} ({d['hired']}/{d['total']})")

rates_after = [s['rate'] for s in stats_after.values() if '_overall' not in s]
di_after = min(rates_after) / max(rates_after) if rates_after else 1
print(f"\nDisparate Impact: {di_after:.2f}")
if di_after >= 0.8:
    print("FAIR: Disparate impact above 80%!")

print("\n" + "=" * 70)
print("[Step 6] BEFORE vs AFTER COMPARISON")
print("=" * 70)
print(f"""
======================================================================
                    BIAS REDUCTION SUMMARY
======================================================================
  Metric                  |  Before BiasGuard |  After BiasGuard
  ------------------------|------------------|------------------
  Disparate Impact       |  {di_before:.2f}             |  {di_after:.2f}
  Overall Hiring Rate    |  {stats_before['_overall']['rate']:.1f}%             |  {stats_after['_overall']['rate']:.1f}%
======================================================================

CONCLUSION:
- BiasGuard reduced disparate impact from {di_before:.2f} to {di_after:.2f}
- {"Fair hiring achieved!" if di_after >= 0.8 else "Further tuning needed"}
""")
