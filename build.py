"""
Cross-platform build script for the PySide6 app using PyInstaller.
- Prefers an existing spec file (BASIL.spec).
- Falls back to building from main.py with sensible defaults.
- Cross-platform versioning support and OS-specific tweaks:
  * Version: CLI/env/git fallback
  * Windows: version resource via --version-file, .ico icon
  * macOS: Info.plist update, .icns icon
  * Linux: output tagging, .png icon
  * UPX auto-detection across OS
  * Cross-platform add-data path separator handling

Usage:
- Windows (PowerShell):
  - py -3 build.py --version 1.2.3 --onefile --tag-output
- macOS (Terminal):
  - python3 build.py --version 1.2.3 --bundle-id com.basil.app --onefile --tag-output
- Linux (Terminal):
  - python3 build.py --version 1.2.3 --onefile --tag-output
"""

from __future__ import annotations

import argparse
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SPEC_FILE = ROOT / "BASIL.spec"
ENTRY = ROOT / "main.py"
DIST = ROOT / "dist"
BUILD = ROOT / "build"
DEFAULT_NAME = "BASIL"

IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")
DATA_SEP = ";" if IS_WIN else ":"

DEFAULT_UPX_DIR = str(Path.home() / "Desktop" / "upx") if IS_WIN else ""
DEFAULT_ICON_WIN = ROOT / "assets" / "icons" / "icon.ico"
DEFAULT_ICON_MAC = ROOT / "assets" / "icons" / "icon.icns"
DEFAULT_ICON_LINUX = ROOT / "assets" / "icons" / "icon.png"
UPX_EXCLUDES = ["vcruntime140.dll", "ucrtbase.dll", "libegl.dll", "c10.dll"]


def _determine_version(cli_version: str | None) -> str:
    if cli_version:
        return cli_version
    env_ver = os.getenv("BUILD_VERSION") or os.getenv("VERSION")
    if env_ver:
        return env_ver
    try:
        out = subprocess.check_output(
            ["git", "describe", "--tags", "--dirty", "--always"],
            cwd=ROOT,
            text=True,
        ).strip()
        return out[1:] if out.startswith("v") else out
    except Exception:
        return "0.0.0"


def _parse_four_tuple(version: str) -> tuple[int, int, int, int]:
    nums, part = [], ""
    for ch in version:
        if ch.isdigit():
            part += ch
        elif part:
            nums.append(int(part))
            part = ""
    if part:
        nums.append(int(part))
    nums = (nums + [0, 0, 0, 0])[:4]
    return tuple(nums)


def _write_win_version_file(version: str, product_name: str) -> Path:
    BUILD.mkdir(parents=True, exist_ok=True)
    vf = BUILD / "version_win.txt"
    major, minor, patch, build = _parse_four_tuple(version)
    contents = f"""
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({major}, {minor}, {patch}, {build}),
    prodvers=({major}, {minor}, {patch}, {build}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '040904E4',
        [StringStruct('CompanyName', 'MML-UNC'),
         StringStruct('FileDescription', '{product_name}'),
         StringStruct('FileVersion', '{version}'),
         StringStruct('InternalName', '{product_name}'),
         StringStruct('LegalCopyright', ''),
         StringStruct('OriginalFilename', '{product_name}.exe'),
         StringStruct('ProductName', '{product_name}'),
         StringStruct('ProductVersion', '{version}')])
      ]),
    VarFileInfo([VarStruct('Translation', [1033, 1252])])
  ]
)
""".lstrip()
    vf.write_text(contents, encoding="utf-8")
    return vf


def _update_macos_plist(app_name: str, version: str, bundle_id: str | None):
    app_plist = DIST / f"{app_name}.app" / "Contents" / "Info.plist"
    if not app_plist.exists():
        return
    with app_plist.open("rb") as f:
        info = plistlib.load(f)
    info["CFBundleShortVersionString"] = version
    info["CFBundleVersion"] = version
    if bundle_id:
        info["CFBundleIdentifier"] = bundle_id
    with app_plist.open("wb") as f:
        plistlib.dump(info, f)


def _tag_output_files(app_name: str, version: str, onefile: bool):
    exe = DIST / f"{app_name}.exe"
    if exe.exists():
        exe.rename(DIST / f"{app_name}-v{version}.exe")
        return
    app = DIST / f"{app_name}.app"
    if app.exists():
        app.rename(DIST / f"{app_name}-v{version}.app")
        return
    # Linux: onefile binary or onedir folder
    linux_bin = DIST / app_name
    if linux_bin.exists() and onefile:
        linux_bin.rename(DIST / f"{app_name}-v{version}")
        return
    linux_dir = DIST / app_name
    if linux_dir.exists():
        linux_dir.rename(DIST / f"{app_name}-v{version}")


