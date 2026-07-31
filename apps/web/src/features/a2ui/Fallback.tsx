"use client";

/**
 * Fallback seguro para una superficie que no pudo mostrarse.
 *
 * Muestra un título estable, una explicación breve sin detalles internos, una
 * acción para continuar y el `trace_id` si la política lo permite. **Nunca**
 * muestra el payload rechazado: un mensaje que incluye lo que falló filtra
 * exactamente lo que un atacante quería ver.
 *
 * Una validación fallida es un problema nuestro; hacérselo pagar a quien
 * preguntaba con una pantalla en blanco es la peor forma de resolverlo, así
 * que el fallback nunca queda vacío.
 */

import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

export function A2UIFallback({
  traceId,
  onRetry,
  textAlternative,
}: {
  traceId?: string;
  onRetry?: () => void;
  /** Equivalente textual, cuando el servidor lo envió junto a la superficie. */
  textAlternative?: string;
}) {
  return (
    <div role="status" className="rounded-xl border border-warning/40 bg-warning/10 p-4">
      <div className="flex items-center gap-2">
        <AlertTriangle className="size-4 text-warning" aria-hidden />
        <p className="text-sm font-semibold">No pudimos mostrar esta información</p>
      </div>
      <p className="mt-2 text-sm text-muted-foreground">
        La respuesta llegó en un formato que no pudimos verificar. Tu conversación quedó guardada y
        no se realizó ninguna operación.
      </p>

      {textAlternative ? (
        <div className="mt-3 rounded-lg border border-border bg-card p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Versión en texto
          </p>
          <p className="mt-1 whitespace-pre-line text-sm">{textAlternative}</p>
        </div>
      ) : null}

      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <RefreshCw className="size-4" aria-hidden /> Intentar de nuevo
        </button>
      ) : null}

      {traceId ? (
        <p className="mono mt-3 text-xs text-muted-foreground">trace_id: {traceId}</p>
      ) : null}
    </div>
  );
}

type BoundaryProps = {
  children: ReactNode;
  traceId?: string;
  onRetry?: () => void;
  onError?: (error: Error, info: ErrorInfo) => void;
};

/**
 * Última red de seguridad: si un adaptador lanza al dibujar, la superficie
 * entera cae al fallback en vez de romper la página del chat.
 */
export class A2UIBoundary extends Component<BoundaryProps, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    this.props.onError?.(error, info);
  }

  private retry = () => {
    this.setState({ failed: false });
    this.props.onRetry?.();
  };

  render() {
    if (this.state.failed) {
      return <A2UIFallback traceId={this.props.traceId} onRetry={this.retry} />;
    }
    return this.props.children;
  }
}
