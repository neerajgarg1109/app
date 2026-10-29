"""Load optional brand fonts without blocking readable system-font content."""
FONT_URL = 'https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&amp;family=Inter:wght@400;500;600;700&amp;display=optional'


def font_links():
    return ('<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            f'<link rel="stylesheet" href="{FONT_URL}" media="print" onload="this.media=\'all\'">'
            f'<noscript><link rel="stylesheet" href="{FONT_URL}"></noscript>')
