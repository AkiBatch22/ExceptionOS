"use server";

import { revalidatePath } from "next/cache";

import { requireSession } from "../../lib/auth";
import { apiFetch } from "../../lib/api-fetch";


export type ResetState = {
  error: string | null;
  message: string | null;
};

export async function resetDemoData(
  _previousState: ResetState,
  formData: FormData,
): Promise<ResetState> {
  await requireSession();

  if (formData.get("confirmation") !== "RESET") {
    return { error: "Type RESET to confirm.", message: null };
  }

  const secret = process.env.DEMO_RESET_SECRET;
  if (!secret) {
    return { error: "Demo reset is not configured.", message: null };
  }

  const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await apiFetch(`${apiUrl}/demo/reset`, {
      method: "POST",
      headers: { "X-Demo-Reset-Secret": secret },
    });
    if (!response.ok) {
      return { error: "Demo data could not be reset.", message: null };
    }
  } catch {
    return { error: "Unable to reach the ExceptionOS API.", message: null };
  }

  revalidatePath("/");
  revalidatePath("/orders");
  return { error: null, message: "Demo orders, reviews, and uploads were removed." };
}
