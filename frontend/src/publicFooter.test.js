import fs from "fs";
import path from "path";

const script = fs.readFileSync(path.resolve(process.cwd(), "../scripts/templates/public-footer.js"), "utf8");
const flush = async () => { for (let i = 0; i < 8; i += 1) await Promise.resolve(); };
const run = fetch => new Function("document", "fetch", "AbortController", "setTimeout", "clearTimeout", script)(document, fetch, AbortController, () => 1, () => {});

beforeEach(() => {
  document.body.innerHTML = '<footer class="customer-footer" data-public-origin="https://findmybest.cards" data-content-url="https://api.findmybest.cards/api/site-content"><div class="customer-footer-grid"><div class="customer-footer-about">CardIQ</div><section>Fallback links</section></div></footer>';
});
afterEach(() => { document.body.innerHTML = ""; });

test("static pages show Admin-published links using the same public and app routes", async () => {
  run(jest.fn().mockResolvedValue({ ok: true, json: async () => ({ footer_groups: [{ title: "Research", links: [{ label: "Cards", url: "/cards?mode=compare" }, { label: "Guides", url: "/guides/" }] }] }) }));
  await flush();
  expect(document.querySelector('h2').textContent).toBe("Research");
  expect(Array.from(document.querySelectorAll('a')).map(a => a.href)).toEqual(["https://findmybest.cards/compare/", "https://findmybest.cards/guides/"]);
  expect(document.querySelector('.customer-footer-about').textContent).toBe("CardIQ");
});

test("an unavailable footer service preserves the complete generated fallback", async () => {
  run(jest.fn().mockRejectedValue(new Error("offline")));
  await flush();
  expect(document.querySelector('section').textContent).toBe("Fallback links");
});

test("invalid destinations leave the existing footer intact", async () => {
  run(jest.fn().mockResolvedValue({ ok: true, json: async () => ({ footer_groups: [{ title: "Unsafe", links: [{ label: "Link", url: "javascript:alert(1)" }] }] }) }));
  await flush();
  expect(document.querySelector('section').textContent).toBe("Fallback links");
});

 test("static footer maps catalogue, calculator and research navigation to crawlable routes", async () => {
  const routes = {"/cards": "/catalog/", "/calculator": "/calculator/", "/updates": "/guides/new-credit-cards/", "/restricted-cards": "/guides/invite-only-credit-cards/"};
  run(jest.fn().mockResolvedValue({ok: true, json: async () => ({footer_groups: [{title: "Discover", links: Object.keys(routes).map(url => ({label: url, url}))}]})}));
  await flush();
  expect(Array.from(document.querySelectorAll('a')).map(a => a.href)).toEqual(Object.values(routes).map(url => "https://findmybest.cards" + url));
});
