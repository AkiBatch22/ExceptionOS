"use server";

import { parsePurchaseOrderForm } from "./form-data";

export type AssessmentIssue = {
  reason: string;
  customer?: string;
  sku?: string;
  requested?: number;
  available?: number | null;
  po_price?: number;
  erp_price?: number;
  item_index?: number;
  document_value?: number;
  expected_value?: number;
};

export type AssessmentState = {
  assessment: {
    decision: "ready" | "human_review_required";
    issues: AssessmentIssue[];
  } | null;
  error: string | null;
};

export async function assessPurchaseOrder(
  _previousState: AssessmentState,
  formData: FormData,
): Promise<AssessmentState> {
  const { purchaseOrder, error } = parsePurchaseOrderForm(formData);

  if (purchaseOrder === null) {
    return { assessment: null, error };
  }

  const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";
  let response: Response;

  try {
    response = await fetch(`${apiUrl}/purchase-orders/assess`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(purchaseOrder),
    });
  } catch {
    return { assessment: null, error: "Unable to reach the ExceptionOS API." };
  }

  if (!response.ok) {
    return { assessment: null, error: "The corrected purchase order is not valid." };
  }

  return {
    assessment: (await response.json()) as AssessmentState["assessment"],
    error: null,
  };
}
