import { api } from './client';

export const getBusinessDescription = (fieldName: string, jurisdictionId: string) =>
  api.get<{ description: string }>(
    `/llm/business-description?field_name=${encodeURIComponent(fieldName)}&jurisdiction_id=${encodeURIComponent(jurisdictionId)}`,
  );
