const fs = require("fs");
const path = require("path");

const source = path.resolve(__dirname, "../../backend/cards_catalog.json");
const destination = path.resolve(__dirname, "../public/cards-catalog.json");

const cards = JSON.parse(fs.readFileSync(source, "utf8"));
if (!Array.isArray(cards) || cards.length === 0) {
  throw new Error("Backend card catalogue is empty or invalid");
}

fs.writeFileSync(destination, `${JSON.stringify(cards)}\n`, "utf8");
console.log(`Generated static fallback with ${cards.length} cards.`);
