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

    function open() {
      drawer.classList.add('is-open');
      if (overlay) overlay.hidden = false;
      document.body.style.overflow = 'hidden';
      var first = drawer.querySelector('a, button');
      if (first) first.focus();
    }
    function close() {
      drawer.classList.remove('is-open');
      if (overlay) overlay.hidden = true;
      document.body.style.overflow = '';
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
    var priceEl = document.querySelector('[data-product-price]');
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
      if (priceEl && match.price_html) priceEl.innerHTML = match.price_html;

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

  function boot(scope) {
    (scope || document).querySelectorAll('[data-carousel]').forEach(initCarousel);
    (scope || document).querySelectorAll('[data-announcement]').forEach(initAnnouncement);
    (scope || document).querySelectorAll('[data-product-form]').forEach(initProductForm);
    (scope || document).querySelectorAll('[data-sort]').forEach(initSort);
  }

  document.addEventListener('DOMContentLoaded', function () {
    boot(document);
    initDrawer();
  });

  /* Re-initialise sections edited in the theme editor. */
  document.addEventListener('shopify:section:load', function (e) {
    boot(e.target);
    initDrawer();
  });
})();
