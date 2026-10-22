export const SESSION_COOKIE = "exceptionos_demo_session";
const SESSION_SECONDS = 12 * 60 * 60;

type SessionPayload = {
  username: string;
  expiresAt: number;
};

function getSecret() {
  const secret = process.env.AUTH_SECRET;
  return secret && secret.length >= 32 ? secret : null;
}

function encode(value: string) {
  return Buffer.from(value, "utf8").toString("base64url");
}

function decode(value: string) {
  return Buffer.from(value, "base64url").toString("utf8");
}

async function signature(value: string, secret: string) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const result = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(value),
  );
  return Buffer.from(result).toString("base64url");
}

function constantTimeEqual(left: string, right: string) {
  const leftBytes = new TextEncoder().encode(left);
  const rightBytes = new TextEncoder().encode(right);
  if (leftBytes.length !== rightBytes.length) return false;

  let difference = 0;
  for (let index = 0; index < leftBytes.length; index += 1) {
    difference |= leftBytes[index] ^ rightBytes[index];
  }
  return difference === 0;
}

export function demoAuthEnabled() {
  return process.env.DEMO_AUTH_ENABLED === "true";
}

export async function createSessionToken(username: string) {
  const secret = getSecret();
  if (!secret) throw new Error("AUTH_SECRET must contain at least 32 characters");

  const payload = encode(
    JSON.stringify({
      username,
      expiresAt: Date.now() + SESSION_SECONDS * 1000,
    } satisfies SessionPayload),
  );
  return `${payload}.${await signature(payload, secret)}`;
}

export async function verifySessionToken(token: string | undefined) {
  if (!demoAuthEnabled()) return { username: "local-demo" };
  if (!token) return null;

  const secret = getSecret();
  if (!secret) return null;

  const [payload, suppliedSignature, extra] = token.split(".");
  if (!payload || !suppliedSignature || extra) return null;

  const expectedSignature = await signature(payload, secret);
  if (!constantTimeEqual(suppliedSignature, expectedSignature)) return null;

  try {
    const parsed = JSON.parse(decode(payload)) as SessionPayload;
    if (
      typeof parsed.username !== "string" ||
      typeof parsed.expiresAt !== "number" ||
      parsed.expiresAt <= Date.now()
    ) {
      return null;
    }
    return { username: parsed.username };
  } catch {
    return null;
  }
}

export function credentialsAreValid(username: string, password: string) {
  const expectedUsername = process.env.DEMO_USERNAME;
  const expectedPassword = process.env.DEMO_PASSWORD;

  if (!demoAuthEnabled()) return true;
  if (!expectedUsername || !expectedPassword || expectedPassword.length < 12) {
    throw new Error("Demo authentication is not configured safely");
  }

  return (
    constantTimeEqual(username, expectedUsername) &&
    constantTimeEqual(password, expectedPassword)
  );
}

export const sessionCookieOptions = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
  path: "/",
  maxAge: SESSION_SECONDS,
};
