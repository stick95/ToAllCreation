# ToAllCreation Design System

Based on the official ToAllCreation logo (Mark 16:15).

## Brand Colors

### Primary Colors
- **Primary Blue**: `#5B8DB8` - Main brand color (speech bubble in logo)
- **Secondary Blue**: `#2B6B8F` - Accent color (globe in logo)  
- **Dark Text**: `#2C3E50` - Main text color

### UI Colors
- **Light Background**: `#F8F9FA` - Page background
- **White**: `#FFFFFF` - Card backgrounds
- **Success**: `#4CAF50` - Success states
- **Error**: `#F44336` - Error states
- **Warning**: `#FF9800` - Warning states

## Typography

- **Font Family**: System font stack (SF Pro, Segoe UI, Roboto, etc.)
- **Weights**: 400 (regular), 500 (medium), 600 (semibold)

## Spacing Scale

- XS: 0.25rem (4px)
- SM: 0.5rem (8px)
- MD: 1rem (16px)
- LG: 1.5rem (24px)
- XL: 2rem (32px)
- 2XL: 3rem (48px)

## Border Radius

- Small: 0.375rem (6px)
- Medium: 0.5rem (8px)
- Large: 0.75rem (12px)
- XL: 1rem (16px)
- Full: 9999px (pill shape)

## Shadows

- SM: Subtle shadow for cards
- MD: Default shadow for interactive elements
- LG: Prominent shadow for modals
- XL: Maximum depth for popovers

## Components

### Buttons
- Primary: Blue background, white text
- Secondary: Darker blue, white text
- Border radius: Large (12px)
- Padding: 0.75rem 1.5rem
- Hover: Slight lift effect

### Cards
- Background: White
- Border radius: XL (16px)
- Shadow: Large
- Padding: 2rem

### Inputs
- Border: 2px solid gray
- Focus: Primary blue border with subtle glow
- Border radius: Medium (8px)
- Padding: 0.75rem 1rem

## Logo Usage

- Minimum size: 48px height
- Clear space: 16px around logo
- Backgrounds: Works on white or light gray
- Never distort or recolor

## Files

- `frontend/src/styles/theme.css` - CSS variables and base styles
- `frontend/src/App.css` - App-specific styles
- `frontend/src/index.css` - Global resets

## Implementation

All styles use CSS custom properties (variables) defined in `theme.css`:

```css
var(--primary-blue)
var(--secondary-blue)
var(--dark-text)
var(--spacing-md)
var(--radius-lg)
var(--shadow-md)
```

This ensures consistent design across all components.
