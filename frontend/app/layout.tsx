import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "ExceptionOS",
  description: "Purchase-order exception review",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav className="appNav" aria-label="Primary navigation">
          <Link className="appBrand" href="/">ExceptionOS</Link>
          <div>
            <Link href="/">Dashboard</Link>
            <Link href="/purchase-orders/new">New purchase order</Link>
            <Link href="/orders">Created orders</Link>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
