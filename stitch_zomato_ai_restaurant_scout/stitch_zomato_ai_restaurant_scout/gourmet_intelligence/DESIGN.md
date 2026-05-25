---
name: Gourmet Intelligence
colors:
  surface: '#fcf9f8'
  surface-dim: '#dcd9d9'
  surface-bright: '#fcf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f2'
  surface-container: '#f0eded'
  surface-container-high: '#eae7e7'
  surface-container-highest: '#e5e2e1'
  on-surface: '#1b1b1b'
  on-surface-variant: '#5b403f'
  inverse-surface: '#313030'
  inverse-on-surface: '#f3f0ef'
  outline: '#8f6f6e'
  outline-variant: '#e4bebc'
  surface-tint: '#bb162c'
  primary: '#b7122a'
  on-primary: '#ffffff'
  primary-container: '#db313f'
  on-primary-container: '#fffbff'
  inverse-primary: '#ffb3b1'
  secondary: '#4648d4'
  on-secondary: '#ffffff'
  secondary-container: '#6063ee'
  on-secondary-container: '#fffbff'
  tertiary: '#006762'
  on-tertiary: '#ffffff'
  tertiary-container: '#00837c'
  on-tertiary-container: '#f3fffd'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdad8'
  primary-fixed-dim: '#ffb3b1'
  on-primary-fixed: '#410007'
  on-primary-fixed-variant: '#92001c'
  secondary-fixed: '#e1e0ff'
  secondary-fixed-dim: '#c0c1ff'
  on-secondary-fixed: '#07006c'
  on-secondary-fixed-variant: '#2f2ebe'
  tertiary-fixed: '#8ef4eb'
  tertiary-fixed-dim: '#71d7cf'
  on-tertiary-fixed: '#00201e'
  on-tertiary-fixed-variant: '#00504c'
  background: '#fcf9f8'
  on-background: '#1b1b1b'
  surface-variant: '#e5e2e1'
typography:
  display-lg:
    fontFamily: DM Sans
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: DM Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: DM Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 34px
  headline-md:
    fontFamily: DM Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: DM Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.05em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 48px
  max-width: 1280px
---

## Brand & Style
The design system is built to evoke a sense of **appetizing intelligence**. It balances the visceral, emotional appeal of high-quality food photography with the precision and reliability of AI-driven data. The brand personality is trustworthy, modern, and high-tech, positioning itself as a sophisticated culinary concierge rather than a simple directory.

The visual style is **Modern / Corporate**, leaning into a clean, card-based architecture. It prioritizes clarity and whitespace to allow the vibrant colors of food imagery to take center stage. High-tech "AI" elements are integrated through subtle motion, shimmering gradients, and precision iconography, ensuring the user feels the power of the recommendation engine without overwhelming the "analog" joy of dining.

## Colors
The palette is led by a vibrant **Deep Coral/Red**, designed to stimulate appetite and signal the brand’s heritage in the food space. This is balanced by a **Deep Slate** for primary typography to ensure maximum legibility and a professional, grounded feel.

A secondary **AI Indigo** (#6366F1) is introduced specifically for machine-learning features, "Smart" tags, and recommendation highlights to differentiate algorithmic insights from standard data. Surfaces are kept strictly white to provide a clean stage for food photography, while the light gray background provides enough contrast to define card boundaries through subtle tonal shifts.

## Typography
This design system utilizes a dual-font strategy. **DM Sans** is used for headlines and titles to provide a modern, geometric, and friendly character that feels premium. **Inter** is employed for all UI elements, body text, and data points, ensuring exceptional readability at small sizes, specifically for restaurant menus and address details.

Hierarchy is established through significant weight variance. Restaurant names use `headline-md` or `headline-sm`, while ratings and "AI Match" scores use bold labels to draw the eye immediately. Captions and meta-data should never drop below 12px for accessibility.

## Layout & Spacing
The layout follows a strict **8px grid system**, ensuring all components align with a predictable rhythm. A **12-column fluid grid** is used for desktop views, transitioning to a single-column stacked layout for mobile.

- **Margins:** 16px on mobile to maximize content real estate; 48px on desktop to allow the UI to breathe.
- **Gutters:** A consistent 24px gutter between cards prevents visual clutter.
- **Content Density:** Restaurant cards utilize 16px (md) internal padding, while tighter UI elements like filters use 8px (sm) padding.
- **AI Sections:** Special "AI Recommended" horizontal carousels should allow the first card to bleed slightly off-edge to indicate scrollability.

## Elevation & Depth
Hierarchy is conveyed through **Tonal Layering** and **Ambient Shadows**. The design system avoids heavy borders, instead using the contrast between White (`#FFFFFF`) surfaces and the Off-White (`#F8F8F8`) background to define depth.

- **Level 0 (Background):** The base layer where the page sits.
- **Level 1 (Cards/Inputs):** Standard restaurant cards use a subtle shadow: `0px 4px 12px rgba(0, 0, 0, 0.05)`.
- **Level 2 (Hover/Active):** When a user interacts with a card, the shadow deepens to `0px 8px 24px rgba(0, 0, 0, 0.1)` and the element lifts slightly.
- **Level 3 (Modals/Overlays):** Used for AI insight panels or restaurant details, featuring a backdrop blur (12px) on the obscured content to maintain focus.
- **AI Special Elevation:** Elements generated by AI (like "Match for You") may feature a very faint primary-colored glow (`rgba(226, 55, 68, 0.1)`) instead of a traditional gray shadow to signify importance.

## Shapes
The shape language is **Rounded and Friendly**. 
- **Standard UI Elements:** Buttons, inputs, and small chips use a `0.5rem` (8px) radius.
- **Containers:** Restaurant cards and major sections use a `1rem` (16px) radius to feel modern and approachable.
- **Interactive Accents:** Selection states and focus rings follow the radius of the parent element. 
- **AI Highlights:** Use the same 16px radius but may feature an additional "Sparkle" icon in the top right corner to denote AI-generated content.

## Components
### Buttons
- **Primary:** Solid `#E23744` with white text. High-emphasis actions like "Book Now."
- **Secondary:** White background with a `#1C1C1C` border. Low-emphasis actions like "View Menu."
- **AI Action:** A gradient button or one with a "sparkle" icon prefix for "Generate Recommendation."

### Cards
- **Restaurant Card:** 16px corner radius, white background, soft shadow. Features a top-aligned image with a 16:9 aspect ratio. Text info sits below with clear spacing for title, rating (star icon), and price level (₹₹).
- **AI Match Chip:** A small, semi-transparent indigo or primary-tinted badge sitting atop cards showing a percentage (e.g., "98% Match").

### Input Fields
- Clean, white backgrounds with a 1px border (`#E0E0E0`). On focus, the border transitions to the Primary Red with a soft 2px outer glow.

### Chips & Tags
- **Status Tags:** Green for "Open Now", Amber for "Filling Fast."
- **Filter Chips:** 8px radius, light gray background, turning black or primary red when selected.

### Icons
- Use a consistent line-weight (2px). Icons for AI features should use the AI Indigo color. Icons for standard actions use Deep Slate.