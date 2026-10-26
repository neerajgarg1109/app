# Homepage card news

Maintain `frontend/src/data/cardNews.json` for the Latest news section beside new launches. It is editorial content, independent of the recommendation catalogue and paid placements.

Use `status: "upcoming"` only when an issuer confirms a forthcoming card. Use `"announcement"` when launch timing is unconfirmed, and state the actual availability in `statusLabel` and `availabilityNote`. Include the official `sourceUrl` and the date the source was checked in `verifiedOn`; this date is not the announcement date. Do not invent launch dates or benefits.

Set `active: false` to withdraw an item, or `status: "launched"` to remove it from this section after confirming launch. Add a launched product to the catalogue and new-launch placements through their normal verification process. News entries do not automatically become recommendations or application links.

The initial 1838 Reserve item reflects ICICI's official page checked on 26 October 2026: invitation-only availability, with no confirmed future launch date on that page. It is deliberately not labelled Coming soon.
