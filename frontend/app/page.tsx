import Link from "next/link";

type ReviewSummary = {
  review_id: string;
  po_number: string;
  customer: string;
  status: "pending";
  issue_count: number;
};

type EmailImportSummary = {
  message_id: string;
  sender: string;
  subject: string;
  attachment_name: string;
  po_number: string | null;
  customer: string | null;
  imported_at: string;
};

async function getPendingReviews(): Promise<ReviewSummary[] | null> {
  try {
    const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";
    const response = await fetch(`${apiUrl}/reviews`, { cache: "no-store" });

    if (!response.ok) {
      return null;
    }

    const data = (await response.json()) as { reviews: ReviewSummary[] };
    return data.reviews;
  } catch {
    return null;
  }
}

async function getEmailImports(): Promise<EmailImportSummary[] | null> {
  try {
    const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";
    const response = await fetch(`${apiUrl}/email-imports`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    const data = (await response.json()) as {
      imports: EmailImportSummary[];
    };
    return data.imports;
  } catch {
    return null;
  }
}

export default async function Home() {
  const [reviews, emailImports] = await Promise.all([
    getPendingReviews(),
    getEmailImports(),
  ]);

  return (
    <main>
      <header>
        <p className="eyebrow">ExceptionOS</p>
        <h1>Operations dashboard</h1>
        <p className="subtitle">Imported orders and human-review decisions.</p>
        <div className="headerActions">
          <Link className="primaryLink" href="/purchase-orders/new">
            Extract a purchase order
          </Link>
          <Link className="secondaryLink" href="/orders">
            View created orders
          </Link>
        </div>
      </header>

      <section className="dashboardSection">
        <h2 className="sectionHeading">Imported order drafts</h2>
        {emailImports === null ? (
          <div className="message error">Unable to load imported orders.</div>
        ) : emailImports.length === 0 ? (
          <div className="message">There are no imported order drafts.</div>
        ) : (
          <div className="reviewList">
            {emailImports.map((emailImport) => (
              <Link
                className="reviewLink"
                href={`/purchase-orders/new?message_id=${encodeURIComponent(emailImport.message_id)}`}
                key={emailImport.message_id}
              >
                <article className="reviewCard">
                  <div>
                    <p className="poNumber">{emailImport.po_number ?? "PO number missing"}</p>
                    <h2>{emailImport.customer ?? emailImport.subject}</h2>
                    <p className="cardDetail">From {emailImport.sender}</p>
                  </div>
                  <div className="reviewMeta">
                    <span>{emailImport.attachment_name}</span>
                    <span className="status">draft</span>
                  </div>
                </article>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section className="dashboardSection">
        <h2 className="sectionHeading">Pending reviews</h2>
        {reviews === null ? (
          <div className="message error">Unable to load pending reviews.</div>
        ) : reviews.length === 0 ? (
          <div className="message">There are no pending reviews.</div>
        ) : (
          <div className="reviewList">
            {reviews.map((review) => (
              <Link
                className="reviewLink"
                href={`/reviews/${encodeURIComponent(review.review_id)}`}
                key={review.review_id}
              >
                <article className="reviewCard">
                  <div>
                    <p className="poNumber">{review.po_number}</p>
                    <h2>{review.customer}</h2>
                  </div>
                  <div className="reviewMeta">
                    <span>{review.issue_count} issue{review.issue_count === 1 ? "" : "s"}</span>
                    <span className="status">{review.status}</span>
                  </div>
                </article>
              </Link>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
