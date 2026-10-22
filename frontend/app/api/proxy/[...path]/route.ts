import { NextRequest, NextResponse } from "next/server";
import { sessionCookieName, verifySessionToken } from "@/lib/session";

const allowed = new Set([
  "health",
  "api/v1/terminal",
  "api/v1/symbols",
  "api/v1/candles",
  "api/v1/indicators",
  "api/v1/metrics",
  "api/v1/signals",
  "api/v1/signals/history",
  "api/v1/backtest",
  "api/v1/metrics",
  "api/v1/config",
]);

async function forward(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const route = path.join("/");
  if (route !== "health" && !verifySessionToken(request.cookies.get(sessionCookieName)?.value)) {
    return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
  }
  const allowedBacktestResult = /^api\/v1\/backtest\/[0-9a-f-]{36}$/i.test(route);
  if (!allowed.has(route) && !allowedBacktestResult) {
    return NextResponse.json({ detail: "Route is not available through this proxy" }, { status: 404 });
  }
  if (request.method !== "GET" &&
      !(route === "api/v1/backtest" && request.method === "POST") &&
      !(route === "api/v1/config" && request.method === "PUT")) {
    return NextResponse.json({ detail: "Method is not allowed" }, { status: 405 });
  }
  const base = process.env.BACKEND_API_URL?.replace(/\/$/, "");
  if (!base) return NextResponse.json({ detail: "Backend API is not configured" }, { status: 503 });
  if (process.env.NODE_ENV === "production" && !base.startsWith("https://")) {
    return NextResponse.json({ detail: "Backend API must use HTTPS" }, { status: 503 });
  }
  const target = new URL(`${base}/${route}`);
  target.search = request.nextUrl.search;
  const headers = new Headers();
  const token = process.env.BACKEND_API_TOKEN;
  if (route !== "health" && token) headers.set("Authorization", `Bearer ${token}`);
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);
  try {
    const response = await fetch(target, {
      method: request.method,
      headers,
      body: request.method === "POST" ? await request.text() : undefined,
      cache: "no-store",
      signal: AbortSignal.timeout(12_000),
    });
    return new NextResponse(response.body, { status: response.status, headers: { "Content-Type": response.headers.get("content-type") || "application/json" } });
  } catch {
    return NextResponse.json({ detail: "Backend service is unavailable" }, { status: 503 });
  }
}

export const GET = forward;
export const POST = forward;
export const PUT = forward;
