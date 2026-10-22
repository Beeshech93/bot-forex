import { createHmac, timingSafeEqual } from "node:crypto";

const cookieName = "ssfx_session";
const sessionHours = 8;

function signature(expiry: string, secret: string): string {
  return createHmac("sha256", secret).update(expiry).digest("base64url");
}

export function createSessionToken(): string | null {
  const secret = process.env.SESSION_SECRET;
  if (!secret || secret.length < 32) return null;
  const expiry = String(Date.now() + sessionHours * 60 * 60 * 1000);
  return `${expiry}.${signature(expiry, secret)}`;
}

export function verifySessionToken(token: string | undefined): boolean {
  const secret = process.env.SESSION_SECRET;
  if (!secret || secret.length < 32 || !token) return false;
  const [expiry, provided, ...extra] = token.split(".");
  if (!expiry || !provided || extra.length || !/^\d{13}$/.test(expiry) || Number(expiry) <= Date.now()) return false;
  const expected = signature(expiry, secret);
  const expectedBytes = Buffer.from(expected);
  const providedBytes = Buffer.from(provided);
  return expectedBytes.length === providedBytes.length && timingSafeEqual(expectedBytes, providedBytes);
}

export const sessionCookieName = cookieName;
