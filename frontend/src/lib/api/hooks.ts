import { useCallback, useEffect, useState } from 'react';
import { api } from './client';
import { ApiClientError, HealthResponse, OverviewResponse, SystemStatusResponse } from './types';

export interface UseApiStatusResult {
  health: HealthResponse | null;
  status: SystemStatusResponse | null;
  loading: boolean;
  error: ApiClientError | null;
  isBackendConnected: boolean;
  refetch: () => Promise<void>;
}

export function useApiStatus(): UseApiStatusResult {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<ApiClientError | null>(null);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [h, s] = await Promise.all([api.getHealth(), api.getStatus()]);
      setHealth(h);
      setStatus(s);
    } catch (err: unknown) {
      if (err instanceof ApiClientError) {
        setError(err);
      } else {
        setError(new ApiClientError(0, {
          code: 'FETCH_ERROR',
          message: 'An unexpected error occurred while fetching system status.',
        }));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return {
    health,
    status,
    loading,
    error,
    isBackendConnected: !!health && !error,
    refetch: fetchStatus,
  };
}

export interface UseOverviewResult {
  overview: OverviewResponse | null;
  loading: boolean;
  error: ApiClientError | null;
  refetch: () => Promise<void>;
}

export function useOverview(): UseOverviewResult {
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<ApiClientError | null>(null);

  const fetchOverview = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getOverview();
      setOverview(data);
    } catch (err: unknown) {
      if (err instanceof ApiClientError) {
        setError(err);
      } else {
        setError(new ApiClientError(0, {
          code: 'OVERVIEW_ERROR',
          message: 'Failed to retrieve overview metrics from backend.',
        }));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  return {
    overview,
    loading,
    error,
    refetch: fetchOverview,
  };
}
