# FaroDocs visual system

Status: current local library preview. This describes the FaroDocs-specific UI in `web/src/app/styles.css`; it is not a reusable system imported from another project.

## Mode and layout

The library is an **Operate** surface. The owner should be able to scan document state, act on one document, and inspect a passage without leaving the work context. Desktop uses a narrow navigation rail, a main document area, an organization panel, and an inline detail region. At narrow widths these areas stack while controls remain keyboard reachable.

## Tokens

| Role | Token | Current value |
| --- | --- | --- |
| Reading background | `--paper` | `#f7f3ea` |
| Control and panel surface | `--surface` | `#fffefb` |
| Main text | `--ink` | `#17263d` |
| Secondary text | `--muted` | `#526176` |
| Rules | `--rule` | `#d8ddd9` |
| Action and link | `--accent` | `#a84128` |
| Action wash | `--accent-wash` | `#f3dfd6` |
| Selected/data wash | `--data-wash` | `#e9eff1` |

The type stack is Segoe UI, Inter, then Arial. Body copy is compact and readable; headings carry the hierarchy. Borders separate work areas, while status chips use distinct warm, green, and red surfaces. Icons in navigation use one authored SVG stroke style. The brand mark is a letterform for this working title.

## Interaction rules

- Keep primary upload visible near the library heading. Make unavailable search and conversations explicit.
- Use inline document details and version tabs so the owner can compare prior versions.
- Label source locators by page, body block, or character range. Link a PDF passage to its original page; do not imply pixel-accurate highlighting.
- Show processing failures with a useful reason and a retry control.
- Preserve visible focus outlines on controls and links. File inputs remain keyboard focusable through their labeled controls.
- Check both language variants, empty and populated states, errors, and 320–390 px layouts whenever this surface changes.
