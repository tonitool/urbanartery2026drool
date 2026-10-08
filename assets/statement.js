/**
 * <statement-section>: reveals the line of type when it scrolls into view.
 * Typewriter types it out letter by letter (the full text stays available
 * to assistive tech via aria-label); fade and blur are CSS transitions.
 * Reduced motion shows the text straight away.
 */
const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)');
const TYPE_DELAY_MS = 45;
const REVEAL_THRESHOLD = 0.4;

class StatementSection extends HTMLElement {
  connectedCallback() {
    this.text = this.querySelector('[data-statement-text]');
    const effect = this.dataset.effect;
    if (!this.text || effect === 'marquee' || REDUCED_MOTION.matches) return;

    this.fullText = this.text.textContent.trim();
    if (effect === 'typewriter') this.prepareTypewriter();
    this.classList.add('is-armed');

    this.observer = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      this.observer.disconnect();
      this.reveal(effect);
    }, { threshold: REVEAL_THRESHOLD });
    this.observer.observe(this);
  }

  disconnectedCallback() {
    this.observer?.disconnect();
    clearTimeout(this.typeTimer);
  }

  prepareTypewriter() {
    this.text.setAttribute('aria-label', this.fullText);
    this.text.textContent = '';
    this.typed = document.createElement('span');
    this.typed.setAttribute('aria-hidden', 'true');
    // Reserve the final size up front so nothing below jumps while typing.
    this.ghost = document.createElement('span');
    this.ghost.setAttribute('aria-hidden', 'true');
    this.ghost.style.visibility = 'hidden';
    this.ghost.textContent = this.fullText;
    const caret = document.createElement('span');
    caret.className = 'statement__caret';
    caret.setAttribute('aria-hidden', 'true');
    this.text.append(this.typed, caret, this.ghost);
  }

  reveal(effect) {
    this.classList.add('is-revealed');
    if (effect !== 'typewriter') return;
    let index = 0;
    const typeNext = () => {
      index += 1;
      this.typed.textContent = this.fullText.slice(0, index);
      this.ghost.textContent = this.fullText.slice(index);
      if (index < this.fullText.length) this.typeTimer = setTimeout(typeNext, TYPE_DELAY_MS);
    };
    typeNext();
  }
}

if (!customElements.get('statement-section')) customElements.define('statement-section', StatementSection);
