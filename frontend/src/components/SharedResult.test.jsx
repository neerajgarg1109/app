import React, { act } from "react";
import { createRoot } from "react-dom/client";
import SharedResult from "./SharedResult";
import { getResult } from "../api";

let mockResultId = "first";
jest.mock("../api", () => ({ getResult: jest.fn() }));
jest.mock("react-router-dom", () => ({
  useParams: () => ({ resultId: mockResultId }), useNavigate: () => jest.fn(),
  Link: ({ to, children }) => <a href={to}>{children}</a>,
}));
jest.mock("./Result", () => ({ scored }) => <p>{scored[0].card.name}</p>);
global.IS_REACT_ACT_ENVIRONMENT = true;

test("hides the previous person's recommendation while another shared result loads", async () => {
  mockResultId = "first";
  getResult.mockResolvedValueOnce({ scored: [{ card: { name: "First card" } }] });
  const container = document.createElement("div"); const root = createRoot(container);
  await act(async () => root.render(<SharedResult />));
  expect(container.textContent).toContain("First card");
  let finish;
  getResult.mockReturnValueOnce(new Promise(resolve => { finish = resolve; }));
  mockResultId = "second";
  await act(async () => root.render(<SharedResult />));
  expect(container.textContent).not.toContain("First card");
  await act(async () => finish({ scored: [{ card: { name: "Second card" } }] }));
  expect(container.textContent).toContain("Second card");
  await act(async () => root.unmount());
});
