import Link from "next/link";
import { notFound } from "next/navigation";

import { requireSession } from "../../../lib/auth";
import { apiFetch } from "../../../lib/api-fetch";

type CreatedOrder = {
  erp_order_id: string;
  po_number: string;
  purchase_order: {
    customer: string;
    ship_to: string;
    po_date?: string | null;
    requested_delivery_date?: string | null;
    currency?: string | null;
    subtotal?: number | string | null;
    discount?: number | string | null;
    tax?: number | string | null;
    freight?: number | string | null;
    total?: number | string | null;
    items: Array<{
      sku: string;
      description?: string | null;
      quantity: number;
      unit_price: number | string;
      line_total?: number | string | null;
      decoration_requirements?: string[] | null;
    }>;
  };
  events: Array<{
    event: string;
    details: Record<string, unknown>;
    created_at?: string;
  }>;
};

async function getOrder(erpOrderId: string): Promise<CreatedOrder | null> {
  const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";
  let response: Response;
  try {
    response = await apiFetch(
      `${apiUrl}/erp-orders/${encodeURIComponent(erpOrderId)}`,
      { cache: "no-store" },
    );
  } catch {
    return null;
  }
  if (response.status === 404) notFound();
  if (!response.ok) return null;
  return (await response.json()) as CreatedOrder;
}

function label(value: string) {
  return value.replaceAll("_", " ");
}

export default async function CreatedOrderPage({
  params,
}: {
  params: Promise<{ erpOrderId: string }>;
}) {
  await requireSession();
  const { erpOrderId } = await params;
  const order = await getOrder(erpOrderId);
  if (order === null) {
    return <main><div className="message error">Unable to load the created order.</div></main>;
  }
  const po = order.purchase_order;

  return (
    <main>
      <Link className="backLink" href="/orders">← Created orders</Link>
      <header className="detailHeader">
        <div>
          <p className="eyebrow">{order.erp_order_id}</p>
          <h1>{po.customer}</h1>
          <p className="subtitle">Source purchase order: {order.po_number}</p>
        </div>
        <span className="status">created</span>
      </header>

      <section className="detailSection">
        <h2>Order details</h2>
        <p className="shipTo">Ship to: {po.ship_to}</p>
        <div className="orderMetadata">
          {po.po_date && <p>PO date: {po.po_date}</p>}
          {po.requested_delivery_date && <p>Requested delivery: {po.requested_delivery_date}</p>}
          {po.currency && <p>Currency: {po.currency}</p>}
        </div>
        <ul className="itemList">
          {po.items.map((item, index) => (
            <li key={`${item.sku}-${index}`}>
              <strong>{item.sku}</strong>
              {item.description && <span>{item.description}</span>}
              <span>Quantity: {item.quantity}</span>
              <span>Unit price: {item.unit_price}</span>
              {item.line_total != null && <span>Line total: {item.line_total}</span>}
              {item.decoration_requirements?.map((requirement) => (
                <span key={requirement}>Decoration: {requirement}</span>
              ))}
            </li>
          ))}
        </ul>
        <div className="financialSummary">
          {(["subtotal", "discount", "tax", "freight", "total"] as const).map(
            (field) => po[field] != null ? (
              <div key={field}><span>{label(field)}</span><strong>{po[field]}</strong></div>
            ) : null,
          )}
        </div>
      </section>

      <section className="detailSection">
        <p className="eyebrow">Traceability</p>
        <h2>Audit trail</h2>
        <ol className="auditTrail">
          {order.events.map((event, index) => (
            <li key={`${event.event}-${index}`}>
              <strong>{label(event.event)}</strong>
              {typeof event.details.duration_ms === "number" && (
                <span>{event.details.duration_ms} ms elapsed</span>
              )}
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}
