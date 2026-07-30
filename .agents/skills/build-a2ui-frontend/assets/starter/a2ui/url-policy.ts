const configuredHosts = (
  process.env.NEXT_PUBLIC_A2UI_ALLOWED_HOSTS ?? ""
)
  .split(",")
  .map((host) => host.trim().toLowerCase())
  .filter(Boolean);

const allowedHosts = new Set(configuredHosts);

export function resolveAllowedA2UIUrl(value: string): string | undefined {
  if (value.startsWith("/") && !value.startsWith("//")) {
    return value;
  }

  try {
    const url = new URL(value);
    if (url.protocol !== "https:") {
      return undefined;
    }
    if (!allowedHosts.has(url.hostname.toLowerCase())) {
      return undefined;
    }
    return url.toString();
  } catch {
    return undefined;
  }
}
