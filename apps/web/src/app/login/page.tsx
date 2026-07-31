import { Suspense } from "react";
import { LoginForm } from "./login-form";

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="grid min-h-screen place-items-center bg-background px-4 text-center">
          <div>
            <span className="wordmark">Nexo AI</span>
            <p className="mt-3 text-sm text-muted-foreground">Preparando inicio de sesión…</p>
          </div>
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
