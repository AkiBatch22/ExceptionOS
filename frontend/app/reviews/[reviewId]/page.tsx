import Link from "next/link";
import { notFound } from "next/navigation";

import DecisionForm from "./decision-form";

type PurchaseOrderItem = {
  sku: string;
  quantity: number;
  unit_price: number | string;
};

type ReviewIssue = {
  reason: string;
  customer?: string;
  sku?: string;
  requested?: number;
  available?: number | null;
  po_price?: number | string;
  erp_price?: number | string;
};

type Review = {
  review_id: string;
  status: "pending" | "approved" | "rejected";
  purchase_order: {
    po_number: string;
    customer: string;
    items: PurchaseOrderItem[];
    ship_to: string;
  };
  issues: ReviewIssue[];
  erp_order_id?: string | null;
};

async function getReview(reviewId: string): Promise<Review | null> {
  const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";
  let response: Response;

  try {
    response = await fetch(`${apiUrl}/reviews/${encodeURIComponent(reviewId)}`, {
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

        <ul className="itemList">
          {purchaseOrder.items.map((item) => (
            <li key={item.sku}>
              <strong>{item.sku}</strong>
              <span>Quantity: {item.quantity}</span>
              <span>PO price: ${item.unit_price}</span>
            </li>
          ))}
        </ul>
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
            </article>
          ))}
        </div>
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
