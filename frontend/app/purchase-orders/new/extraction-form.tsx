"use client";

import { useActionState } from "react";

import {
  extractPurchaseOrder,
  type EmailSource,
  type Extraction,
  type ExtractionState,
} from "./actions";
import AssessmentForm from "./assessment-form";

type ExtractionFormProps = {
  initialExtraction?: Extraction;
  initialEmailSource?: EmailSource;
};

export default function ExtractionForm({
  initialExtraction,
  initialEmailSource,
}: ExtractionFormProps) {
  const initialState: ExtractionState = {
    extraction: initialExtraction ?? null,
    emailSource: initialEmailSource,
    error: null,
  };
  const [state, formAction, isPending] = useActionState(
    extractPurchaseOrder,
    initialState,
  );

  return (
    <>
      <form action={formAction} className="extractionForm">
        <button
          className="button inboxButton"
          disabled={isPending}
          name="source"
          type="submit"
          value="inbox"
        >
          {isPending ? "Checking…" : "Check inbox"}
        </button>

        <p className="formDivider"><span>or upload email</span></p>

        <label htmlFor="email-file">Purchase-order email</label>
        <input id="email-file" name="email_file" type="file" accept=".eml,message/rfc822" />

        <p className="formDivider"><span>or upload PDF</span></p>

        <label htmlFor="po-file">Purchase-order PDF</label>
        <input id="po-file" name="pdf_file" type="file" accept="application/pdf,.pdf" />

        <p className="formDivider"><span>or paste text</span></p>

        <label htmlFor="po-text">Purchase-order text</label>
        <textarea
          id="po-text"
          name="text"
          placeholder="Paste the purchase-order text here..."
          rows={12}
        />
        <button
          className="button extractButton"
          disabled={isPending}
          type="submit"
        >
          {isPending ? "Extracting…" : "Extract purchase order"}
        </button>
      </form>

      {state.error && <section className="message error">{state.error}</section>}

      {state.emailSource && (
        <section className="message emailSource">
          <p className="eyebrow">Email source</p>
          <h2>{state.emailSource.subject || "No subject"}</h2>
          <p><strong>From:</strong> {state.emailSource.sender || "Unknown sender"}</p>
          <p><strong>Attachment:</strong> {state.emailSource.attachment_name}</p>
          {state.emailSource.body && <p>{state.emailSource.body}</p>}
        </section>
      )}

      {state.extraction && (
        <AssessmentForm
          extraction={state.extraction}
          key={JSON.stringify(state.extraction)}
          messageId={state.emailSource?.message_id ?? undefined}
        />
      )}
    </>
  );
}
