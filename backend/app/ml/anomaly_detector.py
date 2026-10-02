import numpy as np
from sklearn.ensemble import IsolationForest
from typing import Dict, Any, List

class VendorAnomalyDetector:
    """
    Enterprise ML Anomaly Detector using Scikit-learn's Isolation Forest.
    Analyzes multivariate operational vectors (age, turnover/headcount ratio,
    mismatch discordance, document density) against calibrated compliance distributions.
    
    Adheres strictly to procurement ethics:
    Never outputs defamatory claims (no 'fraud'). Uses explainable status:
    'Normal benchmark profile' or 'Unusual pattern detected — manual review recommended'.
    """

    def __init__(self):
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.15,
            random_state=42
        )
        self._fit_baseline_model()

    def _generate_synthetic_benchmark_profiles(self) -> np.ndarray:
        """
        Creates synthetic benchmark dataset of typical procurement vendors
        (healthy profiles with reasonable turnover, age, and high match scores)
        plus a few outlier samples to train the Isolation Forest boundary.
        """
        np.random.seed(42)
        n_samples = 300

        # Normal business distributions
        # Feature 0: Company age (years): 1 to 25
        age = np.random.uniform(2, 20, size=n_samples)
        # Feature 1: Employee count: 5 to 500
        employees = np.random.uniform(10, 300, size=n_samples)
        # Feature 2: Turnover (Cr): correlated with age & employees
        turnover = np.clip(employees * np.random.uniform(0.05, 0.3, size=n_samples) + age * 0.5, 0.5, 100)
        # Feature 3: Document count: 2 to 6
        docs = np.random.randint(2, 6, size=n_samples)
        # Feature 4: Name mismatch (0 to 15)
        name_mismatch = np.random.exponential(scale=3, size=n_samples)
        # Feature 5: Address mismatch (0 to 20)
        addr_mismatch = np.random.exponential(scale=5, size=n_samples)
        # Feature 6: Failed verification items (0 to 1)
        mismatch_count = np.random.binomial(n=1, p=0.05, size=n_samples)

        X_normal = np.column_stack([age, employees, turnover, docs, name_mismatch, addr_mismatch, mismatch_count])

        # A few anomalous profiles (e.g. 0.5 yr old with 100 Cr turnover and 2 employees, high mismatches)
        n_outliers = 30
        out_age = np.random.uniform(0.1, 1.0, size=n_outliers)
        out_employees = np.random.uniform(1, 3, size=n_outliers)
        out_turnover = np.random.uniform(40, 200, size=n_outliers)
        out_docs = np.random.randint(1, 2, size=n_outliers)
        out_name_mismatch = np.random.uniform(30, 80, size=n_outliers)
        out_addr_mismatch = np.random.uniform(40, 90, size=n_outliers)
        out_mismatch_count = np.random.randint(2, 5, size=n_outliers)

        X_outliers = np.column_stack([out_age, out_employees, out_turnover, out_docs, out_name_mismatch, out_addr_mismatch, out_mismatch_count])

        return np.vstack([X_normal, X_outliers])

    def _fit_baseline_model(self):
        X_train = self._generate_synthetic_benchmark_profiles()
        self.model.fit(X_train)

    def extract_features(
        self,
        vendor_data: Dict[str, Any],
        doc_count: int,
        matrix: List[Dict[str, Any]]
    ) -> np.ndarray:
        current_year = 2026
        est_year = vendor_data.get("established_year") or 2020
        age = max(0.5, float(current_year - est_year))
        employees = max(1.0, float(vendor_data.get("employee_count") or 10))
        turnover = max(0.1, float(vendor_data.get("turnover_cr") or 1.0))
        docs = max(1.0, float(doc_count))

        matrix_map = {item["field_name"]: item for item in matrix}
        name_sim = matrix_map.get("Company Name", {}).get("similarity_score", 100.0)
        addr_sim = matrix_map.get("Address", {}).get("similarity_score", 100.0)

        name_mismatch = max(0.0, 100.0 - name_sim)
        addr_mismatch = max(0.0, 100.0 - addr_sim)

        mismatches = sum(1 for item in matrix if item.get("match_type") == "MISMATCH")

        return np.array([[age, employees, turnover, docs, name_mismatch, addr_mismatch, float(mismatches)]])

    def evaluate_vendor(
        self,
        vendor_data: Dict[str, Any],
        doc_count: int,
        matrix: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates an explainable anomaly score [0.00, 1.00] and contextual guidance.
        """
        features = self.extract_features(vendor_data, doc_count, matrix)
        raw_score = self.model.decision_function(features)[0]  # negative for anomalies, positive for normal
        
        # Invert and scale decision score to [0.00, 1.00]
        # raw_score typically ranges from -0.3 to +0.25
        normalized_anomaly = float(1.0 / (1.0 + np.exp(raw_score * 8.0)))
        normalized_anomaly = round(max(0.05, min(0.95, normalized_anomaly)), 2)

        # Contextual explanation
        explanations = []
        age = features[0][0]
        employees = features[0][1]
        turnover = features[0][2]
        mismatches = int(features[0][6])

        if normalized_anomaly >= 0.65:
            status = "HIGH ANOMALY"
            explanations.append("Statistical deviation: operational metrics differ significantly from standard vendor cohorts.")
            if age < 2.0 and turnover > 15.0:
                explanations.append(f"High claimed turnover (INR {turnover:.1f} Cr) relative to corporate age ({age:.1f} yrs).")
            if employees < 5 and turnover > 20.0:
                explanations.append("Disproportionate revenue-to-headcount ratio identified.")
            if mismatches >= 2:
                explanations.append(f"Multiple document-to-registry discordances ({mismatches} mismatches) detected.")
            summary_statement = "Unusual operational and discrepancy pattern detected — manual review recommended."
        elif normalized_anomaly >= 0.35:
            status = "MEDIUM ANOMALY"
            explanations.append("Minor statistical variance against cohort medians.")
            summary_statement = "Moderate anomaly indicators noted — secondary document cross-check advised."
        else:
            status = "LOW ANOMALY"
            explanations.append("Operational indicators and verification metrics closely conform to standard enterprise distributions.")
            summary_statement = "Normal operational profile consistent with peer benchmarks."

        return {
            "anomaly_score": normalized_anomaly,
            "anomaly_status": status,
            "findings": explanations,
            "summary_statement": summary_statement
        }

anomaly_detector = VendorAnomalyDetector()
