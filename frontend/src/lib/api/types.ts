/**
 * SignalGate API TypeScript Definitions
 * Strictly mirrors backend/app/schemas.py and docs/api_contract.md
 */

export interface HealthResponse {
  service_name: string;
  version: string;
  status: 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY';
  timestamp: string;
}

export interface DependencyStatus {
  status: 'READY' | 'SYNTHETIC_SMOKE_ONLY' | 'NOT_AVAILABLE' | 'DEGRADED' | 'DISABLED' | 'INVALID';
  details?: string;
}

export interface SystemStatusResponse {
  service_name: string;
  version: string;
  overall_status: 'READY' | 'DEGRADED' | 'NOT_READY' | 'OPERATIONAL_SYNTHETIC' | string;
  evidence_status: string;
  dependencies: {
    dataset: DependencyStatus;
    model_artifacts: DependencyStatus;
    calibrator?: DependencyStatus;
    ensemble?: DependencyStatus;
    frozen_policy: DependencyStatus;
    consolidated_results: DependencyStatus;
    replay_data?: DependencyStatus;
    audit_log?: DependencyStatus;
    explanations: DependencyStatus;
    [key: string]: DependencyStatus | undefined;
  };
  timestamp: string;
}

export interface OverviewResponse {
  dataset_status: string;
  evaluation_status: string;
  total_tested_transactions: number | null;
  available_fraud_count: number | null;
  primary_budget: number | null;
  b2_recall: number | null;
  signalgate_recall: number | null;
  delta_recall_pp: number | null;
  ci_conclusive: boolean | null;
  ci_lower_pp: number | null;
  ci_upper_pp: number | null;
  touched_rate: number | null;
  alert_rate: number | null;
  review_rate: number | null;
  deferred_rate: number | null;
  confident_misses: number | null;
  frozen_config_hash: string | null;
  split_hash: string | null;
  status_fields: Record<string, string>;
}

export interface PolicyComparisonItem {
  policy: string;
  target_budget?: number | null;
  total_transactions?: number | null;
  escalated_count?: number | null;
  touched_rate: number | null;
  recall?: number | null;
  recall_at_touched?: number | null;
  precision: number | null;
  total_fraud?: number | null;
  caught_fraud?: number | null;
  missed_fraud?: number | null;
  deferred_count?: number | null;
  deferred_rate?: number | null;
  fpr?: number | null;
  ci_recall_lower?: number | null;
  ci_recall_upper?: number | null;
}

export interface PolicyCompareResponse {
  budget_multiple: string;
  target_budget: number | null;
  status: string;
  policies: PolicyComparisonItem[];
}

export interface ScenarioItem {
  scenario_id: string;
  name: string;
  status: string;
  description: string;
  sample_count: number | null;
  fraud_count: number | null;
  fraud_prevalence?: number | null;
  is_synthetic: boolean;
  b2_recall?: number | null;
  signalgate_recall?: number | null;
  delta_recall_vs_b2_pp?: number | null;
  scenario_hash?: string;
  replay_available?: boolean;
}

export interface ScenariosResponse {
  status: string;
  scenarios: ScenarioItem[];
}

export interface ReplayRowItem {
  row_id: number;
  case_id: string;
  timestamp: number;
  transaction_id: string;
  amount: float_or_number;
  product_cd: string;
  card4: string;
  p: number;
  u: number;
  u_method: string;
  action: 'FRAUD_ALERT' | 'MANUAL_REVIEW' | 'ROUTINE' | 'HELD_DEFERRED' | string;
  reason_code: string;
  governor_status: string;
  lane_rank: number | null;
  scenario_id: string;
  status: string;
  offline_ground_truth?: {
    is_fraud?: number;
    amount?: number;
    [key: string]: unknown;
  } | null;
}

type float_or_number = number;

export interface ReplayRowsResponse {
  total_rows: number;
  offset: number;
  limit: number;
  scenario_id: string;
  status: string;
  rows: ReplayRowItem[];
}

export interface CaseListItem {
  case_id: string;
  timestamp: number;
  amount: number;
  product_cd: string | null;
  card4: string | null;
  scenario_id: string;
  p: number;
  u: number | null;
  action: string;
  reason_code: string;
  governor_status: string;
  lane_rank: number | null;
  offline_is_fraud: number | null;
}

export interface CasesResponse {
  total_cases: number;
  limit: number;
  offset: number;
  scenario_id: string;
  cases: CaseListItem[];
}

export interface CaseDetailResponse {
  case_id: string;
  timestamp: number;
  amount: number;
  scenario_id: string;
  status: string;
  signals: {
    p_risk: number;
    u_disagreement: number;
    u_method: string;
    ensemble_votes?: Record<string, number>;
  };
  decision: {
    action: string;
    reason_code: string;
    routing_rule: string;
    governor_quota_admitted: boolean;
  };
  features: Record<string, unknown>;
  offline_evaluation?: {
    is_fraud?: number;
    label_provenance?: string;
  } | null;
  explanations: Record<string, unknown>;
}

export interface AuditRecordItem {
  audit_id: string;
  timestamp: string;
  action: string;
  reason_code: string;
  case_id?: string;
  details?: Record<string, unknown>;
  hash_chain?: string;
  sequence_id?: number;
  [key: string]: unknown;
}

export interface AuditListResponse {
  total_records: number;
  offset: number;
  limit: number;
  skipped_records: number;
  records: AuditRecordItem[];
}

export interface SandboxScoreResponse {
  decision_id: string;
  timestamp: string;
  signals: {
    p_risk: number;
    u_disagreement: number;
    u_method: string;
    ensemble_predictions?: Record<string, number>;
  };
  decision: {
    action: string;
    reason_code: string;
    governor_quota_status: string;
  };
  governor: Record<string, unknown>;
  latency_ms: number;
  provenance: Record<string, unknown>;
  audit_logged: boolean;
  notice: string;
}

export interface ResultsResponse {
  evidence_status: string;
  timestamp: string;
  frozen_config_hash: string;
  split_hash: string;
  primary_budget: number;
  test_rows: number;
  comparison_on_identical_test_rows?: Record<string, unknown>;
  shift_scenarios?: Record<string, unknown>;
  latency_p95_ms?: number;
  [key: string]: unknown;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}

export class ApiClientError extends Error {
  code: string;
  status: number;
  details?: Record<string, unknown>;

  constructor(status: number, errorDetail: ApiErrorDetail) {
    super(errorDetail.message);
    this.name = 'ApiClientError';
    this.status = status;
    this.code = errorDetail.code;
    this.details = errorDetail.details;
  }
}
