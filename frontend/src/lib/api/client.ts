import {
  ApiClientError,
  ApiErrorResponse,
  AuditListResponse,
  CaseDetailResponse,
  CasesResponse,
  DriftReportResponse,
  HealthResponse,
  ModesOverviewResponse,
  ModeSelectResponse,
  OverviewResponse,
  PolicyCompareResponse,
  ReplayProposalRecord,
  ReplayRowsResponse,
  ResultsResponse,
  SandboxScoreResponse,
  ScenariosResponse,
  SystemStatusResponse,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const DEFAULT_TIMEOUT_MS = 8000;

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
  getStatus: () => request<SystemStatusResponse>('/api/status'),
  getOverview: () => request<OverviewResponse>('/api/overview'),
  getPoliciesCompare: (budgetMultiple?: string) => {
    const query = budgetMultiple ? `?budget_multiple=${encodeURIComponent(budgetMultiple)}` : '';
    return request<PolicyCompareResponse>(`/api/policies/compare${query}`);
  },
  getScenarios: () => request<ScenariosResponse>('/api/scenarios'),
  getReplayRows: (params?: { scenario?: string; offset?: number; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.scenario) searchParams.set('scenario', params.scenario);
    if (params?.offset !== undefined) searchParams.set('offset', String(params.offset));
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));
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
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.scenario) searchParams.set('scenario', params.scenario);
    if (params?.action) searchParams.set('action', params.action);
    if (params?.reason_code) searchParams.set('reason_code', params.reason_code);
    if (params?.search) searchParams.set('search', params.search);
    if (params?.offset !== undefined) searchParams.set('offset', String(params.offset));
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));
    const qs = searchParams.toString();
    return request<CasesResponse>(`/api/cases${qs ? `?${qs}` : ''}`);
  },
  getCaseDetail: (caseId: string) => request<CaseDetailResponse>(`/api/cases/${encodeURIComponent(caseId)}`),
  getAudit: (params?: { offset?: number; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.offset !== undefined) searchParams.set('offset', String(params.offset));
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));
    const qs = searchParams.toString();
    return request<AuditListResponse>(`/api/audit${qs ? `?${qs}` : ''}`);
  },
  getResults: () => request<ResultsResponse>('/api/results'),
  scoreSandbox: (features: Record<string, unknown>) =>
    request<SandboxScoreResponse>('/api/score-sandbox', {
      method: 'POST',
      body: JSON.stringify({ features }),
    }),
  getModes: () => request<ModesOverviewResponse>('/api/modes'),
  selectMode: (mode: string) =>
    request<ModeSelectResponse>('/api/modes/select', {
      method: 'POST',
      body: JSON.stringify({ mode }),
    }),
  getDrift: (scenario?: string) =>
    request<DriftReportResponse>(`/api/governance/drift${scenario ? `?scenario=${encodeURIComponent(scenario)}` : ''}`),
  getProposals: () => request<ReplayProposalRecord[]>('/api/governance/proposals'),
  validateProposal: (proposal: { proposal_id: string; base_cfg_hash: string; changes: Record<string, unknown>; rationale: string }) =>
    request<ReplayProposalRecord>('/api/governance/proposals/validate', {
      method: 'POST',
      body: JSON.stringify(proposal),
    }),
  approveProposal: (proposalId: string, approver: string) =>
    request<ReplayProposalRecord>('/api/governance/proposals/approve', {
      method: 'POST',
      body: JSON.stringify({ proposal_id: proposalId, approver }),
    }),
  verifyAuditChain: () => request<{ verified: boolean; chain_length: number; genesis_hash: string; head_hash: string; tamper_detected: boolean; details: string }>('/api/governance/audit-chain/verify'),
};
