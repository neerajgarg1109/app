const fs = require('node:fs');
const { generateCardComparisons } = require('../utils/comparisons');

// The static generator passes only its mutually approved editorial pairs.
const approvedPairs = JSON.parse(fs.readFileSync(0, 'utf8'));
const comparisons = approvedPairs.flatMap((pair) => generateCardComparisons(pair));

process.stdout.write(JSON.stringify(comparisons));
