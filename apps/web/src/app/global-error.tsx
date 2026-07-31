"use client";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="es">
      <body
        style={{
          font: "15px/1.5 system-ui, -apple-system, sans-serif",
          background: "#fafafa",
          color: "#111",
          display: "grid",
          placeItems: "center",
          minHeight: "100vh",
          margin: 0,
          padding: "1.5rem",
        }}
      >
        <div style={{ maxWidth: "28rem", width: "100%", textAlign: "center", padding: "2rem" }}>
          <h1 style={{ fontSize: "1.25rem", margin: "0 0 0.5rem" }}>
            No pudimos cargar esta página
          </h1>
          <p style={{ color: "#4b5563", margin: "0 0 1.5rem" }}>
            Algo falló de nuestro lado. Puedes reintentar o volver al inicio.
          </p>
          <div
            style={{ display: "flex", gap: "0.5rem", justifyContent: "center", flexWrap: "wrap" }}
          >
            <button
              onClick={() => reset()}
              style={{
                padding: "0.5rem 1rem",
                borderRadius: "0.375rem",
                font: "inherit",
                cursor: "pointer",
                border: "1px solid transparent",
                background: "#111",
                color: "#fff",
              }}
            >
              Reintentar
            </button>
            {/* eslint-disable-next-line @next/next/no-html-link-for-pages -- último recurso, fuera del árbol del router */}
            <a
              href="/"
              style={{
                padding: "0.5rem 1rem",
                borderRadius: "0.375rem",
                font: "inherit",
                textDecoration: "none",
                background: "#fff",
                color: "#111",
                border: "1px solid #d1d5db",
              }}
            >
              Ir al inicio
            </a>
          </div>
        </div>
      </body>
    </html>
  );
}
