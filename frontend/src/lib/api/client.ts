import {
  ApiClientError,
  ApiErrorResponse,
  AuditListResponse,
  AuditVerifyResponse,
  CaseDetailResponse,
  CasesResponse,
  DriftReportResponse,
  GovernanceDecisionResponse,
  GovernanceProposalResponse,
  HealthResponse,
  ModelCardResponse,
  ModeReadinessResponse,
  OperatingMode,
  OverviewResponse,
  PolicyCompareResponse,
  ReplayControlResponse,
  ReplayRowsResponse,
  ReplayStatusResponse,
  ReplayStepResponse,
  ResultsResponse,
  SandboxScoreResponse,
  ScenariosResponse,
  SystemStatusResponse,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const DEFAULT_TIMEOUT_MS = 30000;

export async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      ...options,
      signal: options.signal || controller.signal,
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorData: ApiErrorResponse | null = null;
      try {
        errorData = await response.json();
      } catch {
        // Response was not JSON
      }

      const code = errorData?.error?.code || `HTTP_${response.status}`;
      const message = errorData?.error?.message || `Request failed with status ${response.status}`;
      const details = errorData?.error?.details || {};

      throw new ApiClientError(response.status, { code, message, details });
    }

    return await response.json();
  } catch (error: unknown) {
    clearTimeout(timeoutId);

    if (error instanceof ApiClientError) {
      throw error;
    }

    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiClientError(408, {
        code: 'REQUEST_TIMEOUT',
        message: `API request timed out after ${DEFAULT_TIMEOUT_MS}ms.`,
      });
    }

    throw new ApiClientError(0, {
      code: 'NETWORK_ERROR',
      message: 'Failed to connect to SignalGate backend API.',
      details: { originalError: String(error) },
    });
  }
}

