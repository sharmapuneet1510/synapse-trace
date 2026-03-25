import { api } from './client';
import type { TranslationResult } from '../types/translation';

export const fetchTranslation = (
  fieldName: string,
  jurisdictionId: string,
) =>
  api.post<TranslationResult>('/translation/explain', {
    field_name: fieldName,
    jurisdiction_id: jurisdictionId,
  });
