import { timingSafeEqual } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";
import { createSessionToken, sessionCookieName } from "@/lib/session";

export async function POST(request: NextRequest) {
  const expected = process.env.DASHBOARD_PASSWORD;
  if (!expected || !process.env.SESSION_SECRET || process.env.SESSION_SECRET.length < 32) {
    return NextResponse.json({ detail: "Dashboard authentication is not configured" }, { status: 503 });
  }
  let submitted = "";
  try { submitted = String((await request.json()).password || ""); } catch { /* malformed request */ }
  const suppliedBytes = Buffer.from(submitted);
  const expectedBytes = Buffer.from(expected);
  const valid = suppliedBytes.length === expectedBytes.length && timingSafeEqual(suppliedBytes, expectedBytes);
  if (!valid) return NextResponse.json({ detail: "Invalid password" }, { status: 401 });
  const token = createSessionToken();
  if (!token) return NextResponse.json({ detail: "Dashboard authentication is not configured" }, { status: 503 });
  const response = NextResponse.json({ status: "ok" });
  response.cookies.set(sessionCookieName, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: 8 * 60 * 60,
  });
  return response;
}
