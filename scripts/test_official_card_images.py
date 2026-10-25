"""Boundary checks for the offline image validation and issuer allowlist."""
import io
import unittest

from PIL import Image
from import_official_card_images import Images, image_info, official_image_host


class OfficialCardImagesTest(unittest.TestCase):
    def test_webp_uses_real_dimensions_and_rejects_invalid_data(self):
        data = io.BytesIO()
        Image.new("RGB", (80, 40)).save(data, "WEBP")
        self.assertEqual(image_info(data.getvalue()), ("webp", 80, 40))
        self.assertIsNone(image_info(b"RIFF0000WEBPinvalid"))
        self.assertIsNone(image_info(b'<svg><script>alert(1)</script></svg>', "image/svg+xml"))

    def test_hosts_are_issuer_specific(self):
        page = "https://www.au.bank.in/cards"
        self.assertTrue(official_image_host(page, "https://aemassets.au.bank.in/card.webp"))
        self.assertFalse(official_image_host(page, "https://other.bank.in/card.webp"))
        self.assertFalse(official_image_host(page, "https://au.bank.in.evil.example/card.webp"))
        curated = "https://issuer-cdn.example/exact-card.webp"
        self.assertTrue(official_image_host(page, curated, curated))
        self.assertFalse(official_image_host(page, curated + "?other", curated))

    def test_picture_lazy_sources(self):
        parser = Images()
        parser.feed('<picture><source data-srcset="/one.webp 1x, /two.webp 2x"><img alt="Card" src="/fallback.png"></picture>')
        self.assertEqual(parser.items, [("/one.webp", ""), ("/two.webp", ""), ("/fallback.png", "Card")])


if __name__ == "__main__":
    unittest.main()
