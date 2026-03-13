export interface QueryResponse {
  answer: string;
  countries: string[];
  fields: string[];
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function queryCountry(
  question: string,
  signal?: AbortSignal
): Promise<QueryResponse> {
  const response = await fetch("/api/query", {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
    signal,
  });

  if (!response.ok) {
    throw new ApiError(response.status, await response.text().catch(() => ''));
  }

  return response.json() as Promise<QueryResponse>;
}
