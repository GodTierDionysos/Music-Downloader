"""
bridge.py — pywebview JS API
UI (HTML/CSS/JS) ile downloader.py arasında köprü.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

import webview

from downloader import fetch_playlist_info, download_videos


def _data_dir() -> Path:
    """
    Ayar/geçmiş klasörü — hem run.bat (python) hem .exe aynı yeri kullanır.
    %APPDATA%\\MusicDownloader
    """
    base = Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))
    d = base / "MusicDownloader"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _settings_path() -> Path:
    return _data_dir() / "settings.json"


def _history_path() -> Path:
    return _data_dir() / "history.json"


def _migrate_legacy_data() -> None:
    """Eski proje / dist yanındaki settings.json'ı AppData'ya bir kez taşı."""
    dest_s = _settings_path()
    if dest_s.exists():
        return

    candidates: list[Path] = []
    here = Path(__file__).resolve().parent
    candidates.append(here)
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir)
        candidates.append(exe_dir.parent)  # dist/ -> proje kökü

    for folder in candidates:
        src = folder / "settings.json"
        if not src.exists():
            continue
        try:
            shutil.copy2(src, dest_s)
            src_h = folder / "history.json"
            dest_h = _history_path()
            if src_h.exists() and not dest_h.exists():
                shutil.copy2(src_h, dest_h)
        except Exception:
            pass
        break


_migrate_legacy_data()

THEME_KEYS = {
    "aurora": "Aurora Glow",
    "neon": "Neon Pulse",
    "sunset": "Sunset Drift",
    "midnight": "Midnight Bloom",
    "ocean": "Ocean Wave",
    "ember": "Ember Rush",
    "lavender": "Lavender Dream",
    "sunrise": "Sunrise Glow",
    "violet": "Violet Pulse",
    "crimson": "Crimson Noir",
    "blood": "Blood Black",
    "graphite": "Graphite",
    "arctic": "Arctic Ice",
    "jade": "Jade Grove",
    "copper": "Copper Forge",
    "ink": "Mono Ink",
    "void": "Void Carbon",
    "ashblood": "Ash Blood",
}
THEME_REVERSE = {v: k for k, v in THEME_KEYS.items()}


class Api:
    def __init__(self):
        self._window = None
        self._cancel = threading.Event()
        self._dl_thread = None
        self._items_cache: list = []
        self._resume_payload: dict | None = None
        self._pending_ui: dict | None = None
        self._ui_lock = threading.Lock()

    def attach(self, window):
        self._window = window

    def _eval(self, script: str):
        if not self._window:
            return
        try:
            self._window.evaluate_js(script)
        except Exception:
            pass

    # ── State ──────────────────────────────────────────────────
    def get_state(self) -> dict:
        settings = self._load_settings()
        theme_key = self._resolve_theme_key(settings)
        return {
            "theme": theme_key,
            "folder": settings.get("folder") or os.path.expanduser("~/Music"),
            "format": settings.get("format", "MP3"),
            "quality": settings.get("quality", "En İyi"),
            "ffmpeg_ok": self._check_ffmpeg(),
        }

    def set_theme(self, key: str) -> bool:
        key = (key or "").strip()
        if key not in THEME_KEYS:
            key = "aurora"
        data = self._load_settings()
        data["theme"] = THEME_KEYS[key]
        data["theme_key"] = key
        self._save_settings(data)
        return True

    @staticmethod
    def _resolve_theme_key(settings: dict) -> str:
        raw_key = settings.get("theme_key")
        if isinstance(raw_key, str) and raw_key in THEME_KEYS:
            return raw_key
        raw = settings.get("theme", "Aurora Glow")
        if isinstance(raw, str) and raw in THEME_KEYS:
            return raw
        return THEME_REVERSE.get(raw, "aurora")

    def pick_folder(self, current: str = "") -> str | None:
        initial = current or os.path.expanduser("~/Music")
        result = self._window.create_file_dialog(
            webview.FOLDER_DIALOG,
            directory=initial if Path(initial).exists() else os.path.expanduser("~"),
        )
        if result and len(result) > 0:
            path = result[0]
            data = self._load_settings()
            data["folder"] = path
            self._save_settings(data)
            return path
        return None

    def get_clipboard(self) -> str:
        """Panodaki metni oku (YouTube linki teklifi için)."""
        text = self._clipboard_win32()
        if text:
            return text
        text = self._clipboard_powershell()
        if text:
            return text
        return ""

    @staticmethod
    def _clipboard_win32() -> str:
        if sys.platform != "win32":
            return ""
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            user32.OpenClipboard.argtypes = [wintypes.HWND]
            user32.OpenClipboard.restype = wintypes.BOOL
            user32.CloseClipboard.argtypes = []
            user32.CloseClipboard.restype = wintypes.BOOL
            user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
            user32.IsClipboardFormatAvailable.restype = wintypes.BOOL
            user32.GetClipboardData.argtypes = [wintypes.UINT]
            user32.GetClipboardData.restype = wintypes.HANDLE
            kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
            kernel32.GlobalLock.restype = ctypes.c_void_p
            kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
            kernel32.GlobalUnlock.restype = wintypes.BOOL

            CF_UNICODETEXT = 13
            if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
                return ""
            if not user32.OpenClipboard(None):
                return ""
            try:
                handle = user32.GetClipboardData(CF_UNICODETEXT)
                if not handle:
                    return ""
                ptr = kernel32.GlobalLock(handle)
                if not ptr:
                    return ""
                try:
                    return (ctypes.wstring_at(ptr) or "").strip()
                finally:
                    kernel32.GlobalUnlock(handle)
            finally:
                user32.CloseClipboard()
        except Exception:
            return ""

    @staticmethod
    def _clipboard_powershell() -> str:
        if sys.platform != "win32":
            return ""
        try:
            flags = 0
            if hasattr(subprocess, "CREATE_NO_WINDOW"):
                flags = subprocess.CREATE_NO_WINDOW
            r = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    "Get-Clipboard -Raw",
                ],
                capture_output=True,
                text=True,
                timeout=3,
                creationflags=flags,
            )
            if r.returncode == 0 and r.stdout:
                return r.stdout.strip()
        except Exception:
            pass
        return ""

    # ── Playlist ───────────────────────────────────────────────
    def fetch_playlist(self, url: str) -> dict:
        try:
            items = fetch_playlist_info(url.strip())
            self._items_cache = items
            return {"ok": True, "items": items}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # ── Download ───────────────────────────────────────────────
    def start_download(self, payload: dict) -> bool:
        if self._dl_thread and self._dl_thread.is_alive():
            return False

        items = payload.get("items") or []
        if not items:
            return False

        folder = payload.get("folder") or os.path.expanduser("~/Music")
        fmt = payload.get("format") or "MP3"
        quality = payload.get("quality") or "En İyi"
        indices = payload.get("indices") or list(range(len(items)))

        data = self._load_settings()
        data["folder"] = folder
        data["format"] = fmt
        data["quality"] = quality
        self._save_settings(data)

        # Yeni tam indirme başlarken önceki devam kaydını temizle
        if not payload.get("is_resume"):
            self._resume_payload = None

        self._cancel.clear()
        total = len(items)
        completed = [0]
        succeeded: set[int] = set()
        index_map = list(indices)

        def on_start(idx, title):
            ui_idx = index_map[idx] if idx < len(index_map) else idx
            safe = json.dumps(title[:80])
            self._eval(f"window.md && window.md.onItemStart({ui_idx}, {safe})")

        def on_progress(idx, pct, speed):
            overall = (completed[0] + pct) / max(total, 1)
            safe_spd = json.dumps(speed or "")
            self._eval(
                f"window.md && window.md.onItemProgress({overall}, {safe_spd})"
            )

        def on_done(idx, success, error_msg=""):
            completed[0] += 1
            if success:
                succeeded.add(idx)
            ui_idx = index_map[idx] if idx < len(index_map) else idx
            err = json.dumps((error_msg or "")[:120])
            self._eval(
                f"window.md && window.md.onItemDone({ui_idx}, {str(success).lower()}, {err})"
            )

        def worker():
            download_videos(
                items=items,
                output_dir=folder,
                fmt=fmt,
                quality=quality,
                on_item_start=on_start,
                on_item_progress=on_progress,
                on_item_done=on_done,
                cancel_event=self._cancel,
            )
            done = len(succeeded)
            finished = completed[0]
            cancelled = self._cancel.is_set()
            if cancelled:
                status = "cancelled"
                remaining_pos = [i for i in range(len(items)) if i not in succeeded]
                if remaining_pos:
                    self._resume_payload = {
                        "items": [items[i] for i in remaining_pos],
                        "indices": [index_map[i] for i in remaining_pos],
                        "folder": folder,
                        "format": fmt,
                        "quality": quality,
                        "is_resume": True,
                    }
                else:
                    self._resume_payload = None
            elif total > 0 and done == total:
                status = "success"
                self._resume_payload = None
            else:
                status = "partial"
                self._resume_payload = None

            try:
                self._save_history(done, total, fmt, folder, status)
            except Exception:
                pass

            event = {
                "type": "download_done",
                "done": done,
                "finished": finished,
                "total": total,
                "status": status,
                "path": folder,
                "can_resume": bool(self._resume_payload),
                "ask_folder": False,
            }

            # İptalde ASLA sor/açma. Doğal bitişte uygulama içi modal sorulacak.
            should_ask_folder = (
                not cancelled
                and done > 0
                and finished == total
                and total > 0
            )
            event["ask_folder"] = should_ask_folder

            with self._ui_lock:
                self._pending_ui = event

            # Uygulama içi modal + durum güncellemesi
            try:
                self._show_download_done_ui(event)
            except Exception:
                pass

        self._dl_thread = threading.Thread(target=worker, daemon=True)
        self._dl_thread.start()
        return True

    def resume_download(self) -> bool:
        """Durdurulan indirmeyi kalan öğelerle sürdürme."""
        if self._dl_thread and self._dl_thread.is_alive():
            return False
        payload = self._resume_payload
        if not payload:
            return False
        self._resume_payload = None
        return self.start_download(payload)

    def cancel_download(self) -> bool:
        self._cancel.set()
        return True

    def has_resume(self) -> bool:
        return bool(self._resume_payload)

    def poll_ui_event(self) -> dict | None:
        """JS periyodik olarak çağırır; indirme bitiş olayını kaçırmamak için."""
        with self._ui_lock:
            ev = self._pending_ui
            self._pending_ui = None
            return ev

    def _show_download_done_ui(self, event: dict) -> None:
        """İndirme bitişini ve (gerekirse) uygulama içi klasör modalını göster."""
        payload = json.dumps(event, ensure_ascii=False)
        path_js = json.dumps(event.get("path") or "", ensure_ascii=False)
        ask = bool(event.get("ask_folder"))

        self._eval(f"window.md && window.md.onDownloadDone({payload})")

        if ask:
            self._eval(
                f"""
