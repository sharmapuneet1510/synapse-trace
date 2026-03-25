import { api } from './client';
import type { JurisdictionSummary, ConfigTypeResponse } from '../types/jurisdiction';

export const fetchJurisdictions = () =>
  api.get<JurisdictionSummary[]>('/jurisdictions');

export const fetchConfigType = (jurisdictionId: string, configType: string) =>
  api.get<ConfigTypeResponse>(`/jurisdictions/${jurisdictionId}/configs/${configType}`);
