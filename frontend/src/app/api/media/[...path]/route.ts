import { NextResponse } from "next/server";

import { BACKONE_API_URL } from "@/config/backend";

type Ctx = { params: Promise<{ path: string[] }> };

export async function GET(req: Request, ctx: Ctx) {
  const { path } = await ctx.params;
  const target = `${BACKONE_API_URL}/media/${path.join("/")}${new URL(req.url).search}`;

  const res = await fetch(target, { cache: "no-store" });
  const headers = new Headers(res.headers);
  headers.delete("set-cookie");

  const data = await res.arrayBuffer();
  return new NextResponse(data, { status: res.status, headers });
}
