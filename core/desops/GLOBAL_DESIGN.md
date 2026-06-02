---
name: NAUTILUS Sovereign UI
version: 1.0.0
tokens:
  colors:
    primary: "#0A84FF"
    secondary: "#5E5CE6"
    background:
      light: "#F2F2F7"
      dark: "#1C1C1E"
    surface:
      light: "#FFFFFF"
      dark: "#2C2C2E"
    text:
      primary: "#000000"
      secondary: "#8E8E93"
  typography:
    font-family:
      heading: "Inter, system-ui, sans-serif"
      body: "Inter, system-ui, sans-serif"
      mono: "JetBrains Mono, monospace"
  rounded:
    sm: 4px
    md: 8px
    lg: 12px
    full: 9999px
  spacing:
    unit: 4px
    xs: 4px
    sm: 8px
    md: 16px
    lg: 24px
    xl: 32px
---

# NAUTILUS Global Design Tokens

This file serves as the **Single Source of Truth** for the visual identity of the NAUTILUS Sovereign Personal Knowledge Mesh.

## Overview
The "Sovereign UI" is designed to be minimalist, high-contrast, and focused on deep context and data density. It follows the **SOVRN v3.3 Architecture**.

## Colors
- **Primary:** Actionable elements and brand presence.
- **Secondary:** Accentuation and complementary UI states.
- **Background:** System-level surface areas.

## Usage
All projects in the `Efforts` directory should inherit from these tokens. Local `DESIGN.md` files may extend these tokens but should not override the core brand identity without justification.
