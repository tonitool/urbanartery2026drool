// Room tour: walk from room to room through the door points in the scene (or the floor-plan tabs
// and arrow keys); a point's card opens on hover on desktop and on tap everywhere, and closes with
// ×, Escape or a tap outside. On phones each scene pans sideways and starts centred.
class RoomTour extends HTMLElement {
  connectedCallback() {
    this.tabs = [...this.querySelectorAll('[data-room-tab]')];
    this.rooms = [...this.querySelectorAll('[data-room]')];
    this.current = Math.max(0, this.rooms.findIndex((room) => !room.hidden));

    this.tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => this.select(index));
      tab.addEventListener('keydown', (event) => this.onTabKey(event, index));
    });
    this.querySelectorAll('[data-room-door]').forEach((door) => {
      door.addEventListener('click', () => this.select(Number(door.dataset.roomDoor)));
    });
    this.querySelectorAll('[data-room-pin]').forEach((pin) => {
      pin.addEventListener('click', () => this.toggle(pin));
    });
    this.querySelectorAll('[data-room-close]').forEach((button) => {
      button.addEventListener('click', () => this.closeAll());
    });

    this.onOutside = (event) => { if (!event.target.closest('.room-tour__point')) this.closeAll(); };
    this.onEscape = (event) => { if (event.key === 'Escape') this.closeAll(); };
    document.addEventListener('click', this.onOutside);
    document.addEventListener('keydown', this.onEscape);

    this.updateNav();
    requestAnimationFrame(() => this.centre());
    window.addEventListener('load', () => this.centre(), { once: true });
    this.preloadRoomsWhenVisible();
  }

  disconnectedCallback() {
    document.removeEventListener('click', this.onOutside);
    document.removeEventListener('keydown', this.onEscape);
  }

  select(index, direction) {
    if (index === this.current || !this.rooms[index]) return;
    this.closeAll();
    this.dataset.direction = direction || (index < this.current ? 'back' : 'forward');
    this.current = index;
    this.tabs.forEach((tab, i) => {
      const isActive = i === index;
      tab.setAttribute('aria-selected', String(isActive));
      tab.tabIndex = isActive ? 0 : -1;
    });
    this.rooms.forEach((room, i) => { room.hidden = i !== index; });
    this.updateNav();
    this.centre();
  }

  // Phones: the scene is wider than the screen; start in its middle.
  centre() {
    const viewport = this.rooms[this.current]?.querySelector('[data-room-viewport]');
    if (viewport) viewport.scrollLeft = (viewport.scrollWidth - viewport.clientWidth) / 2;
  }

  // The counter shows which room you are in.
  updateNav() {
    const counter = this.querySelector('[data-room-current]');
    if (counter) counter.textContent = String(this.current + 1).padStart(2, '0');
  }

  onTabKey(event, index) {
    const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
    if (!step) return;
    event.preventDefault();
    const next = (index + step + this.tabs.length) % this.tabs.length;
    this.select(next, step < 0 ? 'back' : 'forward');
    this.tabs[next].focus();
  }

  toggle(pin) {
    const point = pin.closest('.room-tour__point');
    const willOpen = !point.classList.contains('is-open');
    this.closeAll();
    point.classList.toggle('is-open', willOpen);
    pin.setAttribute('aria-expanded', String(willOpen));
  }

  closeAll() {
    this.querySelectorAll('.room-tour__point.is-open').forEach((point) => {
      point.classList.remove('is-open');
      point.querySelector('[data-room-pin]').setAttribute('aria-expanded', 'false');
    });
  }

  // Hidden rooms and card images load lazily; fetch them once the tour is on screen so walking on and opening a card are instant.
  preloadRoomsWhenVisible() {
    const observer = new IntersectionObserver((entries) => {
      if (!entries.some((entry) => entry.isIntersecting)) return;
      this.querySelectorAll('img[loading="lazy"]').forEach((img) => { img.loading = 'eager'; });
      observer.disconnect();
    }, { rootMargin: '200px' });
    observer.observe(this);
  }
}

if (!customElements.get('room-tour')) customElements.define('room-tour', RoomTour);
