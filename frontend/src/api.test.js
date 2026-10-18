jest.mock("axios", () => {
  const post = jest.fn();
  return { create: jest.fn(() => ({ post })), __mockPost: post };
});

import axios from "axios";
import { submitQuiz } from "./api";

const mockPost = axios.__mockPost;

test("caps recommendation wait time instead of leaving the customer hanging", async () => {
  mockPost.mockResolvedValue({ data: { result_id: "result-1", scored: [{ card: { id: "card-1" } }] } });
  const answers = { goal: "cashback" };

  await expect(submitQuiz(answers)).resolves.toEqual(expect.objectContaining({ result_id: "result-1" }));
  expect(mockPost).toHaveBeenCalledWith(
    "/quiz/submit",
    { answers },
    { timeout: 9000 },
  );
});
