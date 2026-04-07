"""
BiasGuard Complete Pipeline Demo - FIXED VERSION
Shows real bias discrimination and correction
"""
import random
from typing import Dict, List

# Part 1: Resume Database with MIXED qualifications
def generate_candidates():
    skin_tones = ['Very Light', 'Light', 'Medium', 'Dark', 'Very Dark']
    names = ["John", "Michael", "David", "Mary", "Jennifer", "Patricia", "James", "Linda", "Robert", "Barbara"]
    
    # MIXED qualifications - some good, some mediocre
    qualifications = [
        {'exp': 8, 'skills': 95, 'edu': 'PhD', 'gpa': 3.9},   # Very strong
        {'exp': 6, 'skills': 88, 'edu': 'Master', 'gpa': 3.8}, # Strong
        {'exp': 5, 'skills': 82, 'edu': 'Master', 'gpa': 3.6}, # Good
        {'exp': 4, 'skills': 75, 'edu': 'Bachelor', 'gpa': 3.4}, # Average
        {'exp': 3, 'skills': 70, 'edu': 'Bachelor', 'gpa': 3.2}, # Below avg
        {'exp': 2, 'skills': 65, 'edu': 'Bachelor', 'gpa': 3.0}, # Weak
        {'exp': 1, 'skills': 60, 'edu': 'Bachelor', 'gpa': 2.8}, # Very weak
        {'exp': 0, 'skills': 55, 'edu': 'High School', 'gpa': 2.5}, # Poor
    ]
    
    candidates = []
    for i in range(40):
        # Distribute skin tones randomly
        # But keep qualifications random too
        candidates.append({
            'id': i + 1,
            'name': f"{names[i % len(names)]} {chr(65 + i//10)}",
            'skin_tone': random.choice(skin_tones),
            'experience': qualifications[i % 8]['exp'],
            'skills': qualifications[i % 8]['skills'],
            'education': qualifications[i % 8]['edu'],
            'gpa': qualifications[i % 8]['gpa'],
        })
    
    # Shuffle to mix skin tones with qualifications
    random.shuffle(candidates)
    return candidates

# Part 2: Biased Screener (favors light skin)
def score_biased(candidate):
    base = candidate['experience'] * 5 + candidate['skills'] * 0.5 + candidate['gpa'] * 10
    base += {'PhD': 20, 'Master': 15, 'Bachelor': 10, 'High School': 0}.get(candidate['education'], 0)
    
    # THE DISCRIMINATORY BIAS
    bias = {
        'Very Light': +30,  # Huge bonus
        'Light': +20,       # Significant bonus
        'Medium': 0,         # Neutral
        'Dark': -20,        # Significant penalty
        'Very Dark': -35    # Severe penalty
    }.get(candidate['skin_tone'], 0)
    
    total = base + bias
    # Threshold of 60
    return {
        'id': candidate['id'], 
        'name': candidate['name'], 
        'skin_tone': candidate['skin_tone'],
        'experience': candidate['experience'],
        'base': round(base, 1), 
        'bias': bias, 
        'total': round(total, 1), 
        'hired': total >= 60
    }

# Part 3: De-biased Screener (fair)
def score_debiased(candidate):
    base = candidate['experience'] * 5 + candidate['skills'] * 0.5 + candidate['gpa'] * 10
    base += {'PhD': 20, 'Master': 15, 'Bachelor': 10, 'High School': 0}.get(candidate['education'], 0)
    
    # NO BIAS - pure qualifications
    # Slightly lower threshold to compensate for removing bias
    total = base
    return {
        'id': candidate['id'], 
        'name': candidate['name'], 
        'skin_tone': candidate['skin_tone'],
        'experience': candidate['experience'],
        'base': round(base, 1), 
        'bias': 0, 
        'total': round(total, 1), 
        'hired': total >= 55  # Lower threshold
    }

# Part 4: Calculate Statistics
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
        t = stats[tone]['total']
        h = stats[tone]['hired']
        stats[tone]['rate'] = round(h / t * 100, 1) if t > 0 else 0
    
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
print("         Each resume has qualifications + photo (skin tone)")

print("\n" + "=" * 70)
print("[Step 2] RUNNING BIASED RESUME SCREENING (Current Industry System)")
print("=" * 70)
print("\n--- BIASED RESULTS (sorted by total score) ---")
biased_results = [score_biased(c) for c in candidates]

print(f"{'Name':<18} {'Skin Tone':<12} {'Exp':<4} {'Base':<7} {'Bias':<6} {'Total':<7} {'Decision'}")
print("-" * 70)
for r in sorted(biased_results, key=lambda x: x['total'], reverse=True)[:15]:
    d = "HIRED" if r['hired'] else "REJECTED"
    bias_str = f"{r['bias']:+.0f}" if r['bias'] >= 0 else f"{r['bias']:.0f}"
    print(f"{r['name']:<18} {r['skin_tone']:<12} {r['experience']:<4} {r['base']:<7} {bias_str:<6} {r['total']:<7} {d}")

