import Link from "next/link";
import { notFound } from "next/navigation";

import { requireSession } from "../../../lib/auth";
import { apiFetch } from "../../../lib/api-fetch";
import DecisionForm from "./decision-form";
import CorrectionForm, { type CorrectionOption } from "./correction-form";
import SourceLookup from "./source-lookup";

type PurchaseOrderItem = {
  sku: string;
  description?: string | null;
  quantity: number;
  unit_price: number | string;
  line_total?: number | string | null;
  decoration_requirements?: string[] | null;
};

type ReviewIssue = {
  reason: string;
  customer?: string;
  sku?: string;
  requested?: number;
  available?: number | null;
  po_price?: number | string;
  erp_price?: number | string;
  document_value?: number | string;
  expected_value?: number | string;
};

type Review = {
  review_id: string;
  status: "pending" | "approved" | "rejected";
  purchase_order: {
    po_number: string;
    customer: string;
    po_date?: string | null;
    requested_delivery_date?: string | null;
    currency?: string | null;
    items: PurchaseOrderItem[];
    ship_to: string;
    subtotal?: number | string | null;
    discount?: number | string | null;
    tax?: number | string | null;
    freight?: number | string | null;
    total?: number | string | null;
  };
  issues: ReviewIssue[];
  erp_order_id?: string | null;
  source_document_id?: string | null;
  recommendations?: string[];
  events?: Array<{
    event: string;
    details: Record<string, unknown>;
    created_at?: string;
  }>;
};

async function getReview(reviewId: string): Promise<Review | null> {
  const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";
  let response: Response;

  try {
    response = await apiFetch(`${apiUrl}/reviews/${encodeURIComponent(reviewId)}`, {
      cache: "no-store",
    });
  } catch {
    return null;
  }

  if (response.status === 404) {
    notFound();
  }

  if (!response.ok) {
    return null;
  }

  return (await response.json()) as Review;
}

function formatReason(reason: string) {
  return reason.replaceAll("_", " ");
}

