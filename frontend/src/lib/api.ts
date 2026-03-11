const API_BASE = import.meta.env.VITE_API_URL ?? '/api';

export interface QueryResponse {
  answer: string;
  country: string | null;
  fields: string[];
}

export async function queryCountry(
  question: string,
  signal?: AbortSignal
): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
    signal,
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`API error ${response.status}: ${errorText}`);
  }

  return response.json() as Promise<QueryResponse>;
}
