---
name: Heritage
description: Architectural Minimalism meets Journalistic Gravitas for epidemiological surveillance
colors:
  primary: "#1A1C1E"
  secondary: "#6C7278"
  tertiary: "#B8422E"
  tertiary-hover: "#9E3827"
  tertiary-alpha: "rgba(184, 66, 46, 0.08)"
  neutral: "#F7F5F2"
  surface: "#FFFFFF"
  surface-hover: "#F0EEEA"
  surface-elevated: "#FFFFFF"
  border: "#E5E2DC"
  border-strong: "#D1CEC8"
  danger: "#D92D20"
  danger-alpha: "rgba(217, 45, 32, 0.08)"
  warning: "#DC6803"
  warning-alpha: "rgba(220, 104, 3, 0.08)"
  success: "#039855"
  success-alpha: "rgba(3, 152, 85, 0.08)"
typography:
  h1:
    fontFamily: Public Sans
    fontSize: 3rem
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: -0.02em
  h2:
    fontFamily: Public Sans
    fontSize: 2rem
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: -0.01em
  h3:
    fontFamily: Public Sans
    fontSize: 1.25rem
    fontWeight: 600
    lineHeight: 1.3
  body-md:
    fontFamily: Public Sans
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.6
  body-sm:
    fontFamily: Public Sans
    fontSize: 0.875rem
    fontWeight: 400
    lineHeight: 1.5
  label-caps:
    fontFamily: Space Grotesk
    fontSize: 0.75rem
    fontWeight: 500
    letterSpacing: 0.08em
    textTransform: uppercase
rounded:
  sm: 6px
  md: 10px
  lg: 16px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  3xl: 64px
  section: 96px
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: 12px 24px
  button-primary-hover:
    backgroundColor: "{colors.tertiary-hover}"
  button-outline:
    backgroundColor: "transparent"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    padding: 12px 24px
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    padding: 24px
  navbar:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.primary}"
    height: 64px
---

## Overview

**Heritage** is a design language for institutional, data-driven interfaces. It evokes the visual gravitas of a premium broadsheet — warm limestone foundations, deep ink headlines, and a single accent that commands attention without screaming.

ECOS is a national epidemiological surveillance platform for Colombia. The UI must feel **authoritative but approachable** — like a well-designed government publication that a health secretary would trust and a data analyst would enjoy using.

The design intentionally avoids the "IA look" (dark gradients, neon accents, glowing borders). Instead, it channels:
- **Architectural minimalism:** Clean lines, generous whitespace, restrained palette
- **Journalistic gravitas:** Clear typographic hierarchy, data-first layouts
- **Institutional warmth:** Limestone tones over cold whites, clay over cold reds

## Colors

The palette is rooted in high-contrast neutrals and a single accent color.

