import Link from "next/link";

type OrderSummary = {
  erp_order_id: string;
  po_number: string;
  purchase_order: {
    customer: string;
    currency?: string | null;
    total?: number | string | null;
    items: Array<{ quantity: number }>;
  };
};

async function getOrders(): Promise<OrderSummary[] | null> {
  const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${apiUrl}/erp-orders`, { cache: "no-store" });
    if (!response.ok) return null;
    return ((await response.json()) as { orders: OrderSummary[] }).orders;
  } catch {
    return null;
  }
}

export default async function OrdersPage() {
  const orders = await getOrders();

  return (
    <main>
      <header>
        <p className="eyebrow">ERP output</p>
        <h1>Created orders</h1>
        <p className="subtitle">Purchase orders that passed assessment or received human approval.</p>
      </header>

      {orders === null ? (
        <div className="message error">Unable to load created orders.</div>
      ) : orders.length === 0 ? (
        <div className="message">No ERP orders have been created yet.</div>
      ) : (
        <div className="reviewList">
          {orders.map((order) => {
            const units = order.purchase_order.items.reduce(
              (total, item) => total + item.quantity,
              0,
            );
            return (
              <Link
                className="reviewLink"
                href={`/orders/${encodeURIComponent(order.erp_order_id)}`}
                key={order.erp_order_id}
              >
                <article className="reviewCard">
                  <div>
                    <p className="poNumber">{order.po_number}</p>
                    <h2>{order.purchase_order.customer}</h2>
                    <p className="cardDetail">{order.erp_order_id}</p>
                  </div>
                  <div className="reviewMeta">
                    <span>{units} unit{units === 1 ? "" : "s"}</span>
                    {order.purchase_order.total != null && (
                      <span>{order.purchase_order.currency ?? ""} {order.purchase_order.total}</span>
                    )}
                    <span className="status">created</span>
                  </div>
                </article>
              </Link>
            );
          })}
        </div>
      )}
    </main>
  );
}
