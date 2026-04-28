---
version: alpha
name: ECOS
description: Visual identity for the ECOS national early warning platform for epidemiological risk in Colombia.
colors:
  background: "#F7F1E8"
  background-soft: "#EFE6D8"
  surface: "#FFFDF9"
  foreground: "#1C1A17"
  foreground-muted: "#64605A"
  border: "#D7CABB"
  primary: "#1C1A17"
  primary-contrast: "#FFFDF9"
  accent: "#8C441A"
  accent-soft: "#E8B48D"
  signal: "#16725A"
  warning: "#7A4D0F"
  danger: "#9B2D2D"
typography:
  h1:
    fontFamily: Geist
    fontSize: 4rem
    fontWeight: 600
    lineHeight: 1
    letterSpacing: -0.04em
  h2:
    fontFamily: Geist
    fontSize: 2.5rem
    fontWeight: 600
    lineHeight: 1.08
    letterSpacing: -0.03em
  h3:
    fontFamily: Geist
    fontSize: 1.5rem
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: -0.02em
  body-md:
    fontFamily: Geist
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: 0
  body-lg:
    fontFamily: Geist
    fontSize: 1.125rem
    fontWeight: 400
    lineHeight: 1.7
    letterSpacing: 0
  label-caps:
    fontFamily: Geist Mono
    fontSize: 0.75rem
    fontWeight: 600
    lineHeight: 1
    letterSpacing: 0.22em
rounded:
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
components:
  page-background:
    backgroundColor: "{colors.background}"
  section-band:
    backgroundColor: "{colors.background-soft}"
    textColor: "{colors.foreground}"
  hero-surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.xl}"
    padding: "{spacing.2xl}"
  meta-text:
    textColor: "{colors.foreground-muted}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-contrast}"
    rounded: "999px"
    padding: "12px 24px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.foreground}"
    rounded: "999px"
    padding: "12px 24px"
  accent-chip:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.accent}"
    rounded: "999px"
    padding: "8px 16px"
  accent-soft-chip:
    backgroundColor: "{colors.accent-soft}"
    textColor: "{colors.primary}"
    rounded: "999px"
    padding: "8px 16px"
  signal-chip:
    backgroundColor: "{colors.signal}"
    textColor: "{colors.primary-contrast}"
    rounded: "999px"
    padding: "8px 16px"
  warning-badge:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.warning}"
    rounded: "999px"
    padding: "8px 16px"
  warning-chip:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-contrast}"
    rounded: "999px"
    padding: "8px 16px"
  danger-chip:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.primary-contrast}"
    rounded: "999px"
    padding: "8px 16px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.lg}"
    padding: "20px"
  divider:
    backgroundColor: "{colors.border}"
    height: "1px"
    width: "100%"
---

## Overview

ECOS is not a generic SaaS dashboard. The UI should feel like a public-interest instrument: calm, authoritative, and legible under pressure. The visual language mixes editorial seriousness with operational clarity so decision-makers can scan risk quickly without losing context.

The interface should avoid glossy fintech styling, saturated gradients, and decorative motion that competes with the data. Warm neutrals, deep ink typography, and a single amber accent carry the brand. Use green only for positive signal states and red only for risk or alerts.

## Colors

The palette is intentionally restrained. Most screens should be built from neutrals, with accent color reserved for calls to action and highlighted risk indicators.

- **Background (#F7F1E8):** Main canvas. Slightly warm so the product feels human and public-facing.
- **Background soft (#EFE6D8):** Secondary canvas for stacked panels and subtle separation.
- **Surface (#FFFDF9):** Cards, panels, and elevated content areas.
- **Foreground (#1C1A17):** Primary text, headings, and core UI chrome.
- **Foreground muted (#64605A):** Metadata, labels, helper text, and secondary labels.
- **Border (#D7CABB):** Thin separators and panel outlines.
- **Primary (#1C1A17):** Primary action color for strong buttons and key labels.
- **Accent (#A85822):** The only warm interaction accent. Use sparingly for primary CTAs and emphasis.
- **Signal (#16725A):** Supportive positive-state color for stability or low-risk indicators.
- **Warning (#A86B16):** Medium-risk or attention state.
- **Danger (#9B2D2D):** High-risk state, outbreak thresholds, and urgent alerts.

## Typography

Typography should read as concise and institutional. Headlines are compact and confident, while body text stays open enough for dense analytical content.

- **H1 and H2:** Large, tight, and editorial. Use for the main statement and key section titles.
- **H3:** Short functional headings for cards, panels, and module labels.
- **Body text:** Prefer readable line length over compactness. Keep paragraphs calm and legible.
- **Label caps:** Use for status chips, tags, and small system labels only.

## Layout

The default structure is a single dominant hero area with a supporting insight panel. Use generous spacing, clear hierarchy, and a maximum content width that keeps the page from feeling crowded.

- Prefer two-column layouts for desktop, collapsing to a single column on small screens.
- Keep vertical rhythm consistent using 8px and 16px increments.
- Separate dense data modules with soft borders and low-contrast surfaces rather than heavy shadows.
- Reserve full-width sections for high-level summaries and critical signals.

## Elevation & Depth

Depth should be subtle. The product is not trying to feel playful or glossy.

- Use minimal shadow on cards and action chips.
- Prefer border contrast and surface contrast over large blur shadows.
- Higher elevation is reserved for overlays, not ordinary content.

## Shapes

ECOS should feel rounded but not soft in a consumer-app way.

- Buttons use full pill radius.
- Cards use medium to large radius to keep the interface calm and approachable.
- Avoid irregular or highly decorative shapes.

## Components

### Buttons

- Primary button: dark background, light text, compact pill shape.
- Secondary button: light surface with border and dark text.
- Hover states should change contrast slightly, not introduce bright glows.

### Cards

- Cards are used for indicators, explanation panels, and summary modules.
- Card content should start with a short label or eyebrow and then a concise value or explanation.

### Status chips

- Use muted chips for informational labels.
- Use green, amber, or red only when they encode risk or alert state.

### Data panels

- Charts and tables should sit inside clear surfaces with consistent padding.
- Titles, axis labels, and helper text should all use the same muted foreground tone.

## Do's and Don'ts

- Do use warm neutrals, deep ink, and restrained accents.
- Do keep the UI editorial and operational rather than flashy.
- Do make alert language explicit and easy to scan.
- Do use consistent card spacing and clear content hierarchy.
- Don't use purple-heavy defaults, neon gradients, or glassmorphism.
- Don't mix too many accent colors on the same screen.
- Don't decorate charts with effects that reduce readability.
- Don't let the frontend drift back into a generic starter template.