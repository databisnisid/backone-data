import { NextResponse } from "next/server";

import { rotateTokens } from "@/lib/auth";

export async function POST() {
  const ok = await rotateTokens();
  return ok ? NextResponse.json({ ok: true }) : NextResponse.json({ ok: false }, { status: 401 });
}
