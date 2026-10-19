jest.mock("axios", () => {
  const get = jest.fn();
  const post = jest.fn();
  return { get, create: jest.fn(() => ({ get, post })), __mockGet: get, __mockPost: post };
});

import axios from "axios";
import { getCard, getCards, submitQuiz } from "./api";

const mockGet = axios.__mockGet;
const mockPost = axios.__mockPost;

beforeEach(() => jest.clearAllMocks());

test("uses the generated catalogue when the live API is unavailable", async () => {
  mockGet
    .mockRejectedValueOnce(new Error("service waking"))
    .mockResolvedValueOnce({ data: [{ id: "fallback-card" }] });

  await expect(getCards()).resolves.toEqual([{ id: "fallback-card" }]);
  expect(mockGet).toHaveBeenNthCalledWith(1, "/cards", { params: { view: "summary" }, timeout: 2500 });
  expect(mockGet).toHaveBeenNthCalledWith(2, "/cards-catalog-summary.json", { timeout: 10000 });
});

test("prefers current API card data when the service is available", async () => {
  mockGet.mockResolvedValueOnce({ data: [{ id: "live-card" }] });
  await expect(getCards()).resolves.toEqual([{ id: "live-card" }]);
  expect(mockGet).toHaveBeenCalledTimes(1);
});

test("loads one complete card without downloading the full live catalogue", async () => {
  mockGet.mockResolvedValueOnce({ data: { id: "live-card", highlights: ["Full detail"] } });
  await expect(getCard("live-card")).resolves.toEqual(expect.objectContaining({ highlights: ["Full detail"] }));
  expect(mockGet).toHaveBeenCalledWith("/cards/live-card", { timeout: 5000 });
});

test("allows a sleeping recommendation service to wake without waiting forever", async () => {
  mockPost.mockResolvedValue({ data: { result_id: "result-1", scored: [{ card: { id: "card-1" } }] } });
  const answers = { goal: "cashback" };

  await expect(submitQuiz(answers)).resolves.toEqual(expect.objectContaining({ result_id: "result-1" }));
  expect(mockPost).toHaveBeenCalledWith(
    "/quiz/submit",
    { answers },
    { timeout: 50000 },
  );
});
