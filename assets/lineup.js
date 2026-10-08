/**
 * <lineup-arc>: lays figures out on an arc around a continuous position.
 * The centre figure is full size; neighbours shrink, rise and fall back in
 * z-order. Drag/swipe, arrow keys, buttons and click-to-centre move it;
 * autoplay advances every N seconds and stops on hover, focus, the pause
 * button or reduced motion. The track wraps, so it never runs out.
 */
const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)');
const MOBILE = window.matchMedia('(max-width: 749px)');

const SCALE_STEPS = [1, 0.64, 0.4, 0.28];     // figure scale by distance from centre
const SPREAD = [0, 0.27, 0.44, 0.56];          // horizontal offset (share of stage width)
const LIFT = [0, 0.025, 0.075, 0.12];          // feet rise (share of stage height)
const MOBILE_SPREAD = [0, 0.42, 0.66, 0.8];
const EASE = 0.14;                              // follow speed toward the target position
const CLICK_TOLERANCE_PX = 6;
const FLICK_PX = 30;              // a short, deliberate swipe always moves one look

const lerp = (a, b, t) => a + (b - a) * t;

/** Interpolated value from a step table at fractional distance d. */
function stepValue(table, d) {
  const distance = Math.min(Math.abs(d), table.length - 1);
  const low = Math.floor(distance);
  const high = Math.min(low + 1, table.length - 1);
  return lerp(table[low], table[high], distance - low);
}

class LineupArc extends HTMLElement {
  connectedCallback() {
    this.stage = this.querySelector('[data-lineup-stage]');
    this.originals = [...this.querySelectorAll('[data-lineup-figure]')];
    this.titleLink = this.querySelector('[data-lineup-title]');
    if (!this.stage || this.originals.length === 0) return;
    this.figures = this.fillArc();

    this.position = 0;
    this.target = 0;
    this.activeIndex = -1;
    this.autoplayMs = Number(this.dataset.autoplay || 0) * 1000;
    this.isHovered = false;

    this.classList.add('is-ready');
    // The no-JS row may have scroll-snapped sideways; the arc is laid out from 0.
    this.stage.scrollLeft = 0;
    this.bindEvents();
    this.render(true);
    this.startAutoplay();
    this.frame = requestAnimationFrame(() => this.tick());
  }

  disconnectedCallback() {
    cancelAnimationFrame(this.frame);
    clearInterval(this.autoplayTimer);
    this.observer?.disconnect();
  }

  /**
   * Repeats the looks (as copies hidden from assistive tech) until every slot on
   * both sides of the centre is filled, so the arc is always symmetrical.
   */
  fillArc() {
    const slots = (SCALE_STEPS.length - 1) * 2 + 2;
    const figures = [...this.originals];
    if (this.originals.length < 2) return figures;
    while (figures.length < slots) {
      this.originals.forEach((original) => {
        const copy = original.cloneNode(true);
        copy.setAttribute('data-lineup-copy', '');
        copy.setAttribute('aria-hidden', 'true');
        copy.removeAttribute('role');
        copy.querySelectorAll('[data-shopify-editor-block]').forEach((el) => el.removeAttribute('data-shopify-editor-block'));
        copy.removeAttribute('data-shopify-editor-block');
        this.stage.append(copy);
        figures.push(copy);
      });
    }
    return figures;
  }

  get count() {
    return this.figures.length;
  }

  /** Pixels of drag that move one look: the gap between neighbours, so figures follow the finger. */
  get pxPerFigure() {
    const spread = MOBILE.matches ? MOBILE_SPREAD : SPREAD;
    return Math.max(80, this.stage.clientWidth * spread[1]);
  }

  /** Shortest signed distance from the current position to figure i (wraps). */
  distanceTo(index, position = this.position) {
    let d = index - position;
    const half = this.count / 2;
    d = ((((d + half) % this.count) + this.count) % this.count) - half;
    return d;
  }

