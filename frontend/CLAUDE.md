# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the frontend code in this repository.

For more detailed architectural information and development conventions, see `../.github/copilot-instructions.md` and the frontend documentation in `docs/`.

## Common Commands

### Development
```bash
npm install          # Install dependencies
npm run dev          # Development server at http://localhost:5173
npm run build        # Production build
npm run preview      # Preview production build locally
```

### Tech Stack Versions
- **Vue 3**: 3.5.25 (Composition API)
- **Vuetify**: 3.12.0 (Material Design 3)
- **Tailwind CSS**: v4.2.0
- **Vite**: 7.3.1 (build tool)
- **Vue Router**: 5.0.3
- **Pinia**: 3.0.4 (state management, currently empty)
- **Material Design Icons**: @mdi/font 7.4.47

## Architecture Overview

### Fixed Aspect Container Pattern
All page-level components **must** use the `FixedAspectContainer` component with these specifications:

#### Size Specifications
1. **Default size**: `300 × 600px` (component's default props)
2. **Planned size**: `332 × 774.66px` (9:21 aspect ratio, requires explicit props)
3. **Current implementation**: `HomeView` and `SettingsView` use default size; static HTML files (`_page_*/`) use planned size

#### Implementation Requirements
- Must have `id="main-display-block"` for styling and scripting
- Background: `bg-white` + `shadow-2xl`
- Overflow control: Use `useViewportOverflow` composable for automatic detection
- Internal scrolling: `overflow-y: auto` with `.no-scrollbar` class to hide native scrollbars

#### Usage Examples
```vue
<!-- Default size (300×600px) -->
<FixedAspectContainer
  bg-color-class="bg-white"
  extra-class="font-display"
  :shadow="true"
>
  <!-- Page content -->
</FixedAspectContainer>

<!-- Planned size (332×774.66px) -->
<FixedAspectContainer
  :width="332"
  :height="774.66"
  bg-color-class="bg-white"
  extra-class="font-display"
  :shadow="true"
>
  <!-- Page content -->
</FixedAspectContainer>
```

### Four-Layer Message Bubble Architecture
| Component | Responsibility | Notes |
|-----------|----------------|-------|
| `MessageBubble` | **Router** | Distributes based on `name` prop (`'assistant'`/`'user'`) to appropriate component |
| `BasicMessageBubble` | **Generic base** | Accepts `isAssistant` prop; assistant: `bg-primary/10`, user: `bg-slate-100` |
| `AssistantMessageBubble` | **Assistant wrapper** | Thin wrapper, default `icon='smart_toy'`, forwards to `BasicMessageBubble` |
| `UserMessageBubble` | **User wrapper** | Independent implementation; right-aligned, `bg-slate-200` |

**Entry point**: Use `MessageBubble` with `name` prop, or directly use `AssistantMessageBubble`/`UserMessageBubble`.

### Composables Pattern
- **`useLongPress(duration = 350)`**: Long-press interaction logic (`src/composables/useLongPress.js`)
  - **Actual threshold**: 250ms (used in `HomeView`)
  - Returns `{ isActive, start, end, preventClick }`
  - `isActive` controls FAB button styles and `VoiceOverlay` visibility
- **`useViewportOverflow()`**: Viewport adaptation (`src/composables/useViewportOverflow.js`)
  - Automatically detects if `#main-display-block` exceeds `#app` height
  - Adds `.content-exceeds-viewport` class to `#app` for top-aligned layout
  - Monitors `window resize` and component updates

### Layout Architecture
```
div#app (100vw × 100vh, flex centered)
└── div#main-display-block (300 × 600px default / 332 × 774.66px planned)
    ├── Header (sticky if needed)
    ├── Main content (scrollable if exceeds height)
    └── Footer (optional)
```

### Custom Shadow System
Enhanced Material Design 3 effects with custom shadow values:
- **FAB button**: `shadow-[0_8px_20px_rgba(0,0,0,0.35)]`
- **Hover**: `hover:shadow-[0_12px_28px_rgba(0,0,0,0.45)]`
- **Active (listening)**: `!shadow-[0_16px_32px_rgba(0,0,0,0.55)]`

### Voice Interaction
- **Long-press threshold**: 250ms (actual, not 350ms default)
- **Visual feedback**: `ListeningIndicator` with 5‑column waveform animation + double pulse rings
- **Overlay**: `VoiceOverlay` with blur backdrop (`backdrop-blur-md`)
- **Anti‑misclick**: `preventClick` method blocks short taps from triggering `click` events

## Key Files to Read First

| File | Purpose |
|------|---------|
| `docs/ui_design_aesthetics.md` | Complete UI design system (v1.1.0) – colors, typography, spacing, components |
| `docs/ui_design_principles.md` | Core design principles and development guidelines |
| `docs/state_transition_system_design.md` | Four‑state workflow with voice integration patterns |
| `docs/solved_issues.md` | Known problems and solutions (e.g., CSS animation vs. scrolling conflict) |
| `src/components/FixedAspectContainer.vue` | Fixed‑size page container (all pages must use) |
| `src/views/HomeView.vue` | Home page with voice interaction and message dialogs |
| `src/views/SettingsView.vue` | Settings page with complete component library |
| `src/composables/useLongPress.js` | Long‑press logic (250ms threshold) |
| `src/composables/useViewportOverflow.js` | Viewport overflow detection and smart adaptation |
| `src/components/AppBottomNav.vue` | Bottom navigation + FAB microphone button |
| `src/components/message-bubbles/` | Four‑layer message bubble component architecture |
| `src/components/settings/` | Settings‑page‑specific components |

## Development Conventions

### Component Structure
- **`src/views/`** – Page‑level components (mapped from router)
- **`src/components/`** – Reusable components
- **`src/stores/`** – Pinia stores (currently empty)
- **`src/router/index.js`** – Route definitions; use lazy‑loading (`() => import(...)`) for all non‑home views

### Styling Approach
- Use **Vuetify components** (`v-btn`, `v-card`, etc.) for structure and interactions
- Use **Tailwind utility classes** for spacing, typography, layout not covered by Vuetify
- Avoid custom CSS where utilities suffice
- **Custom animations** go in `style.css` with `@keyframes`

### Store Pattern (Setup‑Store Style)
```js
// Example (stores currently empty in project)
export const useCounterStore = defineStore('counter', () => {
  const count = ref(0)
  const doubleCount = computed(() => count.value * 2)
  function increment() { count.value++ }
  return { count, doubleCount, increment }
})
```

### Routing
- Home route (`/`) loads `HomeView`
- Settings route (`/settings`) lazy‑loads `SettingsView`
- Router configured in `src/router/index.js`

## Project Status

### ✅ Completed
- **Base architecture**: Vue 3 + Vite + Vuetify 3 + Tailwind CSS v4
- **Routing system**: Home + Settings pages with lazy loading
- **Core component library**: Full UI component system
- **Voice interaction UI**: Long‑press recording + visual feedback
- **Message system**: Four‑layer message bubble architecture
- **Settings page**: Complete settings interface components
- **Responsive layout**: Smart viewport overflow detection
- **Composables**: `useLongPress` and `useViewportOverflow`

### ⏳ Pending
- **Backend integration**: Currently uses mock data; needs connection to backend API
- **State management**: Pinia stores directory empty, needs implementation
- **Voice functionality**: Speech recognition and synthesis integration
- **Navigation interface**: Hospital map navigation functionality

## Important Constraints

1. **Fixed Aspect Container**: All pages must use `FixedAspectContainer` with consistent sizing.
2. **Long‑press threshold**: Voice interaction uses 250ms (not the default 350ms).
3. **Overflow handling**: Content must not overflow `#app`; use `useViewportOverflow` for adaptation.
4. **Shadow consistency**: Use custom shadow values for enhanced Material Design 3 effects.
5. **Component reusability**: Extract common patterns into reusable components.

## Troubleshooting

### CSS Animation vs. Scrolling Conflict
**Problem**: Adding Vue Transition animations can break scrolling in `ConversationList`.
**Solution**: Three‑container architecture (documented in `docs/solved_issues.md`):
1. Animation container (outer) – handles CSS transitions
2. Positioning container (middle) – maintains layout flow
3. Scroll container (inner) – fixed height with `overflow-y: auto`

### FAB Button Not Showing Listening State
- Ensure `useLongPress(250)` is called with 250ms threshold
- Check that `isActive` controls both FAB styles and `VoiceOverlay` visibility
- Verify `preventClick` is bound to `@click` on the button

### Container Size Mismatch
- `FixedAspectContainer` defaults to 300×600px
- For 332×774.66px, explicitly pass `:width="332" :height="774.66"`
- Check static HTML files in `_page_*/` for reference implementation

## Quick Reference

### Voice Interaction Setup
```vue
<script setup>
import { useLongPress } from '@/composables/useLongPress'

const { isActive: isListening, start, end, preventClick } = useLongPress(250)
</script>

<template>
  <button
    @mousedown="start"
    @touchstart="start"
    @mouseup="end"
    @touchend="end"
    @mouseleave="end"
    @click="preventClick"
    :class="{ 'scale-95 bg-primary/90': isListening }"
  >
    <!-- FAB content -->
  </button>

  <VoiceOverlay :visible="isListening" />
</template>
```

### Viewport Overflow Detection
```vue
<script setup>
import { useViewportOverflow } from '@/composables/useViewportOverflow'

// Automatically monitors and adapts layout
useViewportOverflow()
</script>
```

### Message Bubble Usage
```vue
<!-- Using router component -->
<MessageBubble name="assistant" :message="msg.text" />

<!-- Direct component usage -->
<AssistantMessageBubble :message="msg.text" />
<UserMessageBubble :message="msg.text" />
```