"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(pathname === "/login");
  useEffect(() => {
    if (pathname === "/login") { setReady(true); return; }
    fetch("/api/auth/session", { cache: "no-store" })
      .then((response) => response.json())
      .then((data) => { if (data.authenticated) setReady(true); else router.replace("/login"); })
      .catch(() => router.replace("/login"));
  }, [pathname, router]);
  if (!ready) return <div className="auth-loading">Verificando sesión…</div>;
  return children;
}
