"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

const navigation = [
  ["Dashboard", "/"],
  ["Mercado", "/market"],
  ["Señales", "/signals"],
  ["Backtesting", "/backtesting"],
  ["Configuración", "/settings"],
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  async function signOut() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.replace("/login");
  }
  return (
    <aside className="sidebar">
      <Link className="brand" href="/">
        <span className="brand-mark">S</span>
        <span>Smart Signals <b>FX</b></span>
      </Link>
      <div className="nav-label">Workspace</div>
      <nav aria-label="Principal">
        {navigation.map(([label, href], index) => (
          <Link className={`nav-link ${pathname === href ? "nav-active" : ""}`} href={href} key={href}>
            <span className="nav-icon">{["⌂", "◷", "↗", "▥", "⚙"][index]}</span>{label}
          </Link>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <div className="readonly-pill"><span className="dot" /> Read-only mode</div>
        <p>Las señales son referencias analíticas. No se ejecutan operaciones.</p>
        <button className="signout" onClick={signOut}>Cerrar sesión ↗</button>
      </div>
    </aside>
  );
}
