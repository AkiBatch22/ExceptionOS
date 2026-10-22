import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";

import "./globals.css";
import { getSession } from "../lib/auth";
import { logout } from "./login/actions";

export const metadata: Metadata = {
  title: "ExceptionOS",
  description: "Purchase-order exception review",
};

export default async function RootLayout({ children }: { children: ReactNode }) {
  const session = await getSession();
  return (
    <html lang="en">
      <body>
        {session && (
          <nav className="appNav" aria-label="Primary navigation">
            <Link className="appBrand" href="/">ExceptionOS</Link>
            <div>
              <Link href="/">Dashboard</Link>
              <Link href="/purchase-orders/new">New purchase order</Link>
              <Link href="/orders">Created orders</Link>
              <form action={logout}>
                <button className="navButton" type="submit">Log out</button>
              </form>
            </div>
          </nav>
        )}
        {children}
      </body>
    </html>
  );
}
