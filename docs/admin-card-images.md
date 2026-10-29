# Updating card artwork from Admin

Implemented locally on 29 October 2026; not deployed yet.

1. Open Admin → Cards, find the card and choose **Edit**.
2. The **Card image** section is at the top. Upload PNG, JPEG or WebP artwork (up to 2 MB, minimum 80 pixels per side), or paste an HTTPS image URL. Existing `/cards/` asset paths are also supported.
3. Check the artwork preview, choose **Save draft**, then **Preview** and **Publish card**. Editors can upload/save; publisher or owner access is required to publish. A failed upload leaves the previous selection intact.

Uploads are normalized to a still WebP image, with proportions and transparency retained and metadata omitted. SVG/GIF, unreadable files, animations, oversized uploads and images exceeding 16 megapixels are rejected. The longest side is reduced to 1200 pixels. External URL images are previewed in the browser; the backend does not fetch arbitrary remote URLs.

The authenticated `POST /api/admin/card-images` endpoint accepts raw image bytes and returns a public asset path. The frontend resolves this against its configured backend origin before saving `imageUrl`. Uploaded bytes live in MongoDB's `card_images` collection, keyed by a SHA-256 digest; identical normalized images reuse an asset. `GET /api/card-images/{digest}` serves WebP with immutable cache headers. A new image receives a new URL. Old assets are retained for version history/rollback and unused uploads are not automatically deleted.

Publishing uses the existing card draft/history flow and preserves the old image URL in the previous version. API-driven card views and comparisons use published imageUrl. Generated static articles/catalogue pages and the bundled fallback artwork map refresh during the next site build/deployment; publishing in Admin does not itself trigger a GitHub Pages deployment. Existing saved result payloads that contain an explicit old image URL can retain that historical image.

Uploaded artwork is database content, not a file committed to Git. Include the `card_images` collection when intentionally migrating/restoring the application database. Production backup exports remain disabled; this feature does not enable them or change operations settings. Static deployment builds must retain access to the configured public API image host.

Validation: 129 frontend tests in 33 suites; 23 backend catalogue/image tests using a disposable in-memory database; optimized frontend build. Browser QA in an isolated local database verified upload → preview → save draft → draft preview, including rendering the stored asset over the separate local API origin. No production card was changed during QA.

Relevant sources: `backend/card_images.py`, the image endpoints in `backend/server.py`, `frontend/src/components/CardArtworkEditor.jsx`, `frontend/src/components/Admin.jsx`, and `uploadAdminCardImage` in `frontend/src/api.js`. Backend runtime now requires Pillow (same version range as the catalogue image tooling).

Isolated admin preview: http://127.0.0.1:8770/#/admin (backend on 127.0.0.1:8011). It uses a temporary in-memory database and is separate from production; its data disappears when the preview backend stops.
