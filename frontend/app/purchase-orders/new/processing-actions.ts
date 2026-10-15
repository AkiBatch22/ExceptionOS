"use server";

import { revalidatePath } from "next/cache";

import { parsePurchaseOrderForm } from "./form-data";

export type ProcessingState = {
  result: {
    status: "created" | "human_review_required";
    erp_order_id: string | null;
    review_id?: string;
  } | null;
  error: string | null;
};

export async function processPurchaseOrder(
  _previousState: ProcessingState,
  formData: FormData,
): Promise<ProcessingState> {
  const { purchaseOrder, error } = parsePurchaseOrderForm(formData);

  if (purchaseOrder === null) {
    return { result: null, error };
  }

  const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";
  const messageId = formData.get("message_id");
  const documentId = formData.get("document_id");
  const isEmailImport = typeof messageId === "string" && messageId.length > 0;
  const queryParameters = new URLSearchParams();
  if (isEmailImport) queryParameters.set("message_id", messageId);
  if (
    !isEmailImport &&
    typeof documentId === "string" &&
    documentId.length > 0
  ) {
    queryParameters.set("document_id", documentId);
  }
  const query = queryParameters.size > 0 ? `?${queryParameters}` : "";
  const endpoint = isEmailImport ? "/email-imports/process" : "/purchase-orders/process";
  let response: Response;

  try {
    response = await fetch(`${apiUrl}${endpoint}${query}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(purchaseOrder),
    });
  } catch {
    return { result: null, error: "Unable to reach the ExceptionOS API." };
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    return {
      result: null,
      error: body?.detail ?? "The purchase order could not be processed.",
    };
  }

  const poNumber = purchaseOrder.po_number;
  const feedback = [
    ...formData.getAll("accepted_pattern_ids").map((id) => ({ id, feedback: "accepted" })),
    ...formData.getAll("rejected_pattern_ids").map((id) => ({ id, feedback: "rejected" })),
  ];
  await Promise.allSettled(
    feedback.map(({ id, feedback: patternFeedback }) =>
      fetch(`${apiUrl}/reviews/patterns/${encodeURIComponent(String(id))}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback: patternFeedback, po_number: poNumber }),
      }),
    ),
  );

  revalidatePath("/");

  return {
    result: (await response.json()) as ProcessingState["result"],
    error: null,
  };
}
