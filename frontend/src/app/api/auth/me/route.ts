import { NextResponse } from "next/server";

import { backendFetch, clearAuthCookies } from "@/lib/auth";

export async function GET() {
  const res = await backendFetch("/api/auth/me/");
  const data = await res.json();
  // V82: an expired `bo_access` with no refresh token used to survive every
  // request, so the login redirect bounced straight back here (proxy.ts) and
  // the page sat on "Loading session..." forever. Drop the dead cookies.
  if (res.status === 401) await clearAuthCookies();
  return NextResponse.json(data, { status: res.status });
}
