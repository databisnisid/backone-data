import { NextResponse } from "next/server";

import { BACKONE_API_URL } from "@/config/backend";
import { setAuthCookies } from "@/lib/auth";

export async function POST(req: Request) {
  let body: { username?: string; password?: string };
  try {
    body = (await req.json()) as { username?: string; password?: string };
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body." }, { status: 400 });
  }
  if (!body.username || !body.password) {
    return NextResponse.json({ detail: "username and password required." }, { status: 400 });
  }

  const res = await fetch(`${BACKONE_API_URL}/api/auth/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: body.username, password: body.password }),
    cache: "no-store",
  });
  const data = (await res.json()) as { access?: string; refresh?: string; detail?: string };

  if (!res.ok || !data.access) {
    return NextResponse.json({ detail: data.detail ?? "Login failed." }, { status: res.status });
  }
  await setAuthCookies(data.access, data.refresh);
  return NextResponse.json({ ok: true });
}
