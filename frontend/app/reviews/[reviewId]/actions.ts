"use server";

import { redirect } from "next/navigation";

export type DecisionState = {
  error: string | null;
};

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
