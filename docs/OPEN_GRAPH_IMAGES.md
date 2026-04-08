Open Graph Images — Guide
=========================

This document shows a practical workflow for adding Open Graph (OG) images to a website so that link previews (Facebook, WhatsApp, Twitter, LinkedIn, etc.) show a reliable, high-quality image when pages are shared.

Overview
--------
- Produce a social preview image (the OG canvas) — usually 1200×630px — and host it on a public URL.
- Reference the image using Open Graph meta tags (og:image) and Twitter meta tags in your page's <head>.
- Prefer WebP for smaller size, but include a JPEG/PNG fallback for maximum compatibility.
- Use absolute HTTPS URLs for OG tags and ensure the image is reachable by crawlers.

Recommended sizes and files
---------------------------
- OG social preview canvas (main): 1200 × 630 px (recommended)
  - 2x retina variant: 2400 × 1260 px (optional)
  - Minimum to be safe: 600 × 315 px
- Logo variants (examples):
  - site header / inline logo: 120 × 40 px (or SVG)
  - square logo (for thumbnails): 360 × 360 px (and 720 × 720 px for 2x)
- Favicon / app icons: 16×16, 32×32, 180×180 (apple), 192×192 / 512×512 for PWA

Formats and compression
-----------------------
- Use WebP for small size where supported. WebP often yields much smaller files than JPEG for the same quality.
- Keep a JPEG fallback (or PNG if you need lossless transparency). Many social platforms accept WebP but some older clients do not.
- Aim for <200 KB for OG images; smaller is better to speed up crawlers and previews.

How to generate images (examples)
---------------------------------
Using ImageMagick (installed on many Linux systems):

1) Resize logo to square 360×360 and a 2x variant:

```bash
convert logo.png -resize 360x360^ -gravity center -extent 360x360 -strip -quality 85 logo-360.png
convert logo.png -resize 720x720^ -gravity center -extent 720x720 -strip -quality 85 logo-720.png
```

2) Create a 1200×630 OG canvas and composite the logo centered:

```bash
convert -size 1200x630 xc:'#0b2540' bg-1200x630.png
composite -gravity center logo-360.png bg-1200x630.png og-1200x630.jpg
```

3) Create a WebP compressed variant:

```bash
convert og-1200x630.jpg -quality 80 og-1200x630.webp
```

Using sharp (Node.js) for high-performance builds (example resize):

```bash
npx sharp logo.png --resize 360,360 --toFile logo-360.png
npx sharp og-1200x630.jpg --quality 80 --toFormat webp --toFile og-1200x630.webp
```

Integration in build process
----------------------------
- Add a build step that regenerates OG images when the logo or template changes. For example, you can add this to your repository's build script (e.g., `build.sh`) so the images exist before `collectstatic` runs.
- Example (bash snippet to put in a build script):

```bash
# Ensure output dir
mkdir -p frontend/public/static/og
# Resize and create webp
convert frontend/public/static/balonrank-logo.png -resize 360x360 -gravity center -extent 360x360 frontend/public/static/og/logo-360.png
convert frontend/public/static/og/og-1200x630.jpg -quality 80 frontend/public/static/og/og-1200x630.webp
# Then run collectstatic (Django)
python manage.py collectstatic --noinput
```

Server & URL considerations
--------------------------
- Use absolute HTTPS URLs in OG tags, e.g. `https://example.com/static/og/og-1200x630.webp` — this avoids ambiguity for social crawlers.
- Ensure the URL is publicly accessible without authentication, and served with correct Content-Type headers (image/webp, image/jpeg).
- If you rely on a CDN, ensure the CDN responds to social crawlers and is not blocked by robots or firewall rules.

Page meta tags (basic example)
-----------------------------
Add these tags to your page <head> (replace the absolute domain as needed):

```html
<meta property="og:type" content="website" />
<meta property="og:title" content="Site Title" />
<meta property="og:description" content="Site description goes here." />
<!-- Prefer WebP but add a JPEG fallback for Twitter if you like -->
<link rel="preload" as="image" href="https://example.com/static/og/og-1200x630.webp" type="image/webp" />
<meta property="og:image" content="https://example.com/static/og/og-1200x630.webp" />
<meta property="og:image:type" content="image/webp" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:image" content="https://example.com/static/og/og-1200x630.jpg" />
```

Django example (using settings.SITE_URL)
----------------------------------------
If your Django settings include a SITE_URL or you can construct absolute URLs from a request, render absolute URLs into templates.

Example snippet in a Django template (base.html):

```django
{% load static %}
{% with site_url=settings.SITE_URL|default:"https://example.com" %}
  <meta property="og:image" content="{{ site_url }}{% static 'og/og-1200x630.webp' %}" />
  <meta name="twitter:image" content="{{ site_url }}{% static 'og/og-1200x630.jpg' %}" />
{% endwith %}
```

Or compute from a request in a view:

```python
def view(request):
    absolute = request.build_absolute_uri(static('og/og-1200x630.jpg'))
    return render(request, 'page.html', {'og_image': absolute})
```

Compatibility & caveats
-----------------------
- Facebook/WhatsApp use Facebook's scraper. They cache scraped metadata. If you replace the OG image or tags, use Facebook Sharing Debugger to re-scrape and clear the cache.
- Twitter uses its own Card Validator. Twitter historically favored JPEG/PNG; keep JPEG fallback for safety.
- Some platforms do not support WebP — the JPEG fallback covers them.
- If social previews still show older images, clear caches (FB Debugger) and wait for propagation.

Testing & validation
--------------------
- Facebook Sharing Debugger: https://developers.facebook.com/tools/debug/ — paste your page URL and click "Scrape Again" to force refresh.
- Twitter Card Validator: https://cards-dev.twitter.com/validator — validate how your page appears on Twitter.
- Manual test: send the URL to WhatsApp, Telegram, and check LinkedIn share preview.

Accessibility
-------------
- Add an `og:image:alt` meta tag where supported; although Open Graph doesn't standardize alt text, Twitter and other platforms may use available accessibility fields in advanced metadata. For in-page images, ensure alt attributes are present.

Security & privacy
------------------
- Ensure the OG image URL does not expose sensitive data and is publicly safe to be scraped.
- Do not include user-specific or session-authenticated images in OG tags.

Automation and CI
-----------------
- Add image generation to CI or the deploy/build script so the OG images are always up-to-date and present in the static assets before deploy.
- Example: in your `build.sh` (Vercel root build script) run the ImageMagick/sharp steps before `collectstatic`.

Troubleshooting
---------------
- Not showing correct image: ensure absolute URL, respond 200, correct content-type, accessible by external crawlers.
- Image too small/blurry: regenerate at 1200×630 (or 2x) and recompress.
- Social platform shows old image: use the platform's debugger to force re-scrape.

Further improvements
--------------------
- Dynamically generate social-share images with a small service (e.g., Puppeteer or headless browser) for personalized previews.
- Use a Redis cache and a background job to warm/refresh images if generation is expensive.
- Implement a token-bucket limiter on scrapers if you face abusive scraping of OG images.

References
----------
- Facebook Open Graph: https://developers.facebook.com/docs/sharing/webmasters
- Twitter Cards: https://developer.twitter.com/en/docs/twitter-for-websites/cards/overview/abouts-cards
- Image size recommendations: many guides recommend 1200x630 for cross-platform compatibility.

End of guide