- **Primary (#1A1C1E):** Deep ink for headlines, core text, and primary UI elements. The foundation of all typography.
- **Secondary (#6C7278):** Sophisticated slate for body copy, borders, captions, metadata. Never competes with primary.
- **Tertiary (#B8422E):** "Boston Clay" — the sole driver of user interaction. Buttons, links, focus states, and alert accents. Used sparingly: every instance means "act on this."
- **Neutral (#F7F5F2):** Warm limestone foundation. The page background. Softer than pure white, warmer than gray. This is the canvas that makes everything else feel premium.
- **Surface (#FFFFFF):** Cards, panels, elevated content. Pure white creates a subtle lift against the limestone background.

### Alert Colors (Epidemiological Context)

- **Danger (#D92D20):** Outbreak confirmed, critical alerts — `🔴 ALERTA ALTA`
- **Warning (#DC6803):** Surveillance, elevated indicators — `🟡 VIGILANCIA`
- **Success (#039855):** Normal range, no alert — `🟢 ESTABLE`

These map directly to the epidemiological alert levels used by INS Colombia.

## Typography

Two fonts, one voice:

- **Public Sans** — The workhorse. Used for all body copy, headings, and interface text. A neutral, professional geometric sans-serif from the US Web Design System. It reads clean at every size.
- **Space Grotesk** — The accent voice. Used exclusively for `UPPERCASE LABELS`, technical metadata, and system indicators. Its geometric personality adds a subtle "data console" quality when used sparingly.

### Rules

1. Headlines use Public Sans 700, tracking tight (-0.02em). The density signals authority.
2. Body text uses Public Sans 400 at 1rem/1.6. Generous line-height for readability.
3. Labels use Space Grotesk 500, UPPERCASE, tracking wide (0.08em). This is the "system voice."
4. Never use bold (700) for body text. Hierarchy comes from size and color, not weight.
5. Maximum two font weights per page: 400 (body) and 700 (headlines). Exception: 600 for card titles.

## Layout

### Spacing Philosophy

The spacing system follows an 8px base with intentional jumps:

- **Within cards:** 8–16px (tight, data-dense)
- **Between cards:** 16–24px (breathing room)
- **Between sections:** 48–96px (cinematic pacing)

Each section is a distinct "scene" on the page. The generous section spacing creates a sense of editorial pacing — the user scrolls through a narrative, not a wall of data.

### Container

- Max width: 1200px, centered
- Page padding: 16px (mobile), 24px (tablet), 32px (desktop)

### Grid

- Feature cards: 2-column grid (desktop), single column (mobile)
- Data cards: 3-column grid (desktop), 2-column (tablet), single (mobile)
- Breakpoint: 768px (md), 1024px (lg)

## Elevation & Depth

Heritage uses **subtle elevation**, not dramatic shadows:

| Level | Treatment | Use |
|-------|-----------|-----|
| Level 0 (Flat) | No shadow, border `#E5E2DC` | Default cards, containers |
| Level 1 (Lifted) | `0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06)` | Interactive cards, hover |
| Level 2 (Elevated) | `0 4px 12px rgba(0,0,0,0.06), 0 2px 4px rgba(0,0,0,0.04)` | Chat window, modals |
| Level 3 (Floating) | `0 12px 40px rgba(0,0,0,0.08)` | Floating button, tooltips |

Shadows use pure black at very low opacity (4–8%). The effect is barely perceptible but creates a professional sense of depth without the "material design" heaviness.

## Shapes

- **Cards & containers:** `10px` radius — soft enough to feel modern, sharp enough to feel institutional
- **Buttons:** `10px` radius for standard, `9999px` for pill-shaped CTAs
- **Input fields:** `10px` radius, `1px solid #E5E2DC` border
- **Badges:** `6px` radius — tighter, more utilitarian

## Components

### Buttons

Primary buttons are Boston Clay on white text. They are the only element with the tertiary color as background. This makes them impossible to miss.

Outline buttons have a transparent background with a visible border. They are the secondary action — present but not demanding.

Ghost buttons have no border or background. Used for tertiary actions (close, dismiss, icon actions).

### Cards

Cards sit on white (`#FFFFFF`) against the limestone background (`#F7F5F2`). The contrast is subtle but sufficient — the card "lifts" without needing heavy shadows.

Cards use `1px solid #E5E2DC` borders by default. On hover, the border transitions to `#D1CEC8` for a subtle acknowledgment.

### Badges

Compact, utilitarian chips for metadata and status. Use Space Grotesk uppercase for text. Variants map to alert colors:
- `destructive` → danger red background alpha
- `warning` → warning amber background alpha
- `success` → success green background alpha
- `outline` → transparent with strong border

## Do's and Don'ts

### Do

- Use the limestone background (`#F7F5F2`) as the primary canvas — it's warmer than white and instantly premium
- Reserve Boston Clay (`#B8422E`) for interactive elements only — buttons, links, focus rings
- Use Space Grotesk UPPERCASE labels for system-level metadata ("FUENTE: SIVIGILA", "SEMANA 18")
- Create depth through border differences and subtle shadow, never through color
- Let data breathe — generous spacing between sections, tight spacing within cards
- Use serif hints through letter-spacing and weight, not serif fonts

### Don't

- Don't use gradients, glows, or neon accents — this is a government surveillance tool, not a SaaS product
- Don't use dark backgrounds for primary surfaces — Heritage is light-mode native
- Don't apply Boston Clay to backgrounds or large surfaces — it's for borders, links, and small accents
- Don't use more than 2 font weights (400, 700) in any component
- Don't add decorative elements that don't serve the data
- Don't use generic blue/green/purple — the palette is deliberately restrained
