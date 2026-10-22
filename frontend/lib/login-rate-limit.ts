import { headers } from "next/headers";


const WINDOW_MS = 15 * 60 * 1000;
const MAX_FAILURES = 5;
const failures = new Map<string, number[]>();


async function clientKey() {
  const requestHeaders = await headers();
  return (
    requestHeaders.get("x-forwarded-for")?.split(",", 1)[0].trim() ||
    requestHeaders.get("x-real-ip") ||
    "unknown"
  );
}

function recentFailures(key: string) {
  const cutoff = Date.now() - WINDOW_MS;
  const recent = (failures.get(key) ?? []).filter((attempt) => attempt > cutoff);
  if (recent.length) failures.set(key, recent);
  else failures.delete(key);
  return recent;
}

export async function loginIsLimited() {
  return recentFailures(await clientKey()).length >= MAX_FAILURES;
}

export async function recordLoginFailure() {
  const key = await clientKey();
  failures.set(key, [...recentFailures(key), Date.now()]);
}

export async function clearLoginFailures() {
  failures.delete(await clientKey());
}
