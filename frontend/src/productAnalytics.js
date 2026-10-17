import { trackProductEvent } from "./api";

const SESSION_KEY = "ciq_anonymous_session";

export function productSessionId() {
  try {
    const existing = localStorage.getItem(SESSION_KEY);
    if (existing) return existing;
    const created = globalThis.crypto?.randomUUID?.().replaceAll("-", "")
      || `${Date.now().toString(36)}${Math.random().toString(36).slice(2)}`;
    localStorage.setItem(SESSION_KEY, created);
    return created;
  } catch (error) {
    return `session${Date.now().toString(36)}${Math.random().toString(36).slice(2)}`;
  }
}

export function recordProductEvent(event, resultId = null, metadata = {}) {
  return trackProductEvent(event, productSessionId(), resultId, metadata).catch(() => null);
}
