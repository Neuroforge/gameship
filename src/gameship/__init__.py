"""gameship — ship your Python game.

One command from a pygame/pygame-ce (or any windowed Python) project to
per-OS distributables and an itch.io release:

    gameship build              # freeze with PyInstaller -> dist/<platform>/
    gameship push user/game     # butler push to itch.io (auto-installs butler)
    gameship web                # pygbag -> browser build (pygame-ce only)
    gameship ci                 # write the 3-OS GitHub Actions workflow

Zero config: entry point, name, and assets are detected; flags override.
"""
import argparse
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

__version__ = "0.1.2"

PLATFORM = {"darwin": "mac", "win32": "windows"}.get(sys.platform, "linux")
BUTLER_URL = (
    "https://broth.itch.zone/butler/{os}-amd64/LATEST/archive/default".format(
        os={"mac": "darwin", "windows": "windows"}.get(PLATFORM, "linux")
    )
)


def die(msg: str) -> "None":
    print(f"gameship: {msg}", file=sys.stderr)
    sys.exit(1)


def find_entry(root: Path, explicit: str | None) -> Path:
    if explicit:
        p = root / explicit
        if not p.exists():
            die(f"entry file not found: {p}")
        return p
    for name in ("main.py", "game.py", "run_game.py"):
        if (root / name).exists():
            return root / name
    candidates = [p for p in root.glob("*.py") if not p.name.startswith("_")]
    if len(candidates) == 1:
        return candidates[0]
    die(
        f"couldn't pick an entry point in {root} — found "
        f"{[c.name for c in candidates] or 'no .py files'}. "
        "Name it main.py or pass --entry FILE."
    )


def game_name(root: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        import tomllib

        try:
            name = tomllib.loads(pyproject.read_text()).get("project", {}).get("name")
            if name:
                return name
        except tomllib.TOMLDecodeError:
            pass
    return root.resolve().name


def build(args) -> None:
    root = Path(args.path)
    if not root.is_dir():
        die(f"not a directory: {root}")
    entry = find_entry(root, args.entry)
    name = game_name(root, args.name)
    dist = Path(args.dist or (root / "dist" / PLATFORM)).resolve()
    work = dist.parent / ".gameship-work"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--windowed", "--name", name,
        "--distpath", str(dist), "--workpath", str(work),
        "--specpath", str(work),
    ]
    sep = ";" if PLATFORM == "windows" else ":"
    for adir in ("assets", "data", "resources"):
        if (root / adir).is_dir():
            cmd += ["--add-data", f"{root / adir}{sep}{adir}"]
    if args.onefile:
        cmd.append("--onefile")
    cmd.append(str(entry))

    print(f"gameship: building '{name}' from {entry.name} for {PLATFORM}")
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        die("PyInstaller not found — pip install pyinstaller")
    except subprocess.CalledProcessError as e:
        die(f"PyInstaller failed (exit {e.returncode})")
    shutil.rmtree(work, ignore_errors=True)
    print(f"gameship: done -> {dist}")
    print("gameship: note — bundled asset paths resolve relative to the exe; "
          "load files relative to __file__ or sys._MEIPASS-aware helpers.")


def butler_bin() -> str:
    found = shutil.which("butler")
    if found:
        return found
    cache = Path.home() / ".cache" / "gameship"
    exe = cache / ("butler.exe" if PLATFORM == "windows" else "butler")
    if exe.exists():
        return str(exe)
    cache.mkdir(parents=True, exist_ok=True)
    zip_path = cache / "butler.zip"
    print(f"gameship: fetching butler ({BUTLER_URL})")
    urllib.request.urlretrieve(BUTLER_URL, zip_path)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(cache)
    zip_path.unlink()
    exe.chmod(0o755)
    return str(exe)


def push(args) -> None:
    if "/" not in args.target:
        die("target must be user/game (your itch.io username/project slug)")
    dist = Path(args.path or f"dist/{PLATFORM}")
    if not dist.is_dir():
        die(f"no build at {dist} — run `gameship build` first")
    if not os.environ.get("BUTLER_API_KEY"):
        die("BUTLER_API_KEY not set — get one at https://itch.io/user/settings/api-keys")
    channel = args.channel or PLATFORM
    cmd = [butler_bin(), "push", str(dist), f"{args.target}:{channel}"]
    if args.userversion:
        cmd += ["--userversion", args.userversion]
    print("gameship:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        die(
            f"butler push failed (exit {e.returncode}). If the error above says "
            f"'invalid game': the itch.io project doesn't exist yet — create it at "
            f"https://itch.io/game/new with the URL slug exactly "
            f"'{args.target.split('/', 1)[1]}', save as draft, then re-run."
        )


