"use client";

/**
 * Confirmación de una acción pendiente (`RunResult.available_actions` cuando
 * el run está en `waiting_confirmation`), con costo/dependencias/tiempo
 * estimado si el run trae un `Estimate`. Compone las cards ya existentes en
 * vez de inventar una nueva superficie visual.
 */

import type { A2UIAction, Estimate } from "@/generated/contracts";
import type { Money } from "@/generated/contracts/estimate";
import { ConfirmCard } from "./actions";
import { CostCard } from "./cards";

function formatMoney(money?: Money | null): string {
  if (!money) return "—";
  return `${(money.amount_minor / 100).toFixed(2)} ${money.currency}`;
}

export function PendingActionCard({
  action,
  estimate,
  pending,
  onConfirm,
  onCancel,
}: {
  action: A2UIAction;
  estimate?: Estimate | null;
  pending?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const detalles = [
    `Herramienta: ${action.tool_name}`,
    ...(estimate?.steps ?? []).flatMap((step) => {
      const dependencias = step.depends_on?.length
        ? ` · depende de ${step.depends_on.join(", ")}`
        : "";
      const duracion = step.duration_days != null ? ` · ${step.duration_days} día(s)` : "";
      return [`${step.title}${dependencias}${duracion}`];
    }),
  ];

  return (
    <div className="space-y-3">
      <ConfirmCard
        titulo={action.label}
        detalles={detalles}
        pending={pending}
        confirmLabel="Confirmar"
        onConfirmar={onConfirm}
        onCancelar={onCancel}
      />
      {estimate?.steps?.length ? (
        <CostCard
          items={estimate.steps
            .filter((step) => step.cost)
            .map((step) => ({ concepto: step.title, monto: formatMoney(step.cost) }))}
          total={formatMoney(estimate.total_cost)}
        />
      ) : null}
    </div>
  );
}
