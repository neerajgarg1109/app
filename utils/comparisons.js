/**
 * @typedef {{ cardA: string, cardB: string, pairSlug: string }} CardComparison
 */

/**
 * Generate one comparison route for each distinct, unordered card pair.
 * Input order determines the A/B order in the resulting URL.
 * @param {string[]} slugs
 * @returns {CardComparison[]}
 */
function generateCardComparisons(slugs) {
  const uniqueSlugs = [...new Set(slugs)];
  const pairs = [];

  for (let i = 0; i < uniqueSlugs.length; i++) {
    for (let j = i + 1; j < uniqueSlugs.length; j++) {
      const cardA = uniqueSlugs[i];
      const cardB = uniqueSlugs[j];

      pairs.push({
        cardA,
        cardB,
        pairSlug: `${cardA}-vs-${cardB}`,
      });
    }
  }

  return pairs;
}

module.exports = { generateCardComparisons };
