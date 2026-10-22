import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { sessionCookieName, verifySessionToken } from "@/lib/session";

export async function GET() {
  const token = (await cookies()).get(sessionCookieName)?.value;
  return NextResponse.json({ authenticated: verifySessionToken(token) });
}