export const api = {
  getHealth: () => request<HealthResponse>('/api/health'),
  getMode: () => request<ModeReadinessResponse>('/api/mode'),
  getStatus: (mode?: OperatingMode | string) => {
    const query = mode ? `?mode=${encodeURIComponent(mode)}` : '';
    return request<SystemStatusResponse>(`/api/status${query}`);
  },
  getModelCard: (mode?: OperatingMode | string) => {
    const query = mode ? `?mode=${encodeURIComponent(mode)}` : '';
    return request<ModelCardResponse>(`/api/model/card${query}`);
  },
  getDriftReport: (mode?: OperatingMode | string) => {
    const query = mode ? `?mode=${encodeURIComponent(mode)}` : '';
    return request<DriftReportResponse>(`/api/drift/report${query}`);
  },
  getProposals: () => request<GovernanceProposalResponse[]>('/api/governance/proposals'),
  getProposal: (id: string) =>
    request<GovernanceProposalResponse>(`/api/governance/proposals/${encodeURIComponent(id)}`),
  replayProposal: (id: string, scenario?: string) => {
    const query = scenario ? `?scenario=${encodeURIComponent(scenario)}` : '';
    return request<GovernanceProposalResponse>(
      `/api/governance/proposals/${encodeURIComponent(id)}/replay${query}`,
      { method: 'POST' }
    );
  },
  approveProposal: (id: string, approver: string, rationale: string) =>
    request<GovernanceDecisionResponse>(
      `/api/governance/proposals/${encodeURIComponent(id)}/approve`,
      {
        method: 'POST',
        body: JSON.stringify({ approver, rationale }),
      }
    ),
  rejectProposal: (id: string, reviewer: string, reason: string) =>
    request<GovernanceDecisionResponse>(
      `/api/governance/proposals/${encodeURIComponent(id)}/reject`,
      {
        method: 'POST',
        body: JSON.stringify({ reviewer, reason }),
      }
    ),
  verifyAuditChain: () => request<AuditVerifyResponse>('/api/audit/verify'),
  getOverview: (mode?: OperatingMode | string) => {
    const query = mode ? `?mode=${encodeURIComponent(mode)}` : '';
    return request<OverviewResponse>(`/api/overview${query}`);
  },
  getPoliciesCompare: (budgetMultiple?: string, mode?: OperatingMode | string) => {
    const searchParams = new URLSearchParams();
    if (budgetMultiple) searchParams.set('budget_multiple', budgetMultiple);
    if (mode) searchParams.set('mode', mode);
    const qs = searchParams.toString();
    return request<PolicyCompareResponse>(`/api/policies/compare${qs ? `?${qs}` : ''}`);
  },
  getScenarios: (mode?: OperatingMode | string) => {
    const query = mode ? `?mode=${encodeURIComponent(mode)}` : '';
    return request<ScenariosResponse>(`/api/scenarios${query}`);
  },
  getReplayRows: (params?: {
    scenario?: string;
    offset?: number;
    limit?: number;
    mode?: OperatingMode | string;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.scenario) searchParams.set('scenario', params.scenario);
    if (params?.offset !== undefined) searchParams.set('offset', String(params.offset));
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));
    if (params?.mode) searchParams.set('mode', params.mode);
    const qs = searchParams.toString();
    return request<ReplayRowsResponse>(`/api/replay/rows${qs ? `?${qs}` : ''}`);
  },
  getCases: (params?: {
    scenario?: string;
    action?: string;
    reason_code?: string;
    search?: string;
    offset?: number;
    limit?: number;
    mode?: OperatingMode | string;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.scenario) searchParams.set('scenario', params.scenario);
    if (params?.action) searchParams.set('action', params.action);
    if (params?.reason_code) searchParams.set('reason_code', params.reason_code);
    if (params?.search) searchParams.set('search', params.search);
    if (params?.offset !== undefined) searchParams.set('offset', String(params.offset));
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));
    if (params?.mode) searchParams.set('mode', params.mode);
    const qs = searchParams.toString();
    return request<CasesResponse>(`/api/cases${qs ? `?${qs}` : ''}`);
  },
  getCaseDetail: (caseId: string, mode?: OperatingMode | string) => {
    const query = mode ? `?mode=${encodeURIComponent(mode)}` : '';
    return request<CaseDetailResponse>(`/api/cases/${encodeURIComponent(caseId)}${query}`);
  },
  getAudit: (params?: {
    offset?: number;
    limit?: number;
    action?: string;
    reason_code?: string;
    case_id?: string;
    mode?: OperatingMode | string;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.offset !== undefined) searchParams.set('offset', String(params.offset));
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));
    if (params?.action) searchParams.set('action', params.action);
    if (params?.reason_code) searchParams.set('reason_code', params.reason_code);
    if (params?.case_id) searchParams.set('case_id', params.case_id);
    if (params?.mode) searchParams.set('mode', params.mode);
    const qs = searchParams.toString();
    return request<AuditListResponse>(`/api/audit${qs ? `?${qs}` : ''}`);
  },
  getResults: (mode?: OperatingMode | string) => {
    const query = mode ? `?mode=${encodeURIComponent(mode)}` : '';
    return request<ResultsResponse>(`/api/results${query}`);
  },
  scoreSandbox: (features: Record<string, unknown>, mode?: OperatingMode | string) =>
    request<SandboxScoreResponse>('/api/score-sandbox', {
      method: 'POST',
      body: JSON.stringify({
        features,
        mode: mode || 'SYNTHETIC_SMOKE_ONLY',
      }),
    }),
  getReplayStatus: () => request<ReplayStatusResponse>('/api/replay/status'),
  startReplay: (limit = 500, delayMs = 100) =>
    request<ReplayControlResponse>('/api/replay/start', {
      method: 'POST',
      body: JSON.stringify({ limit, delay_ms: delayMs }),
    }),
  stopReplay: () => request<ReplayControlResponse>('/api/replay/stop', { method: 'POST' }),
  stepReplay: () => request<ReplayStepResponse>('/api/replay/step', { method: 'POST' }),
  resetReplay: () => request<ReplayControlResponse>('/api/replay/reset', { method: 'POST' }),
};
