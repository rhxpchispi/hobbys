import type { SearchRequest, SearchResponse } from '../types/course'

const SEARCH_ENDPOINT = '/api/search'

export class SearchApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message)
    this.name = 'SearchApiError'
  }
}

export async function postSearch(request: SearchRequest): Promise<SearchResponse> {
  const response = await fetch(SEARCH_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const detail = await response.text().catch(() => '')
    throw new SearchApiError(
      detail || `Error del servidor (${response.status})`,
      response.status,
    )
  }

  return response.json() as Promise<SearchResponse>
}
