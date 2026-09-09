---
name: site-to-sections
description: Convert any reference website into this repo's Shopify section structure. Use when someone supplies a URL, a saved page, or screenshots and wants it rebuilt as an Online Store 2.0 theme — "clone this site", "build this as a Shopify theme", "match this layout", "add a section like X on their homepage". Covers band inventory, section classification, design-token extraction, templates/index.json assembly, and verification.
---

# Reference site → section structure

Turn a reference site into a working theme in this repo by decomposing its pages
into **horizontal bands**, mapping each band onto an existing section type, and
expressing the whole page as `templates/index.json`.

The rule that makes this fast: **almost every marketing page is a vertical stack
of full-width bands.** You are not reproducing a page, you are classifying a
stack. Twelve section types cover the overwhelming majority of storefronts.

---

## 1. Get the source

In rough order of fidelity:

| Input | How | Fidelity |
| --- | --- | --- |
| Live HTML/CSS | `wget -mkEpnp <url>`, or browser → Save Page As → Webpage, Complete | Exact — real spacing, fonts, breakpoints |
| Rendered DOM | DevTools → Elements → copy outer HTML of `<body>` | High — post-JS, but no stylesheet |
| Full-page screenshot | DevTools → Cmd/Ctrl-Shift-P → "Capture full size screenshot" | Structural only — proportions and order |
| Description | Prose | Low — treat output as a proposal |

**Egress is often blocked in cloud sessions.** Check before promising a fetch:

```bash
curl -sS -o /dev/null -w "%{http_code}\n" https://example.com/
curl -sS "$HTTPS_PROXY/__agentproxy/status"   # names the blocked host and reason
```

A `403 connect_rejected` is an organization policy denial — do not route around
it. Ask for a saved copy or screenshots instead, and say plainly that the result
will be a structural rebuild rather than a copy.

**State the fidelity you actually achieved.** A build from one screenshot is a
layout-level match: order, proportion, type scale and interaction patterns. Exact
fonts, spacing values and hover behaviour are inference. Say so.

---

## 2. Inventory the bands

Walk the page top to bottom. For each band record six things:

1. **Full-bleed or contained?** — does content run edge to edge or stop at a gutter?
2. **Background** — page white, subtle grey, or dark?
3. **Payload** — products, collections, photos, text, a form, logos?
4. **Arrangement** — horizontal scroll, fixed grid, single column, split?
5. **Item count and shape** — how many visible, what aspect ratio?
6. **Trailing action** — a centered button, a link, nothing?

Number them. This numbered list becomes the `order` array in `templates/index.json`,
one-to-one. Do the classification pass only after the inventory is complete —
deciding section types band by band tends to force early bands into the wrong type.

---

## 3. Classify each band

### Section catalogue

| Band looks like | Section | Repeatable | Key settings |
| --- | --- | --- | --- |
| Rotating promo strip, accent background | `announcement-bar` | in header group | `message` blocks, `interval`, `link_list` |
| Logo + nav + search/account/cart | `header` | in header group | `logo`, `menu` (2 nesting levels → mega menu) |
| Two-column: copy panel + big image | `hero-split` | yes | `heading`, `text`, rating, two CTAs, `image` |
| Row of press/partner wordmarks | `press-bar` | yes | `label`, `logo` blocks |
| Horizontally scrolling **product** cards | `product-carousel` | yes | `collection`, `products_to_show`, `slide_width`, `button_label`, `color_scheme` |
| Horizontally scrolling **collection/editorial** tiles | `collection-carousel` | yes | `edit` blocks, `slide_width` |
| Edge-to-edge grid of category tiles, dark | `category-tiles` | yes | `tile` blocks (label + collection + image) |
| Centered headline + one button, full-bleed colour | `cta-banner` | yes | `heading`, `text`, `button_*`, `color_scheme` |
| Stars + headline + testimonial cards | `reviews` | yes | `review` blocks (rating, title, text, author) |
| Social handle + square photo grid | `community` | yes | `photo` blocks, `eyebrow`, `link` |
| Email capture + fine print | `newsletter` | yes | `heading`, `button_label`, `fine_print` |
| Icon + title + line of copy, 3 across | `trust-badges` | in footer group | `badge` blocks (`icon`, `title`, `text`) |
| Multi-column link lists + legal row | `footer` | in footer group | `brand`/`links`/`text` blocks, `policy_menu` |

### Disambiguation

These four pairs cause nearly all misclassification:

- **`product-carousel` vs `collection-carousel`** — does a card show a *price*?
  Price → product. A card that is one photo plus a label → collection.
