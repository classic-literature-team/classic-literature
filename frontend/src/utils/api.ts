// 백엔드 API 베이스 경로. vite dev 서버에서 /api → http://localhost:8000 로 프록시된다.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/**
 * 얇은 fetch 래퍼. JSON 요청/응답을 처리하고 실패 시 ApiError를 던진다.
 */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const message = await response.text()
    throw new ApiError(response.status, message || response.statusText)
  }

  // 204 No Content 대응
  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}
