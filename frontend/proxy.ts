import { NextRequest, NextResponse } from "next/server";

import {
  demoAuthEnabled,
  SESSION_COOKIE,
  verifySessionToken,
} from "./lib/session-token";


export async function proxy(request: NextRequest) {
  if (!demoAuthEnabled()) return NextResponse.next();

  const path = request.nextUrl.pathname;

  if (path === "/api/health") return NextResponse.next();

  const session = await verifySessionToken(
    request.cookies.get(SESSION_COOKIE)?.value,
  );

  if (path === "/login") {
    return session
      ? NextResponse.redirect(new URL("/", request.url))
      : NextResponse.next();
  }

  if (!session) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", `${path}${request.nextUrl.search}`);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
