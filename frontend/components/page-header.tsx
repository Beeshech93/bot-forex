export function PageHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description?: string }) {
  return (
    <header className="page-header">
      <div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{description && <p>{description}</p>}</div>
      <div className="header-date"><span className="dot" /> Datos en tiempo real al conectar MT5</div>
    </header>
  );
}