  bindEvents() {
    this.querySelector('[data-lineup-prev]')?.addEventListener('click', () => this.step(-1));
    this.querySelector('[data-lineup-next]')?.addEventListener('click', () => this.step(1));

    this.stage.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowLeft') this.step(-1);
      else if (event.key === 'ArrowRight') this.step(1);
      else if (event.key === 'Enter') this.openActive();
      else return;
      event.preventDefault();
    });

    this.addEventListener('pointerenter', () => { this.isHovered = true; });
    this.addEventListener('pointerleave', () => { this.isHovered = false; });
    this.addEventListener('focusin', () => { this.isHovered = true; });
    this.addEventListener('focusout', () => { this.isHovered = false; });

    // Horizontal wheel / trackpad swipe only; vertical scrolling stays with the page.
    this.stage.addEventListener('wheel', (event) => {
      if (Math.abs(event.deltaX) <= Math.abs(event.deltaY)) return;
      event.preventDefault();
      this.target += event.deltaX / this.pxPerFigure;
      clearTimeout(this.wheelSnap);
      this.wheelSnap = setTimeout(() => { this.target = Math.round(this.target); }, 120);
    }, { passive: false });

    this.stage.addEventListener('pointerdown', (event) => this.startDrag(event));

    // Theme editor: selecting a block brings its figure to the centre.
    document.addEventListener('shopify:block:select', (event) => {
      const index = this.originals.findIndex((figure) => figure.contains(event.target) || event.target.contains(figure));
      if (index >= 0) this.goTo(this.nearestCopy(index));
    });

    this.observer = new ResizeObserver(() => this.render(true));
    this.observer.observe(this.stage);
  }

  startDrag(event) {
    if (event.button !== 0) return;
    const startX = event.clientX;
    const startTarget = Math.round(this.target);
    const pxPerFigure = this.pxPerFigure;
    let moved = 0;
    let dx = 0;
    const onMove = (moveEvent) => {
      dx = moveEvent.clientX - startX;
      moved = Math.max(moved, Math.abs(dx));
      if (moved > CLICK_TOLERANCE_PX) this.stage.setPointerCapture?.(event.pointerId);
      this.target = startTarget - dx / pxPerFigure;
      this.position = this.target; // follow the finger directly while dragging
      this.render();
    };
    const onUp = (upEvent) => {
      this.stage.removeEventListener('pointermove', onMove);
      this.stage.removeEventListener('pointerup', onUp);
      this.stage.removeEventListener('pointercancel', onUp);
      if (moved <= CLICK_TOLERANCE_PX) {
        this.handleClick(upEvent);
        return;
      }
      let next = Math.round(this.target);
      if (next === startTarget && Math.abs(dx) > FLICK_PX) next = startTarget - Math.sign(dx);
      this.target = next;
      this.restartAutoplay();
    };
    this.stage.addEventListener('pointermove', onMove);
    this.stage.addEventListener('pointerup', onUp);
    this.stage.addEventListener('pointercancel', onUp);
  }

  handleClick(event) {
    const figure = event.target.closest('[data-lineup-figure]');
    if (!figure) return;
    const index = this.figures.indexOf(figure);
    if (index === this.activeIndex) this.openActive();
    else this.goTo(index);
  }

  /** Index of the copy of original `index` closest to the current position. */
  nearestCopy(index) {
    const n = this.originals.length;
    let best = index;
    for (let i = index; i < this.count; i += n) {
      if (Math.abs(this.distanceTo(i)) < Math.abs(this.distanceTo(best))) best = i;
    }
    return best;
  }

  openActive() {
    const url = this.figures[this.activeIndex]?.dataset.url;
    if (url) window.location.href = url;
  }

  step(direction) {
    this.target = Math.round(this.target) + direction;
    this.restartAutoplay();
  }

  goTo(index) {
    this.target = this.position + this.distanceTo(index);
    this.restartAutoplay();
  }

  startAutoplay() {
    if (!this.autoplayMs || REDUCED_MOTION.matches) return;
    this.autoplayTimer = setInterval(() => {
      if (this.isHovered || this.classList.contains('is-paused') || document.hidden) return;
      this.target = Math.round(this.target) + 1;
    }, this.autoplayMs);
  }

  restartAutoplay() {
    clearInterval(this.autoplayTimer);
    this.startAutoplay();
  }

  tick() {
    const delta = this.target - this.position;
    if (Math.abs(delta) > 0.0005) {
      this.position = REDUCED_MOTION.matches ? this.target : this.position + delta * EASE;
      this.render();
    }
    this.frame = requestAnimationFrame(() => this.tick());
  }

  render(force = false) {
    if (this.stage.scrollLeft !== 0) this.stage.scrollLeft = 0;
    const width = this.stage.clientWidth;
    const height = this.stage.clientHeight;
    const spread = MOBILE.matches ? MOBILE_SPREAD : SPREAD;
    const visibleRange = SCALE_STEPS.length - 1;

    this.figures.forEach((figure, index) => {
      const d = this.distanceTo(index);
      const distance = Math.abs(d);
      if (distance > visibleRange + 0.5) {
        figure.setAttribute('data-hidden', '');
        return;
      }
      figure.removeAttribute('data-hidden');
      const x = Math.sign(d) * stepValue(spread, d) * width;
      const y = -stepValue(LIFT, d) * height;
      const scale = stepValue(SCALE_STEPS, d);
      figure.style.transform = `translate(calc(-50% + ${x.toFixed(1)}px), ${y.toFixed(1)}px) scale(${scale.toFixed(3)})`;
      figure.style.zIndex = String(100 - Math.round(distance * 10));
      figure.style.opacity = String(Math.max(0, Math.min(1, visibleRange + 0.5 - distance)));
    });

    const active = ((Math.round(this.position) % this.count) + this.count) % this.count;
    if (active !== this.activeIndex || force) this.setActive(active);
  }

  setActive(index) {
    this.activeIndex = index;
    const originalIndex = index % this.originals.length;
    this.figures.forEach((figure, i) => figure.classList.toggle('is-active', i === index));
    this.originals.forEach((figure, i) => figure.setAttribute('aria-current', i === originalIndex ? 'true' : 'false'));
    const figure = this.figures[index];
    if (!this.titleLink || !figure) return;
    this.titleLink.textContent = figure.dataset.title || '';
    if (figure.dataset.url) this.titleLink.href = figure.dataset.url;
    else this.titleLink.removeAttribute('href');
  }
}

if (!customElements.get('lineup-arc')) customElements.define('lineup-arc', LineupArc);