def web(args) -> None:
    root = Path(args.path)
    entry = find_entry(root, args.entry)
    try:
        import pygame  # noqa: F401

        if not getattr(pygame, "IS_CE", False):
            print(
                "gameship: warning — pygbag supports pygame-ce, not classic pygame "
                "(pip install pygame-ce). Also: your main loop must be async "
                "(https://pygame-web.github.io/wiki/pygbag/). Continuing anyway."
            )
    except ImportError:
        pass
    try:
        subprocess.run(
            [sys.executable, "-m", "pygbag", "--build", str(entry.parent)], check=True
        )
    except FileNotFoundError:
        die("pygbag not found — pip install pygbag")
    except subprocess.CalledProcessError as e:
        die(f"pygbag failed (exit {e.returncode})")
    print(f"gameship: web build -> {entry.parent / 'build' / 'web'}")


WORKFLOW = """\
# Made by `gameship ci` — builds your game for Windows/macOS/Linux on every
# version tag (and by hand from the Actions tab). To also publish to itch.io:
#   1. repo Settings > Secrets > Actions: add BUTLER_API_KEY
#   2. repo Settings > Variables > Actions: add ITCH_TARGET = youruser/your-game
name: gameship
on:
  push:
    tags: ["v*"]
  workflow_dispatch:

jobs:
  build:
    strategy:
      fail-fast: false
      matrix:
        include:
          - { os: ubuntu-latest,  channel: linux }
          - { os: windows-latest, channel: windows }
          - { os: macos-latest,   channel: mac }
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - name: install game deps
        shell: bash
        run: |
          pip install pyinstaller gameship
          [ -f requirements.txt ] && pip install -r requirements.txt || pip install pygame-ce
      - run: gameship build
      - uses: actions/upload-artifact@v4
        with:
          name: game-${{ matrix.channel }}
          path: dist/
      - name: publish to itch.io
        if: ${{ env.KEY != '' && vars.ITCH_TARGET != '' }}
        shell: bash
        env:
          KEY: ${{ secrets.BUTLER_API_KEY }}
          BUTLER_API_KEY: ${{ secrets.BUTLER_API_KEY }}
        run: gameship push "${{ vars.ITCH_TARGET }}" --channel "${{ matrix.channel }}"
"""


def ci(args) -> None:
    out = Path(args.path) / ".github" / "workflows" / "gameship.yml"
    if out.exists() and not args.force:
        die(f"{out} exists — pass --force to overwrite")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(WORKFLOW)
    print(f"gameship: wrote {out}")
    print("gameship: tag a release (git tag v1.0 && git push --tags) to build; "
          "add BUTLER_API_KEY + ITCH_TARGET to publish.")


def main() -> None:
    ap = argparse.ArgumentParser(prog="gameship", description=__doc__.splitlines()[0])
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="freeze the game for this OS -> dist/<platform>/")
    b.add_argument("path", nargs="?", default=".")
    b.add_argument("--entry", help="entry .py (default: auto-detect main.py)")
    b.add_argument("--name", help="app name (default: pyproject name or folder)")
    b.add_argument("--dist", help="output dir (default: dist/<platform>)")
    b.add_argument("--onefile", action="store_true", help="single-file binary")
    b.set_defaults(fn=build)

    p = sub.add_parser("push", help="push a build to itch.io via butler")
    p.add_argument("target", help="itch.io user/game")
    p.add_argument("path", nargs="?", help="build dir (default dist/<platform>)")
    p.add_argument("--channel", help="itch channel (default: this platform)")
    p.add_argument("--userversion", help="version string shown on itch")
    p.set_defaults(fn=push)

    w = sub.add_parser("web", help="browser build via pygbag (pygame-ce)")
    w.add_argument("path", nargs="?", default=".")
    w.add_argument("--entry")
    w.set_defaults(fn=web)

    c = sub.add_parser("ci", help="write the 3-OS GitHub Actions workflow")
    c.add_argument("path", nargs="?", default=".")
    c.add_argument("--force", action="store_true")
    c.set_defaults(fn=ci)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
