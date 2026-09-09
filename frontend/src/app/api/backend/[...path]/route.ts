import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/auth";

type Ctx = { params: Promise<{ path: string[] }> };

async function proxy(req: Request, _ctx: Ctx, method: string): Promise<NextResponse> {
  const url = new URL(req.url);
  // Preserve the exact remainder (incl. trailing slash) after /api/backend
  const PREFIX = "/api/backend/";
  const target = `/api/${url.pathname.startsWith(PREFIX) ? url.pathname.slice(PREFIX.length) : ""}${url.search}`;

  const body = method === "GET" || method === "HEAD" ? undefined : await req.arrayBuffer();
  const headers = new Headers(req.headers);
  headers.delete("host");
  headers.delete("cookie");
  headers.delete("authorization");

  const res = await backendFetch(target, {
    method,
    headers,
    body,
  });

  const resHeaders = new Headers(res.headers);
  resHeaders.delete("set-cookie");
  const data = await res.arrayBuffer();
  return new NextResponse(data, { status: res.status, headers: resHeaders });
}

export async function GET(req: Request, ctx: Ctx) {
  return proxy(req, ctx, "GET");
}
export async function POST(req: Request, ctx: Ctx) {
  return proxy(req, ctx, "POST");
}
export async function PATCH(req: Request, ctx: Ctx) {
  return proxy(req, ctx, "PATCH");
}
export async function PUT(req: Request, ctx: Ctx) {
  return proxy(req, ctx, "PUT");
}
export async function DELETE(req: Request, ctx: Ctx) {
  return proxy(req, ctx, "DELETE");
}
