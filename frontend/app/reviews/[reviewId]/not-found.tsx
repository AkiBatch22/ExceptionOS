import Link from "next/link";

export default function ReviewNotFound() {
  return (
    <main>
      <Link className="backLink" href="/">← Pending reviews</Link>
      <section className="message">
        This review does not exist or is no longer available.
      </section>
    </main>
  );
}
