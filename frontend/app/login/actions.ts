"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import {
  createSessionToken,
  credentialsAreValid,
  SESSION_COOKIE,
  sessionCookieOptions,
} from "../../lib/auth";
import {
  clearLoginFailures,
  loginIsLimited,
  recordLoginFailure,
} from "../../lib/login-rate-limit";


export type LoginState = { error: string | null };

function safeDestination(value: FormDataEntryValue | null) {
  return typeof value === "string" && value.startsWith("/") && !value.startsWith("//")
    ? value
    : "/";
}

export async function login(
  _previousState: LoginState,
  formData: FormData,
): Promise<LoginState> {
  const username = formData.get("username");
  const password = formData.get("password");

  if (typeof username !== "string" || typeof password !== "string") {
    return { error: "Enter the demo username and password." };
  }

  if (await loginIsLimited()) {
    return { error: "Too many failed attempts. Try again in 15 minutes." };
  }

  try {
    if (!credentialsAreValid(username, password)) {
      await recordLoginFailure();
      return { error: "The username or password is incorrect." };
    }

    await clearLoginFailures();

    const cookieStore = await cookies();
    cookieStore.set(
      SESSION_COOKIE,
      await createSessionToken(username),
      sessionCookieOptions,
    );
  } catch {
    return { error: "The private demo is not configured correctly." };
  }

  redirect(safeDestination(formData.get("next")));
}

export async function logout() {
  const cookieStore = await cookies();
  cookieStore.delete(SESSION_COOKIE);
  redirect("/login");
}
