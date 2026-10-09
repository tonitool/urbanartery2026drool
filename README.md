# Urban Artery — Shopify theme

An Online Store 2.0 theme for **Urban Artery** (urban-artery.de): handmade,
customer-designed street-art originals. The page structure follows the
conversion layout of a contemporary art-print storefront (drool-art.com) —
split hero, product carousels, dark category band, CTA band, social proof,
community grid, newsletter, trust row — filled with Urban Artery's own business:
the photo-to-art configurator, artist editions, before/after customisation,
commissions and gift vouchers.

Brand: black and hot pink (`#E60073` — the site's `#FF0080`, darkened just enough for 4.5:1 contrast with white text), square buttons, uppercase stencil headings
(Allerta Stencil) over a monospace body (Inconsolata). Storefront copy is German;
`locales/de.json` translates every theme string.

Everything is section-based and editable in the theme customizer. No build step,
no dependencies — plain Liquid, CSS and vanilla JS.

## Structure

```
assets/        base.css, theme.js, bundled brand fonts (woff2)
config/        settings_schema.json, settings_data.json
layout/        theme.liquid
locales/       en.default.json, de.json
sections/      homepage sections, template sections, header/footer groups
snippets/      product-card, section-heading, icon, stars, meta-tags
templates/     index, product, collection, cart, search, page, 404, list-collections
media/         Urban Artery's own images, web-optimised — upload to Shopify Files
preview/       build.py → index.html, a static render of the homepage
```

### Fully on Shopify

The storefront, configurator and checkout all run on the one Shopify store — no
separate site and no configurator subdomain. The configurator is the product
`masterprodukt-individuelle-streetart` with the Zakeke app block on its product
page. **Theme settings → Konfigurator** stores that product once; every
„Jetzt gestalten“ / „Zum Konfigurator“ button with an empty link points to it.

### Homepage (order in `templates/index.json`)

| # | Band | Section | Reference slot it fills |
| --- | --- | --- | --- |
| 1 | „Dein Street-Art-Unikat.“ + Gestalten / Inspirieren | `hero-split` | Split hero |
| 2 | Press logos — **disabled** until there is real coverage | `press-bar` | As seen in |
| 3 | Inspiration / October Picks | `product-carousel` | Best sellers |
| 4 | Vorher & Nachher sliders | `before-after` (new) | Explore edits |
| 5 | Werke anderer Kunden + „Selbst gestalten“ | `collection-carousel` | Trending today |
| 6 | Trägermaterialien / Gutscheine tiles | `category-tiles` | Dark category band |
| 7 | Motive zum Individualisieren | `product-carousel` | Canvas prints |
| 8 | Auftragsarbeit CTA | `cta-banner` | Quiz CTA |
| 9 | So funktioniert's — 4 numbered steps | `trust-badges` (numbered) | New drops |
| 10 | Reviews — **disabled** until there are real reviews | `reviews` | Reviews |
| 11 | Mehr von Urban Artery — overlay cards | `collection-carousel` (overlay) | — |
| 12 | Behind the scenes video | `video` (new) | — |
| 13 | Instagram grid | `community` | Community love |
| 14 | Newsletter with consent line | `newsletter` | Newsletter |

Header (dark, announcement bar in pink) and footer (trust row, four columns,
payment icons) live in `sections/header-group.json` and `sections/footer-group.json`.

### Product page (`templates/product.json`)

Buy box → **app block slot** (for the Zakeke configurator or a reviews app) →
trust icons → description and accordions (sizes & materials, shipping,
withdrawal) → before/after → how it works → commission CTA → FAQ (with
`FAQPage` structured data) → related products. The price line carries the
„inkl. MwSt., zzgl. Versandkosten“ note required for German consumer sales.

### New or extended sections

| Section | What it adds |
| --- | --- |
| `before-after.liquid` | Drag-to-compare image pairs (range input + `clip-path`, keyboard accessible) |
| `video.liquid` | Shopify-hosted video band — no third-party embed, no cookies |
| `faq.liquid` | Accordion list with optional FAQ structured data |
| `trust-badges.liquid` | Optional heading, numbered-steps mode, more icons |
| `collection-carousel.liquid` | Card text, „Mehr erfahren“ link, overlay card style, footer button |
| `main-product.liquid` | `@app` blocks, trust icons, description block, tax/shipping note |
| `header.liquid` / `footer.liquid` | Dark header scheme, logo height, footer colours, payment icons |
| `page-header.liquid` | Dark title band for content pages (falls back to the page title) |
| `rich-text.liquid` | Heading + rich text + button, optional image beside the text |
| `text-columns.liquid` | Columns of title + rich text, plain or as quote cards |
| `contact-form.liquid` | Contact channels + Shopify contact form (name, email, order no., subject) |

## Install

Requires the [Shopify CLI](https://shopify.dev/docs/api/shopify-cli).

```bash
shopify theme dev   --store your-store.myshopify.com   # local preview with hot reload
shopify theme push  --store your-store.myshopify.com --unpublished
```

Or build a zip of the theme folders and upload it under **Online Store → Themes →
Add theme → Upload zip**:

```bash
zip -r dist/urban-artery-theme.zip assets config layout locales sections snippets templates
```

## Setup after install

1. **Upload the images** — Content → Files → upload everything in `media/`
   (keep the file names). The templates reference them as
   `shopify://shop_images/<name>`, so they appear automatically once uploaded.
2. **Configurator** — check Theme settings → Konfigurator points at the configurator
   product, and add the Zakeke app block to the product section directly under the
   buy button.
3. **Pages** — Online Store → Pages → Add page, give it the handle below and pick
   the matching theme template. The content lives in the template, so the page body
   can stay empty.

   | Page | Handle | Template |
   | --- | --- | --- |
   | Auftragsarbeiten | `auftragsarbeiten` | `page.auftragsarbeiten` |
   | Über Urban Artery | `uber-urban-artery` | `page.ueber-uns` |
   | So startest du mit Blanks | `so-startest-du` | `page.so-startest-du` |
   | So funktioniert's | `so-funktionierts` | `page.so-gehts` |
   | Häufige Fragen | `faqs` | `page.faq` |
   | Verpackung und Versand | `verpackung-und-versand` | `page.versand` |
   | Kontakt | `kontakt` | `page.kontakt` |
   | Merkliste | `merkliste` | `page.wishlist` |

   These are the handles the live shop uses (urban-artery.de). Theme links point to
   them, so keep them when renaming a page. The contact layout also renders on the
   default page template for the handle `kontakt`.

   The contact form is Shopify's own and emails the store's sender address.
   Impressum, Datenschutz and AGB belong in Settings → Policies.
4. **Collections** — assign collections to the three product carousels
   (Beliebte Werke, Werke anderer Kunden, Neue Motive) and create `inspiration`
   (linked from the hero and a tile).
5. **Navigation** — `main-menu`: Konfigurator, Inspiration, Über uns,
   Auftragsarbeiten, Kontakt. Footer link lists: Hilfe (So funktioniert's, FAQs,
   Verpackung & Versand), Urban Artery (Über Urban Artery, Auftragsarbeiten,
   Nimm Kontakt auf), Rechtliches (Impressum, Datenschutz, AGB & Widerrufsrecht).
6. **Newsletter discount** — the newsletter promises 10 % off the first order;
   set up that discount (e.g. Shopify Email welcome flow) or change the text.
7. **Social proof** — press bar, reviews and the Instagram grid are disabled until
   there is real coverage, real reviews and real customer photos.
8. **Social links** — Instagram and Facebook under **Theme settings → Social**.

## Customising

Colors and typography are driven by CSS custom properties written into
`layout/theme.liquid` from theme settings, so most rebranding is done in the
customizer rather than in CSS. The accent color drives the announcement bar,
eyebrows, the bar under section titles and the steps' icons; the dark color drives
the header, hero panel, category band, CTA and video bands.

**Fonts.** „Use bundled brand fonts“ (on by default) serves Allerta Stencil and
Inconsolata from the theme's own assets, so no request goes to Google Fonts — the
privacy-safe choice for a German storefront. Both fonts are licensed under the SIL
Open Font License 1.1 (licence text embedded in the font files; see
<https://openfontlicense.org>). Untick it to fall back to the font pickers.

Card width on every carousel is a per-section setting (`slide_width`), so the number
of visible cards adapts to the page width without touching CSS.

## Preview without a store

```bash
python3 preview/build.py          # regenerate preview/index.html and preview/page.*.html
python3 -m http.server 8791       # then open http://localhost:8791/preview/
```

The preview renders the same markup as the Liquid sections, with generated
placeholder artwork and neutral demo products.

## Content notice

Storefront copy and images are Urban Artery's own (from the previous Lovable site,
`UALove-main`, and the shop's product options). Only the **layout** follows the reference store; none of its
copy, imagery, reviews or logos are used. Still placeholders before launch:

- review blocks (section disabled — publish only reviews you have received),
- press-bar logos (section disabled — upload only marks you may display),
- Instagram photos (section disabled),
- product images, which come from the products themselves.

Check before launch: the old FAQ lists Leinwand, Aluminium-Dibond and Holz as
materials, but the configurator offers LightBeton®, Premium-Aquarellpapier and
Leinwand auf Keilrahmen. The theme copy follows the configurator.

The theme ships no product artwork; empty carousels render Shopify's built-in
placeholder graphics.

## Rebuilding another site into this structure

`.claude/skills/site-to-sections/SKILL.md` is the playbook for pointing this
theme's section vocabulary at a different reference site: how to inventory a page
into bands, classify each band into a section type, pull design tokens out into
theme settings, assemble `templates/index.json`, and verify the result. It works
as plain documentation, and in Claude Code it is invocable as `/site-to-sections`.

## Browser support

Modern evergreen browsers. Carousels use CSS scroll-snap with JS controls and
degrade to plain horizontal scrolling if JS is unavailable.
