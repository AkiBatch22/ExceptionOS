import Link from "next/link";

import { requireSession } from "../../../lib/auth";
import { apiFetch } from "../../../lib/api-fetch";
import type { EmailSource, Extraction } from "./actions";
import ExtractionForm from "./extraction-form";

type EmailImport = EmailSource & {
  message_id: string;
  extraction: Extraction;
};

async function getEmailImport(messageId: string): Promise<EmailImport | null> {
  const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";
  const query = new URLSearchParams({ message_id: messageId });

  try {
    const response = await apiFetch(`${apiUrl}/email-imports/detail?${query}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    const result = (await response.json()) as Omit<EmailImport, "body">;
    return { ...result, body: "" };
  } catch {
    return null;
  }
}

export default async function NewPurchaseOrderPage({
  searchParams,
}: {
  searchParams: Promise<{ message_id?: string }>;
}) {
  await requireSession();
  const { message_id: messageId } = await searchParams;
  const emailImport = messageId ? await getEmailImport(messageId) : null;

  return (
    <main>
      <Link className="backLink" href="/">← Dashboard</Link>

      <header>
        <p className="eyebrow">ExceptionOS</p>
        <h1>Extract a purchase order</h1>
        <p className="subtitle">
          Check the configured inbox, upload an EML email or PDF, or paste raw text. Nothing will be processed or created until you confirm it.
        </p>
      </header>

      {messageId && emailImport === null && (
        <section className="message error">Unable to load the imported order.</section>
      )}

      <ExtractionForm
        initialEmailSource={emailImport ?? undefined}
        initialExtraction={emailImport?.extraction}
      />
    </main>
  );
}
