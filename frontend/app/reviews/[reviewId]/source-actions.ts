"use server";

import { requireSession } from "../../../lib/auth";
import { apiFetch } from "../../../lib/api-fetch";

export type SourceResult = {
  found: boolean;
  page?: number;
  snippet?: string;
  method?: string;
  reason?: string;
  cached?: boolean;
};

export async function findFieldSource(input: {
  documentId: string;
  fieldPath: string;
  value: string;
  context?: string;
}): Promise<SourceResult> {
  await requireSession();
  const { documentId, fieldPath, value, context = "" } = input;
  if (
    !documentId.startsWith("DOC-") ||
    !fieldPath ||
    fieldPath.length > 200 ||
    !value ||
    value.length > 500 ||
    context.length > 500
  ) {
    return { found: false, reason: "The source request is not valid." };
  }

  const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";
  const query = new URLSearchParams({
    field_path: fieldPath,
    value,
    context,
  });

  try {
    const response = await apiFetch(
      `${apiUrl}/documents/${encodeURIComponent(documentId)}/source?${query}`,
      { cache: "no-store" },
    );
    if (!response.ok) {
      return { found: false, reason: "The source could not be retrieved." };
    }
    return (await response.json()) as SourceResult;
  } catch {
    return { found: false, reason: "Unable to reach the ExceptionOS API." };
  }
}
