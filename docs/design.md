# Design Document — The Lenny Growth Assistant

## UI/UX Principles

1. **Grounded clarity**: Every answer shows its source. Users should never wonder "did the AI make this up?"
2. **Minimal friction**: One click to start a new chat. No login, no setup visible to the user.
3. **Content-first**: The chat and artifact panel share the screen equally when an artifact is present; the chat takes full width otherwise.
4. **Honest states**: Loading, empty, error, and success states are all explicitly designed — no silent failures.
5. **Accessible by default**: Sufficient color contrast, keyboard navigation, ARIA labels on interactive elements.

---

## Information Architecture

```
App
├── Sidebar (left, collapsible on mobile)
│   ├── Logo / App name
│   ├── "New Chat" button
│   └── Session list (future: recent chats)
├── Chat Panel (center)
│   ├── EmptyState (when no messages)
│   ├── Message list
│   │   ├── UserMessage
│   │   └── AssistantMessage
│   │       ├── Markdown body
│   │       ├── Source citation badge
│   │       └── "View Artifact" button (if artifact present)
│   └── ChatInput (bottom)
│       ├── Textarea (auto-resize)
│       ├── Model indicator badge
│       └── Send button
└── Artifact Panel (right, shown when artifact exists)
    ├── Tab bar: "Preview" | "Source"
    ├── Preview: sandboxed iframe (HTML) or ReactMarkdown (Markdown)
    └── Source: raw code with copy button
```

---

## Key Interaction States

### Chat Input
- **Idle**: Placeholder text "Ask about product growth, retention, pricing..."
- **Typing**: Character count visible at 500+ chars
- **Sending**: Input disabled, spinner on send button
- **Error**: Red border, error message below input

### Assistant Message
- **Loading**: Animated ellipsis "Thinking..."
- **Streaming** (future): Text appears progressively
- **Complete**: Full message with source badge
- **No source found**: Message displayed without badge; note "Based on general knowledge"

### Artifact Viewer
- **No artifact**: Panel hidden; chat takes full width
- **Artifact present**: Panel slides in from right (desktop) or appears below chat (mobile)
- **HTML artifact**: Rendered in `<iframe sandbox="allow-same-origin">` — scripts blocked, forms blocked, popups blocked
- **Markdown artifact**: Rendered via react-markdown with syntax highlighting

---

## Responsive Behavior

| Breakpoint | Layout |
|---|---|
| ≥1024px (desktop) | Sidebar (240px) + Chat + Artifact panel side-by-side |
| 768–1023px (tablet) | Sidebar hidden (hamburger toggle) + Chat + Artifact stacked |
| <768px (mobile) | Single column; artifact appears below chat |

---

## Accessibility Considerations

- All buttons have `aria-label` attributes
- Chat messages use `role="log"` and `aria-live="polite"` for screen reader announcements
- Color is never the sole indicator of state (icons + text used alongside color)
- Focus is moved to the new message after send
- Keyboard shortcut: `Ctrl+Enter` / `Cmd+Enter` to send message

---

## Design Decisions

### Why TailwindCSS?
Utility-first CSS keeps component styles co-located with markup, reducing context switching. No separate CSS files to maintain.

### Why react-markdown for Markdown rendering?
Safe by default — no raw HTML injection. Supports GFM (tables, task lists) needed for Ship30 essays.

### Why sandboxed iframe for HTML artifacts?
Generated HTML is untrusted. The `sandbox` attribute without `allow-scripts` prevents JavaScript execution, form submission, and navigation. This is the simplest isolation strategy that doesn't require a separate origin or CSP headers.

**What the viewer permits:**
- Rendering HTML structure and CSS styles
- Displaying images from data URIs

**What the viewer blocks:**
- JavaScript execution (`allow-scripts` not set)
- Form submission (`allow-forms` not set)
- Opening popups or navigating the parent frame
- Access to cookies or localStorage

### Why a side panel instead of a modal for artifacts?
Modals interrupt the conversation flow. A persistent side panel lets users reference the artifact while continuing to chat — matching the Claude Artifacts UX pattern specified in the assignment.

### Model indicator badge
The current LLM provider and model name are shown in the chat input area. This satisfies the assignment requirement to make the selected provider visible in the UI without cluttering the interface.
