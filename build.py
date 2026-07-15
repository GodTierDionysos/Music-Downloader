#!/usr/bin/env python3
"""
build.py — MusicDownloader .exe Derleme Scripti
PyInstaller ile tek dosya .exe üretir.

Kullanım:
    python build.py
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

# ── Renkli çıktı ───────────────────────────────────────────────
def info(msg):  print(f"  {msg}")
def ok(msg):    print(f"  [OK]  {msg}")
def fail(msg):  print(f"  [X]  {msg}"); sys.exit(1)

# ── Paket yolu ─────────────────────────────────────────────────
def pkg_path(name: str) -> str:
    import importlib
    try:
        m = importlib.import_module(name)
        return os.path.dirname(m.__file__)
    except ImportError:
        fail(f"'{name}' paketi bulunamadı. Önce: pip install {name}")

def main():
    print()
    print("=" * 52)
    print("   MusicDownloader  —  .exe Derleme")
    print("=" * 52)
    print()

    # ── Bağımlılık kontrolü ────────────────────────────────────
    info("Bağımlılıklar kontrol ediliyor...")
    for pkg in ("webview", "yt_dlp", "PIL"):
        try:
            __import__(pkg)
            ok(pkg)
        except ImportError:
            fail(f"'{pkg}' kurulu değil. Önce: pip install -r requirements.txt")

    # ── Yollar ────────────────────────────────────────────────
    sep = ";" if sys.platform == "win32" else ":"
    webui_dir = str(Path("webui").resolve())
    assets_dir = Path("assets").resolve()
    icon_file = assets_dir / "app.ico"

    if not icon_file.exists():
        fail("assets\\app.ico bulunamadı. Önce ikon dosyasını oluşturun.")

    # ── Önceki derlemeyi temizle ───────────────────────────────
    for d in ("build", "dist", "__pycache__"):
        if Path(d).exists():
            shutil.rmtree(d)
    for f in Path(".").glob("*.spec"):
        f.unlink()

    print()
    info("Derleniyor — bu birkaç dakika sürebilir...")
    print()

    # ── PyInstaller komutu ─────────────────────────────────────
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onefile",
        "--name", "MusicDownloader",
        f"--icon={icon_file}",

        f"--add-data={webui_dir}{sep}webui",
        f"--add-data={assets_dir}{sep}assets",
        "--collect-all", "yt_dlp",
        "--collect-all", "webview",

        "--hidden-import", "downloader",
        "--hidden-import", "bridge",
        "--hidden-import", "webview",
        "--hidden-import", "PIL._tkinter_finder",

        "--log-level", "WARN",

        "main.py",
    ]

    result = subprocess.run(cmd, capture_output=False)

    print()
    if result.returncode != 0:
        fail("Derleme başarısız! Yukarıdaki hata mesajlarını inceleyin.")

    exe_path = Path("dist") / "MusicDownloader.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / 1_048_576
        print("=" * 52)
        ok(f"Derleme tamamlandı!")
        ok(f"Konum : dist\\MusicDownloader.exe")
        ok(f"Boyut  : {size_mb:.1f} MB")
        print("=" * 52)
        print()

        # dist klasörünü aç
        os.startfile(str(Path("dist").resolve()))
    else:
        fail("dist\\MusicDownloader.exe oluşturulamadı.")


if __name__ == "__main__":
    main()
