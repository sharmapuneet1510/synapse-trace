import { api } from './client';
import type { FieldDetail } from '../types/field';

export const fetchFieldDetail = (jurisdictionId: string, fieldName: string) =>
  api.get<FieldDetail>(`/fields/${jurisdictionId}/${fieldName}`);