export default async function ReviewPage({
  params,
}: {
  params: Promise<{ reviewId: string }>;
}) {
  await requireSession();
  const { reviewId } = await params;
  const review = await getReview(reviewId);

  if (review === null) {
    return (
      <main>
        <Link className="backLink" href="/">← Pending reviews</Link>
        <section className="message error">
          Unable to reach the ExceptionOS API. Make sure the backend is running.
        </section>
      </main>
    );
  }

  const purchaseOrder = review.purchase_order;
  const correctionOptions: CorrectionOption[] = [
    { label: "Customer", path: "customer", value: purchaseOrder.customer, rememberable: true },
    { label: "Ship to", path: "ship_to", value: purchaseOrder.ship_to, rememberable: true },
    ...purchaseOrder.items.flatMap((item, index) => [
      { label: `Item ${index + 1} SKU`, path: `items[${index}].sku`, value: item.sku, rememberable: true },
      { label: `Item ${index + 1} quantity`, path: `items[${index}].quantity`, value: String(item.quantity), rememberable: false },
      { label: `Item ${index + 1} unit price`, path: `items[${index}].unit_price`, value: String(item.unit_price), rememberable: false },
    ]),
  ];
  const measuredMs = (review.events ?? []).reduce((total, event) => {
    const duration = event.details.duration_ms;
    return total + (typeof duration === "number" ? duration : 0);
  }, 0);

  return (
    <main>
      <Link className="backLink" href="/">← Pending reviews</Link>

      <header className="detailHeader">
        <div>
          <p className="eyebrow">{purchaseOrder.po_number}</p>
          <h1>{purchaseOrder.customer}</h1>
        </div>
        <span className="status">{review.status}</span>
      </header>

      <section className="detailSection">
        <h2>Purchase order</h2>
        <p className="shipTo">Ship to: {purchaseOrder.ship_to}</p>
        <div className="orderMetadata">
          {purchaseOrder.po_date && <p>PO date: {purchaseOrder.po_date}</p>}
          {purchaseOrder.requested_delivery_date && (
            <p>Requested delivery: {purchaseOrder.requested_delivery_date}</p>
          )}
          {purchaseOrder.currency && <p>Currency: {purchaseOrder.currency}</p>}
        </div>

        {review.source_document_id && (
          <SourceLookup
            context={purchaseOrder.customer}
            documentId={review.source_document_id}
            fieldPath="ship_to"
            value={purchaseOrder.ship_to}
          />
        )}

        <ul className="itemList">
          {purchaseOrder.items.map((item, index) => (
            <li key={`${item.sku}-${index}`}>
              <strong>{item.sku}</strong>
              {item.description && <span>{item.description}</span>}
              <span>Quantity: {item.quantity}</span>
              <span>PO price: ${item.unit_price}</span>
              {item.line_total !== undefined && item.line_total !== null && (
                <span>Line total: {item.line_total}</span>
              )}
              {item.decoration_requirements?.map((requirement) => (
                <span key={requirement}>Decoration: {requirement}</span>
              ))}
              {review.source_document_id && (
                <SourceLookup
                  context={`${item.sku} ${item.description ?? ""}`}
                  documentId={review.source_document_id}
                  fieldPath={`items[${index}].quantity`}
                  value={item.quantity}
                />
              )}
            </li>
          ))}
        </ul>

        <div className="financialSummary">
          {(["subtotal", "discount", "tax", "freight", "total"] as const).map(
            (field) => purchaseOrder[field] !== undefined && purchaseOrder[field] !== null ? (
              <div key={field}>
                <span>{formatReason(field)}</span>
                <strong>{purchaseOrder[field]}</strong>
                {review.source_document_id && (
                  <SourceLookup
                    context={purchaseOrder.po_number}
                    documentId={review.source_document_id}
                    fieldPath={field}
                    value={purchaseOrder[field] as string | number}
                  />
                )}
              </div>
            ) : null,
          )}
        </div>
      </section>

      <section className="detailSection">
        <h2>Issues</h2>
        <div className="issueList">
          {review.issues.map((issue, index) => (
            <article className="issueCard" key={`${issue.reason}-${index}`}>
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
          ))}
        </div>
      </section>

      {review.recommendations && review.recommendations.length > 0 && (
        <section className="detailSection recommendations">
          <p className="eyebrow">Safe guidance</p>
          <h2>Recommended next actions</h2>
          <ul>
            {review.recommendations.map((recommendation) => (
              <li key={recommendation}>{recommendation}</li>
            ))}
          </ul>
          <p>Recommendations are limited to routine operational issues. A person still makes the decision.</p>
        </section>
      )}

      {review.status === "pending" && (
        <section className="detailSection">
          <p className="eyebrow">Human correction</p>
          <h2>Correct extracted data</h2>
          <CorrectionForm options={correctionOptions} reviewId={review.review_id} />
        </section>
      )}

      <section className="detailSection">
        <div className="auditHeading">
          <div>
            <p className="eyebrow">Measured workflow</p>
            <h2>Audit trail</h2>
          </div>
          {measuredMs > 0 && <strong>{(measuredMs / 1000).toFixed(2)} sec automated processing</strong>}
        </div>
        <ol className="auditTrail">
          {(review.events ?? []).map((event, index) => (
            <li key={`${event.event}-${index}`}>
              <strong>{formatReason(event.event)}</strong>
              {typeof event.details.duration_ms === "number" && (
                <span>{event.details.duration_ms} ms elapsed</span>
              )}
            </li>
          ))}
        </ol>
      </section>

      <section className="detailSection">
        <h2>Decision</h2>
        {review.status === "pending" ? (
          <>
            <p className="decisionHelp">
              Approval creates the ERP order. Rejection closes the review without creating one.
            </p>
            <DecisionForm reviewId={review.review_id} />
          </>
        ) : (
          <p className="decisionResult">
            This review was {review.status}.
            {review.erp_order_id && ` ERP order: ${review.erp_order_id}.`}
          </p>
        )}
      </section>
    </main>
  );
}
