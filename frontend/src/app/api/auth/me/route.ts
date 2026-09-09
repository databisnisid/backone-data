import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/auth";

export async function GET() {
  const res = await backendFetch("/api/auth/me/");
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