- **`collection-carousel` vs `category-tiles`** — carousels scroll and have a
  gutter; tiles are a fixed edge-to-edge grid, usually dark, usually 2 or 4 across.
- **`cta-banner` vs `hero-split`** — a hero has an image column. A CTA band is
  centered text on flat colour with one button.
- **`community` vs `collection-carousel`** — community is a square grid of
  user/lifestyle photography with no per-item label. Labels → collection tiles.

**Same section, different settings, repeated.** Four product carousels with
different headings and collections is correct and expected — that is what
`color_scheme`, `heading` and `slide_width` exist for. Do not author
`best-sellers.liquid`, `trending.liquid` and `new-drops.liquid`.

### Bands that map to nothing

Before writing a new section, try in order:

1. An existing section with different settings.
2. An existing section plus one new setting (cheap, backwards-compatible).
3. A new section — only when the *arrangement* is genuinely new, not the content.

Skip decorative bands that carry no content (spacer rules, parallax filler).

---

## 4. Extract the design tokens

Every visual value belongs in `config/settings_schema.json`, never hardcoded in a
section. `layout/theme.liquid` writes them into `:root` as custom properties, and
`assets/base.css` consumes only those. This is what makes one theme reskinnable.

Pull from the reference:

| Token | Where to look |
| --- | --- |
| `color_accent` | The announcement bar — usually the brand's loudest colour |
| `color_dark` | Hero panel / category band / CTA background |
| `color_subtle` | The alternating band background between white sections |
| `color_fg` / `color_bg` | Body text and page ground — rarely pure `#000`/`#fff`, check |
| `color_sale` | Sale price and badges |
| `page_width` | Measure the content gutter on a wide viewport |
| `button_style` | Square, slightly rounded, or pill |
| `card_image_ratio` | Measure one product card's image box |
| `font_heading` / `font_body` | DevTools computed `font-family`, else nearest match |

If a colour appears exactly once, it is probably a section setting, not a theme
token. If it appears in three unrelated bands, it is a token.

---

## 5. Assemble the template

`templates/index.json` is the deliverable — an ordered map of section instances.
Instance keys are yours to name; make them describe the band, not the type:

```json
{
  "sections": {
    "hero":     { "type": "hero-split", "settings": { "heading": "…" } },
    "trending": {
      "type": "product-carousel",
      "settings": { "heading": "Trending today", "slide_width": 260, "color_scheme": "default" }
    },
    "edits": {
      "type": "collection-carousel",
      "blocks": { "e1": { "type": "edit", "settings": {} } },
      "block_order": ["e1"],
      "settings": { "heading": "Explore edits" }
    }
  },
  "order": ["hero", "trending", "edits"]
}
```

Rules that bite:

- Every key in `blocks` must appear in `block_order`, or it silently vanishes.
- `order` is the visual sequence. It must list every key in `sections`.
- `type` must match the section filename without `.liquid`.
- Header and footer bands do **not** belong here — they live in
  `sections/header-group.json` and `sections/footer-group.json`.
- A section instance is not required to set every setting; omitted ones fall back
  to the schema `default`.

---

## 6. Authoring a new section

Match the house style or the theme stops being coherent.

```liquid
<section class="section {% if section.settings.color_scheme == 'subtle' %}section--subtle
                        {%- elsif section.settings.color_scheme == 'dark' %}section--dark{% endif %}">
  <div class="container section-header">
    <h2 class="section-header__title">{{ section.settings.heading }}</h2>
  </div>
  …
</section>

{% schema %}
{
  "name": "Thing",
  "settings": [
    { "type": "text", "id": "heading", "label": "Heading", "default": "Thing" },
    { "type": "select", "id": "color_scheme", "label": "Colour scheme", "default": "default",
      "options": [
        { "value": "default", "label": "Default" },
        { "value": "subtle",  "label": "Subtle"  },
        { "value": "dark",    "label": "Dark"    }
      ]}
  ],
  "blocks": [ { "type": "item", "name": "Item", "settings": [] } ],
  "presets": [ { "name": "Thing", "blocks": [ { "type": "item" } ] } ]
}
{% endschema %}
```

Conventions:

- Layout classes: `.container`, `.container--wide`, `.container--narrow`;
  bands get `.section` plus `.section--subtle` / `.section--dark`.
- Anything repeated is a **block**, never a numbered flat setting
  (`item_1_title`, `item_2_title` is the failure mode).
- Every section gets a `presets` entry or merchants cannot add it.
- New CSS goes in `assets/base.css` under a commented banner, using existing
  custom properties. No hardcoded hex.
- Icons go in `snippets/icon.liquid` as a new `when` branch.
- User-facing strings go through `locales/en.default.json` and `| t`.
- Every image needs a `placeholder_svg_tag` fallback so empty sections still render.

