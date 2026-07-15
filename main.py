#!/usr/bin/env python3
"""
Music Downloader — PulseTube tarzı cam UI (HTML/CSS/JS + pywebview)
İndirme motoru: downloader.py (değişmedi)
Eski CustomTkinter arayüz: legacy_ctk_main.py
"""

import sys
from pathlib import Path

import webview

from bridge import Api

# Sizer tarzı: ekranda görünen dış çerçeve boyutu (fiziksel piksel)
WINDOW_WIDTH = 1800
WINDOW_HEIGHT = 950


def _enable_dpi_awareness():
    if sys.platform != "win32":
        return
    import ctypes
    from ctypes import c_void_p

    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(c_void_p(-4))
        return
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass


def _base_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def _webui_index() -> Path:
    return _base_dir() / "webui" / "index.html"


def _app_icon() -> str | None:
    """Pencere / görev çubuğu ikonu (.ico)."""
    icon = _base_dir() / "assets" / "app.ico"
    return str(icon) if icon.exists() else None


def _work_area():
    """Görev çubuğu hariç çalışma alanı (fiziksel px)."""
    import ctypes
    from ctypes import wintypes

    rect = wintypes.RECT()
    ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0)
    return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top


def _logical_for_create(physical_w: int, physical_h: int):
    """pywebview create_window için logical boyut (sonra Sizer ile fiziksel sabitleyeceğiz)."""
    if sys.platform != "win32":
        return physical_w, physical_h
    import ctypes

    try:
        dpi = ctypes.windll.user32.GetDpiForSystem()
    except Exception:
        dpi = 96
    scale = max(dpi / 96.0, 0.5)
    return max(400, int(round(physical_w / scale))), max(300, int(round(physical_h / scale)))


def _sizer_place(window, width: int = WINDOW_WIDTH, height: int = WINDOW_HEIGHT):
    """
    Sizer 4.0 gibi: görünür boyut width×height, work area ortasında.
    Win11 gizli resize border için DWM extended bounds kullanılır.
    """
    if sys.platform != "win32":
        return

    import ctypes
    from ctypes import wintypes

    try:
        native = getattr(window, "native", None)
        if native is None:
            return
        hwnd = int(native.Handle.ToInt32())
        left, top, work_w, work_h = _work_area()

        # Önce kabaca yerleştir
        x = left + max(0, (work_w - width) // 2)
        y = top + max(0, (work_h - height) // 2)
        ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, width, height, 0x0044)

        window_rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(window_rect))
        ext = wintypes.RECT()
        DWMWA_EXTENDED_FRAME_BOUNDS = 9
        ctypes.windll.dwmapi.DwmGetWindowAttribute(
            hwnd,
            DWMWA_EXTENDED_FRAME_BOUNDS,
            ctypes.byref(ext),
            ctypes.sizeof(ext),
        )

        pad_l = ext.left - window_rect.left
        pad_t = ext.top - window_rect.top
        pad_r = window_rect.right - ext.right
        pad_b = window_rect.bottom - ext.bottom

        outer_w = width + max(0, pad_l + pad_r)
        outer_h = height + max(0, pad_t + pad_b)

        # Görünür (extended) alan work area ortasında olsun
        vis_x = left + max(0, (work_w - width) // 2)
        vis_y = top + max(0, (work_h - height) // 2)
        outer_x = vis_x - max(0, pad_l)
        outer_y = vis_y - max(0, pad_t)

        ctypes.windll.user32.SetWindowPos(
            hwnd, 0, outer_x, outer_y, outer_w, outer_h, 0x0044
        )
    except Exception:
        pass


def main():
    _enable_dpi_awareness()

    ui = _webui_index()
    if not ui.exists():
        raise SystemExit(f"UI bulunamadı: {ui}")

    width, height = _logical_for_create(WINDOW_WIDTH, WINDOW_HEIGHT)
    api = Api()
    window = webview.create_window(
        title="Music Downloader",
        url=ui.as_uri(),
        js_api=api,
        width=width,
        height=height,
        resizable=True,
        fullscreen=False,
        maximized=False,
        min_size=(900, 600),
        background_color="#06070f",
    )
    api.attach(window)

    def place():
        _sizer_place(window)

    try:
        window.events.shown += place
        # WinForms DPI/autosize sonrası tekrar sabitle (Sizer gibi net boyut)
        window.events.loaded += place
    except Exception:
        pass

    icon = _app_icon()
    webview.start(debug=False, icon=icon)


if __name__ == "__main__":
    main()
