import React, { act, useState } from "react";
import { createRoot } from "react-dom/client";
import CardArtworkEditor from "./CardArtworkEditor";
import { uploadAdminCardImage } from "../api";

jest.mock("../api", () => ({ uploadAdminCardImage: jest.fn() }));
global.IS_REACT_ACT_ENVIRONMENT = true;

function Harness({ busy }) {
  const [url, setUrl] = useState("/cards/original.webp");
  return <CardArtworkEditor card={{ id: "test", name: "Test Card" }} imageUrl={url} token="editor-token" onChange={setUrl} onBusyChange={busy} />;
}

async function choose(container, file) {
  const input = container.querySelector('input[type="file"]');
  Object.defineProperty(input, "files", { configurable: true, value: [file] });
  await act(async () => input.dispatchEvent(new Event("change", { bubbles: true })));
}

test("upload updates the draft image preview using the authenticated API", async () => {
  const container = document.createElement("div"), root = createRoot(container), busy = jest.fn();
  uploadAdminCardImage.mockResolvedValue("https://api.example/api/card-images/new");
  await act(async () => root.render(<Harness busy={busy} />));
  const file = new File(["image"], "card.png", { type: "image/png" });
  await choose(container, file);
  expect(uploadAdminCardImage).toHaveBeenCalledWith("editor-token", file);
  expect(container.querySelector("img").getAttribute("src")).toBe("https://api.example/api/card-images/new");
  expect(container.querySelector('input:not([type="file"])').value).toBe("https://api.example/api/card-images/new");
  expect(container.textContent).toContain("preview and publish");
  expect(busy.mock.calls).toEqual([[true], [false]]);
  await act(async () => root.unmount());
});

test("rejects unsupported uploads and preserves the previous artwork on server failure", async () => {
  const container = document.createElement("div"), root = createRoot(container);
  uploadAdminCardImage.mockReset();
  await act(async () => root.render(<Harness />));
  await choose(container, new File(["<svg/>"], "bad.svg", { type: "image/svg+xml" }));
  expect(uploadAdminCardImage).not.toHaveBeenCalled();
  expect(container.textContent).toContain("up to 2 MB");
  uploadAdminCardImage.mockRejectedValue(new Error("Offline"));
  await choose(container, new File(["image"], "card.png", { type: "image/png" }));
  expect(container.querySelector("img").getAttribute("src")).toBe("/cards/original.webp");
  expect(container.textContent).toContain("previous image is unchanged");
  await act(async () => root.unmount());
});

test("a broken image URL prevents saving until corrected", async () => {
  const container = document.createElement("div"), root = createRoot(container);
  await act(async () => root.render(<Harness />));
  await act(async () => container.querySelector("img").dispatchEvent(new Event("error")));
  expect(container.querySelector('input:not([type="file"])').validationMessage).toContain("could not be loaded");
  await act(async () => root.unmount());
});
