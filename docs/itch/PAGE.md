# itch.io page kit — Catcher (gameship demo)

Media in this folder: `cover.gif` (animated cover, 596K), `cover.png`
(static fallback), `shot_1..3.png` (gameplay screenshots).

## Fields

**Title:** Catcher — gameship demo
**Short description / tagline:**
> A 60-line pygame catcher, shipped to this page with one command. Packaged & published with gameship.

**Classification:** Game · **Kind:** Downloadable · **Pricing:** No payments
**Genre:** Arcade · **Made with:** pygame · **Average session:** A few minutes
**Tags (itch field):** `pygame`, `arcade`, `demo`, `open-source`, `short`, `singleplayer`

## Description (paste into the rich-text editor)

Catch the falling squares. Arrows or A/D to move. That's the whole game —
it exists to prove a pipeline:

**This page was built and published with [gameship](https://github.com/Neuroforge/gameship)** — a small open tool that takes a pygame project and ships it:

- `gameship build` → a real double-clickable app (PyInstaller, zero config)
- `gameship push` → this itch.io page (butler, auto-installed)
- `gameship ci` → a GitHub Actions workflow that builds Windows/macOS/Linux on every version tag

`pip install gameship` — free for making and selling your games (FSL; each release becomes MIT after 2 years).

The catcher itself is 60 lines of pygame, no assets, [source here](https://github.com/Neuroforge/gameship/blob/main/example/main.py).

**macOS note:** the build is unsigned (right-click → Open the first time). That's an honest limitation of free packaging today — a signing pipeline is on the gameship roadmap.

## Upload settings

- butler-pushed channel `mac` appears automatically → tick **Executable → macOS**
- When Windows/Linux channels land via CI later, tick their platforms the same way.

## After publish

1. Copy the page URL → goes into gameship's README ("see it in the wild").
2. Check the page shows the animated cover (falls back to PNG if the GIF is rejected).
