Implement the following feature for this RAG chatbot project: $ARGUMENTS

Follow these steps:

1. **Understand the codebase** — read the relevant frontend files (`frontend/index.html`, `frontend/style.css`, `frontend/script.js`) and any backend files needed for context before writing any code.

2. **Plan** — identify exactly what needs to change (HTML, CSS, JS, backend) and explain the approach before implementing.

3. **Implement** — make all necessary changes following the existing design conventions:
   - Dark theme base using CSS custom properties in `:root`
   - Flat SVG icons (stroke-based, no fill)
   - Transitions on interactive elements (`0.2s ease`)
   - `focus-visible` rings using `var(--focus-ring)` for keyboard accessibility
   - Bump the cache-busting version query string on `style.css` and `script.js` references in `index.html`

4. **Accessibility** — ensure any new interactive elements have:
   - Meaningful `aria-label` attributes (updated dynamically if state changes)
   - Keyboard navigability (native `<button>` elements where possible)
   - `focus-visible` outline styles

5. **Persistence** — if the feature involves a user preference (e.g. theme, layout), persist it in `localStorage` and restore it on page load.

6. **Summary** — briefly describe what changed and why each decision was made.
