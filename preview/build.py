#!/usr/bin/env python3
"""Build static previews of the homepage and content pages from the theme's JSON templates.

A static stand-in for `shopify theme dev`: it reads templates/index.json, every
templates/page.*.json and the header/footer groups, and emits the same markup the
Liquid sections produce, using the images in media/. Re-run after editing a template:

    python3 preview/build.py
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PREVIEW = ROOT / "preview"

TOKENS = {
    "--font-body": "'Inconsolata', ui-monospace, Menlo, Consolas, monospace",
    "--font-body-weight": "400",
    "--font-heading": "'Allerta Stencil', 'Arial Narrow', sans-serif",
    "--font-heading-weight": "400",
    "--heading-tracking": "0.03em",
    "--font-size-base": "15px",
    "--heading-scale": "1",
    "--heading-transform": "uppercase",
    "--heading-bar": "block",
    "--color-bg": "#ffffff",
    "--color-fg": "#000000",
    "--color-muted": "#5c5c5c",
    "--color-border": "#e2e2e2",
    "--color-subtle": "#f1f1f1",
    "--color-dark": "#000000",
    "--color-dark-fg": "#ffffff",
    "--color-accent": "#e60073",
    "--color-accent-fg": "#ffffff",
    "--color-btn-bg": "#e60073",
    "--color-btn-fg": "#ffffff",
    "--color-sale": "#e60073",
    "--page-width": "1440px",
    "--gap": "20px",
    "--btn-radius": "0px",
    "--card-ratio": "3 / 4",
}

NAV = [("Konfigurator", "product.html"), ("Inspiration", "collection.html"), ("Über uns", "page.ueber-uns.html"),
       ("Auftragsarbeiten", "page.auftragsarbeiten.html"), ("Kontakt", "page.kontakt.html")]
PAGE_LINKS = {"So funktioniert's": "page.so-gehts.html", "FAQs": "page.faq.html",
              "Verpackung & Versand": "page.versand.html", "Über Urban Artery": "page.ueber-uns.html",
              "Auftragsarbeiten": "page.auftragsarbeiten.html", "Nimm Kontakt auf": "page.kontakt.html"}
FOOTER_LINKS = {
    "Hilfe": ["So funktioniert's", "FAQs", "Verpackung & Versand"],
    "Urban Artery": ["Über Urban Artery", "Auftragsarbeiten", "Nimm Kontakt auf"],
    "Rechtliches": ["Impressum", "Datenschutz", "AGB & Widerrufsrecht"],
}
PAYMENT = ["VISA", "MC", "AMEX", "PayPal", "Klarna", "G Pay", "Pay"]

# Preview-only product cards. Neutral names: real products come from the store.
DEMO_IMAGES = ["ua-motiv-por-favor.jpg", "ua-foto-kunst-nachher.jpg", "ua-motiv-whoa.jpg",
               "ua-quer-hoch-nachher.jpg", "ua-motiv-trane.jpg", "ua-auftragsarbeiten.jpg"]
# Sample piece names for the preview (the real store shows its own product titles).
DEMO_NAMES = ["Kopfkino", "Katzenjammer", "Bitte, Teufel", "Lauter Kopf",
              "Altbau Blues", "König Schrei", "Hörnchen", "Sonntag im Loft"]
DEMO_PRODUCTS = [(name, "Ab 200,00 €") for name in DEMO_NAMES]


# Which sample piece shows which artwork (packshot name -> demo number), matching preview/make_demo.py.
ART_TO_DEMO = {"trane": 1, "whoa": 2, "por-favor": 3, "robot": 5}


def demo_name(n: int) -> str:
    """Name of sample piece n (1-based)."""
    return DEMO_NAMES[(n - 1) % len(DEMO_NAMES)]
DEMO_BADGES = {0: "Neu", 3: "Limitiert", 5: "Unikat"}   # from product tags badge:<text> in the real theme
DEMO_QUICK_ADD = {1, 4, 6}                                # single-variant products only
DEMO_DESCRIPTION = ("Beispieltext: Handgefertigtes Street-Art-Unikat auf LightBeton®, von unseren Künstlern "
                    "von Hand umgesetzt. Erhältlich von S (20 × 30 cm) bis XL (120 × 180 cm), im Hoch- oder Querformat.")
MEDIA_PREFIX = "shopify://shop_images/"

e = html.escape


# --------------------------------------------------------------------------
# Icons (subset of snippets/icon.liquid)
# --------------------------------------------------------------------------
ICONS = {
    "arrow-left": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M10 3 5 8l5 5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "arrow-right": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M6 3l5 5-5 5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "search": '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="8.6" cy="8.6" r="5.6"/><path d="M12.8 12.8 17 17" stroke-linecap="round"/></svg>',
    "account": '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="10" cy="6.6" r="3.4"/><path d="M3.6 17c0-3.3 2.9-5.4 6.4-5.4s6.4 2.1 6.4 5.4" stroke-linecap="round"/></svg>',
    "cart": '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3.4 5.6h13.2l-1.1 10a1.4 1.4 0 0 1-1.4 1.3H5.9a1.4 1.4 0 0 1-1.4-1.3z"/><path d="M7.2 8V5.2a2.8 2.8 0 0 1 5.6 0V8" stroke-linecap="round"/></svg>',
    "menu": '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M3 6h14M3 10h14M3 14h14" stroke-linecap="round"/></svg>',
    "heart": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M12 20.5s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.6a4.3 4.3 0 0 1 7.5 2.7c0 5.6-7.5 10.2-7.5 10.2z" stroke-linejoin="round"/></svg>',
    "plus": '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M10 4v12M4 10h12" stroke-linecap="round"/></svg>',
    "close": '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M5 5l10 10M15 5L5 15" stroke-linecap="round"/></svg>',
    "caret": '<svg class="nav__caret" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 4l3 3 3-3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "mail": '<svg class="trust__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="5.5" width="18" height="13" rx="1"/><path d="m3.5 6.5 8.5 6.5 8.5-6.5" stroke-linejoin="round"/></svg>',
    "phone": '<svg class="trust__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6.6 3.5h3l1.4 4-2 1.3a11 11 0 0 0 6.2 6.2l1.3-2 4 1.4v3a1.6 1.6 0 0 1-1.7 1.6C10.6 18.4 5.6 13.4 5 5.2a1.6 1.6 0 0 1 1.6-1.7z" stroke-linejoin="round"/></svg>',
    "package": '<svg class="trust__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 3 20 7v10l-8 4-8-4V7z" stroke-linejoin="round"/><path d="M4 7l8 4 8-4M12 11v10M8 5l8 4" stroke-linejoin="round"/></svg>',
    "clock": '<svg class="trust__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "play": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5.5v13l10.5-6.5z"/></svg>',
    "upload": '<svg class="trust__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 15.5V4m0 0L7.5 8.5M12 4l4.5 4.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M4 14.5v4A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5v-4" stroke-linecap="round"/></svg>',
    "frame": '<svg class="trust__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3.5" y="3.5" width="17" height="17"/><rect x="7" y="7" width="10" height="10"/><path d="m7 15 3-3 2 2 2-2.5 3 3.5"/></svg>',
    "hand": '<svg class="trust__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M8 12.5V5.5a1.5 1.5 0 0 1 3 0v6m0-1V4a1.5 1.5 0 0 1 3 0v6.5m0-.5V5.5a1.5 1.5 0 0 1 3 0V14c0 4-2.6 7-6.5 7-2.4 0-3.9-1-5.3-3L3.6 14a1.5 1.5 0 0 1 2.4-1.8L8 14.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "truck": '<svg class="trust__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 6.5h11v10H2zM13 9.5h4.4l3.6 3.4v3.6h-8z"/><circle cx="6.6" cy="18" r="1.8"/><circle cx="16.4" cy="18" r="1.8"/></svg>',
    "palette": '<svg class="trust__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 3a9 9 0 1 0 0 18c1.2 0 1.9-.9 1.9-1.8 0-1.4-1.1-1.7-1.1-2.7 0-.8.7-1.4 1.5-1.4H16A5 5 0 0 0 21 10c0-3.9-4-7-9-7z"/></svg>',
    "shield": '<svg class="trust__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 3 4.5 6v5.5c0 4.6 3.2 8.2 7.5 9.5 4.3-1.3 7.5-4.9 7.5-9.5V6z" stroke-linejoin="round"/><path d="m8.8 12 2.2 2.2 4.2-4.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "badge": '<svg class="trust__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="9.5" r="6"/><path d="m8.4 14.6-1.2 6 4.8-2.4 4.8 2.4-1.2-6" stroke-linejoin="round"/></svg>',
    "instagram": '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2.8" y="2.8" width="14.4" height="14.4" rx="4.2"/><circle cx="10" cy="10" r="3.6"/></svg>',
}

# --------------------------------------------------------------------------
# Placeholder artwork: flat stencil-style compositions, generated not sourced.
# --------------------------------------------------------------------------
GROUNDS = ["#f4e9ef", "#ececec", "#f6efe2", "#e3e9ef", "#f9d9e8", "#dfe6dd", "#efe4f3", "#f2f2f2"]


def art(seed: int, w: int = 300, h: int = 400, photo: bool = False) -> str:
    g = GROUNDS[seed % len(GROUNDS)]
    if photo:  # the "before" photo: soft, desaturated
        return (f'<svg class="placeholder-svg" viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMid slice">'
                f'<rect width="{w}" height="{h}" fill="#cfc9c2"/>'
                f'<ellipse cx="{w*.5}" cy="{h*.42}" rx="{w*.16}" ry="{h*.2}" fill="#a79f97"/>'
                f'<rect x="{w*.26}" y="{h*.6}" width="{w*.48}" height="{h*.4}" rx="{w*.18}" fill="#8f877f"/></svg>')
    cx, cy = w * (0.42 + (seed % 3) * 0.08), h * 0.42
    drips = "".join(
        f'<rect x="{w*(0.2+i*0.14)}" y="{h*0.08}" width="{w*0.035}" height="{h*(0.18+((seed+i)%4)*0.09)}" fill="#e60073"/>'
        for i in range(5)
    )
    return (f'<svg class="placeholder-svg" viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMid slice">'
            f'<rect width="{w}" height="{h}" fill="{g}"/>{drips}'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{w*.18}" ry="{h*.17}" fill="#1c1c1c"/>'
            f'<ellipse cx="{cx+w*.03}" cy="{cy+h*.02}" rx="{w*.12}" ry="{h*.12}" fill="#8a8a8a"/>'
            f'<path d="M{w*.14} {h} Q{cx} {h*.5} {w*.86} {h}Z" fill="#1c1c1c"/>'
            f'<path d="M{w*.3} {h} Q{cx} {h*.62} {w*.7} {h}Z" fill="#bdbdbd"/></svg>')


def picture(value: str | None, seed: int, cls: str = "", fit: str = "cover", alt: str = "") -> str:
    """Render a template image reference from media/, or generated art when unset."""
    if value and value.startswith(MEDIA_PREFIX):
        name = value[len(MEDIA_PREFIX):]
        return f'<img class="{cls}" src="../media/{e(name)}" alt="{e(alt)}" loading="lazy" style="width:100%;height:100%;object-fit:{fit}">'
    return art(seed)


def demo_image(i: int, alt: str = "") -> str:
    """Product-card image: a room mockup from preview/demo/ (rendered by mockups/place.py)."""
    demos = sorted((PREVIEW / "demo").glob("demo-*.jpg"))
    if demos:
        return f'<img src="demo/{demos[i % len(demos)].name}" alt="{e(alt)}" loading="lazy" style="width:100%;height:100%;object-fit:cover">'
    return picture(MEDIA_PREFIX + DEMO_IMAGES[i % len(DEMO_IMAGES)], i)


def scheme(s: dict) -> str:
    return {"subtle": " section--subtle", "dark": " section--dark"}.get(s.get("color_scheme", "default"), "")


def heading(s: dict) -> str:
    parts = []
    if s.get("eyebrow"):
        parts.append(f'<p class="section-header__eyebrow">{e(s["eyebrow"])}</p>')
    if s.get("heading"):
        parts.append(f'<h2 class="section-header__title">{e(s["heading"])}</h2>')
    if s.get("subheading"):
        parts.append(f'<p class="section-header__subtitle">{e(s["subheading"])}</p>')
    return f'<div class="container section-header">{"".join(parts)}</div>' if parts else ""


def button(label: str | None, dark: bool = False, arrow: bool = False) -> str:
    if not label:
        return ""
    cls = "btn btn--light" if dark else "btn"
    return f'<div class="section-footer"><a class="{cls}" href="#">{e(label)}{" " + ICONS["arrow-right"] if arrow else ""}</a></div>'


def carousel(slides: list[str], width: int, extra: str = "") -> str:
    return (f'<div class="carousel{extra}" data-carousel style="--slide-width: {width}px;">'
            f'<button class="carousel__btn carousel__btn--prev" type="button" data-carousel-prev aria-label="Zurück">{ICONS["arrow-left"]}</button>'
            f'<ul class="carousel__track" data-carousel-track>{"".join(slides)}</ul>'
            f'<button class="carousel__btn carousel__btn--next" type="button" data-carousel-next aria-label="Weiter">{ICONS["arrow-right"]}</button></div>')


# --------------------------------------------------------------------------
# Section renderers — one per section type used in the templates
# --------------------------------------------------------------------------
def r_announcement(sec: dict) -> str:
    msgs = [sec["blocks"][k]["settings"]["text"] for k in sec["block_order"]]
    items = "".join(f'<div class="announcement__message{" is-active" if i == 0 else ""}">{e(m)}</div>' for i, m in enumerate(msgs))
    return (f'<div class="announcement" data-announcement data-interval="{sec["settings"].get("interval", 5) * 1000}">'
            f'<div class="container container--wide announcement__inner"><div class="announcement__messages">{items}</div></div></div>')


def r_header(sec: dict) -> str:
    dark = sec["settings"].get("color_scheme") == "dark"
    links = "".join(f'<li class="nav__item"><a class="nav__link" href="{h}">{e(n)}</a></li>' for n, h in NAV)
    logo_value = sec["settings"].get("logo", "")
    logo = (f'<img src="../media/{e(logo_value[len(MEDIA_PREFIX):])}" alt="Urban Artery" style="max-height:{sec["settings"].get("logo_height", 34)}px;width:auto">'
            if logo_value.startswith(MEDIA_PREFIX) else None) or ('<svg viewBox="0 0 120 52" height="42" aria-label="Urban Artery" role="img">'
            '<text x="60" y="22" text-anchor="middle" font-family="Allerta Stencil" font-size="22" fill="currentColor">URBAN</text>'
            '<text x="60" y="47" text-anchor="middle" font-family="Georgia, serif" font-style="italic" font-weight="700" font-size="24" fill="currentColor">Artery</text></svg>')
    return (f'<header class="header{" header--dark" if dark else ""}"><div class="container container--wide header__inner">'
            f'<button class="header__toggle" type="button" data-drawer-open aria-controls="MenuDrawer" aria-expanded="false" aria-label="Menü">{ICONS["menu"]}</button>'
            f'<a class="header__logo" href="index.html">{logo}</a>'
            f'<nav class="nav" aria-label="Menü"><ul class="nav__list">{links}</ul></nav>'
            f'<div class="header__actions"><a class="btn btn--small header__cta" href="#">{e(sec["settings"].get("cta_label", ""))}</a>'
            f'<a class="header__action" href="#" aria-label="Suche">{ICONS["search"]}</a>'
            f'<a class="header__action" href="#" aria-label="Merkliste">{ICONS["heart"]}<span class="cart-count" data-wishlist-count hidden>0</span></a>'
            f'<a class="header__action" href="#" aria-label="Konto">{ICONS["account"]}</a>'
            f'<a class="header__action" href="#" aria-label="Warenkorb">{ICONS["cart"]}<span class="cart-count">1</span></a></div>'
            f'</div></header>'
            f'<div class="drawer" id="MenuDrawer" role="dialog" aria-modal="true" aria-label="Menü">'
            f'<div class="drawer__head"><span class="header__logo">Urban Artery</span>'
            f'<button class="header__action" type="button" data-drawer-close aria-label="Schließen">{ICONS["close"]}</button></div>'
            + "".join(f'<a class="drawer__link" href="{h}">{e(n)}</a>' for n, h in NAV)
            + '</div><div id="Overlay" class="overlay" hidden></div>')


def r_hero(sec: dict) -> str:
    s = sec["settings"]
    b2 = f'<a class="btn btn--outline" href="#">{e(s["button_label_2"])}</a>' if s.get("button_label_2") else ""
    return (f'<section class="hero"><div class="hero__panel"><h1 class="hero__title">{e(s["heading"])}</h1>'
            f'<p class="hero__text">{e(s["text"])}</p>'
            f'<div class="hero__buttons"><a class="btn" href="#">{e(s["button_label"])}</a>{b2}</div></div>'
            f'<div class="hero__media">{hero_media(s)}</div></section>')


def hero_media(s: dict) -> str:
    if s.get("video_url"):
        poster = s.get("image", "")
        poster_attr = f' poster="../media/{e(poster[len(MEDIA_PREFIX):])}"' if poster.startswith(MEDIA_PREFIX) else ""
        return (f'<video class="hero__video" autoplay muted loop playsinline preload="metadata" data-autoplay{poster_attr}>'
                f'<source src="{e(s["video_url"])}" type="video/mp4"></video>')
    return picture(s.get("image"), 4, alt=s.get("heading", ""))


def demo_card(n: int) -> str:
    """Sample product card n (1-based), same markup as snippets/product-card.liquid."""
    i = n - 1
    title = demo_name(n)
    badge = f'<span class="product-card__badge product-card__badge--tag">{DEMO_BADGES[i]}</span>' if i in DEMO_BADGES else ""
    heart = (f'<button class="wishlist-button" type="button" data-wishlist-toggle="beispielwerk-{n:02d}" aria-pressed="false" '
             f'aria-label="{title} merken" data-label-add="{title} merken" data-label-remove="{title} von der Merkliste entfernen">{ICONS["heart"]}</button>')
    quick = (f'<form class="product-card__quick-add" onsubmit="return false"><button class="product-card__quick-add-btn" type="submit" '
             f'aria-label="{title} in den Warenkorb">{ICONS["plus"]}<span>In den Warenkorb</span></button></form>') if i in DEMO_QUICK_ADD else ""
    return (f'<div class="product-card"><div class="product-card__media-wrap">'
            f'<a class="product-card__media" href="#demo-{n:02d}" data-quick-view="#demo-{n:02d}" aria-haspopup="dialog" '
            f'aria-label="Schnellansicht: {title}">{demo_image(i, title)}{badge}</a>{heart}{quick}</div>'
            f'<div class="product-card__info"><h3 class="product-card__title"><a href="product.html">{title}</a></h3>'
            f'<p class="product-card__price">Ab 200,00 €</p></div></div>')


def r_product_carousel(sec: dict) -> str:
    s = sec["settings"]
    offset = len(s["heading"])
    slides = [f'<li class="carousel__slide">{demo_card((i + offset) % len(DEMO_PRODUCTS) + 1)}</li>' for i in range(len(DEMO_PRODUCTS))]
    dark = s.get("color_scheme") == "dark"
    return f'<section class="section{scheme(s)}">{heading(s)}{carousel(slides, s["slide_width"])}{button(s.get("button_label"), dark)}</section>'


def r_main_collection(sec: dict) -> str:
    cards = "".join(f"<li>{demo_card(n)}</li>" for n in range(1, len(DEMO_PRODUCTS) + 1))
    return ('<div class="container"><div class="collection-hero"><h1 class="collection-hero__title">Fertige Werke</h1>'
            '<div class="collection-hero__desc rte"><p>Beispieltext: Fertig gestaltet, handgefertigt, bereit zum Aufhängen.</p></div></div>'
            f'<div class="collection-toolbar"><span>{len(DEMO_PRODUCTS)} Werke</span><label><span class="visually-hidden">Sortieren nach</span>'
            '<select class="field" style="min-height:38px;padding-block:7px;"><option>Beliebt</option><option>Neueste</option>'
            '<option>Preis aufsteigend</option></select></label></div>'
            f'<ul class="product-grid">{cards}</ul></div>')


def r_related(sec: dict) -> str:
    slides = [f'<li class="carousel__slide">{demo_card(n)}</li>' for n in (1, 2, 4, 5, 6, 7)]
    return (f'<section class="section"><div class="container section-header"><h2 class="section-header__title">{e(sec["settings"]["heading"])}</h2></div>'
            f'{carousel(slides, 260)}</section>')


def r_main_product(sec: dict) -> str:
    """Sample product page: same markup as sections/main-product.liquid, with demo 03."""
    manifest = json.loads((PREVIEW / "demo" / "manifest.json").read_text())[2]["slides"]
    title = demo_name(3)
    main_img = f'<img id="ProductMainImage" src="demo/{manifest[0]["file"]}" alt="{title} – {manifest[0]["label"]}">'
    thumbs = "".join(
        f'<button class="product__thumb" type="button" onclick="document.getElementById(\'ProductMainImage\').src=\'demo/{sl["file"]}\'" '
        f'aria-label="{e(sl["label"])}"><img src="demo/{sl["file"]}" width="160" height="160" alt="{title} – {e(sl["label"])}"></button>' for sl in manifest)
    def options(name, values, checked=0):
        pills = "".join(f'<label class="option__value"><input type="radio" name="opt-{name}" value="{e(v)}" {"checked" if k == checked else ""}><span>{e(v)}</span></label>'
                        for k, v in enumerate(values))
        return f'<div class="option"><span class="option__label">{name}</span><div class="option__values">{pills}</div></div>'
    b = sec["blocks"]
    trust = "".join(f'<li class="product-trust__item">{ICONS.get(b[k]["settings"]["icon"], "")}<span>{e(b[k]["settings"]["text"])}</span></li>'
                    for k in sec["block_order"] if b[k]["type"] == "trust_item")
    acc = []
    for k in sec["block_order"]:
        blk = b[k]
        if blk["type"] == "description":
            acc.append(f'<details class="accordion" open><summary>{e(blk["settings"]["title"])} {ICONS["caret"]}</summary>'
                       f'<div class="accordion__body rte"><p>{e(DEMO_DESCRIPTION)}</p></div></details>')
        elif blk["type"] == "accordion":
            acc.append(f'<details class="accordion"><summary>{e(blk["settings"]["title"])} {ICONS["caret"]}</summary>'
                       f'<div class="accordion__body rte">{blk["settings"]["content"]}</div></details>')
    pay = "".join(f'<li><span class="payment-icon payment-icon--demo">{p}</span></li>' for p in PAYMENT)
    s = sec["settings"]
    return (f'<div class="container product"><div class="product__gallery"><div class="product__main-image">{main_img}</div>'
            f'<div class="product__thumbs">{thumbs}</div></div>'
            f'<div class="product__details"><div class="product__title-row"><h1 class="product__title">{title}</h1>'
            f'<button class="wishlist-button" type="button" data-wishlist-toggle="beispielwerk-03" aria-pressed="false" aria-label="{title} merken" '
            f'data-label-add="{title} merken" data-label-remove="{title} von der Merkliste entfernen">{ICONS["heart"]}</button></div>'
            f'<p class="product__vendor">Von Urban Artery</p><p class="product__price" data-product-price><span>Ab 200,00 €</span></p>'
            f'<p class="product__tax-note">inkl. MwSt., zzgl. Versandkosten</p>'
            f'<form class="product-form" onsubmit="return false">'
            f'{options("Größe", ["S (20×30 cm)", "M (40×60 cm)", "L (80×120 cm)", "XL (120×180 cm)"], 2)}'
            f'{options("Format", ["Hochformat", "Querformat"], 1)}'
            f'{options("Trägermaterial", ["LightBeton®", "Premium-Aquarellpapier", "Leinwand auf Keilrahmen"])}'
            f'<div class="preview-app-slot">Hier erscheint der Zakeke-Konfigurator (App-Block)</div>'
            f'<button class="btn btn--full" type="submit" data-add-to-cart>In den Warenkorb</button>'
            f'<p class="product__delivery">{ICONS["clock"]}<span>{e(s.get("delivery_note", ""))}</span></p>'
            f'<ul class="product__payment" role="list">{pay}</ul></form>'
            f'<ul class="product-trust" role="list">{trust}</ul>{"".join(acc)}</div></div>'
            f'<div class="sticky-buy" data-sticky-buy hidden><div class="sticky-buy__info"><p class="sticky-buy__title">{title}</p>'
            f'<p class="sticky-buy__price" data-product-price>Ab 200,00 €</p></div><button class="btn" type="button">In den Warenkorb</button></div>')


def r_collection_carousel(sec: dict) -> str:
    s = sec["settings"]
    overlay = s.get("card_style") == "overlay"
    slides = []
    for i, k in enumerate(sec["block_order"]):
        b = sec["blocks"][k]["settings"]
        text = f'<p class="edit-card__text">{e(b["text"])}</p>' if b.get("text") else ""
        cta = f'<span class="edit-card__cta">{e(b["link_label"])} {ICONS["arrow-right"]}</span>' if b.get("link_label") else ""
        media = picture(b.get("image"), i + 2, alt=b.get("title", ""))
        slides.append(f'<li class="carousel__slide"><a class="edit-card" href="#"><div class="edit-card__media">{media}</div>'
                      f'<div class="edit-card__body"><p class="edit-card__title">{e(b.get("title", ""))}</p>{text}{cta}</div></a></li>')
    extra = " carousel--overlay" if overlay else ""
    return f'<section class="section{scheme(s)}">{heading(s)}{carousel(slides, s["slide_width"], extra)}{button(s.get("button_label"), arrow=True)}</section>'


def r_before_after(sec: dict) -> str:
    s = sec["settings"]
    figs = []
    for i, k in enumerate(sec["block_order"]):
        b = sec["blocks"][k]["settings"]
        figs.append(f'<figure class="ba"><figcaption class="ba__title">{e(b["title"])}</figcaption>'
                    f'<div class="ba__frame" data-before-after style="--ba-pos: 50%;">'
                    f'<div class="ba__layer ba__layer--after">{picture(b.get("image_after"), i + 5, alt=b["title"] + " – " + s["after_label"])}</div>'
                    f'<div class="ba__layer ba__layer--before">{picture(b.get("image_before"), 0, alt=b["title"] + " – " + s["before_label"])}</div>'
                    f'<span class="ba__tag ba__tag--before">{e(s["before_label"])}</span><span class="ba__tag ba__tag--after">{e(s["after_label"])}</span>'
                    f'<span class="ba__handle">{ICONS["arrow-left"]}{ICONS["arrow-right"]}</span>'
                    f'<input class="ba__range" type="range" min="0" max="100" value="50" aria-label="Vorher und Nachher vergleichen: {e(b["title"])}" data-before-after-range>'
                    f'</div>{"<p class=ba__text>" + e(b["text"]) + "</p>" if b.get("text") else ""}</figure>')
    btn = button(s.get("button_label"))
    return f'<section class="section{scheme(s)}">{heading(s)}<div class="container"><div class="ba-grid">{"".join(figs)}</div>{btn}</div></section>'


def r_category_tiles(sec: dict) -> str:
    tiles = "".join(f'<a class="tile" href="#">{picture(sec["blocks"][k]["settings"].get("image"), i + 3, alt=sec["blocks"][k]["settings"]["label"])}<span class="tile__label">{e(sec["blocks"][k]["settings"]["label"])}</span></a>'
                    for i, k in enumerate(sec["block_order"]))
    return f'<section class="tile-band"><div class="tile-band__grid">{tiles}</div></section>'


def r_cta(sec: dict) -> str:
    s = sec["settings"]
    dark = s.get("color_scheme") == "dark"
    return (f'<section class="cta-band{scheme(s)}"><div class="container container--narrow"><h2 class="cta-band__title">{e(s["heading"])}</h2>'
            f'<p class="cta-band__text">{e(s["text"])}</p>'
            + (f'<a class="btn{" btn--light" if dark else ""}" href="#">{e(s["button_label"])}</a>' if s.get("button_label") else "")
            + '</div></section>')


def r_trust(sec: dict) -> str:
    s = sec["settings"]
    has_heading = bool(s.get("heading") or s.get("eyebrow"))
    items = []
    for i, k in enumerate(sec["block_order"]):
        b = sec["blocks"][k]["settings"]
        step = f'<span class="trust__step">{i + 1}</span>' if s.get("numbered") else ""
        items.append(f'<li class="trust__item">{step}{ICONS.get(b["icon"], "")}<p class="trust__title">{e(b["title"])}</p><p class="trust__text">{e(b["text"])}</p></li>')
    cls = "trust" + (" trust--section section" if has_heading else "") + (" trust--numbered" if s.get("numbered") else "") + scheme(s)
    return (f'<section class="{cls}">{heading(s) if has_heading else ""}<div class="container container--wide">'
            f'<ol class="trust__grid" role="list">{"".join(items)}</ol>{button(s.get("button_label"))}</div></section>')


def r_video(sec: dict) -> str:
    s = sec["settings"]
    if s.get("video_url"):
        poster = s.get("poster", "")
        poster_attr = f' poster="../media/{e(poster[len(MEDIA_PREFIX):])}"' if poster.startswith(MEDIA_PREFIX) else ""
        media = f'<video class="video-band__media" controls playsinline preload="none"{poster_attr}><source src="{e(s["video_url"])}" type="video/mp4"></video>'
    else:
        media = f'<div class="video-band__placeholder">{art(2, 1600, 900)}<span class="video-band__play">{ICONS["play"]}</span></div>'
    return f'<section class="section{scheme(s)}">{heading(s)}<div class="container"><div class="video-band">{media}</div></div></section>'


def r_community(sec: dict) -> str:
    s = sec["settings"]
    photos = "".join(f'<a class="community__item" href="#">{art(i, 400, 400)}</a>' for i in range(len(sec["block_order"])))
    return (f'<section class="section{scheme(s)}"><div class="container community">'
            f'<p class="community__eyebrow">{e(s["eyebrow"])}</p><h2 class="community__title">{e(s["heading"])}</h2>'
            f'<p class="community__text">{e(s["text"])}</p></div><div class="community__grid">{photos}</div></section>')


def r_newsletter(sec: dict) -> str:
    s = sec["settings"]
    return (f'<section class="section{scheme(s)}"><div class="container newsletter">'
            f'<div class="section-header"><h2 class="section-header__title">{e(s["heading"])}</h2><p class="section-header__subtitle">{e(s["text"])}</p></div>'
            f'<form class="newsletter__form" onsubmit="return false"><input class="field" type="email" placeholder="E-Mail-Adresse" aria-label="E-Mail-Adresse">'
            f'<button class="btn" type="submit">{e(s["button_label"])}</button></form>'
            f'<div class="newsletter__fine rte">{s["fine_print"]}</div></div></section>')


def r_footer(sec: dict) -> str:
    s = sec["settings"]
    cols = []
    for k in sec["block_order"]:
        b = sec["blocks"][k]
        title = b["settings"].get("title", "")
        if b["type"] == "links":
            items = "".join(f'<li><a href="{PAGE_LINKS.get(x, "#")}">{e(x)}</a></li>' for x in FOOTER_LINKS.get(title, []))
            cols.append(f'<div><p class="footer__title">{e(title)}</p><ul class="footer__list">{items}</ul></div>')
        else:
            cols.append(f'<div><p class="footer__title">{e(title)}</p><div class="rte" style="font-size:0.8rem">{b["settings"].get("text", "")}</div>'
                        f'<div class="footer__social"><a href="#" aria-label="Instagram">{ICONS["instagram"]}</a></div></div>')
    pay = "".join(f'<li><span class="payment-icon payment-icon--demo">{p}</span></li>' for p in PAYMENT) if s.get("show_payment_icons") else ""
    bg = s.get("background_image", "")
    bg_css = f"--footer-image: url('../media/{bg[len(MEDIA_PREFIX):]}');" if bg.startswith(MEDIA_PREFIX) else ""
    logo = s.get("logo", "")
    logo_html = (f'<a class="footer__logo" href="#"><img src="../media/{e(logo[len(MEDIA_PREFIX):])}" alt="Urban Artery"></a>'
                 if logo.startswith(MEDIA_PREFIX) else "")
    return (f'<footer class="footer{" footer--image" if bg_css else ""}" style="{bg_css}--footer-bg: {s["background"]}; --footer-fg: {s["text_color"]};"><div class="container container--wide">'
            f'<div class="footer__grid">{"".join(cols)}</div>{logo_html}<ul class="footer__payment" role="list">{pay}</ul>'
            f'<div class="footer__bottom"><span>&copy; 2026 Urban Artery</span><span>Impressum · Datenschutz · AGB</span></div></div></footer>')


def r_page_header(sec: dict) -> str:
    s = sec["settings"]
    eyebrow = f'<p class="section-header__eyebrow">{e(s["eyebrow"])}</p>' if s.get("eyebrow") else ""
    text = f'<p class="page-header__text">{e(s["text"])}</p>' if s.get("text") else ""
    return (f'<section class="page-header{scheme(s)}"><div class="container container--narrow">{eyebrow}'
            f'<h1 class="page-header__title">{e(s.get("heading") or "Seitentitel")}</h1>{text}</div></section>')


def r_rich_text(sec: dict) -> str:
    s = sec["settings"]
    has_image = bool(s.get("image"))
    media = f'<div class="rich-text__media">{picture(s["image"], 1)}</div>' if has_image else ""
    eyebrow = f'<p class="section-header__eyebrow">{e(s["eyebrow"])}</p>' if s.get("eyebrow") else ""
    title = f'<h2 class="rich-text__title">{e(s["heading"])}</h2>' if s.get("heading") else ""
    btn = ""
    if s.get("button_label"):
        cls = "btn btn--outline" if s.get("button_style") == "outline" else "btn"
        btn = f'<a class="{cls}" href="#">{e(s["button_label"])} {ICONS["arrow-right"]}</a>'
    layout = "rich-text--with-image" if has_image else "container--narrow"
    return (f'<section class="section rich-text{scheme(s)}"><div class="container {layout} rich-text--{s.get("alignment", "left")}">'
            f'{media}<div class="rich-text__body">{eyebrow}{title}<div class="rte">{s.get("text", "")}</div>{btn}</div></div></section>')


def r_text_columns(sec: dict) -> str:
    s = sec["settings"]
    cols = []
    for k in sec["block_order"]:
        b = sec["blocks"][k]["settings"]
        media = f'<div class="text-columns__media">{picture(b["image"], 2)}</div>' if b.get("image") else ""
        cols.append(f'<div class="text-columns__item">{media}<h3 class="text-columns__title">{e(b.get("title", ""))}</h3>'
                    f'<div class="text-columns__text rte">{b.get("text", "")}</div></div>')
    quote = " text-columns--quote" if s.get("style") == "quote" else ""
    return f'<section class="section{scheme(s)}">{heading(s)}<div class="container"><div class="text-columns{quote}">{"".join(cols)}</div></div></section>'


def r_faq(sec: dict) -> str:
    s = sec["settings"]
    items = "".join(f'<details class="accordion"><summary>{e(sec["blocks"][k]["settings"]["question"])} {ICONS["caret"]}</summary>'
                    f'<div class="accordion__body rte">{sec["blocks"][k]["settings"]["answer"]}</div></details>' for k in sec["block_order"])
    return f'<section class="section{scheme(s)}">{heading(s)}<div class="container container--narrow faq">{items}</div></section>'


def r_contact(sec: dict) -> str:
    s = sec["settings"]
    channels = []
    for k in sec["block_order"]:
        b = sec["blocks"][k]["settings"]
        text = f'<p class="contact__channel-text">{e(b["text"])}</p>' if b.get("text") else ""
        channels.append(f'<li class="contact__channel"><span class="contact__icon">{ICONS.get(b["icon"], "")}</span><div>'
                        f'<p class="contact__channel-title">{e(b["title"])}</p><a class="contact__channel-link" href="{e(b["link"])}">{e(b["link_label"])}</a>{text}</div></li>')
    field = lambda ph, t="text": f'<input class="field" type="{t}" placeholder="{ph}" aria-label="{ph}">'
    form = (f'<form class="contact__form" onsubmit="return false"><div class="contact__row">{field("Vorname")}{field("Nachname")}</div>'
            f'{field("E-Mail-Adresse", "email")}{field("Bestellnummer (optional)")}{field("Betreff")}'
            f'<textarea class="field contact__message" rows="6" placeholder="Deine Nachricht" aria-label="Deine Nachricht"></textarea>'
            f'<div class="contact__privacy rte">{s.get("privacy_note", "")}</div><button class="btn" type="submit">Nachricht senden</button></form>')
    return (f'<section class="section"><div class="container contact"><div class="contact__info"><h2 class="contact__heading">{e(s["info_heading"])}</h2>'
            f'<ul class="contact__channels" role="list">{"".join(channels)}</ul><p class="contact__note">{e(s.get("note", ""))}</p></div>'
            f'<div class="contact__form-wrap"><h2 class="contact__heading">{e(s["form_heading"])}</h2>{form}</div></div></section>')


def media_img(value: str, cls: str, alt: str = "") -> str:
    if value and value.startswith(MEDIA_PREFIX):
        return f'<img class="{cls}" src="../media/{e(value[len(MEDIA_PREFIX):])}" alt="{e(alt)}" draggable="false">'
    return art(1)


def motion_toggle(target: str, cls: str) -> str:
    return (f'<button type="button" class="motion-toggle {cls}" data-motion-toggle="{target}" aria-controls="{target}" data-paused="false">'
            '<span class="motion-toggle__pause">Pause</span><span class="motion-toggle__play">Abspielen</span></button>')


def r_statement(sec: dict) -> str:
    s = sec["settings"]
    sid = "statement-preview"
    eyebrow = f'<p class="statement__eyebrow">{e(s["eyebrow"])}</p>' if s.get("eyebrow") else ""
    btn = f'<a class="btn btn--light" href="#">{e(s["button_label"])}</a>' if s.get("button_label") else ""
    return (f'<statement-section id="{sid}" class="statement statement--{s["effect"]} statement--{s["alignment"]} full-width" '
            f'style="--statement-overlay: {s["overlay"] / 100}; --statement-text: {s["text_color"]}; --statement-size: var(--statement-size-{s["text_size"]}); --statement-speed: {s["marquee_speed"]}s;" '
            f'data-effect="{s["effect"]}"><div class="statement__backdrop" aria-hidden="true"><div class="statement__fixed">'
            f'{media_img(s.get("image", ""), "statement__image")}</div></div>'
            f'<div class="statement__body">{eyebrow}<p class="statement__text" data-statement-text>{e(s["text"])}</p>{btn}</div></statement-section>')


def r_scene(sec: dict) -> str:
    s = sec["settings"]
    points = "".join(
        f'<a class="scene__point" href="#" style="--x: {b["settings"]["x"]}%; --y: {b["settings"]["y"]}%;" data-scene-point>'
        f'<span class="scene__dot" aria-hidden="true"></span><span class="scene__label">{e(b["settings"]["label"])}</span></a>'
        for b in (sec["blocks"][k] for k in sec["block_order"]))
    heading = f'<div class="scene__header"><h2 class="scene__heading">{e(s["heading"])}</h2></div>' if s.get("heading") else ""
    return (f'<explore-scene class="scene scene--{s["height"]} full-width" style="--scene-ratio: 2.33; --scene-point: {s["point_color"]};">{heading}'
            f'<div class="scene__viewport" tabindex="0" aria-label="Ziehen, um den Raum zu erkunden" data-scene-viewport>'
            f'<div class="scene__canvas" data-scene-canvas>{media_img(s.get("image", ""), "scene__image", s.get("image_alt", ""))}{points}</div></div>'
            f'<div class="scene__hint" aria-hidden="true" data-scene-hint><svg viewBox="0 0 64 32" width="48" height="24"><path d="M6 16h52M14 8l-8 8 8 8M50 8l8 8-8 8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
            f'<span>Ziehen zum Entdecken</span></div></explore-scene>')


def r_lineup(sec: dict) -> str:
    s = sec["settings"]
    lid = "lineup-preview"
    figures = "".join(
        f'<div role="listitem" class="lineup__figure" data-lineup-figure data-title="{e(demo_name(n))}" data-url="#demo-{n:02d}">'
        f'{media_img(b["settings"]["image"], "lineup__image", demo_name(n))}</div>'
        for n, b in ((ART_TO_DEMO.get(sec["blocks"][k]["settings"]["image"].rsplit("ua-packshot-", 1)[-1].split(".")[0], 1), sec["blocks"][k])
                     for k in sec["block_order"]))
    return (f'<lineup-arc id="{lid}" class="lineup lineup--hover-{s["hover_effect"]} full-width" style="--lineup-height: {s["figure_height"]}svh;" data-autoplay="{s["autoplay"]}">'
            f'<h2 class="lineup__heading">{e(s["heading"])}</h2>'
            f'<div class="lineup__stage" role="list" tabindex="0" aria-label="{e(s["heading"])}" data-lineup-stage>{figures}</div>'
            f'<div class="lineup__footer"><a class="lineup__title" href="#" data-lineup-title aria-live="polite"></a><div class="lineup__controls">'
            f'<button type="button" class="lineup__arrow" data-lineup-prev><span aria-hidden="true">←</span><span class="visually-hidden">Zurück</span></button>'
            f'<button type="button" class="lineup__arrow" data-lineup-next><span aria-hidden="true">→</span><span class="visually-hidden">Weiter</span></button>'
            f'{motion_toggle(lid, "lineup__toggle")}</div></div></lineup-arc>')




def r_ugc(sec: dict) -> str:
    """Mirror sections/ugc-feed.liquid: two drifting rows split odd/even, a tape strip between."""
    s = sec["settings"]
    posts = [sec["blocks"][k]["settings"] for k in sec["block_order"] if sec["blocks"][k]["settings"].get("image")]
    copies = int(s.get("copies", 4))

    def row(items: list, reverse: bool) -> str:
        tiles = []
        for copy in range(copies):
            hidden = ' aria-hidden="true"' if copy else ""
            for b in items:
                tiles.append(f'<li class="ugc-tile"{hidden}><a class="ugc-tile__link" href="#">'
                             f'{media_img(b["image"], "", b.get("title", ""))}'
                             f'<span class="ugc-tile__caption"><span class="ugc-tile__title">{e(b.get("title", ""))}</span>'
                             f'<span class="ugc-tile__place">{e(b.get("place", ""))}</span></span></a></li>')
        return f'<div class="ugc-row{" ugc-row--reverse" if reverse else ""}"><ul class="ugc-row__track" role="list">{"".join(tiles)}</ul></div>'

    tape = ""
    if s.get("tape_text"):
        tape = '<div class="ugc-tape" aria-hidden="true"><div class="ugc-tape__track">' + f'<span>{e(s["tape_text"])}</span>' * 12 + "</div></div>"
    outline = f'<span class="ugc-feed__title-outline">{e(s["heading_outline"])}</span>' if s.get("heading_outline") else ""
    return (f'<section class="ugc-feed" style="--ugc-height: {s.get("image_height", 220)}px; --ugc-duration: {s.get("duration", 50)}s; --ugc-copies: {copies};">'
            f'<div class="container container--wide ugc-feed__header"><div class="ugc-feed__heading">'
            f'<p class="ugc-feed__eyebrow">{e(s.get("eyebrow", ""))}</p><h2 class="ugc-feed__title">{e(s.get("heading", ""))}{outline}</h2></div>'
            f'<div class="ugc-feed__aside"><p class="ugc-feed__count"><strong>{len(posts)}</strong> {e(s.get("count_label", ""))}</p>'
            f'<a class="ugc-feed__invite" href="#">{e(s.get("invite_label", ""))}</a></div></div>'
            f'<div class="ugc-feed__stage">{row(posts[0::2], False)}{tape}{row(posts[1::2], True)}</div>'
            f'<p class="container container--wide ugc-feed__note">{e(s.get("note", ""))}</p></section>')


RENDERERS = {
    "announcement-bar": r_announcement, "header": r_header, "hero-split": r_hero,
    "product-carousel": r_product_carousel, "collection-carousel": r_collection_carousel,
    "before-after": r_before_after, "category-tiles": r_category_tiles, "cta-banner": r_cta,
    "trust-badges": r_trust, "video": r_video, "community": r_community,
    "newsletter": r_newsletter, "footer": r_footer,
    "page-header": r_page_header, "rich-text": r_rich_text, "text-columns": r_text_columns,
    "faq": r_faq, "contact-form": r_contact,
    "main-product": r_main_product, "related-products": r_related, "main-collection": r_main_collection,
    "statement": r_statement, "ugc-feed": r_ugc, "explore-scene": r_scene, "lineup": r_lineup,
}


def quick_view_templates() -> str:
    """One <template> per sample product, same markup as snippets/quick-view.liquid."""
    manifest_path = PREVIEW / "demo" / "manifest.json"
    if not manifest_path.exists():
        return ""
    out = []
    for n, item in enumerate(json.loads(manifest_path.read_text()), 1):
        title = demo_name(n)
        slides = "".join(
            f'<figure class="qv__slide" data-qv-slide><img src="demo/{e(sl["file"])}" alt="{e(title)} – {e(sl["label"])}" loading="lazy">'
            f'<figcaption class="qv__caption">{e(sl["label"])}</figcaption></figure>' for sl in item["slides"])
        thumbs = "".join(
            f'<button class="qv__thumb" type="button" role="tab" data-qv-thumb="{k}" aria-label="{e(sl["label"])}">'
            f'<img src="demo/{e(sl["file"])}" alt="" loading="lazy"></button>' for k, sl in enumerate(item["slides"]))
        buy = ('<form class="qv__buy" data-quick-add="true" onsubmit="return false"><button class="btn btn--full" type="submit">Dieses Werk bestellen</button></form>'
               if (n - 1) in DEMO_QUICK_ADD else '<a class="btn btn--full" href="#">Dieses Werk bestellen</a>')
        out.append(
            f'<template data-quick-view-template="#demo-{n:02d}"><div class="qv" data-qv><div class="qv__media">'
            f'<div class="qv__track" data-qv-track tabindex="0" aria-label="Bilder von {title}">{slides}</div>'
            f'<button class="qv__nav qv__nav--prev" type="button" data-qv-prev aria-label="Zurück">{ICONS["arrow-left"]}</button>'
            f'<button class="qv__nav qv__nav--next" type="button" data-qv-next aria-label="Weiter">{ICONS["arrow-right"]}</button>'
            f'<div class="qv__thumbs" role="tablist">{thumbs}</div></div>'
            f'<div class="qv__info"><p class="qv__artist">Urban Artery</p><h2 class="qv__title" id="QuickViewTitle">{title}</h2>'
            f'<p class="qv__price">Ab 200,00 €</p><p class="product__tax-note">inkl. MwSt., zzgl. Versandkosten</p>'
            f'<div class="qv__desc rte">{e(DEMO_DESCRIPTION)}</div>'
            f'<div class="qv__actions">{buy}<a class="btn btn--outline btn--full" href="#">Selbst gestalten</a></div>'
            f'<a class="qv__details link-underline" href="#">Alle Details ansehen</a></div></div></template>')
    return "\n".join(out)


QUICK_VIEW_DIALOG = (
    '<dialog class="qv-dialog" id="QuickView" aria-labelledby="QuickViewTitle" data-quick-view-dialog '
    'data-error="Dieses Werk konnte nicht geladen werden.">'
    '<button class="qv-dialog__close header__action" type="button" data-quick-view-close aria-label="Schließen">{close}</button>'
    '<div class="qv-dialog__body" data-quick-view-body></div></dialog>')


def render_group(path: Path) -> str:
    data = json.loads(path.read_text())
    out = []
    for key in data["order"]:
        sec = data["sections"][key]
        if sec.get("disabled"):
            continue
        render = RENDERERS.get(sec["type"])
        if render is None:
            raise SystemExit(f"No preview renderer for section type '{sec['type']}' ({path.name}:{key})")
        out.append(f"<!-- {key} ({sec['type']}) -->\n{render(sec)}")
    return "\n".join(out)


def render_page(template: Path, out: Path) -> None:
    tokens = "\n".join(f"  {k}: {v};" for k, v in TOKENS.items())
    page = f"""<!doctype html>
