import React, { useEffect, useRef, useState } from "react";
import { uploadAdminCardImage } from "../api";
import { getCardArtwork } from "./CreditCardVisual";

export default function CardArtworkEditor({ card, imageUrl, token, onChange, onBusyChange }) {
  const input = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [imageError, setImageError] = useState(false);
  const source = imageUrl || getCardArtwork({ ...card, imageUrl: null });
  useEffect(() => { setImageError(false); input.current?.setCustomValidity(""); }, [source]);
  const upload = async event => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setMessage("");
    if (!["image/png", "image/jpeg", "image/webp"].includes(file.type) || file.size > 2 * 1024 * 1024) {
      setMessage("Choose a PNG, JPEG or WebP image up to 2 MB.");
      return;
    }
    setUploading(true); onBusyChange?.(true);
    try {
      const url = await uploadAdminCardImage(token, file);
      onChange(url);
      setMessage("Image uploaded. Save the draft, then preview and publish the card to show it to customers.");
    } catch (error) {
      setMessage(error.response?.data?.detail || "Image upload failed. Your previous image is unchanged. Try again.");
    } finally { setUploading(false); onBusyChange?.(false); }
  };
  return <section className="space-y-3 rounded-2xl border p-4 sm:col-span-2" aria-label="Card artwork">
    <h3 className="text-sm font-bold">Card image</h3>
    <p className="text-xs text-slate-600">Upload the real card artwork or paste an HTTPS image URL. Uploads are stored with the project; previous images remain available for change history.</p>
    <div className="grid gap-4 sm:grid-cols-[220px_1fr]">
      <div className="grid min-h-36 place-items-center rounded-xl border bg-slate-50 p-3">
        {source && !imageError ? <img key={source} src={source} alt={`${card.name || "Card"} artwork preview`} className="h-36 w-full object-contain" onError={() => {
          setImageError(true);
          if (imageUrl) input.current?.setCustomValidity("The image could not be loaded. Check the URL or upload a file.");
        }} /> : <p className="text-center text-xs text-slate-500">{imageError ? "Image could not be loaded. Check the URL or upload a file." : "No artwork selected"}</p>}
      </div>
      <div className="space-y-3">
        <label className="block space-y-1 text-xs font-semibold">Card image URL<input ref={input} className="w-full rounded-xl border px-3 py-2 text-sm" value={imageUrl || ""} onChange={event => { input.current.setCustomValidity(""); onChange(event.target.value); }} placeholder="/cards/card.webp or https://…" /></label>
        <label className="block space-y-1 text-xs font-semibold">Upload card image<input disabled={uploading} type="file" accept="image/png,image/jpeg,image/webp" onChange={upload} className="block w-full text-xs" /></label>
        <p className="text-xs text-slate-500">PNG, JPEG or WebP · up to 2 MB · minimum 80 × 80 px. Leave the URL empty to use the catalogue artwork where available.</p>
      </div>
    </div>
    {uploading && <p role="status" className="text-xs">Uploading card image…</p>}
    {message && <p role="status" className="text-xs">{message}</p>}
  </section>;
}
