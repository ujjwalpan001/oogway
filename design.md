# Design: The Lenny Growth Assistant

---

## Design Principles

1. **Trust through transparency** — Every answer shows its sources. Citations are not a footnote; they're a first-class UI element.
2. **Focus over features** — The interface does three things: chat, generate content, view artifacts. Nothing else clutters the screen.
3. **Earned density** — Information is revealed progressively. Citations collapse; the artifact panel only appears when there's something to show.
4. **Confidence at a glance** — The model badge shows the current LLM and health status without opening a settings screen.

---

## Color & Typography

**Color palette:**
- Background: Deep navy (`#0a0a0f`) — warmer and less harsh than pure black
- Surface: Layered glassmorphism — `rgba(255,255,255,0.04)` with `1px` borders
- Accent: Purple (`#7c6df0`) — sophisticated, not the default blue that every AI tool uses
- Green for online, Red for errors — universally understood signal colors

**Typography:**
- Body: `Inter` — the clearest sans-serif for reading dense information
- Code: `JetBrains Mono` — optimized for code blocks and transcript excerpts
- Scale: 14px body / 12px secondary / 11px metadata

---

## Information Architecture

```
┌─────────────────────────────────────────────────────┐
│  Sidebar (260px)       │  Header (56px)              │
│  - Brand logo          │  - Session title            │
│  - New chat button     │  - Model badge + health     │
│  - Session list        │                             │
│    (title + date)      ├─────────────────────────────│
│  - Footer note         │  Chat column (flex:1)       │
│                        │  - Message list             │
│                        │    - User bubble (right)    │
│                        │    - Assistant bubble       │
│                        │      - Markdown content     │
│                        │      - Skill banner         │
│                        │      - Artifact preview     │
│                        │      - Citations (collapse) │
│                        │                             │
│                        │  Chat input (bottom)        │
│                        │  - Skill selector pills     │
│                        │  - Textarea + send/stop     │
│                        │  - Keyboard hint            │
│                        │                             │
│                        ├─────────────────────────────│
│                        │  Artifact viewer (480px)    │ ← conditional
│                        │  - Header: title, toggle    │
│                        │  - Preview | Code tab       │
│                        │  - Sandboxed iframe         │
│                        │  - Security note (bottom)   │
└────────────────────────┴─────────────────────────────┘
```

---

## Key Interaction States

### Message Bubble
| State | Visual |
|-------|--------|
| Streaming | Three pulsing dots |
| Skill running | Purple banner "Generating Ship 30 essay..." |
| Complete | Markdown rendered, citations collapsible |
| Error | Red inline error with message |

### Artifact Viewer
| State | Visual |
|-------|--------|
| No artifact | Panel hidden, full width for chat |
| Artifact generated | Panel slides in from right (350ms cubic-bezier) |
| Preview tab | Iframe with styled content |
| Code tab | Monospace scrollable raw content |

### Model Badge
| State | Visual |
|-------|--------|
| Groq + online | Purple badge, pulsing green dot |
| Ollama + online | Green badge, pulsing dot |
| LLM unavailable | Badge + red dot |
| Hover | Health tooltip with per-component status rows |

---

## Animations

All animations serve a purpose — they're not decorative:

- **Message fade-in** (`fadeIn 200ms`) — communicates new content arrived
- **Artifact slide-in** (`slideInRight 350ms cubic-bezier(0.16,1,0.3,1)`) — shows the panel emerges from the right edge
- **Skeleton shimmer** — communicates the sidebar is loading, not empty
- **Status dot pulse** — communicates the system is live (not a static indicator)
- **Hover lift on suggestion cards** (`translateY(-2px)`) — invites interaction

---

## Responsive Behavior

| Breakpoint | Behavior |
|-----------|---------|
| ≥1280px | Full layout: sidebar + chat + artifact panel |
| 900px–1280px | Sidebar hidden on artifact open (chat stays at ≥480px) |
| 768px–900px | Sidebar collapses to icons only |
| <768px | Single-column: sidebar accessible via slide-out |

*(Breakpoints implemented via CSS `min-width` media queries — not yet in this MVP build, but the layout is flexbox-based to make them trivial to add.)*

---

## Accessibility

- All interactive elements have `aria-label` or visible text
- `aria-current="true"` on the active session item
- Focus-visible styles on all buttons (2px purple outline, 2px offset)
- Session list items are keyboard-navigable (`role="button"`, `tabIndex=0`, `onKeyDown`)
- Color is never the only differentiator — icons and text accompany all status indicators
- Screen reader friendly: artifact type, session title, and citation content are announced

---

## Design Decisions

**Why not show the raw system prompt?**
Showing prompts encourages prompt hacking. The system prompt is an implementation detail; the UI surface is citations and essays, not model internals.

**Why collapsible citations rather than inline?**
Inline citations would break reading flow. The collapsible pattern lets power users dig in while keeping the default view clean.

**Why sandboxed iframe over a modal/new tab?**
A side panel is where Claude.ai renders artifacts. It's the right metaphor — the artifact is related to the current conversation, not a separate document. A new tab loses that relationship.

**Why purple as the accent?**
Every AI tool in 2024-2025 uses bright blue (#3b82f6) or green (#10b981). Purple with a dark background signals "thoughtful and premium" without being try-hard. It also reads well on dark backgrounds at small sizes.
