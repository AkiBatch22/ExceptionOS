"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

export type DecisionState = {
  error: string | null;
};

export type CorrectionState = {
  error: string | null;
  message: string | null;
};

export async function submitReviewCorrection(
  reviewId: string,
  _previousState: CorrectionState,
  formData: FormData,
): Promise<CorrectionState> {
  const fieldPath = formData.get("field_path");
  const correctedValue = formData.get("corrected_value");
  const remember = formData.get("remember") === "true";

  if (typeof fieldPath !== "string" || typeof correctedValue !== "string" || !correctedValue.trim()) {
    return { error: "Choose a field and enter its corrected value.", message: null };
  }

  const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";
  let response: Response;
  try {
    response = await fetch(`${apiUrl}/reviews/${encodeURIComponent(reviewId)}/corrections`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        field_path: fieldPath,
        corrected_value: correctedValue.trim(),
        remember,
      }),
    });
  } catch {
    return { error: "Unable to reach the ExceptionOS API.", message: null };
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    return { error: body?.detail ?? "The correction could not be applied.", message: null };
  }

  revalidatePath(`/reviews/${reviewId}`);
  revalidatePath("/");
  return {
    error: null,
    message: remember
      ? "Correction applied and saved as a future supplier suggestion."
      : "Correction applied to this review only.",
  };
}

export async function submitReviewDecision(
  reviewId: string,
  _previousState: DecisionState,
  formData: FormData,
): Promise<DecisionState> {
  const decision = formData.get("decision");

  if (decision !== "approved" && decision !== "rejected") {
    return { error: "Choose approve or reject." };
  }

  const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";
  let response: Response;

  try {
    response = await fetch(
      `${apiUrl}/reviews/${encodeURIComponent(reviewId)}/decision`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision }),
      },
    );
  } catch {
    return { error: "Unable to reach the ExceptionOS API." };
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    return { error: body?.detail ?? "The review decision failed." };
  }

  redirect("/");
}
