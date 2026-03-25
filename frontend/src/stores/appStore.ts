import { create } from 'zustand';

interface AppState {
  jurisdictionId: string | null;
  configType: string | null;
  fieldName: string | null;
  assetClass: string | null;
  showTranslation: boolean;
  activeView: 'explorer' | 'dashboard';
  chatOpen: boolean;
  chatSessionId: string | null;
  detailViewMode: 'business' | 'technical';
  setJurisdiction: (id: string) => void;
  setConfigType: (ct: string) => void;
  setField: (name: string | null) => void;
  setAssetClass: (ac: string | null) => void;
  setShowTranslation: (show: boolean) => void;
  setActiveView: (view: 'explorer' | 'dashboard') => void;
  setChatOpen: (open: boolean) => void;
  setChatSessionId: (id: string | null) => void;
  setDetailViewMode: (mode: 'business' | 'technical') => void;
}

export const useAppStore = create<AppState>((set) => ({
  jurisdictionId: null,
  configType: null,
  fieldName: null,
  assetClass: null,
  showTranslation: false,
  activeView: 'explorer',
  setJurisdiction: (id) => set({ jurisdictionId: id, configType: null, fieldName: null }),
  setConfigType: (ct) => set({ configType: ct, fieldName: null }),
  setField: (name) => set({ fieldName: name }),
  setAssetClass: (ac) => set({ assetClass: ac }),
  setShowTranslation: (show) => set({ showTranslation: show }),
  setActiveView: (view) => set({ activeView: view }),
  chatOpen: false,
  chatSessionId: null,
  detailViewMode: 'business',
  setChatOpen: (open) => set({ chatOpen: open }),
  setChatSessionId: (id) => set({ chatSessionId: id }),
  setDetailViewMode: (mode) => set({ detailViewMode: mode }),
}));
