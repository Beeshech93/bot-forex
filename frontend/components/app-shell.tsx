"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  if (pathname === "/login") return <>{children}</>;
  return <div className="app-frame"><Sidebar /><main className="main-content">{children}</main></div>;
}
