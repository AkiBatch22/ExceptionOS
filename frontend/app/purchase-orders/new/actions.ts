"use server";

export type SuggestedCorrection = {
  pattern_id: number;
  party_label: string;
  field_path: string;
  original_value: string;
  corrected_value: string;
  confirmation_count: number;
  status: "suggestion_only" | "trusted_suggestion";
};

export type Extraction = {
  document_id?: string | null;
  extraction_quality?: {
    score: number;
    level: "high" | "medium" | "low";
    signals: string[];
  } | null;
  po_number: string | null;
  customer: string | null;
  po_date?: string | null;
  requested_delivery_date?: string | null;
  currency?: string | null;
  items: Array<{
    sku: string | null;
    description?: string | null;
    quantity: number | null;
    unit_price: number | null;
    line_total?: number | string | null;
    decoration_requirements?: string[] | null;
  }>;
  ship_to: string | null;
  subtotal?: number | string | null;
  discount?: number | string | null;
  tax?: number | string | null;
  freight?: number | string | null;
  total?: number | string | null;
  missing_fields: string[];
  suggested_corrections?: SuggestedCorrection[];
};

export type EmailSource = {
  message_id?: string | null;
  sender: string;
  subject: string;
  body: string;
  attachment_name: string;
};

export type ExtractionState = {
  extraction: Extraction | null;
  error: string | null;
  emailSource?: EmailSource;
};

export async function extractPurchaseOrder(
  _previousState: ExtractionState,
  formData: FormData,
): Promise<ExtractionState> {
  if (formData.get("source") === "inbox") {
    return importInboxPurchaseOrder();
  }

  const text = formData.get("text");
  const pdfFile = formData.get("pdf_file");
  const emailFile = formData.get("email_file");

  if (emailFile instanceof File && emailFile.size > 0) {
    if (!emailFile.name.toLowerCase().endsWith(".eml")) {
      return { extraction: null, error: "Upload an EML email file." };
    }

    return extractEmailPurchaseOrder(emailFile);
  }

  if (pdfFile instanceof File && pdfFile.size > 0) {
    if (pdfFile.type !== "application/pdf") {
      return { extraction: null, error: "Upload a PDF file." };
    }

    return extractPdfPurchaseOrder(pdfFile);
  }

  if (typeof text !== "string" || !text.trim()) {
    return {
      extraction: null,
      error: "Upload an EML email, upload a PDF, or paste purchase-order text.",
    };
  }

  const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";
  let response: Response;

  try {
    response = await fetch(`${apiUrl}/purchase-orders/extract`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
  } catch {
    return { extraction: null, error: "Unable to reach the ExceptionOS API." };
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    return { extraction: null, error: body?.detail ?? "Extraction failed." };
  }

  return {
    extraction: (await response.json()) as Extraction,
    error: null,
  };
}


async function extractPdfPurchaseOrder(file: File): Promise<ExtractionState> {
  const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";
  const upload = new FormData();
  upload.set("file", file);
  let response: Response;

  try {
    response = await fetch(`${apiUrl}/purchase-orders/extract-pdf`, {
      method: "POST",
      body: upload,
    });
  } catch {
    return { extraction: null, error: "Unable to reach the ExceptionOS API." };
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    return { extraction: null, error: body?.detail ?? "PDF extraction failed." };
  }

  return {
    extraction: (await response.json()) as Extraction,
    error: null,
  };
}


async function extractEmailPurchaseOrder(file: File): Promise<ExtractionState> {
  const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";
  const upload = new FormData();
  upload.set("file", file);
  let response: Response;

  try {
    response = await fetch(`${apiUrl}/purchase-orders/extract-email`, {
      method: "POST",
      body: upload,
    });
  } catch {
    return { extraction: null, error: "Unable to reach the ExceptionOS API." };
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    return { extraction: null, error: body?.detail ?? "Email extraction failed." };
  }

  const result = (await response.json()) as {
    message_id?: string | null;
    sender: string;
    subject: string;
    body: string;
    attachment_name: string;
    purchase_order: Extraction;
  };

  return {
    extraction: result.purchase_order,
    error: null,
    emailSource: {
      message_id: result.message_id,
      sender: result.sender,
      subject: result.subject,
      body: result.body,
      attachment_name: result.attachment_name,
    },
  };
}


async function importInboxPurchaseOrder(): Promise<ExtractionState> {
  const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";
  let response: Response;

  try {
    response = await fetch(`${apiUrl}/purchase-orders/import-email`, {
      method: "POST",
    });
  } catch {
    return { extraction: null, error: "Unable to reach the ExceptionOS API." };
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    return { extraction: null, error: body?.detail ?? "Inbox import failed." };
  }

  const result = (await response.json()) as {
    message_id: string;
    sender: string;
    subject: string;
    body: string;
    attachment_name: string;
    purchase_order: Extraction;
  };

  return {
    extraction: result.purchase_order,
    error: null,
    emailSource: {
      message_id: result.message_id,
      sender: result.sender,
      subject: result.subject,
      body: result.body,
      attachment_name: result.attachment_name,
    },
  };
}
