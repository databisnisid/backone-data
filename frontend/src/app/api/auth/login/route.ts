import { NextResponse } from "next/server";

import { BACKONE_API_URL } from "@/config/backend";
import { setAuthCookies } from "@/lib/auth";

export async function POST(req: Request) {
  let body: { username?: string; password?: string; next?: string; remember?: boolean };

  // Accept both JSON and form-encoded bodies (form-encoded enables a pure
  // server-rendered HTML <form> with visible inputs that submits without JS).
  const contentType = req.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    try {
      body = (await req.json()) as { username?: string; password?: string; remember?: boolean };
    } catch {
      return NextResponse.json({ detail: "Invalid JSON body." }, { status: 400 });
    }
  } else {
    const formData = await req.formData();
    body = {
      username: formData.get("username")?.toString(),
      password: formData.get("password")?.toString(),
      next: formData.get("next")?.toString(),
    };
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
  await setAuthCookies(data.access, data.refresh, body.remember);

  // For HTML form submissions, redirect to dashboard (next param or /).
  // For JSON/API calls, return JSON.
  if (contentType.includes("application/json")) {
    return NextResponse.json({ ok: true });
  }

  // Use path-only Location header so the browser resolves it against the real
  // public origin (req.url may contain the internal container hostname in
  // the standalone build). 303 See Other is the correct status for a
  // successful POST form submission.
  const next = body.next ?? "/";
  const response = new NextResponse(null, { status: 303 });
  response.headers.set("Location", next);
  return response;
}
