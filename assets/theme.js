/* Urban Artery — theme behaviour. No dependencies. */
(function () {
  'use strict';

  /* ---------------------------------------------------------------------
     Carousel: horizontal scroll-snap track with prev/next controls.
     --------------------------------------------------------------------- */
  function initCarousel(root) {
    var track = root.querySelector('[data-carousel-track]');
    var prev = root.querySelector('[data-carousel-prev]');
    var next = root.querySelector('[data-carousel-next]');
    if (!track) return;

    function page() {
      var slide = track.querySelector('.carousel__slide');
      if (!slide) return track.clientWidth;
      var gap = parseFloat(getComputedStyle(track).columnGap || '0') || 0;
      var per = Math.max(1, Math.floor(track.clientWidth / (slide.offsetWidth + gap)));
      return (slide.offsetWidth + gap) * per;
    }

    function sync() {
      var max = track.scrollWidth - track.clientWidth - 2;
      if (prev) prev.disabled = track.scrollLeft <= 2;
      if (next) next.disabled = track.scrollLeft >= max;
    }

    if (prev) prev.addEventListener('click', function () { track.scrollBy({ left: -page(), behavior: 'smooth' }); });
    if (next) next.addEventListener('click', function () { track.scrollBy({ left: page(), behavior: 'smooth' }); });

    track.addEventListener('scroll', function () {
      window.clearTimeout(track._t);
      track._t = window.setTimeout(sync, 60);
    }, { passive: true });

    window.addEventListener('resize', sync);
    sync();
  }

  /* ---------------------------------------------------------------------
     Announcement bar rotation.
     --------------------------------------------------------------------- */
  function initAnnouncement(root) {
    var items = root.querySelectorAll('.announcement__message');
    if (items.length < 2) return;
    var interval = parseInt(root.dataset.interval, 10) || 5000;
    var i = 0;
    window.setInterval(function () {
      items[i].classList.remove('is-active');
      i = (i + 1) % items.length;
      items[i].classList.add('is-active');
    }, interval);
  }

  /* ---------------------------------------------------------------------
     Mobile navigation drawer.
     --------------------------------------------------------------------- */
  function initDrawer() {
    var drawer = document.getElementById('MenuDrawer');
    var overlay = document.getElementById('Overlay');
    var openers = document.querySelectorAll('[data-drawer-open]');
    var closers = document.querySelectorAll('[data-drawer-close]');
    if (!drawer) return;

    function setExpanded(value) {
      openers.forEach(function (el) { el.setAttribute('aria-expanded', value ? 'true' : 'false'); });
    }

    function open() {
      drawer.classList.add('is-open');
      setExpanded(true);
      if (overlay) overlay.hidden = false;
      document.body.style.overflow = 'hidden';
      var first = drawer.querySelector('a, button');
      if (first) first.focus();
    }
    function close() {
      drawer.classList.remove('is-open');
      setExpanded(false);
      if (overlay) overlay.hidden = true;
      document.body.style.overflow = '';
      if (openers[0]) openers[0].focus();
    }

    openers.forEach(function (el) { el.addEventListener('click', open); });
    closers.forEach(function (el) { el.addEventListener('click', close); });
    if (overlay) overlay.addEventListener('click', close);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && drawer.classList.contains('is-open')) close();
    });
  }

  /* ---------------------------------------------------------------------
     Product form: keep variant, price and availability in sync.
     --------------------------------------------------------------------- */
  function initProductForm(root) {
    var dataEl = root.querySelector('[data-variants]');
    var idInput = root.querySelector('[data-variant-id]');
    var submit = root.querySelector('[data-add-to-cart]');
    var priceEls = document.querySelectorAll('[data-product-price]');
    if (!dataEl || !idInput) return;

    var variants;
    try { variants = JSON.parse(dataEl.textContent); } catch (e) { return; }

    function selected() {
      return Array.prototype.map.call(
        root.querySelectorAll('[data-option-index]'),
        function (group) {
          var checked = group.querySelector('input:checked');
          return checked ? checked.value : null;
        }
      );
    }

    function update() {
      var chosen = selected();
      var match = variants.find(function (v) {
        return chosen.every(function (value, i) { return value === null || v.options[i] === value; });
      });

      if (!match) {
        if (submit) { submit.disabled = true; submit.textContent = submit.dataset.unavailable; }
        return;
      }

      idInput.value = match.id;

      if (submit) {
        submit.disabled = !match.available;
        submit.textContent = match.available ? submit.dataset.add : submit.dataset.soldOut;
      }
      if (match.price_html) priceEls.forEach(function (el) { el.innerHTML = match.price_html; });

      if (window.history.replaceState) {
        var url = new URL(window.location.href);
        url.searchParams.set('variant', match.id);
        window.history.replaceState({}, '', url.toString());
      }
    }

    root.addEventListener('change', function (e) {
      if (e.target.matches('input[type="radio"]')) update();
    });
    update();
  }

  /* ---------------------------------------------------------------------
     Before / after slider: a transparent range input drives --ba-pos.
     --------------------------------------------------------------------- */
  function initBeforeAfter(frame) {
    var range = frame.querySelector('[data-before-after-range]');
    if (!range) return;
    function sync() {
      frame.style.setProperty('--ba-pos', range.value + '%');
      range.setAttribute('aria-valuetext', range.value + ' % ' + (range.dataset.beforeLabel || ''));
    }
    range.addEventListener('input', sync);
    sync();
  }

  /* ---------------------------------------------------------------------
     Collection sort.
     --------------------------------------------------------------------- */
  function initSort(select) {
    select.addEventListener('change', function () {
      var url = new URL(window.location.href);
      url.searchParams.set('sort_by', select.value);
      url.searchParams.delete('page');
      window.location.href = url.toString();
    });
  }

  /* ---------------------------------------------------------------------
     Background videos: respect reduced-motion preferences.
     --------------------------------------------------------------------- */
  function initAutoplay(video) {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      video.removeAttribute('autoplay');
      video.pause();
    }
  }

  /* ---------------------------------------------------------------------
     Wishlist: product handles kept in this browser only.
     --------------------------------------------------------------------- */
  var WISHLIST_KEY = 'ua-wishlist';

  function readWishlist() {
    try { return JSON.parse(window.localStorage.getItem(WISHLIST_KEY)) || []; } catch (e) { return []; }
  }
  function writeWishlist(list) {
    try { window.localStorage.setItem(WISHLIST_KEY, JSON.stringify(list)); } catch (e) { /* storage blocked: state stays in-memory */ }
  }
  function syncWishlistUi() {
    var list = readWishlist();
    document.querySelectorAll('[data-wishlist-toggle]').forEach(function (btn) {
      var on = list.indexOf(btn.dataset.wishlistToggle) !== -1;
      btn.setAttribute('aria-pressed', on ? 'true' : 'false');
      btn.setAttribute('aria-label', on ? btn.dataset.labelRemove : btn.dataset.labelAdd);
    });
    document.querySelectorAll('[data-wishlist-count]').forEach(function (el) {
      el.textContent = list.length;
      el.hidden = list.length === 0;
    });
  }
  function initWishlist() {
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-wishlist-toggle]');
      if (!btn) return;
      e.preventDefault();
      var handle = btn.dataset.wishlistToggle;
      var list = readWishlist();
      var i = list.indexOf(handle);
      if (i === -1) list = list.concat([handle]); else list = list.slice(0, i).concat(list.slice(i + 1));
      writeWishlist(list);
      syncWishlistUi();
    });
    syncWishlistUi();
  }
  function renderWishlistPage(root) {
    var grid = root.querySelector('[data-wishlist-grid]');
    var empty = root.querySelector('[data-wishlist-empty]');
    var handles = readWishlist();
    if (!handles.length) { empty.hidden = false; return; }
    Promise.all(handles.map(function (h) {
      return fetch('/products/' + encodeURIComponent(h) + '?view=card')
        .then(function (r) { return r.ok ? r.text() : ''; })
        .catch(function () { return ''; });
    })).then(function (cards) {
      var html = cards.filter(Boolean).map(function (c) { return '<li>' + c + '</li>'; }).join('');
      if (!html) { empty.hidden = false; return; }
      grid.innerHTML = html;
      syncWishlistUi();
    });
  }

  /* ---------------------------------------------------------------------
     Quick add: post the card's form without leaving the page.
     --------------------------------------------------------------------- */
  function initQuickAdd() {
    document.addEventListener('submit', function (e) {
      var form = e.target.closest('[data-quick-add]');
      if (!form || !window.fetch) return;
      e.preventDefault();
      var btn = form.querySelector('button');
      btn.disabled = true;
      fetch('/cart/add.js', { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' } })
        .then(function (r) { if (!r.ok) throw new Error('add failed'); return fetch('/cart.js'); })
        .then(function (r) { return r.json(); })
        .then(function (cart) {
          document.querySelectorAll('.cart-count').forEach(function (el) {
            if (el.hasAttribute('data-wishlist-count')) return;
            el.textContent = cart.item_count; el.hidden = cart.item_count === 0;
          });
          btn.classList.add('is-added');
          window.setTimeout(function () { btn.classList.remove('is-added'); }, 1600);
        })
        .catch(function () { form.submit(); })
        .then(function () { btn.disabled = false; });
    });
  }

  /* ---------------------------------------------------------------------
     Sticky buy bar: shown on mobile once the main buy button scrolls away.
     --------------------------------------------------------------------- */
  function initStickyBuy(bar) {
    var main = document.querySelector('[data-add-to-cart]');
    if (!main || !('IntersectionObserver' in window)) return;
    new IntersectionObserver(function (entries) {
      bar.hidden = entries[0].isIntersecting || entries[0].boundingClientRect.top > 0;
    }).observe(main);
  }

  /* ---------------------------------------------------------------------
     Quick view: product cards open a dialog with a slideshow and actions.
     Content comes from /products/<handle>?view=quick (or, in the static
     preview, from a <template data-quick-view-template="<url>">).
     Without JavaScript the card link simply opens the product page.
     --------------------------------------------------------------------- */
  function initQuickViewSlides(root) {
    var track = root.querySelector('[data-qv-track]');
    if (!track) return;
    var slides = track.querySelectorAll('[data-qv-slide]');
    var thumbs = root.querySelectorAll('[data-qv-thumb]');
    var index = 0;
    function sync() {
      thumbs.forEach(function (t, i) { t.setAttribute('aria-selected', i === index ? 'true' : 'false'); });
    }
    function go(i) {
      index = Math.max(0, Math.min(slides.length - 1, i));
      track.scrollTo({ left: slides[index].offsetLeft, behavior: 'smooth' });
      sync();
    }
    function current() { return index; }
    var prev = root.querySelector('[data-qv-prev]');
    var next = root.querySelector('[data-qv-next]');
    if (prev) prev.addEventListener('click', function () { go(current() - 1); });
    if (next) next.addEventListener('click', function () { go(current() + 1); });
    thumbs.forEach(function (t) { t.addEventListener('click', function () { go(Number(t.dataset.qvThumb)); }); });
    track.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') { go(current() - 1); e.preventDefault(); }
      if (e.key === 'ArrowRight') { go(current() + 1); e.preventDefault(); }
    });
    // A swipe settles on a slide: read it back once scrolling stops.
    track.addEventListener('scroll', function () {
      window.clearTimeout(track._qv);
      track._qv = window.setTimeout(function () {
        index = Math.round(track.scrollLeft / Math.max(track.clientWidth, 1));
        sync();
      }, 120);
    }, { passive: true });
    sync();
  }

  function initQuickView() {
    var dialog = document.querySelector('[data-quick-view-dialog]');
    if (!dialog || typeof dialog.showModal !== 'function') return;
    var body = dialog.querySelector('[data-quick-view-body]');
    var opener = null;

    function load(url) {
      var local = document.querySelector('template[data-quick-view-template="' + url + '"]');
      if (local) return Promise.resolve(local.innerHTML);
      return fetch(url + (url.indexOf('?') === -1 ? '?' : '&') + 'view=quick')
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); });
    }
    function close() { dialog.close(); }

    document.addEventListener('click', function (e) {
      var link = e.target.closest('[data-quick-view]');
      // defaultPrevented: e.g. the explore scene's first tap only opens a point's label.
      if (!link || e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
      e.preventDefault();
      opener = link;
      var url = link.dataset.quickView;
      body.innerHTML = '';
      dialog.classList.add('is-loading');
      dialog.showModal();
      load(url).then(function (html) {
        body.innerHTML = html;
        initQuickViewSlides(body);
        syncWishlistUi();
      }).catch(function () {
        body.innerHTML = '<p class="qv-dialog__error">' + (dialog.dataset.error || '') + ' <a class="link-underline" href="' + url + '">' + url + '</a></p>';
      }).then(function () {
        dialog.classList.remove('is-loading');
        var focusTarget = body.querySelector('[data-qv-track]') || dialog;
        focusTarget.focus();
      });
    });
    dialog.querySelector('[data-quick-view-close]').addEventListener('click', close);
    dialog.addEventListener('click', function (e) { if (e.target === dialog) close(); });
    dialog.addEventListener('close', function () {
      body.innerHTML = '';
      if (opener) opener.focus();
    });
  }

  /* ---------------------------------------------------------------------
     Motion toggle: pause/play self-moving set pieces.
     --------------------------------------------------------------------- */
  function initMotionToggles() {
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-motion-toggle]');
      if (!btn) return;
      var target = document.getElementById(btn.dataset.motionToggle);
      if (!target) return;
      var paused = btn.dataset.paused !== 'true';
      btn.dataset.paused = paused ? 'true' : 'false';
      target.classList.toggle('is-paused', paused);
      target.querySelectorAll('video').forEach(function (v) { if (paused) v.pause(); else v.play().catch(function () {}); });
    });
  }

  /* ---------------------------------------------------------------------
     Product recommendations: fetched from Shopify's recommendations route.
     --------------------------------------------------------------------- */
  function initRecommendations(root) {
    if (root.dataset.loaded || !window.fetch || root.children.length) return;
    root.dataset.loaded = 'true';
    fetch(root.dataset.recommendations)
      .then(function (r) { return r.ok ? r.text() : ''; })
      .then(function (html) {
        if (!html) return;
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var fresh = doc.querySelector('[data-recommendations]');
        if (!fresh || !fresh.children.length) return;
        root.innerHTML = fresh.innerHTML;
        root.querySelectorAll('[data-carousel]').forEach(initCarousel);
        syncWishlistUi();
      })
      .catch(function () { /* recommendations are optional; the section stays empty */ });
  }

  function boot(scope) {
    (scope || document).querySelectorAll('[data-carousel]').forEach(initCarousel);
    (scope || document).querySelectorAll('[data-announcement]').forEach(initAnnouncement);
    (scope || document).querySelectorAll('[data-product-form]').forEach(initProductForm);
    (scope || document).querySelectorAll('[data-sort]').forEach(initSort);
    (scope || document).querySelectorAll('[data-before-after]').forEach(initBeforeAfter);
    (scope || document).querySelectorAll('video[data-autoplay]').forEach(initAutoplay);
    (scope || document).querySelectorAll('[data-sticky-buy]').forEach(initStickyBuy);
    (scope || document).querySelectorAll('[data-wishlist-page]').forEach(renderWishlistPage);
    (scope || document).querySelectorAll('[data-recommendations]').forEach(initRecommendations);
    syncWishlistUi();
  }

  document.addEventListener('DOMContentLoaded', function () {
    boot(document);
    initDrawer();
    initWishlist();
    initQuickAdd();
    initQuickView();
    initMotionToggles();
  });

  /* Re-initialise sections edited in the theme editor. */
  document.addEventListener('shopify:section:load', function (e) {
    boot(e.target);
    initDrawer();
  });
})();
