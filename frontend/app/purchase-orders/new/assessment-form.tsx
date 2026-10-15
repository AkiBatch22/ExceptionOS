"use client";

import Link from "next/link";
import { useActionState } from "react";

import type { Extraction } from "./actions";
import MemoryAwareInput from "./memory-aware-input";
import {
  assessPurchaseOrder,
  type AssessmentIssue,
  type AssessmentState,
} from "./assessment-actions";
import {
  processPurchaseOrder,
  type ProcessingState,
} from "./processing-actions";

const initialState: AssessmentState = {
  assessment: null,
  error: null,
};

const initialProcessingState: ProcessingState = {
  result: null,
  error: null,
};

function formatReason(reason: string) {
  return reason.replaceAll("_", " ");
}

function Issue({ issue }: { issue: AssessmentIssue }) {
  return (
    <article className="issueCard">
      <h3>{formatReason(issue.reason)}</h3>
      {issue.customer && <p>Customer: {issue.customer}</p>}
      {issue.sku && <p>SKU: {issue.sku}</p>}
      {issue.requested !== undefined && <p>Requested: {issue.requested}</p>}
      {issue.available !== undefined && (
        <p>Available: {issue.available ?? "SKU not found"}</p>
      )}
      {issue.po_price !== undefined && <p>PO price: ${issue.po_price}</p>}
      {issue.erp_price !== undefined && <p>ERP price: ${issue.erp_price}</p>}
      {issue.document_value !== undefined && (
        <p>Document value: {issue.document_value}</p>
      )}
      {issue.expected_value !== undefined && (
        <p>Calculated value: {issue.expected_value}</p>
      )}
    </article>
  );
}

