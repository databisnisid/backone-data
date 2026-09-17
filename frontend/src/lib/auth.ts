import { cookies } from "next/headers";

import { ACCESS_MAX_AGE, BACKONE_API_URL, COOKIE_ACCESS, COOKIE_REFRESH, REFRESH_MAX_AGE } from "@/config/backend";

function baseCookieOptions() {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
  } as const;
}

export async function setAuthCookies(access: string, refresh?: string, remember?: boolean) {
  const store = await cookies();
  const accessMaxAge = remember ? 30 * 24 * 60 * 60 : ACCESS_MAX_AGE;
  const refreshMaxAge = remember ? 30 * 24 * 60 * 60 : REFRESH_MAX_AGE;
  store.set(COOKIE_ACCESS, access, {
    ...baseCookieOptions(),
    maxAge: accessMaxAge,
  });
  if (refresh) {
    store.set(COOKIE_REFRESH, refresh, {
      ...baseCookieOptions(),
      maxAge: refreshMaxAge,
    });
  }
}

export async function clearAuthCookies() {
  const store = await cookies();
  store.delete(COOKIE_ACCESS);
  store.delete(COOKIE_REFRESH);
}

export async function getAccessToken() {
  return (await cookies()).get(COOKIE_ACCESS)?.value ?? null;
}

/** Exchange a refresh token with the Django backend for a new access+refresh pair. */
export async function rotateTokens(): Promise<boolean> {
  const store = await cookies();
  const refresh = store.get(COOKIE_REFRESH)?.value;
  if (!refresh) return false;

  const res = await fetch(`${BACKONE_API_URL}/api/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
    cache: "no-store",
  });
  if (!res.ok) {
    await clearAuthCookies();
    return false;
  }
  const data = (await res.json()) as { access: string; refresh?: string };
  await setAuthCookies(data.access, data.refresh ?? refresh);
  return true;
}

/** Authenticated fetch to Django with silent one-shot refresh on 401. */
export async function backendFetch(path: string, init: RequestInit = {}): Promise<Response> {
  let access = await getAccessToken();
  const headers = new Headers(init.headers);
  if (access) headers.set("Authorization", `Bearer ${access}`);

  let res = await fetch(`${BACKONE_API_URL}${path}`, { ...init, headers, cache: "no-store" });

  if (res.status === 401 && (await rotateTokens())) {
    access = await getAccessToken();
    if (access) headers.set("Authorization", `Bearer ${access}`);
    res = await fetch(`${BACKONE_API_URL}${path}`, { ...init, headers, cache: "no-store" });
  }
  return res;
}

/** `/api/auth/me/` flags used by server-side route guards (V41/V51). Fails closed to no-groups. */
export async function getMeAccess(): Promise<{ isSuperuser: boolean; groups: string[] }> {
  try {
    const res = await backendFetch("/api/auth/me/");
    if (!res.ok) return { isSuperuser: false, groups: [] };
    const data = (await res.json()) as { is_superuser?: boolean; groups?: string[] };
    return { isSuperuser: data.is_superuser ?? false, groups: data.groups ?? [] };
  } catch {
    return { isSuperuser: false, groups: [] };
  }
}
