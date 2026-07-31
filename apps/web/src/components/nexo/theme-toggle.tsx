"use client";

import { useSyncExternalStore } from "react";
import { Moon, Sun } from "lucide-react";

// El tema vive en el DOM: el script inline de app/layout.tsx pone la clase antes de
// hidratar. Aquí solo lo leemos como fuente externa, sin duplicarlo en estado de React.
function subscribe(onChange: () => void) {
  const observer = new MutationObserver(onChange);
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
  return () => observer.disconnect();
}

const getSnapshot = () => document.documentElement.classList.contains("dark");

// En el servidor no hay clase, así que el HTML sale siempre en claro y React reconcilia
// tras hidratar si la preferencia guardada era oscura.
const getServerSnapshot = () => false;

export function ThemeToggle() {
  const dark = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  function toggle() {
    const next = !dark;
    document.documentElement.classList.toggle("dark", next);
    window.localStorage.setItem("nexo-theme", next ? "dark" : "light");
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={dark ? "Activar modo claro" : "Activar modo oscuro"}
      className="inline-flex size-9 shrink-0 items-center justify-center rounded-full border border-border bg-card text-muted-foreground transition-colors hover:text-foreground"
    >
      {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
    </button>
  );
}
