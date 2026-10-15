/**
 * <explore-scene>: centres the panorama on load, adds mouse drag-to-pan on
 * top of native touch scrolling, hides the swipe hint after the first move,
 * and on touch screens opens a point's label on the first tap (the second
 * tap follows the link).
 */
const COARSE_POINTER = window.matchMedia('(pointer: coarse)');
const DRAG_THRESHOLD_PX = 5;

class ExploreScene extends HTMLElement {
  connectedCallback() {
    this.viewport = this.querySelector('[data-scene-viewport]');
    if (!this.viewport) return;
    requestAnimationFrame(() => this.centre());
    this.querySelector('.scene__image')?.addEventListener('load', () => this.centre(), { once: true });
    this.viewport.addEventListener('scroll', () => this.markMoved(), { passive: true });
    // Only a visitor's own drag, swipe, wheel or key counts as moving, never our centring.
    ['pointerdown', 'touchstart', 'wheel', 'keydown'].forEach((type) => {
      this.viewport.addEventListener(type, () => { this.hasInteracted = true; }, { passive: true });
    });
    this.viewport.addEventListener('pointerdown', (event) => this.startDrag(event));
    this.viewport.addEventListener('keydown', (event) => this.handleKey(event));
    this.querySelectorAll('[data-scene-point]').forEach((point) => {
      point.addEventListener('click', (event) => this.handlePointClick(event, point));
    });
    document.addEventListener('shopify:block:select', (event) => {
      const point = event.target.closest?.('[data-scene-point]');
      if (point && this.contains(point)) this.reveal(point);
    });
  }

  centre() {
    if (this.hasMoved) return;
    this.isCentring = true;
    this.viewport.scrollLeft = (this.viewport.scrollWidth - this.viewport.clientWidth) / 2;
    requestAnimationFrame(() => { this.isCentring = false; });
  }

  markMoved() {
    if (this.isCentring || this.hasMoved || !this.hasInteracted) return;
    this.hasMoved = true;
    this.classList.add('has-moved');
  }

  startDrag(event) {
    if (event.pointerType !== 'mouse' || event.button !== 0) return;
    const startX = event.clientX;
    const startScroll = this.viewport.scrollLeft;
    let isDragging = false;
    const onMove = (moveEvent) => {
      const dx = moveEvent.clientX - startX;
      if (!isDragging && Math.abs(dx) > DRAG_THRESHOLD_PX) {
        isDragging = true;
        this.viewport.classList.add('is-dragging');
        this.viewport.setPointerCapture(event.pointerId);
      }
      if (isDragging) this.viewport.scrollLeft = startScroll - dx;
    };
    const onUp = () => {
      this.viewport.classList.remove('is-dragging');
      this.viewport.removeEventListener('pointermove', onMove);
      this.viewport.removeEventListener('pointerup', onUp);
      // Swallow the click that ends a drag so a point under the cursor does not open.
      if (isDragging) this.viewport.addEventListener('click', (e) => e.preventDefault(), { capture: true, once: true });
    };
    this.viewport.addEventListener('pointermove', onMove);
    this.viewport.addEventListener('pointerup', onUp);
  }

  handleKey(event) {
    if (event.target !== this.viewport) return;
    const step = this.viewport.clientWidth * 0.4;
    if (event.key === 'ArrowLeft') this.viewport.scrollBy({ left: -step, behavior: 'smooth' });
    else if (event.key === 'ArrowRight') this.viewport.scrollBy({ left: step, behavior: 'smooth' });
    else return;
    event.preventDefault();
  }

  /** Touch: first tap opens the label, second tap follows the link. */
  handlePointClick(event, point) {
    if (!COARSE_POINTER.matches || point.classList.contains('is-open')) return;
    event.preventDefault();
    this.querySelectorAll('.scene__point.is-open').forEach((open) => open.classList.remove('is-open'));
    point.classList.add('is-open');
  }

  reveal(point) {
    point.classList.add('is-open');
    const left = point.offsetLeft - this.viewport.clientWidth / 2;
    this.viewport.scrollTo({ left, behavior: 'smooth' });
  }
}

if (!customElements.get('explore-scene')) customElements.define('explore-scene', ExploreScene);
