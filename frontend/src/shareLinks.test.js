import { cardShareDetails, socialShareUrl } from "./shareLinks";

const card = { id: "cashback card", name: "Cashback & More", issuer: "Test Bank", rewardLine: "5% cashback" };

beforeAll(() => { process.env.REACT_APP_PUBLIC_APP_URL = "https://neerajgarg1109.github.io/app"; });
afterAll(() => { delete process.env.REACT_APP_PUBLIC_APP_URL; });

test("uses the crawlable public card URL rather than the hash route", () => {
  const details = cardShareDetails(card);
  expect(details.url).toBe("https://neerajgarg1109.github.io/app/cards/cashback%20card/");
  expect(details.url).not.toContain("#");
  expect(details.text).toContain("Cashback & More by Test Bank");
});

test.each(["whatsapp", "x", "facebook"])("builds an encoded %s sharing URL", (channel) => {
  const url = socialShareUrl(channel, cardShareDetails(card));
  expect(url).toContain(encodeURIComponent("https://neerajgarg1109.github.io/app/cards/cashback%20card/"));
  expect(url).not.toContain("Cashback & More");
});

test("rejects unsupported sharing destinations", () => {
  expect(() => socialShareUrl("email", cardShareDetails(card))).toThrow("Unsupported share channel");
});
