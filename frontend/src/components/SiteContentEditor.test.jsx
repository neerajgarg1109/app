import React, { act } from "react";
import { createRoot } from "react-dom/client";
import SiteContentEditor from "./SiteContentEditor";

global.IS_REACT_ACT_ENVIRONMENT = true;

test("lets an editor configure featured cards and footer groups", async () => {
  const container = document.createElement("div");
  const root = createRoot(container);
  const onSave = jest.fn();
  const content = { footer_groups: [{ title: "Discover", links: [{ label: "Cards", url: "/cards" }] }], featured_cards: [] };
  await act(async () => root.render(<SiteContentEditor content={content} cards={[{ id: "scapia", name: "Scapia Axis Bank", issuer: "Axis Bank" }]} canEdit saving={false} onSave={onSave} />));
  await act(async () => Array.from(container.querySelectorAll("button")).find((button) => button.textContent.includes("Add featured card")).click());
  expect(container.querySelector('option[value="scapia"]').getAttribute("label")).toContain("Scapia Axis Bank");
  await act(async () => Array.from(container.querySelectorAll("button")).find((button) => button.textContent.includes("Publish site content")).click());
  expect(onSave).toHaveBeenCalledWith(expect.objectContaining({ featured_cards: [expect.objectContaining({ card_id: "scapia", placement_type: "launch" })] }));
  await act(async () => root.unmount());
});