<html lang="de" class="js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Urban Artery – Vorschau</title>
<style>
@font-face {{ font-family: 'Allerta Stencil'; src: url(../assets/allerta-stencil.woff2) format('woff2'); font-display: swap; }}
@font-face {{ font-family: 'Inconsolata'; src: url(../assets/inconsolata-variable.woff2) format('woff2'); font-weight: 200 900; font-display: swap; }}
:root {{
{tokens}
}}
.payment-icon--demo {{ display: inline-flex; align-items: center; justify-content: center; background: #fff; color: #111; font: 700 9px/1 sans-serif; }}
.preview-app-slot {{ padding: 18px; border: 1px dashed #bbb; color: #777; font: 12px/1.4 ui-monospace, monospace; text-align: center; }}
.preview-note {{ position: fixed; right: 12px; bottom: 12px; z-index: 99; padding: 8px 12px; background: #000; color: #fff; font: 12px/1.4 ui-monospace, monospace; }}
</style>
<link rel="stylesheet" href="../assets/base.css">
<link rel="stylesheet" href="../assets/statement.css">
<link rel="stylesheet" href="../assets/scene.css">
<link rel="stylesheet" href="../assets/lineup.css">
<link rel="stylesheet" href="../assets/ugc-feed.css">
<script src="../assets/statement.js" type="module"></script>
<script src="../assets/scene.js" type="module"></script>
<script src="../assets/lineup.js" type="module"></script>
</head>
<body class="template-{template.stem.split('.')[0]}">
<!-- Generated by preview/build.py from templates/{template.name}. Do not edit by hand. -->
{render_group(ROOT / "sections" / "header-group.json")}
<main id="MainContent" class="main">
{render_group(template)}
</main>
{render_group(ROOT / "sections" / "footer-group.json")}
<p class="preview-note">Statische Vorschau · Platzhalter-Grafiken &amp; -Produkte</p>
{QUICK_VIEW_DIALOG.format(close=ICONS["close"])}
{quick_view_templates()}
<script src="../assets/theme.js"></script>
</body>
</html>
"""
    out.write_text(page)
    print(f"wrote {out.relative_to(ROOT)}")


def main() -> None:
    render_page(ROOT / "templates" / "index.json", PREVIEW / "index.html")
    render_page(ROOT / "templates" / "product.json", PREVIEW / "product.html")
    render_page(ROOT / "templates" / "collection.json", PREVIEW / "collection.html")
    for template in sorted((ROOT / "templates").glob("page.*.json")):
        types = {s["type"] for s in json.loads(template.read_text())["sections"].values()}
        if not types <= RENDERERS.keys():
            print(f"skip {template.name}: rendered at runtime ({', '.join(sorted(types - RENDERERS.keys()))})")
            continue
        render_page(template, PREVIEW / f"{template.stem}.html")


if __name__ == "__main__":
    main()
