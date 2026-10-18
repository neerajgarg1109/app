const ACTIVE_EXPERIMENT = { id: "landing-cta-clarity-v1", variants: ["control", "value-led"] };

export function experimentAssignment() {
  try {
    const key = `ciq_experiment_${ACTIVE_EXPERIMENT.id}`;
    const stored = localStorage.getItem(key);
    if (ACTIVE_EXPERIMENT.variants.includes(stored)) return { experiment_id: ACTIVE_EXPERIMENT.id, variant: stored };
    const seed = globalThis.crypto?.getRandomValues ? globalThis.crypto.getRandomValues(new Uint8Array(1))[0] : Math.floor(Math.random() * 256);
    const variant = ACTIVE_EXPERIMENT.variants[seed % ACTIVE_EXPERIMENT.variants.length];
    localStorage.setItem(key, variant);
    return { experiment_id: ACTIVE_EXPERIMENT.id, variant };
  } catch (error) {
    return { experiment_id: ACTIVE_EXPERIMENT.id, variant: "control" };
  }
}