**Liquid trap:** `| t` binds to the whole filter chain. `{{ a | default: 'key' | t }}`
translates the *result*, not the key. Assign first:

```liquid
{%- assign fallback = 'some.key' | t -%}
{{ a | default: fallback }}
```

---

## 7. Content and rights

The layout is the deliverable. The content is not yours to take.

**Rebuild:** grid, spacing, type scale, colour system, component structure,
interaction patterns, section order.

**Do not ship:** artwork and product photography, marketing copy beyond generic
labels ("Best sellers", "View more"), press and partner logos, testimonials and
review text, the reference brand's name or wordmark.

Ship placeholders instead, and say so in the README and in any preview. For a
demo, prefer generated abstract SVG over stock imagery — it never carries a
licence question. Invent neutral product names; never reuse the reference's.

Set the store name to the new brand, not the reference's.

---

## 8. Verify before handing over

```bash
# every section's schema is valid JSON
python3 - <<'PY'
import json, re, glob
for p in sorted(glob.glob('sections/*.liquid')):
    m = re.search(r'\{%\s*schema\s*%\}(.*?)\{%\s*endschema\s*%\}', open(p).read(), re.S)
    if not m: print('NO SCHEMA', p); continue
    try: json.loads(m.group(1))
    except Exception as e: print('INVALID', p, e)
print('schemas checked')
PY

# every JSON template parses
for f in templates/*.json sections/*-group.json; do
  python3 -c "import json;json.load(open('$f'))" || echo "INVALID $f"
done

# liquid tags balance
python3 - <<'PY'
import re, glob
pairs = {'if':1,'unless':1,'for':1,'case':1,'form':1,'paginate':1,'schema':1,
         'comment':1,'capture':1,'style':1,'javascript':1}
for p in sorted(glob.glob('sections/*.liquid')+glob.glob('snippets/*.liquid')+glob.glob('layout/*.liquid')):
    stack=[]
    for t in re.findall(r'\{%-?\s*(\w+)', open(p).read()):
        if t in pairs: stack.append(t)
        elif t.startswith('end'):
            if stack and stack[-1]==t[3:]: stack.pop()
            else: print(p,'unexpected',t)
    if stack: print(p,'unclosed',stack)
print('balance checked')
PY
```

Then **look at it rendered** — layout bugs are close to invisible in source. Two
real ones found this way: an absolutely-positioned element resolving against the
padding box and clipping off-screen, and a nav/logo grid-column swap. Neither
shows up in any static check.

```bash
/opt/pw-browsers/chromium-1194/chrome-linux/chrome --headless --disable-gpu \
  --no-sandbox --hide-scrollbars --window-size=1440,1200 \
  --screenshot=/tmp/preview.png --virtual-time-budget=3000 \
  "file://$PWD/preview/index.html"
```

Against a real store: `shopify theme dev --store <store>.myshopify.com`.

Final pass: does band *n* in the reference correspond to `order[n]` in the
template? Any drift means a band was merged or dropped.

---

## Worked example

An art-print storefront homepage, from one screenshot, decomposed into twelve
bands (header and footer excluded, they live in the section groups):

| # | Band in reference | Section | Notes |
| --- | --- | --- | --- |
| 1 | Yellow promo strip, right-hand utility links | `announcement-bar` | header group |
| 2 | Wordmark left, facet nav centre, icons right | `header` | header group |
| 3 | Black copy panel + gallery-wall photo | `hero-split` | rating + one CTA |
| 4 | "As seen in" + five wordmarks | `press-bar` | own logos only |
| 5 | Best sellers, scrolling, "View more" | `product-carousel` | instance 1 |
| 6 | Explore edits, wide scrolling tiles | `collection-carousel` | `subtle` scheme |
| 7 | Trending today, scrolling | `product-carousel` | instance 2 |
| 8 | Dark 4-up category grid | `category-tiles` | edge to edge |
| 9 | Canvas prints, scrolling + subtitle | `product-carousel` | instance 3 |
| 10 | "Unsure where to start?" + quiz button | `cta-banner` | `dark` scheme |
| 11 | New drops, scrolling | `product-carousel` | instance 4 |
| 12 | Stars + headline + 3 testimonials | `reviews` | placeholder text |
| 13 | Instagram grid | `community` | |
| 14 | Email capture + fine print | `newsletter` | |
| 15 | 3 icon/title/text columns | `trust-badges` | footer group |
| 16 | 4 link columns + legal row | `footer` | footer group |

Four bands collapsed onto one section type with different settings. That ratio is
typical, and it is the signal that the decomposition is right.