(function(){{
  var path = {path_js};
  var modal = document.getElementById('folderModal');
  var preview = document.getElementById('folderPreview');
  if (preview) preview.textContent = path;
  if (modal) {{
    modal.classList.remove('hidden');
    modal.style.display = 'grid';
    modal.style.zIndex = '99999';
  }} else if (window.md && window.md.askOpenFolder) {{
    window.md.askOpenFolder(path);
  }}
}})();
"""
            )

    # ── History ────────────────────────────────────────────────
    def get_history(self) -> list:
        return self._load_history()

    def clear_history(self) -> bool:
        try:
            _history_path().unlink(missing_ok=True)
        except Exception:
            pass
        return True

    def open_folder(self, path: str = "") -> bool:
        """İndirme klasörünü dosya gezgininde aç."""
        return self._reveal_folder(path or self._load_settings().get("folder") or "")

    # ── Helpers ────────────────────────────────────────────────
    @staticmethod
    def _reveal_folder(path: str) -> bool:
        try:
            target = Path(path).expanduser()
            if not target.exists():
                target.mkdir(parents=True, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(str(target))  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.run(["open", str(target)], check=False)
            else:
                subprocess.run(["xdg-open", str(target)], check=False)
            return True
        except Exception:
            return False

    @staticmethod
    def _check_ffmpeg() -> bool:
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            return True
        except Exception:
            return False

    @staticmethod
    def _load_settings() -> dict:
        path = _settings_path()
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    return json.load(fh)
            except Exception:
                return {}
        return {}

    @staticmethod
    def _save_settings(data: dict) -> None:
        try:
            with open(_settings_path(), "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @staticmethod
    def _load_history() -> list:
        path = _history_path()
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    return json.load(fh)
            except Exception:
                return []
        return []

    def _save_history(self, done, total, fmt, path, status):
        records = self._load_history()
        records.insert(
            0,
            {
                "date": datetime.now().strftime("%Y-%m-%d  %H:%M"),
                "count": done,
                "total": total,
                "fmt": fmt,
                "path": path,
                "status": status,
            },
        )
        try:
            with open(_history_path(), "w", encoding="utf-8") as fh:
                json.dump(records[:100], fh, ensure_ascii=False, indent=2)
        except Exception:
            pass