# Count rejections
rejected = [r for r in biased_results if not r['hired']]
print(f"\n... and {len(rejected)} more results")

print("\n" + "=" * 70)
print("[Step 3] BIAS ANALYSIS - BEFORE BIASGUARD")
print("=" * 70)

stats_before = calc_stats(biased_results)
print("\nHiring Rates by Skin Tone (BEFORE BiasGuard):")
print("-" * 50)
for tone in ['Very Light', 'Light', 'Medium', 'Dark', 'Very Dark']:
    if tone in stats_before:
        d = stats_before[tone]
        bar = "#" * int(d['rate'] / 5)
        print(f"  {tone:<12}: {d['rate']:>5.1f}% {bar:20} ({d['hired']}/{d['total']})")

rates = [s['rate'] for s in stats_before.values() if '_overall' not in s]
di_before = min(rates) / max(rates) if rates else 1
print(f"\nDisparate Impact Ratio: {di_before:.2f}")
if di_before < 0.8:
    print("WARNING: BIAS DETECTED - Disparate impact below 80% threshold!")
    print("         This indicates illegal discrimination based on skin tone.")

print("\n" + "=" * 70)
print("[Step 4] APPLYING BIASGUARD DE-BIASING")
print("=" * 70)
print("\nBiasGuard removes skin tone from scoring and recalculates...")

debiased_results = [score_debiased(c) for c in candidates]

print("\n--- DE-BIASED RESULTS (sorted by total score) ---")
print(f"{'Name':<18} {'Skin Tone':<12} {'Exp':<4} {'Base':<7} {'Bias':<6} {'Total':<7} {'Decision'}")
print("-" * 70)
for r in sorted(debiased_results, key=lambda x: x['total'], reverse=True)[:15]:
    d = "HIRED" if r['hired'] else "REJECTED"
    print(f"{r['name']:<18} {r['skin_tone']:<12} {r['experience']:<4} {r['base']:<7} {r['bias']:<6} {r['total']:<7} {d}")

print("\n" + "=" * 70)
print("[Step 5] BIAS ANALYSIS - AFTER BIASGUARD")
print("=" * 70)

stats_after = calc_stats(debiased_results)
print("\nHiring Rates by Skin Tone (AFTER BiasGuard):")
print("-" * 50)
for tone in ['Very Light', 'Light', 'Medium', 'Dark', 'Very Dark']:
    if tone in stats_after:
        d = stats_after[tone]
        bar = "#" * int(d['rate'] / 5)
        print(f"  {tone:<12}: {d['rate']:>5.1f}% {bar:20} ({d['hired']}/{d['total']})")

rates_after = [s['rate'] for s in stats_after.values() if '_overall' not in s]
di_after = min(rates_after) / max(rates_after) if rates_after else 1
print(f"\nDisparate Impact Ratio: {di_after:.2f}")
if di_after >= 0.8:
    print("PASS: Disparate impact is now above 80% - FAIR hiring!")

print("\n" + "=" * 70)
print("[Step 6] BEFORE vs AFTER COMPARISON REPORT")
print("=" * 70)

# Get specific rates for comparison
vl_before = stats_before.get('Very Light', {}).get('rate', 0)
vd_before = stats_before.get('Very Dark', {}).get('rate', 0)
vl_after = stats_after.get('Very Light', {}).get('rate', 0)
vd_after = stats_after.get('Very Dark', {}).get('rate', 0)

print(f"""
======================================================================
                    BIAS REDUCTION SUMMARY REPORT
======================================================================
 Metric                     |  BEFORE BiasGuard  |  AFTER BiasGuard
---------------------------|--------------------|--------------------
 Disparate Impact          |  {di_before:.2f}               |  {di_after:.2f}
 Very Light Hiring Rate    |  {vl_before:.1f}%              |  {vl_after:.1f}%
 Very Dark Hiring Rate     |  {vd_before:.1f}%              |  {vd_after:.1f}%
 Overall Hiring Rate       |  {stats_before['_overall']['rate']:.1f}%              |  {stats_after['_overall']['rate']:.1f}%
======================================================================

CONCLUSION:
- BiasGuard reduced disparate impact from {di_before:.2f} to {di_after:.2f}
- {"Fair hiring achieved - no discrimination!" if di_after >= 0.8 else "Some bias still remains"}
- Very Dark candidates: {vd_before:.1f}% -> {vd_after:.1f}% hiring rate
""")
