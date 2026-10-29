import React, { act } from "react";
import { createRoot } from "react-dom/client";
import Compare from "./Compare";

global.IS_REACT_ACT_ENVIRONMENT = true;

test("comparison headings show each card's real artwork", async () => {
  const container = document.createElement("div");
  const root = createRoot(container);
  const cards = [
    { id: "one", name: "First card", issuer: "Bank One", imageUrl: "/cards/one.webp" },
    { id: "two", name: "Second card", issuer: "Bank Two", imageUrl: "/cards/two.webp" },
  ];
  await act(async () => root.render(<Compare cards={cards} onClose={() => {}} />));
  expect([...container.querySelectorAll("img")].map(image => image.getAttribute("src"))).toEqual(["/cards/one.webp", "/cards/two.webp"]);
  await act(async () => root.unmount());
});
