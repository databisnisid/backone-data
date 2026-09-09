export const BACKONE_API_URL = process.env.BACKONE_API_URL ?? "http://localhost:8009";

export const COOKIE_ACCESS = "bo_access";
export const COOKIE_REFRESH = "bo_refresh";

export const ACCESS_MAX_AGE = 30 * 60; // matches SIMPLE_JWT access lifetime
export const REFRESH_MAX_AGE = 7 * 24 * 60 * 60; // matches SIMPLE_JWT refresh lifetime
