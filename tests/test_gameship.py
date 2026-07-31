"""Unit tests for gameship's pure logic (no PyInstaller/butler/network)."""
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import gameship


def test_version_flag():
    with pytest.raises(SystemExit) as e:
        sys.argv = ["gameship", "--version"]
        gameship.main()
    assert e.value.code == 0


def test_find_entry_prefers_main(tmp_path):
    (tmp_path / "main.py").touch()
    (tmp_path / "other.py").touch()
    assert gameship.find_entry(tmp_path, None).name == "main.py"


def test_find_entry_single_candidate(tmp_path):
    (tmp_path / "mygame.py").touch()
    assert gameship.find_entry(tmp_path, None).name == "mygame.py"


def test_find_entry_explicit_and_missing(tmp_path):
    (tmp_path / "play.py").touch()
    assert gameship.find_entry(tmp_path, "play.py").name == "play.py"
    with pytest.raises(SystemExit):
        gameship.find_entry(tmp_path, "nope.py")


def test_find_entry_ambiguous_dies(tmp_path):
    (tmp_path / "a.py").touch()
    (tmp_path / "b.py").touch()
    with pytest.raises(SystemExit):
        gameship.find_entry(tmp_path, None)


def test_game_name_sources(tmp_path):
    assert gameship.game_name(tmp_path, "Explicit") == "Explicit"
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "toml-name"\n')
    assert gameship.game_name(tmp_path, None) == "toml-name"
    (tmp_path / "pyproject.toml").write_text("not [valid toml")
    assert gameship.game_name(tmp_path, None) == tmp_path.resolve().name


def test_build_command_construction(tmp_path, monkeypatch):
    (tmp_path / "main.py").touch()
    (tmp_path / "assets").mkdir()
    seen = {}
    monkeypatch.setattr(gameship.subprocess, "run", lambda cmd, check: seen.setdefault("cmd", cmd))
    args = SimpleNamespace(path=str(tmp_path), entry=None, name="MyGame", dist=None, onefile=True,
                           collect=["mylib"])
    gameship.build(args)
    cmd = seen["cmd"]
    assert "--windowed" in cmd and "--onefile" in cmd
    assert cmd[cmd.index("--name") + 1] == "MyGame"
    assert any(str(tmp_path / "assets") in c for c in cmd)  # --add-data wired
    collected = [cmd[i + 1] for i, c in enumerate(cmd) if c == "--collect-all"]
    assert "mylib" in collected  # --collect flag propagates


def test_ci_writes_and_respects_force(tmp_path):
    gameship.ci(SimpleNamespace(path=str(tmp_path), force=False))
    wf = tmp_path / ".github" / "workflows" / "gameship.yml"
    text = wf.read_text()
    assert "windows-latest" in text and "macos-latest" in text and "ubuntu-latest" in text
    assert "BUTLER_API_KEY" in text
    with pytest.raises(SystemExit):
        gameship.ci(SimpleNamespace(path=str(tmp_path), force=False))
    gameship.ci(SimpleNamespace(path=str(tmp_path), force=True))  # no raise


def test_push_validates_target_and_build_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        gameship.push(SimpleNamespace(target="no-slash", path=None, channel=None, userversion=None))
    with pytest.raises(SystemExit):  # valid target, but no build dir
        gameship.push(SimpleNamespace(target="user/game", path=None, channel=None, userversion=None))


def test_cli_smoke():
    out = subprocess.run(
        [sys.executable, "-c", "import gameship; print(gameship.__version__)"],
        capture_output=True, text=True, check=True,
    )
    assert out.stdout.strip() == gameship.__version__


def test_web_command_construction(tmp_path, monkeypatch):
    (tmp_path / "main.py").touch()
    seen = {}
    monkeypatch.setattr(gameship.subprocess, "run", lambda cmd, check: seen.setdefault("cmd", cmd))
    gameship.web(SimpleNamespace(path=str(tmp_path), entry=None))
    assert "pygbag" in seen["cmd"] and "--build" in seen["cmd"]


def test_push_butler_failure_dies_with_hint(tmp_path, monkeypatch, capsys):
    (tmp_path / "dist").mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BUTLER_API_KEY", "x")
    monkeypatch.setattr(gameship, "butler_bin", lambda: "/bin/butler")
    def boom(cmd, check):
        raise subprocess.CalledProcessError(1, cmd)
    monkeypatch.setattr(gameship.subprocess, "run", boom)
    with pytest.raises(SystemExit):
        gameship.push(SimpleNamespace(target="user/game", path="dist", channel=None, userversion=None))
    assert "itch.io/game/new" in capsys.readouterr().err
