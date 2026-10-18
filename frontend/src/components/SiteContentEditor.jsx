import React, { useEffect, useState } from "react";
import { Plus, Save, Trash2 } from "lucide-react";

export default function SiteContentEditor({ content, cards, canEdit, saving, onSave }) {
  const [draft, setDraft] = useState(content || { footer_groups: [], featured_cards: [] });
  useEffect(() => { if (content) setDraft(content); }, [content]);
  if (!content) return <div className="rounded-2xl border bg-white p-5 text-sm">Loading site content…</div>;

  const updateGroup = (index, patch) => setDraft((current) => ({ ...current, footer_groups: current.footer_groups.map((group, i) => i === index ? { ...group, ...patch } : group) }));
  const removeGroup = (index) => setDraft((current) => ({ ...current, footer_groups: current.footer_groups.filter((_, i) => i !== index) }));
  const updateFeature = (index, patch) => setDraft((current) => ({ ...current, featured_cards: current.featured_cards.map((item, i) => i === index ? { ...item, ...patch } : item) }));

  return <div className="space-y-5">
    <section className="rounded-2xl border bg-white p-5" style={{ borderColor: "var(--ciq-line)" }}>
      <h2 className="font-display text-lg font-extrabold">Homepage promotional cards</h2>
      <p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Choose up to four cards. Partner features receive a commission disclosure; launches remain editorial placements.</p>
      <div className="mt-4 space-y-3">{draft.featured_cards.map((item, index) => <div key={`${item.card_id}-${index}`} className="grid gap-2 rounded-xl border p-3 md:grid-cols-[2fr_1fr_1fr_2fr_auto]">
        <select aria-label={`Featured card ${index + 1}`} value={item.card_id} onChange={(e) => updateFeature(index, { card_id: e.target.value })} className="rounded-lg border px-2 py-2 text-xs">{cards.map((card) => <option key={card.id} value={card.id} label={`${card.name} · ${card.issuer}`} />)}</select>
        <select aria-label={`Placement type ${index + 1}`} value={item.placement_type} onChange={(e) => updateFeature(index, { placement_type: e.target.value })} className="rounded-lg border px-2 py-2 text-xs"><option value="launch">New launch</option><option value="partner">Partner feature</option></select>
        <input aria-label={`Placement label ${index + 1}`} value={item.label} onChange={(e) => updateFeature(index, { label: e.target.value })} placeholder="Label" className="rounded-lg border px-2 py-2 text-xs" />
        <input aria-label={`Placement summary ${index + 1}`} value={item.summary || ""} onChange={(e) => updateFeature(index, { summary: e.target.value })} placeholder="Short homepage summary" className="rounded-lg border px-2 py-2 text-xs" />
        <button type="button" aria-label={`Remove featured card ${index + 1}`} onClick={() => setDraft((current) => ({ ...current, featured_cards: current.featured_cards.filter((_, i) => i !== index) }))} className="rounded-lg border p-2"><Trash2 className="h-4 w-4" /></button>
      </div>)}</div>
      <button type="button" disabled={!canEdit || draft.featured_cards.length >= 4 || !cards.length} onClick={() => setDraft((current) => ({ ...current, featured_cards: [...current.featured_cards, { card_id: cards[0]?.id || "", placement_type: "launch", label: "New launch", summary: "", active: true }] }))} className="mt-3 inline-flex items-center gap-1 rounded-full border px-3 py-2 text-xs font-semibold disabled:opacity-40"><Plus className="h-4 w-4" /> Add featured card</button>
    </section>

    <section className="rounded-2xl border bg-white p-5" style={{ borderColor: "var(--ciq-line)" }}>
      <h2 className="font-display text-lg font-extrabold">Footer links</h2>
      <p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Enter one link per line as <strong>Label | /path</strong> or <strong>Label | https://example.com</strong>.</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">{draft.footer_groups.map((group, index) => <div key={index} className="rounded-xl border p-3">
        <div className="flex gap-2"><input aria-label={`Footer group title ${index + 1}`} value={group.title} onChange={(e) => updateGroup(index, { title: e.target.value })} className="min-w-0 flex-1 rounded-lg border px-3 py-2 text-sm font-semibold" /><button type="button" aria-label={`Remove footer group ${index + 1}`} onClick={() => removeGroup(index)} className="rounded-lg border p-2"><Trash2 className="h-4 w-4" /></button></div>
        <textarea aria-label={`Footer links ${index + 1}`} rows="5" value={group.links.map((link) => `${link.label} | ${link.url}`).join("\n")} onChange={(e) => updateGroup(index, { links: parseLinks(e.target.value) })} className="mt-2 w-full rounded-lg border px-3 py-2 text-xs" />
      </div>)}</div>
      <button type="button" disabled={!canEdit || draft.footer_groups.length >= 8} onClick={() => setDraft((current) => ({ ...current, footer_groups: [...current.footer_groups, { title: "New section", links: [{ label: "New link", url: "/" }] }] }))} className="mt-3 inline-flex items-center gap-1 rounded-full border px-3 py-2 text-xs font-semibold disabled:opacity-40"><Plus className="h-4 w-4" /> Add footer group</button>
    </section>

    <button type="button" disabled={!canEdit || saving} onClick={() => onSave(draft)} className="ciq-primary-gradient inline-flex items-center gap-2 rounded-xl px-5 py-3 text-sm font-semibold text-white disabled:opacity-40"><Save className="h-4 w-4" /> {saving ? "Saving…" : "Publish site content"}</button>
  </div>;
}

function parseLinks(value) {
  return value.split("\n").map((line) => line.split("|")).filter((parts) => parts.length >= 2).map(([label, ...url]) => ({ label: label.trim(), url: url.join("|").trim() })).filter((link) => link.label && link.url);
}
