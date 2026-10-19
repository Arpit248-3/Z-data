import React, { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { OperatingMode, ModeReadinessResponse } from '../lib/api/types';
import { api } from '../lib/api/client';

export interface ModeContextType {
  mode: OperatingMode;
  setMode: (mode: OperatingMode) => void;
  modeReadiness: ModeReadinessResponse | null;
  loading: boolean;
  error: string | null;
  refreshReadiness: () => Promise<void>;
  isRealDataMode: boolean;
  isSmokeMode: boolean;
  isLiveDisconnected: boolean;
}

const ModeContext = createContext<ModeContextType | undefined>(undefined);

const MODE_STORAGE_KEY = 'signalgate_operating_mode';

export const ModeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [mode, setModeState] = useState<OperatingMode>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(MODE_STORAGE_KEY) as OperatingMode | null;
      if (
        stored === 'SYNTHETIC_SMOKE_ONLY' ||
        stored === 'IEEE_CIS_OFFLINE_BENCHMARK' ||
        stored === 'LIVE_SOURCE_NOT_CONNECTED'
      ) {
        return stored;
      }
    }
    return 'SYNTHETIC_SMOKE_ONLY';
  });

  const [modeReadiness, setModeReadiness] = useState<ModeReadinessResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refreshReadiness = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getMode();
      setModeReadiness(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to query operating mode readiness');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshReadiness();
  }, [refreshReadiness]);

  const setMode = (newMode: OperatingMode) => {
    setModeState(newMode);
    if (typeof window !== 'undefined') {
      localStorage.setItem(MODE_STORAGE_KEY, newMode);
    }
  };

  const isRealDataMode = mode === 'IEEE_CIS_OFFLINE_BENCHMARK';
  const isSmokeMode = mode === 'SYNTHETIC_SMOKE_ONLY';
  const isLiveDisconnected = mode === 'LIVE_SOURCE_NOT_CONNECTED';

  return (
    <ModeContext.Provider
      value={{
        mode,
        setMode,
        modeReadiness,
        loading,
        error,
        refreshReadiness,
        isRealDataMode,
        isSmokeMode,
        isLiveDisconnected,
      }}
    >
      {children}
    </ModeContext.Provider>
  );
};

export const useMode = (): ModeContextType => {
  const context = useContext(ModeContext);
  if (!context) {
    throw new Error('useMode must be used within a ModeProvider');
  }
  return context;
};
