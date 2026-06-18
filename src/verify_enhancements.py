import json
import os
import sys

def main():
    print("==================================================")
    print("      VERIFYING CYBER DNA ENHANCEMENTS            ")
    print("==================================================")
    
    json_path = 'web_app/src/cyber_dna_data.json'
    
    if not os.path.exists(json_path):
        print(f"Error: JSON data file not found at {json_path}. Run export_to_web.py first.")
        sys.exit(1)
        
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print("\n--- Check 1: Users and Department Ingest ---")
    users = data['users']
    depts = data['user_departments']
    print(f"Ingested Users: {users}")
    print(f"Department Assignments: {depts}")
    assert 'Eve' in users, "Eve must be in the ingested users."
    assert depts['Eve'] == 'HR', "Eve's original department must be HR."
    print("  => User & LDAP Ingest: SUCCESS")
    
    print("\n--- Check 2: Z-Score Departmental Suppression (Experiment 1) ---")
    alerts = data['alerts']
    
    # Find alerts related to Eve
    eve_alerts = [a for a in alerts if "Eve" in a['desc']]
    print(f"Eve's Alerts: {eve_alerts}")
    
    # Assert there is a suppressed role transition alert
    blue_transition_alerts = [a for a in eve_alerts if a['type'] == 'blue']
    red_drift_alerts = [a for a in eve_alerts if a['type'] == 'red']
    
    assert len(blue_transition_alerts) > 0, "Eve must have a suppressed Legitimate Role Transition alert."
    assert len(red_drift_alerts) == 0, "Eve's red drift alert must be suppressed by the Departmental filter."
    print("  => Departmental Filter Suppression: SUCCESS")
    
    print("\n--- Check 3: Anthropological Scores ---")
    anthro = data['anthropology']
    print(f"Alice Anthropology: {anthro['Alice']}")
    print(f"Eve Anthropology: {anthro['Eve']}")
    
    assert anthro['Alice']['IDP'] > 0.99, "Alice's Identity Persistence must be near 1.0 (highly stable)."
    assert anthro['Eve']['IDP'] < 0.85, "Eve's Identity Persistence must be lower due to departmental drift."
    assert anthro['Eve']['BC'] < 0.75, "Eve's Behavioral Continuity must be lower due to sudden shift in Week 3."
    print("  => Anthropological Scoring Formulas: SUCCESS")
    
    print("\n--- Check 4: Unsupervised Baseline Metrics ---")
    ml = data['ml_metrics']
    print("Baseline Metrics Summary:")
    for model, metrics in ml.items():
        print(f"  {model}: F1-Score = {metrics['f1']:.4f}")
        
    assert 'Isolation Forest' in ml, "Isolation Forest metrics must be exported."
    assert 'One-Class SVM' in ml, "One-Class SVM metrics must be exported."
    assert ml['Isolation Forest']['f1'] > 0.0, "Isolation Forest must have a valid F1 score."
    assert ml['One-Class SVM']['f1'] > 0.0, "One-Class SVM must have a valid F1 score."
    print("  => Unsupervised ML Baseline Evaluation: SUCCESS")
    
    print("\nStatus: All Cyber DNA Enhancements verified successfully!")
    print("==================================================")

if __name__ == '__main__':
    main()
