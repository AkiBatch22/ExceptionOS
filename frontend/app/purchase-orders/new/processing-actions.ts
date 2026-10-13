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
  const isEmailImport = typeof messageId === "string" && messageId.length > 0;
  const query = isEmailImport
    ? `?${new URLSearchParams({ message_id: messageId })}`
    : "";
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

  if (isEmailImport) {
    revalidatePath("/");
  }

  return {
    result: (await response.json()) as ProcessingState["result"],
    error: null,
  };
}
