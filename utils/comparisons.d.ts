export type CardComparison = {
  cardA: string;
  cardB: string;
  pairSlug: string;
};

export function generateCardComparisons(slugs: string[]): CardComparison[];
