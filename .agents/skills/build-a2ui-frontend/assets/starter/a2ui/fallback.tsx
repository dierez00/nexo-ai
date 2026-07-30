"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

type A2UIFallbackProps = {
  onRetry?: () => void;
};

export function A2UIFallback({ onRetry }: A2UIFallbackProps) {
  return (
    <Alert
      role="status"
      className="border-[hsl(var(--warning)/0.4)] bg-[hsl(var(--warning)/0.05)]"
    >
      <AlertTitle>No pudimos mostrar esta información</AlertTitle>
      <AlertDescription className="mt-2">
        Puedes intentarlo de nuevo o continuar con la explicación en texto.
      </AlertDescription>
      {onRetry ? (
        <Button className="mt-4" variant="outline" onClick={onRetry}>
          Intentar de nuevo
        </Button>
      ) : null}
    </Alert>
  );
}

type A2UIBoundaryProps = {
  children: ReactNode;
  onRetry?: () => void;
  onError?: (error: Error, info: ErrorInfo) => void;
};

type A2UIBoundaryState = {
  failed: boolean;
};

export class A2UIBoundary extends Component<
  A2UIBoundaryProps,
  A2UIBoundaryState
> {
  state: A2UIBoundaryState = { failed: false };

  static getDerivedStateFromError(): A2UIBoundaryState {
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
      return <A2UIFallback onRetry={this.retry} />;
    }
    return this.props.children;
  }
}
