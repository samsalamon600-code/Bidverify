export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  company_name?: string;
  vendor_id?: number;
}

export interface DocumentItem {
  id: number;
  vendor_id: number;
  doc_type: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  status: string;
  ocr_confidence: number;
  uploaded_at: string;
  extracted_data?: Record<string, any>;
}

export interface VerificationMatrixItem {
  id?: number;
  field_name: string;
  doc_value: string;
  portal_value: string;
  match_type: 'EXACT' | 'PARTIAL' | 'MISMATCH';
  similarity_score: number;
  source_portal?: string;
  status_label?: string;
}

export interface ComplianceCheckItem {
  id?: number;
  check_name: string;
  status: 'PASS' | 'REVIEW' | 'FAIL';
  rule_description?: string;
  failure_reason?: string;
  weight: number;
}

export interface RiskFactor {
  factor_name: string;
  raw_risk: number;
  weight_percent: number;
  weighted_impact: number;
  status: 'PASS' | 'ELEVATED' | 'HIGH_RISK';
}

export interface RiskAssessment {
  total_risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  factors: RiskFactor[];
  explanations: string[];
  recommended_action: string;
}

export interface Vendor {
  id: number;
  name: string;
  legal_name?: string;
  gstin?: string;
  pan?: string;
  cin?: string;
  udyam_number?: string;
  address?: string;
  state?: string;
  pincode?: string;
  contact_email?: string;
  contact_phone?: string;
  turnover_cr: number;
  employee_count: number;
  established_year: number;
  verification_status: 'Verified' | 'Partially Verified' | 'Requires Review' | 'Failed' | 'Pending';
  compliance_score: number;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  match_score: number;
  ocr_confidence: number;
  anomaly_score: number;
  anomaly_status: 'LOW ANOMALY' | 'MEDIUM ANOMALY' | 'HIGH ANOMALY';
  recommended_action: string;
  last_verified?: string;
  created_at: string;
  documents?: DocumentItem[];
  verification_results?: VerificationMatrixItem[];
  compliance_checks?: ComplianceCheckItem[];
  risk_assessment?: RiskAssessment;
}

export interface DashboardKPIs {
  total_vendors: number;
  verified_vendors: number;
  review_required_vendors: number;
  high_risk_vendors: number;
  avg_compliance_score: number;
  avg_risk_score: number;
  avg_verification_time_mins: number;
}

export interface ChartDataPoint {
  label: string;
  value: number;
  category?: string;
}

export interface DashboardData {
  kpis: DashboardKPIs;
  compliance_distribution: ChartDataPoint[];
  risk_distribution: ChartDataPoint[];
  verification_status: ChartDataPoint[];
  monthly_trend: ChartDataPoint[];
  risk_factors: ChartDataPoint[];
}

export interface AuditLogItem {
  id: number;
  user_email: string;
  vendor_id?: number;
  vendor_name?: string;
  action: string;
  details?: Record<string, any>;
  timestamp: string;
}

export interface WeightSettings {
  weight_identity_mismatch: number;
  weight_document_issues: number;
  weight_registration_issues: number;
  weight_address_mismatch: number;
  weight_ml_anomaly: number;
  weight_missing_info: number;
}
