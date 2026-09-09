import { type NextRequest, NextResponse } from "next/server";

const PROTECTED = ["/sites", "/quota", "/networks", "/organizations", "/dashboard"];

export function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const hasAccess = req.cookies.has("bo_access");

  // Authenticated user hitting login → straight to sites
  if (pathname.startsWith("/auth/") && hasAccess) {
    return NextResponse.redirect(new URL("/sites", req.url));
  }

  // Unauthenticated user on a protected page → login
  if (!hasAccess && (pathname === "/" || PROTECTED.some((p) => pathname === p || pathname.startsWith(`${p}/`)))) {
    const url = new URL("/auth/v1/login", req.url);
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};