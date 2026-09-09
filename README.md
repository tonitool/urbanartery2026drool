# Urban Artery — Shopify theme

An Online Store 2.0 Shopify theme built to the layout of a contemporary art-print
storefront: split hero, press bar, product and collection carousels, dark category
tiles, quiz CTA, reviews, community gallery, newsletter, trust badges and a
four-column footer.

Everything is section-based and editable in the theme customizer. No build step,
no dependencies — plain Liquid, CSS and vanilla JS.

## Structure

```
assets/        base.css, theme.js
config/        settings_schema.json, settings_data.json
layout/        theme.liquid
locales/       en.default.json
sections/      homepage sections, template sections, header/footer groups
snippets/      product-card, icon, stars, meta-tags
templates/     index, product, collection, cart, search, page, 404, list-collections
```

### Homepage sections (order in `templates/index.json`)

| Section | File | Notes |
| --- | --- | --- |
| Split hero | `hero-split.liquid` | Dark copy panel + lifestyle image, star rating, two CTAs |
| Press logos | `press-bar.liquid` | Blocks; upload your own logos |
| Best sellers | `product-carousel.liquid` | Pick a collection per instance |
| Explore edits | `collection-carousel.liquid` | Wide collection tiles |
| Trending today | `product-carousel.liquid` | Second instance |
| Category tiles | `category-tiles.liquid` | Dark 4-up band |
| Canvas prints | `product-carousel.liquid` | Third instance |
| Quiz CTA | `cta-banner.liquid` | Dark band |
| New drops | `product-carousel.liquid` | Fourth instance |
| Reviews | `reviews.liquid` | Blocks, star ratings |
| Community gallery | `community.liquid` | Instagram-style grid |
| Newsletter | `newsletter.liquid` | Shopify customer form |

`trust-badges` and `footer` live in `sections/footer-group.json`;
`announcement-bar` and `header` live in `sections/header-group.json`.

## Install

Requires the [Shopify CLI](https://shopify.dev/docs/api/shopify-cli).

```bash
shopify theme dev   --store your-store.myshopify.com   # local preview with hot reload
shopify theme push  --store your-store.myshopify.com --unpublished
```

Or zip the repository root and upload it under **Online Store → Themes → Add theme →
Upload zip**.

## Setup after install

1. **Navigation** — create a `main-menu` link list. Two levels of nesting render as a
   mega menu; one level renders as a simple dropdown.
2. **Collections** — assign a collection to each product carousel and to the category
   tiles. Carousels fall back to placeholder cards while empty.
3. **Images** — upload the hero image, edit tiles, category tiles and community photos.
4. **Theme settings** — colors, fonts, page width, button shape and product-card
   options are all under **Theme settings**.
5. **Footer menus** — create link lists for the footer columns and the policy row.

## Customising

Colors and typography are driven by CSS custom properties written into
`layout/theme.liquid` from theme settings, so most rebranding is done in the
customizer rather than in CSS. The accent color drives the announcement bar; the
dark color drives the hero panel, category band and quiz CTA.

Card width on every carousel is a per-section setting (`slide_width`), so the number
of visible cards adapts to the page width without touching CSS.

## Content notice

All copy, reviews and imagery shipped with the theme are **placeholders**. Before
launch, replace:

- the placeholder review blocks (publish only reviews you have actually received),
- the press-bar logos (upload only marks you are licensed to display),
- hero, tile and gallery images,
- announcement-bar and newsletter copy.

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
