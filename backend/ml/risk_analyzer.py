import json
import numpy as np
from sklearn.ensemble import IsolationForest


# Reference baseline matrix of normal GeM procurement bids:
# Columns: [price_to_estimate_ratio, warranty_years, delivery_days, local_content_percent]
BASELINE_NORMAL_BIDS = np.array([
    [0.92, 3.0, 30, 60.0],
    [0.95, 3.0, 28, 65.0],
    [0.88, 2.0, 21, 55.0],
    [0.98, 3.0, 30, 70.0],
    [0.90, 5.0, 45, 62.0],
    [0.94, 3.0, 25, 58.0],
    [0.91, 1.0, 15, 52.0],
    [0.97, 3.0, 30, 75.0],
    [0.89, 2.0, 35, 60.0],
    [0.96, 4.0, 30, 68.0],
    [0.93, 3.0, 20, 64.0],
    [0.99, 3.0, 40, 55.0],
    [0.87, 2.0, 25, 53.0],
    [0.95, 3.0, 30, 61.0],
    [0.92, 3.0, 28, 66.0],
    [1.01, 3.0, 30, 59.0],
    [0.86, 1.0, 18, 54.0],
    [0.94, 5.0, 35, 72.0],
    [0.90, 3.0, 30, 60.0],
    [0.93, 2.0, 22, 57.0],
], dtype=float)


def run_isolation_forest_risk_analysis(bid, tender, compliance_results):
    """
    Uses Scikit-learn IsolationForest to detect statistical anomalies in structured bid parameters
    and combines ML anomaly signals with rule-based compliance risk factors to produce an explainable
    Risk Level (LOW, MEDIUM, HIGH).

    IMPORTANT:
    Does NOT declare a company fraudulent or automatically reject a bidder.
    Generates 'Potential Anomaly -> Human Review Required'.
    """
    est_val = float(tender.estimated_value or 1000000.0)
    if est_val <= 0:
        est_val = 1000000.0

    quoted = float(bid.quoted_amount or est_val)
    price_ratio = round(quoted / est_val, 3)
    warranty = float(bid.warranty_years or 3.0)
    delivery = float(bid.delivery_days or 30.0)
    local_content = float(bid.local_content_declared or 50.0)

    # Fit IsolationForest on baseline + peer bids
    clf = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
    clf.fit(BASELINE_NORMAL_BIDS)

    sample = np.array([[price_ratio, warranty, delivery, local_content]], dtype=float)
    pred = int(clf.predict(sample)[0])  # 1 = normal, -1 = anomaly
    decision_val = float(clf.decision_function(sample)[0])

    # Convert decision_function to a 0-100 anomaly score (higher = more anomalous)
    anomaly_score = max(0.0, min(100.0, round((0.25 - decision_val) * 160.0, 2)))
    is_anomaly_flagged = (pred == -1)

    anomaly_notes = []
    if warranty > 10.0 or warranty <= 0.2:
        is_anomaly_flagged = True
        anomaly_score = max(anomaly_score, 82.5)
        anomaly_notes.append(
            f"Unusual warranty period detected ({warranty:g} years vs normal 1-5 years): Potential Anomaly -> Human Review Required."
        )
    if price_ratio < 0.45 or price_ratio > 1.55:
        is_anomaly_flagged = True
        anomaly_score = max(anomaly_score, 78.0)
        anomaly_notes.append(
            f"Unusual bid quote ratio ({price_ratio * 100:.1f}% of estimated tender value): Potential Anomaly -> Human Review Required."
        )
    if delivery > 180 or delivery < 2:
        is_anomaly_flagged = True
        anomaly_score = max(anomaly_score, 74.0)
        anomaly_notes.append(
            f"Unusual delivery schedule ({int(delivery)} days vs standard 15-45 days): Potential Anomaly -> Human Review Required."
        )
    if local_content > 100.0 or local_content < 0.0:
        is_anomaly_flagged = True
        anomaly_score = max(anomaly_score, 88.0)
        anomaly_notes.append(
            f"Invalid local content percentage ({local_content}%): Potential Anomaly -> Human Review Required."
        )

    if is_anomaly_flagged and not anomaly_notes:
        anomaly_notes.append(
            "Scikit-learn Isolation Forest identified multi-dimensional parameter deviation from peer distribution: Potential Anomaly -> Human Review Required."
        )

    # Collect explainable risk factors from compliance results
    risk_factors = []
    non_compliant_count = 0
    needs_review_count = 0

    for res in compliance_results:
        if res.status == "NON_COMPLIANT":
            non_compliant_count += 1
            risk_factors.append({
                "severity": "HIGH",
                "category": res.category,
                "factor": f"{res.check_name}: {res.reason}",
            })
        elif res.status == "NEEDS_REVIEW":
            needs_review_count += 1
            risk_factors.append({
                "severity": "MEDIUM",
                "category": res.category,
                "factor": f"{res.check_name}: {res.reason}",
            })

    for note in anomaly_notes:
        risk_factors.append({
            "severity": "MEDIUM",
            "category": "ML_ANOMALY_DETECTION",
            "factor": note,
        })

    # Compute transparent composite Risk Score (0 - 100) and Risk Level (LOW, MEDIUM, HIGH)
    risk_score = min(
        100.0,
        round((non_compliant_count * 22.0) + (needs_review_count * 10.0) + (anomaly_score * 0.35), 1),
    )

    if non_compliant_count >= 2 or risk_score >= 55.0:
        risk_level = "HIGH"
    elif non_compliant_count == 1 or needs_review_count >= 1 or is_anomaly_flagged or risk_score >= 25.0:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    if not risk_factors:
        risk_factors.append({
            "severity": "LOW",
            "category": "OVERALL",
            "factor": "All mandatory documents, technical specifications, and statutory checks passed without anomalies.",
        })

    ml_explanation = (
        " ".join(anomaly_notes)
        if anomaly_notes
        else (
            f"Scikit-learn Isolation Forest evaluated [Price/Estimate={price_ratio:.2f}, "
            f"Warranty={warranty:g} yrs, Delivery={int(delivery)} days, LocalContent={local_content:.1f}%] "
            "as within normal procurement bounds. Final decision rests with the authorized Procurement Officer."
        )
    )

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "anomaly_score": anomaly_score,
        "is_anomaly_flagged": is_anomaly_flagged,
        "risk_factors_json": json.dumps(risk_factors),
        "ml_explanation": ml_explanation,
        "requires_human_review": True,
    }
