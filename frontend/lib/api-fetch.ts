import "server-only";

export function apiFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  const secret = process.env.API_SHARED_SECRET;

  if (secret) {
    headers.set("X-ExceptionOS-Key", secret);
  }

  return fetch(input, { ...init, headers });
}