def _write_version_data(version: str) -> Path:
    BUILD.mkdir(parents=True, exist_ok=True)
    vf = BUILD / "VERSION"
    vf.write_text(version, encoding="utf-8")
    return vf


def _resolve_upx_dir(cli_upx: str | None) -> str | None:
    if cli_upx and Path(cli_upx).exists():
        return cli_upx
    which = shutil.which("upx")
    if which:
        return str(Path(which).parent)
    if DEFAULT_UPX_DIR and Path(DEFAULT_UPX_DIR).exists():
        return DEFAULT_UPX_DIR
    return None


def _resolve_icon(cli_icon: str | None) -> Path | None:
    if cli_icon and Path(cli_icon).exists():
        return Path(cli_icon)
    if IS_WIN and DEFAULT_ICON_WIN.exists():
        return DEFAULT_ICON_WIN
    if IS_MAC and DEFAULT_ICON_MAC.exists():
        return DEFAULT_ICON_MAC
    if IS_LINUX and DEFAULT_ICON_LINUX.exists():
        return DEFAULT_ICON_LINUX
    return None


def run(cmd: list[str]) -> int:
    print("\n> ", " ".join(cmd))
    return subprocess.call(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PySide6 app with PyInstaller")
    parser.add_argument("--clean", action="store_true", help="Clean previous builds and cache")
    parser.add_argument("--onefile", action="store_true", help="Build as a single-file executable")
    parser.add_argument("--name", default=DEFAULT_NAME, help="Application name")
    parser.add_argument("--upx-dir", default=DEFAULT_UPX_DIR, help="UPX directory (optional)")
    parser.add_argument("--icon", help="Path to app icon (.ico on Windows, .icns on macOS, .png on Linux)")
    parser.add_argument("--version", help="Version string (falls back to env/git/0.0.0)")
    parser.add_argument("--tag-output", action="store_true", help="Append version to output filename")
    parser.add_argument("--bundle-id", help="macOS bundle identifier (e.g., com.BASIL.app)")
    args = parser.parse_args()

    version = _determine_version(args.version)
    print(f"Build version: {version}")

    if args.clean:
        for p in (DIST, BUILD, ROOT / "__pycache__"):
            if p.exists():
                print(f"Removing {p}")
                shutil.rmtree(p, ignore_errors=True)
        pycache = ROOT / ".pyinstaller"
        if pycache.exists():
            print(f"Removing {pycache}")
            shutil.rmtree(pycache, ignore_errors=True)

    pyinstaller_cmd = [sys.executable, "-m", "PyInstaller"]

    upx_dir = _resolve_upx_dir(args.upx_dir)
    icon_path = _resolve_icon(args.icon)
    version_data = _write_version_data(version)

    if SPEC_FILE.exists():
        print("Note: BASIL.spec detected; configure versioning/icon in the spec for embedded metadata.")
        cmd = pyinstaller_cmd + [str(SPEC_FILE)]
        rc = run(cmd)
    else:
        # Fallback sensible defaults for a windowed PySide6 app
        if not ENTRY.exists():
            print("Error: main.py not found and no main.spec present.")
            return 1
        cmd = pyinstaller_cmd + [
            "--name",
            args.name,
            "--noconfirm",
            "--clean",
            "--windowed",
            "--onedir",
        ]

        if upx_dir:
            cmd += ["--upx-dir", upx_dir]

        for exclude in UPX_EXCLUDES:
            cmd += ["--upx-exclude", exclude]
        if icon_path:
            cmd += ["--icon", str(icon_path)]

        cmd += [
            "--exclude-module",
            "tkinter",
            "--exclude-module",
            "pytest",
        ]

        if args.onefile:
            cmd.append("--onefile")

        if IS_WIN:
            vf = _write_win_version_file(version, args.name)
            cmd += ["--version-file", str(vf)]

        # Ship VERSION file for all platforms
        cmd += [
            "--add-data",
            f"{version_data}{DATA_SEP}.",
            "--add-data",
            f"assets{DATA_SEP}assets",
        ]

        cmd.append(str(ENTRY))
        rc = run(cmd)

    if rc == 0:
        if IS_MAC:
            _update_macos_plist(args.name, version, args.bundle_id)
        if args.tag_output:
            _tag_output_files(args.name, version, args.onefile)

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