export default function AssessmentForm({
  extraction,
  messageId,
}: {
  extraction: Extraction;
  messageId?: string;
}) {
  const [state, formAction, isPending] = useActionState(
    assessPurchaseOrder,
    initialState,
  );
  const [processingState, processingAction, isProcessing] = useActionState(
    processPurchaseOrder,
    initialProcessingState,
  );
  const items = extraction.items.length > 0
    ? extraction.items
    : [{ sku: null, quantity: null, unit_price: null }];
  const suggestionFor = (fieldPath: string) =>
    extraction.suggested_corrections?.find(
      (suggestion) => suggestion.field_path === fieldPath,
    );

  return (
    <section className="detailSection extractionResult">
      <p className="eyebrow">AI preview</p>
      <h2>Review and correct</h2>

      {extraction.extraction_quality && (
        <div className={`qualitySummary ${extraction.extraction_quality.level}`}>
          <strong>
            Extraction confidence: {extraction.extraction_quality.level} ({Math.round(
              extraction.extraction_quality.score * 100,
            )}%)
          </strong>
          <ul>
            {extraction.extraction_quality.signals.map((signal) => (
              <li key={signal}>{signal}</li>
            ))}
          </ul>
          <p>This is a rule-based quality signal, not an AI-generated certainty.</p>
        </div>
      )}

      {extraction.missing_fields.length > 0 && (
        <div className="missingFields">
          <h3>Needs human input</h3>
          <ul>
            {extraction.missing_fields.map((field) => (
              <li key={field}>{field}</li>
            ))}
          </ul>
        </div>
      )}

      <form action={formAction} className="confirmationForm">
        {messageId && <input name="message_id" type="hidden" value={messageId} />}
        {extraction.document_id && (
          <input name="document_id" type="hidden" value={extraction.document_id} />
        )}
        <div className="fieldGrid">
          <label>
            <span>PO number</span>
            <input defaultValue={extraction.po_number ?? ""} name="po_number" required />
          </label>
          <label>
            <span>Customer</span>
            <MemoryAwareInput
              defaultValue={extraction.customer ?? ""}
              name="customer"
              required
              suggestion={suggestionFor("customer")}
            />
          </label>
          <label className="fullWidthField">
            <span>Ship to</span>
            <MemoryAwareInput
              defaultValue={extraction.ship_to ?? ""}
              name="ship_to"
              required
              suggestion={suggestionFor("ship_to")}
            />
          </label>
          <label>
            <span>PO date</span>
            <input defaultValue={extraction.po_date ?? ""} name="po_date" type="date" />
          </label>
          <label>
            <span>Requested delivery date</span>
            <input
              defaultValue={extraction.requested_delivery_date ?? ""}
              name="requested_delivery_date"
              type="date"
            />
          </label>
          <label>
            <span>Currency</span>
            <input
              defaultValue={extraction.currency ?? ""}
              maxLength={3}
              name="currency"
              placeholder="USD"
            />
          </label>
        </div>

        <h3>Items</h3>
        <input name="item_count" type="hidden" value={items.length} />
        <div className="editableItems">
          {items.map((item, index) => (
            <fieldset key={index}>
              <legend>Item {index + 1}</legend>
              <label>
                <span>SKU</span>
                <MemoryAwareInput
                  defaultValue={item.sku ?? ""}
                  name={`items.${index}.sku`}
                  required
                  suggestion={suggestionFor(`items[${index}].sku`)}
                />
              </label>
              <label className="wideItemField">
                <span>Description</span>
                <input
                  defaultValue={item.description ?? ""}
                  name={`items.${index}.description`}
                />
              </label>
              <label>
                <span>Quantity</span>
                <input
                  defaultValue={item.quantity ?? ""}
                  min="1"
                  name={`items.${index}.quantity`}
                  required
                  step="1"
                  type="number"
                />
              </label>
              <label>
                <span>Unit price</span>
                <input
                  defaultValue={item.unit_price ?? ""}
                  min="0"
                  name={`items.${index}.unit_price`}
                  required
                  step="0.01"
                  type="number"
                />
              </label>
              <label>
                <span>Line total</span>
                <input
                  defaultValue={item.line_total ?? ""}
                  min="0"
                  name={`items.${index}.line_total`}
                  step="0.01"
                  type="number"
                />
              </label>
              <label className="wideItemField">
                <span>Decoration requirements, one per line</span>
                <textarea
                  defaultValue={(item.decoration_requirements ?? []).join("\n")}
                  name={`items.${index}.decoration_requirements`}
                  rows={3}
                />
              </label>
            </fieldset>
          ))}
        </div>

        <h3>Financial totals</h3>
        <div className="totalsGrid">
          {(["subtotal", "discount", "tax", "freight", "total"] as const).map(
            (field) => (
              <label key={field}>
                <span>{formatReason(field)}</span>
                <input
                  defaultValue={extraction[field] ?? ""}
                  min="0"
                  name={field}
                  step="0.01"
                  type="number"
                />
              </label>
            ),
          )}
        </div>

        <div className="orderActions">
          <button
            className="button assessButton"
            disabled={isPending || isProcessing || processingState.result !== null}
            type="submit"
          >
            {isPending ? "Assessing…" : "Assess purchase order"}
          </button>
          {state.assessment && processingState.result === null && (
            <button
              className={`button ${
                state.assessment.decision === "human_review_required"
                  ? "humanReviewButton"
                  : "processButton"
              }`}
              disabled={isPending || isProcessing}
              formAction={processingAction}
              type="submit"
            >
              {isProcessing
                ? "Processing…"
                : state.assessment.decision === "human_review_required"
                  ? "Create human review"
                  : "Create ERP order"}
            </button>
          )}
        </div>
      </form>

      {state.error && <p className="decisionError">{state.error}</p>}
      {processingState.error && (
        <p className="decisionError">{processingState.error}</p>
      )}

      {state.assessment && (
        <div className="assessmentResult">
          <p className="eyebrow">Assessment</p>
          <h3>{formatReason(state.assessment.decision)}</h3>
          {state.assessment.issues.length === 0 ? (
            <p>No deterministic issues were found.</p>
          ) : (
            <div className="issueList">
              {state.assessment.issues.map((issue, index) => (
                <Issue issue={issue} key={`${issue.reason}-${index}`} />
              ))}
            </div>
          )}
        </div>
      )}

      {processingState.result && (
        <div className="processingResult">
          <p className="eyebrow">Processing result</p>
          {processingState.result.status === "created" ? (
            <>
              <h3>ERP order created</h3>
              <p>{processingState.result.erp_order_id}</p>
              {processingState.result.erp_order_id && (
                <Link
                  className="primaryLink"
                  href={`/orders/${encodeURIComponent(processingState.result.erp_order_id)}`}
                >
                  Open created order
                </Link>
              )}
            </>
          ) : (
            <>
              <h3>Human review required</h3>
              <p>The order was not created.</p>
              {processingState.result.review_id && (
                <Link
                  className="primaryLink"
                  href={`/reviews/${encodeURIComponent(processingState.result.review_id)}`}
                >
                  Open review
                </Link>
              )}
            </>
          )}
        </div>
      )}
    </section>
  );
}
