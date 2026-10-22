"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setLoading(true); setError("");
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      if (!response.ok) { const data = await response.json(); throw new Error(data.detail || "No se pudo iniciar sesión."); }
      router.replace("/");
    } catch (e) { setError(e instanceof Error ? e.message : "No se pudo iniciar sesión."); }
    finally { setLoading(false); }
  }
  return <div className="login-wrap"><form className="panel login-panel" onSubmit={submit}>
    <div className="brand-mark">S</div><div className="eyebrow" style={{ marginTop: 20 }}>Smart Signals FX</div>
    <h1>Iniciar sesión</h1><p className="muted">Ingresa la contraseña del dashboard configurada en el servidor.</p>
    <label className="form-field" style={{ marginTop: 22 }}>Contraseña<input className="field" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} /></label>
    {error && <p className="error">{error}</p>}
    <button className="button" style={{ width: "100%", marginTop: 16 }} disabled={loading}>{loading ? "Verificando…" : "Continuar"}</button>
    <p className="footnote" style={{ marginTop: 18 }}>Acceso protegido con una cookie de sesión HTTP-only.</p>
  </form></div>;
}
