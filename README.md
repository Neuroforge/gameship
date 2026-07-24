# gameship

**Ship your Python game.** One command from a pygame project to real
Windows / macOS / Linux builds and an itch.io release — the workflow every
Python gamedev currently hand-rolls from PyInstaller + GitHub Actions + butler
blog posts, packaged.

```bash
pip install gameship pyinstaller

gameship build                # freeze this OS's build   -> dist/<platform>/
gameship push you/your-game   # publish to itch.io (butler auto-installed)
gameship ci                   # write the 3-OS GitHub Actions workflow
gameship web                  # browser build via pygbag (pygame-ce)
```

## Why

Python gamedevs are great at game code and stuck on the last mile: a real
double-clickable app for people who don't have Python, built for all three
OSes, uploaded to itch.io. The tools all exist — PyInstaller can't
cross-compile so you need per-OS builders, butler is scriptable but manual,
the GitHub Actions matrix is a blog-post ritual. gameship glues them so you
never think about it:

- **`gameship build`** — detects your entry point (`main.py`) and `assets/`
  folder, names the app from your `pyproject.toml` or folder, runs PyInstaller
  windowed, outputs to `dist/<platform>/`.
- **`gameship ci`** — drops a ready GitHub Actions workflow: every `v*` tag
  builds Windows + macOS + Linux in parallel and uploads artifacts. Add a
  `BUTLER_API_KEY` secret and an `ITCH_TARGET` variable and it also publishes
  each build to the right itch.io channel.
- **`gameship push`** — wraps [butler](https://itch.io/docs/butler/), itch.io's
  official CLI (downloads it on first use), so local pushes are one line too.
- **`gameship web`** — wraps [pygbag](https://pygame-web.github.io/) for a
  browser build you can host on itch.io's HTML5 player (pygame-ce projects
  with an async main loop).

## Quick start (60 seconds, local)

```bash
cd your-game/          # has a main.py that runs your game
pip install gameship pyinstaller
gameship build
open "dist/mac/YourGame.app"        # or dist/windows/, dist/linux/
```

## Full release pipeline (10 minutes, once)

```bash
gameship ci
git add .github && git commit -m "release workflow" && git push
# GitHub repo -> Settings -> Secrets -> Actions: BUTLER_API_KEY (from itch.io)
# GitHub repo -> Settings -> Variables -> Actions: ITCH_TARGET=you/your-game
git tag v1.0 && git push --tags
```

Three OS builds appear as artifacts; each pushes to `you/your-game:windows`,
`:mac`, `:linux` on itch.io. Delta uploads, versioned channels — butler's
whole feature set, none of its setup.

## Honest limitations (v0)

- PyInstaller quirks are inherited: Windows Defender sometimes flags frozen
  Python apps (code-signing fixes it; on the roadmap), and asset paths inside
  the bundle should be loaded relative to your script, not the cwd.
- `gameship web` requires pygame-ce and an async-ified main loop — that's a
  [pygbag rule](https://pygame-web.github.io/wiki/pygbag/), not ours; we warn
  rather than rewrite your code.
- macOS builds are unsigned/un-notarized (players right-click > Open). Signing
  + notarization service is the roadmap item after this one.
- Steam/Epic: not yet. itch.io first, on purpose.

## Example

[`example/`](example/) is a complete 60-line pygame catcher — the repo's CI
builds it on all three OSes and smoke-runs the frozen binary headless
(`SDL_VIDEODRIVER=dummy GAMESHIP_MAX_FRAMES=120`).

## Common questions this answers

**How do I turn my pygame game into an .exe?** `gameship build` on a Windows
machine (or let the generated workflow's Windows runner do it) — PyInstaller
under the hood, no spec file to write.

**How do I make a Mac .app from a pygame game?** Same command on macOS:
`gameship build` → `dist/mac/YourGame.app`.

**How do I upload a pygame game to itch.io automatically?** `gameship push
you/your-game` locally, or add the `BUTLER_API_KEY` secret so every tagged
release publishes to your itch channels from CI.

**How do I build my game for Windows, Mac, and Linux at once?** You can't
cross-compile Python — nobody can — so `gameship ci` writes the GitHub
Actions matrix that builds natively on all three, free on public repos.

**Can my pygame game run in the browser?** If it's pygame-ce with an async
main loop: `gameship web` (pygbag), then upload the build as an itch.io HTML5
game.

## License

MIT. Assets: none — the example uses shapes.
