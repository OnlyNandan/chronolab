# Frontend Guidelines

## Design Aesthetics
ChronoLab requires a **premium, state-of-the-art** visual design. MVP-level or basic generic styling is unacceptable. 

### Core Rules
- **Color Palette:** Do not use plain generic colors (e.g., standard red, blue, green). Use harmonious, curated HSL palettes (e.g., sleek dark modes).
- **Typography:** Use modern, premium Google Fonts (e.g., Inter, Roboto, Outfit). Do not rely on browser default fonts.
- **Micro-interactions:** Add subtle hover effects, smooth transitions, and dynamic micro-animations to encourage interaction and feel "alive".
- **Glassmorphism:** Use backdrop filters and translucent layers to achieve depth where applicable.

## Architecture
- **Tooling:** React + Vite.
- **Styling Method:** Vanilla CSS only (`index.css` and `App.css`). No TailwindCSS.
- **Component Strategy:** Build reusable, encapsulated components leveraging the defined design system tokens in the CSS files.
- **Charts:** Use `Recharts` for the core timeline visualization (`Timeline.jsx`).

## Constraints
- Do not build complex global state management (like Redux) unless strictly necessary; keep state localized or use Context API if it scales.
- Ensure all data visualizations are accurate and handle edge cases (e.g., missing records or mismatched units).
