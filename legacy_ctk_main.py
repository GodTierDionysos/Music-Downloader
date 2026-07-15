#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║   Music Downloader  —  YouTube Playlist      ║
║   Modern Dark UI  •  v1.0                    ║
╚══════════════════════════════════════════════╝
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os
import threading
import subprocess
import json
import urllib.request
import io
from pathlib import Path
from datetime import datetime
import math
from downloader import fetch_playlist_info, download_videos

try:
    from PIL import Image as PilImage, ImageDraw, ImageFilter, ImageTk as PilImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

HISTORY_FILE  = Path(__file__).parent / "history.json"
SETTINGS_FILE = Path(__file__).parent / "settings.json"


def _hex_to_rgb(h: str) -> tuple:
    """'#rrggbb' → (r, g, b) int tuple."""
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(rgb: tuple) -> str:
    """(r, g, b) → '#rrggbb'."""
    r, g, b = (max(0, min(255, int(c))) for c in rgb)
    return f"#{r:02x}{g:02x}{b:02x}"


def _lerp_rgb(c1: tuple, c2: tuple, t: float) -> tuple:
    """İki RGB renk arasında lineer geçiş."""
    t = max(0.0, min(1.0, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def refresh_glass_tokens() -> None:
    """PulseTube tarzı cam yüzey renklerini aktif temadan üretip C'ye yazar."""
    bg = _hex_to_rgb(C["bg"])
    card = _hex_to_rgb(C.get("card", C["bg"]))
    accent = _hex_to_rgb(C["accent"])
    white = (255, 255, 255)
    # rgba(255,255,255,0.06–0.12) benzeri — koyu üzeri hafif açık cam
    C["glass"] = _rgb_to_hex(_lerp_rgb(bg, white, 0.09))
    C["glass2"] = _rgb_to_hex(_lerp_rgb(bg, white, 0.14))
    C["glass_border"] = _rgb_to_hex(_lerp_rgb(bg, white, 0.22))
    C["glass_inner"] = _rgb_to_hex(_lerp_rgb(card, white, 0.08))
    C["glass_hero"] = _rgb_to_hex(
        _lerp_rgb(_lerp_rgb(bg, white, 0.07), accent, 0.14)
    )

# ═══════════════════════════════════════════════════════════════
#  TEMA & RENK PALETİ
# ═══════════════════════════════════════════════════════════════
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── Renkler ─────────────────────────────────────────────────────
C = {
    # Arka planlar
    "bg":            "#09090F",    # Ana arka plan (en koyu)
    "bg2":           "#0F0F1C",    # İkincil arka plan (panel)
    "card":          "#15152A",    # Kart / liste kutusu
    "card2":         "#1D1D38",    # Hover / çift satır vurgu
    "input":         "#0A0A1A",    # Input alanı

    # Kenarlıklar
    "border":        "#252542",    # Normal kenarlık
    "border2":       "#3A3A60",    # Aktif kenarlık

    # Vurgu renkleri
    "accent":        "#E94560",    # Ana vurgu — kırmızı/pembe
    "accent_dark":   "#B5293F",    # Koyu vurgu (pressed)
    "accent_hover":  "#FF5C78",    # Hover vurgu
    "blue":          "#4A90E2",    # İkincil mavi
    "blue_hover":    "#5AA3F5",    # Mavi hover

    # Metin
    "text":          "#F0F0F6",    # Ana metin (beyaz)
    "text2":         "#7878A0",    # İkincil metin (gri-mor)
    "text3":         "#40405A",    # Soluk/pasif metin
    "text_inv":      "#FFFFFF",    # Tersine metin (buton içi)

    # Durum renkleri
    "success":       "#00D2B4",    # Başarı (yeşil-turkuaz)
    "warning":       "#FFB347",    # Uyarı (turuncu)
    "error":         "#FF6B6B",    # Hata (kırmızı)
}

# ── Temalar ───────────────────────────────────────────────────────
THEMES: dict[str, dict] = {
    "Aurora Glow": {
        "bg": "#06070f", "bg2": "#11152a", "card": "#221839", "card2": "#13244c",
        "input": "#05060c", "border": "#2a2f55", "border2": "#4040a0",
        "accent": "#e96100", "accent_dark": "#b54c00", "accent_hover": "#ff7820",
        "blue": "#2455f5", "blue_hover": "#4a6fff",
        "text": "#f9f7ff", "text2": "#b8c0de", "text3": "#5a6080", "text_inv": "#ffffff",
        "success": "#00D2B4", "warning": "#FFB347", "error": "#FF6B6B",
        "_swatches": ["#e96100", "#ffb84d", "#2455f5", "#6b2edb", "#221839", "#06070f"],
    },
    "Neon Pulse": {
        "bg": "#050610", "bg2": "#121833", "card": "#17153c", "card2": "#0f2e45",
        "input": "#040510", "border": "#25275a", "border2": "#4a4daf",
        "accent": "#ff2f92", "accent_dark": "#cc1f72", "accent_hover": "#ff5aaa",
        "blue": "#00d4ff", "blue_hover": "#33ddff",
        "text": "#f9f7ff", "text2": "#b8c0de", "text3": "#5a6080", "text_inv": "#ffffff",
        "success": "#14f7c4", "warning": "#FFB347", "error": "#FF6B6B",
        "_swatches": ["#ff2f92", "#00d4ff", "#7a4dff", "#14f7c4", "#17153c", "#050610"],
    },
    "Sunset Drift": {
        "bg": "#120709", "bg2": "#2b1114", "card": "#431f20", "card2": "#5f2433",
        "input": "#0f0507", "border": "#5a2a2a", "border2": "#8a4040",
        "accent": "#ff5d3b", "accent_dark": "#cc3a1f", "accent_hover": "#ff7a5a",
        "blue": "#ff2e6d", "blue_hover": "#ff558a",
        "text": "#f9f7ff", "text2": "#b8c0de", "text3": "#7a6060", "text_inv": "#ffffff",
        "success": "#00D2B4", "warning": "#ffb347", "error": "#FF6B6B",
        "_swatches": ["#ff5d3b", "#ffb347", "#ff2e6d", "#8a2be2", "#431f20", "#120709"],
    },
    "Midnight Bloom": {
        "bg": "#04050d", "bg2": "#0f142b", "card": "#161c3d", "card2": "#172a57",
        "input": "#03040a", "border": "#252d60", "border2": "#4040a0",
        "accent": "#4f46e5", "accent_dark": "#3730b3", "accent_hover": "#6c63ff",
        "blue": "#06b6d4", "blue_hover": "#22d3ee",
        "text": "#f9f7ff", "text2": "#b8c0de", "text3": "#5a6080", "text_inv": "#ffffff",
        "success": "#00D2B4", "warning": "#FFB347", "error": "#FF6B6B",
        "_swatches": ["#4f46e5", "#7c3aed", "#06b6d4", "#ec4899", "#161c3d", "#04050d"],
    },
    "Ocean Wave": {
        "bg": "#03131d", "bg2": "#0a2740", "card": "#103952", "card2": "#164e63",
        "input": "#021018", "border": "#1a4060", "border2": "#2a6090",
        "accent": "#0ea5e9", "accent_dark": "#0284c7", "accent_hover": "#38bdf8",
        "blue": "#2563eb", "blue_hover": "#3b82f6",
        "text": "#f9f7ff", "text2": "#b8c0de", "text3": "#5a7080", "text_inv": "#ffffff",
        "success": "#14b8a6", "warning": "#FFB347", "error": "#FF6B6B",
        "_swatches": ["#0ea5e9", "#22d3ee", "#2563eb", "#14b8a6", "#103952", "#03131d"],
    },
    "Ember Rush": {
        "bg": "#140606", "bg2": "#2a0d0d", "card": "#401716", "card2": "#5b1f1c",
        "input": "#0f0404", "border": "#601a18", "border2": "#902828",
        "accent": "#f97316", "accent_dark": "#c55a0d", "accent_hover": "#fb923c",
        "blue": "#ef4444", "blue_hover": "#f87171",
        "text": "#f9f7ff", "text2": "#b8c0de", "text3": "#7a5a5a", "text_inv": "#ffffff",
        "success": "#00D2B4", "warning": "#FFB347", "error": "#FF6B6B",
        "_swatches": ["#f97316", "#fb923c", "#ef4444", "#b91c1c", "#401716", "#140606"],
    },
    "Lavender Dream": {
        "bg": "#0c0716", "bg2": "#22143a", "card": "#322055", "card2": "#51316a",
        "input": "#090511", "border": "#3a2560", "border2": "#6040a0",
        "accent": "#8b5cf6", "accent_dark": "#7c3aed", "accent_hover": "#a78bfa",
        "blue": "#ec4899", "blue_hover": "#f472b6",
        "text": "#f9f7ff", "text2": "#b8c0de", "text3": "#7060a0", "text_inv": "#ffffff",
        "success": "#00D2B4", "warning": "#FFB347", "error": "#FF6B6B",
        "_swatches": ["#8b5cf6", "#c084fc", "#ec4899", "#38bdf8", "#322055", "#0c0716"],
    },
    "Sunrise Glow": {
        "bg": "#140b06", "bg2": "#2b130d", "card": "#431a11", "card2": "#612417",
        "input": "#0f0804", "border": "#5a2010", "border2": "#903020",
        "accent": "#ff7a00", "accent_dark": "#cc6000", "accent_hover": "#ff9a33",
        "blue": "#ff4d6d", "blue_hover": "#ff7a8a",
        "text": "#f9f7ff", "text2": "#b8c0de", "text3": "#7a6050", "text_inv": "#ffffff",
        "success": "#00D2B4", "warning": "#ffd166", "error": "#FF6B6B",
        "_swatches": ["#ff7a00", "#ffd166", "#ff4d6d", "#7c4dff", "#431a11", "#140b06"],
    },
    "Violet Pulse": {
        "bg": "#090611", "bg2": "#17112b", "card": "#23153d", "card2": "#2d1850",
        "input": "#07040e", "border": "#301a5a", "border2": "#5040a0",
        "accent": "#7c3aed", "accent_dark": "#6020c0", "accent_hover": "#a78bfa",
        "blue": "#ec4899", "blue_hover": "#f472b6",
        "text": "#f9f7ff", "text2": "#b8c0de", "text3": "#6050a0", "text_inv": "#ffffff",
        "success": "#06b6d4", "warning": "#FFB347", "error": "#FF6B6B",
        "_swatches": ["#7c3aed", "#a78bfa", "#ec4899", "#06b6d4", "#23153d", "#090611"],
    },
}
DEFAULT_THEME = "Aurora Glow"

# ── Fontlar ──────────────────────────────────────────────────────
F          = "Segoe UI"           # Ana font ailesi
F_MONO     = "Consolas"           # Monospace (süreler, sayılar)

# ── Mock Veri (Tasarım Önizlemesi) ───────────────────────────────
MOCK_PLAYLIST = [
    {"id":  1, "title": "Lofi Hip Hop Radio — Beats to Relax/Study",   "channel": "Lofi Girl",       "duration": "3:45"},
    {"id":  2, "title": "Chill Vibes 2024 — Deep Focus Music Mix",     "channel": "ChillMix",        "duration": "4:22"},
    {"id":  3, "title": "The Weeknd — Blinding Lights (Official MV)",  "channel": "The Weeknd",      "duration": "3:20"},
    {"id":  4, "title": "Alan Walker — Faded (Restrung)",              "channel": "Alan Walker",     "duration": "4:11"},
    {"id":  5, "title": "Eminem — Lose Yourself (8 Mile Soundtrack)",  "channel": "Eminem",          "duration": "5:26"},
    {"id":  6, "title": "BTS — Dynamite (Official MV)",                "channel": "BTS HYBE",        "duration": "3:43"},
    {"id":  7, "title": "Coldplay — Yellow (Official Video)",          "channel": "Coldplay",        "duration": "4:29"},
    {"id":  8, "title": "Imagine Dragons — Believer",                  "channel": "Imagine Dragons", "duration": "3:24"},
    {"id":  9, "title": "Ed Sheeran — Shape of You",                   "channel": "Ed Sheeran",      "duration": "3:53"},
    {"id": 10, "title": "Billie Eilish — bad guy",                     "channel": "Billie Eilish",   "duration": "3:14"},
    {"id": 11, "title": "Post Malone — Circles",                       "channel": "Post Malone",     "duration": "3:35"},
    {"id": 12, "title": "Dua Lipa — Levitating (Official Video)",      "channel": "Dua Lipa",        "duration": "3:23"},
]


# ═══════════════════════════════════════════════════════════════
#  ANA UYGULAMA SINIFI
# ═══════════════════════════════════════════════════════════════
class MusicDownloaderApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        # ── Tema yükle ─────────────────────────────────────────
        self.current_theme_name = self._load_theme_preference()
        C.update(THEMES.get(self.current_theme_name, THEMES[DEFAULT_THEME]))
        refresh_glass_tokens()

        # ── Pencere ────────────────────────────────────────────
        self.title("Music Downloader")
        self.geometry("1020x820")
        self.minsize(860, 680)
        self.configure(fg_color=C["bg"])

        # ── Grid: hero / nav / cam kart stack ───────────────────
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)   # Hero
        self.grid_rowconfigure(1, weight=0)   # FFmpeg
        self.grid_rowconfigure(2, weight=0)   # Pill nav
        self.grid_rowconfigure(3, weight=0)   # URL card
        self.grid_rowconfigure(4, weight=0)   # Options card
        self.grid_rowconfigure(5, weight=1)   # Playlist card
        self.grid_rowconfigure(6, weight=0)   # Progress + actions card
        self.grid_rowconfigure(7, weight=0)   # History card

        # ── State değişkenleri ──────────────────────────────────
        self.url_var             = tk.StringVar()
        self.format_var          = tk.StringVar(value="MP3")
        self.quality_var         = tk.StringVar(value="En İyi")
        self.download_path       = tk.StringVar(value=os.path.expanduser("~/Music"))
        self.status_var          = tk.StringVar(value="Bir YouTube playlist URL'si girin ve 'Getir' butonuna tıklayın.")
        self.progress_var        = tk.DoubleVar(value=0.0)
        self.select_all_var      = tk.BooleanVar(value=True)
        self.check_vars:         list = []
        self.playlist_items:     list = []
        self.row_status_labels:  list = []
        self.thumb_labels:       list = []
        self.row_errors:         dict = {}
        self._cancel_event       = threading.Event()
        self._dl_thread          = None
        self._ffmpeg_ok:         bool = False
        self._tooltip_win        = None
        self._nav_active         = "indir"
        self._nav_btns:          dict = {}
        self._header_accent      = None
        self._playlist_dot       = None

        # ── Arayüzü inşa et ────────────────────────────────────
        self._build_header()
        self._build_ffmpeg_warning()
        self._build_nav()
        self._build_url_section()
        self._build_options_section()
        self._build_playlist_section()
        self._build_progress_section()
        self._build_history_section()
        threading.Thread(target=self._check_ffmpeg_bg, daemon=True).start()

        # ── Animasyonlu arka plan ─────────────────────────────
        self._bg_t      = 0.0
        self._anim_job  = None
        self._bg_canvas = None
        self._bg_photo  = None
        self._build_animated_background()


    # ─────────────────────────────────────────────────────────────
    # Cam yüzey yardımcısı
    # ─────────────────────────────────────────────────────────────
    def _glass_card(self, parent, *, hero: bool = False, **pack_kw):
        """PulseTube tarzı yuvarlak cam kart çerçevesi."""
        return ctk.CTkFrame(
            parent,
            fg_color=C["glass_hero"] if hero else C["glass"],
            border_color=C["glass_border"],
            border_width=1,
            corner_radius=20,
            **pack_kw,
        )

    # ─────────────────────────────────────────────────────────────
    # 1  HERO — cam kart
    # ─────────────────────────────────────────────────────────────
    def _build_header(self):
        hero = self._glass_card(self, hero=True)
        hero.grid(row=0, column=0, sticky="ew", padx=28, pady=(20, 0))

        inner = ctk.CTkFrame(hero, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=14)

        ico = ctk.CTkFrame(
            inner, fg_color=C["accent"], width=42, height=42, corner_radius=14,
        )
        ico.pack(side="left", padx=(0, 14))
        ico.pack_propagate(False)
        ctk.CTkLabel(
            ico, text="\u266b", font=(F, 18, "bold"), text_color=C["text_inv"],
        ).place(relx=.5, rely=.5, anchor="center")

        tc = ctk.CTkFrame(inner, fg_color="transparent")
        tc.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(
            tc, text="YOUTUBE DOWNLOAD STUDIO",
            font=(F, 9, "bold"), text_color=C["accent_hover"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            tc, text="Music Downloader",
            font=(F, 22, "bold"), text_color=C["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            tc, text="Playlist \u0130ndirici",
            font=(F, 11), text_color=C["text2"],
        ).pack(anchor="w", pady=(2, 0))

        # İnce aksan çizgisi (pulse hedefi)
        self._header_accent = ctk.CTkFrame(
            hero, fg_color=C["accent"], height=2, corner_radius=0,
        )
        self._header_accent.pack(side="bottom", fill="x", padx=1, pady=(0, 1))

    # ─────────────────────────────────────────────────────────────
    # 2  PILL NAV — İndir / Geçmiş / Tema
    # ─────────────────────────────────────────────────────────────
    def _build_nav(self):
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=2, column=0, sticky="ew", padx=28, pady=(12, 0))

        self._nav_btns = {}
        specs = [
            ("indir", "\u0130ndir", self._nav_indir),
            ("gecmis", "Geçmiş", self._nav_gecmis),
            ("tema", "Tema", self._nav_tema),
        ]
        for key, label, cmd in specs:
            btn = ctk.CTkButton(
                nav, text=label, font=(F, 12, "bold"),
                corner_radius=999, height=36, width=100,
                border_width=0, command=cmd,
            )
            btn.pack(side="left", padx=(0, 8))
            self._nav_btns[key] = btn
        self._sync_nav_styles()

    def _sync_nav_styles(self):
        for key, btn in self._nav_btns.items():
            if key == self._nav_active:
                btn.configure(
                    fg_color=C["accent"], hover_color=C["accent_hover"],
                    text_color=C["text_inv"],
                )
            else:
                btn.configure(
                    fg_color=C["glass"], hover_color=C["glass2"],
                    text_color=C["text2"],
                )

    def _nav_indir(self):
        self._nav_active = "indir"
        self._sync_nav_styles()
        if getattr(self, "_history_frame", None) and self._history_frame.winfo_ismapped():
            self._history_frame.grid_remove()

    def _nav_gecmis(self):
        self._nav_active = "gecmis"
        self._sync_nav_styles()
        if getattr(self, "_history_frame", None):
            self._history_frame.grid()
            self._refresh_history_ui()

    def _nav_tema(self):
        self._nav_active = "tema"
        self._sync_nav_styles()
        self._open_theme_menu()

    # ─────────────────────────────────────────────────────────────
    # 3  URL cam kart
    # ─────────────────────────────────────────────────────────────
    def _build_url_section(self):
        card = self._glass_card(self)
        card.grid(row=3, column=0, sticky="ew", padx=28, pady=(12, 0))
        card.grid_columnconfigure(0, weight=1)

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.grid(row=0, column=0, sticky="ew", padx=14, pady=14)
        row.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            row,
            textvariable=self.url_var,
            placeholder_text="Playlist veya video URL'si yapıştırın…",
            font=(F, 13),
            fg_color=C["glass_inner"],
            border_color=C["glass_border"],
            border_width=1,
            text_color=C["text"],
            placeholder_text_color=C["text3"],
            corner_radius=14,
            height=44,
        )
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.url_entry.bind("<Return>", lambda e: self._fetch_playlist())

        self.fetch_btn = ctk.CTkButton(
            row,
            text="Getir",
            font=(F, 13, "bold"),
            fg_color=C["accent"],
            hover_color=C["accent_hover"],
            text_color=C["text_inv"],
            corner_radius=14,
            height=44, width=104,
            border_width=0,
            command=self._fetch_playlist,
        )
        self.fetch_btn.grid(row=0, column=1)

    # ─────────────────────────────────────────────────────────────
    # 4  Seçenekler cam kart
    # ─────────────────────────────────────────────────────────────
    def _build_options_section(self):
        card = self._glass_card(self)
        card.grid(row=4, column=0, sticky="ew", padx=28, pady=(10, 0))
        card.grid_columnconfigure(0, weight=1)

        bar = ctk.CTkFrame(card, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=14, pady=12)
        bar.grid_columnconfigure(2, weight=1)

        self._pill_option(bar, col=0,
                          label="Format",
                          values=["MP3","MP4","FLAC","WAV","AAC","OGG","M4A (iOS)"],
                          variable=self.format_var, width=120)

        self._pill_option(bar, col=1, padx=(12, 0),
                          label="Kalite",
                          values=["En \u0130yi","320 kbps","256 kbps","192 kbps","128 kbps"],
                          variable=self.quality_var, width=124)

        fc = ctk.CTkFrame(bar, fg_color="transparent")
        fc.grid(row=0, column=2, sticky="ew", padx=(12, 0))
        fc.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(fc, text="Klasör",
                     font=(F, 8, "bold"), text_color=C["text3"]).pack(anchor="w", pady=(0, 3))

        fr = ctk.CTkFrame(fc, fg_color="transparent")
        fr.pack(fill="x")

        self.folder_entry = ctk.CTkEntry(
            fr, textvariable=self.download_path,
            font=(F, 11),
            fg_color=C["glass_inner"],
            border_color=C["glass_border"],
            border_width=1,
            text_color=C["text2"],
            corner_radius=12, height=34,
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(fr, text="Seç",
                      font=(F, 10, "bold"),
                      fg_color=C["accent"], hover_color=C["accent_hover"],
                      text_color=C["text_inv"],
                      border_width=0,
                      corner_radius=12, height=34, width=52,
                      command=self._select_folder).pack(side="right")

    def _pill_option(self, parent, col, label, values, variable, width=140, padx=(0,0)):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=0, column=col, sticky="w", padx=padx)
        ctk.CTkLabel(wrap, text=label, font=(F, 8, "bold"),
                     text_color=C["text3"]).pack(anchor="w", pady=(0, 3))
        ctk.CTkOptionMenu(
            wrap, values=values, variable=variable,
            font=(F, 11),
            fg_color=C["glass_inner"],
            button_color=C["glass2"], button_hover_color=C["glass_border"],
            text_color=C["text"],
            dropdown_fg_color=C["card2"], dropdown_hover_color=C["border"],
            dropdown_text_color=C["text"],
            corner_radius=12, width=width, height=34,
        ).pack()

    # ─────────────────────────────────────────────────────────────
    # 5  Playlist cam kart (scroll + empty içeride)
    # ─────────────────────────────────────────────────────────────
    def _build_playlist_section(self):
        card = self._glass_card(self)
        card.grid(row=5, column=0, sticky="nsew", padx=28, pady=(10, 0))
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)
        self._playlist_card = card

        tb = ctk.CTkFrame(card, fg_color="transparent")
        tb.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))
        tb.grid_columnconfigure(1, weight=1)

        title_row = ctk.CTkFrame(tb, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="w")

        self._playlist_dot = ctk.CTkFrame(
            title_row, fg_color=C["accent"],
            width=6, height=6, corner_radius=3,
        )
        self._playlist_dot.pack(side="left", padx=(2, 8))
        self._playlist_dot.pack_propagate(False)
        ctk.CTkLabel(title_row, text="Playlist",
                     font=(F, 13, "bold"), text_color=C["text"]).pack(side="left")

        self.count_label = ctk.CTkLabel(tb, text="",
                                        font=(F, 10), text_color=C["text3"])
        self.count_label.grid(row=0, column=1, sticky="w", padx=(8, 0))

        self.select_all_cb = ctk.CTkCheckBox(
            tb, text="Tümünü Seç",
            font=(F, 10), text_color=C["text2"],
            fg_color=C["accent"], hover_color=C["accent_hover"],
            border_color=C["glass_border"], checkmark_color=C["text_inv"],
            corner_radius=4,
            variable=self.select_all_var, command=self._toggle_all,
        )
        self.select_all_cb.grid(row=0, column=2, sticky="e")

        self.scroll_frame = ctk.CTkScrollableFrame(
            card,
            fg_color="transparent",
            scrollbar_button_color=C["glass_border"],
            scrollbar_button_hover_color=C["accent"],
            corner_radius=0,
            border_width=0,
        )
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(8, 12))
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self.empty_label = ctk.CTkLabel(
            self.scroll_frame,
            text="URL yapıştırıp Getir'e basın",
            font=(F, 13),
            text_color=C["text2"],
            fg_color="transparent",
        )
        self.empty_label.pack(pady=56)

    def _show_playlist_empty(self, msg: str = "URL yapıştırıp Getir'e basın"):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        self.empty_label = ctk.CTkLabel(
            self.scroll_frame,
            text=msg,
            font=(F, 13),
            text_color=C["text2"],
            fg_color="transparent",
        )
        self.empty_label.pack(pady=56)
        self.count_label.configure(text="")

    def _show_playlist_scroll(self):
        # Scroll zaten cam kartta; empty temizlenir populate içinde
        pass

    def _populate_playlist(self, items: list[dict]):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        self.playlist_items    = items
        self.check_vars        = []
        self.row_status_labels = []
        self.thumb_labels      = []
        self.row_errors        = {}

        if not items:
            self._show_playlist_empty("Playlist boş — yeni bir URL girin")
            return

        self.count_label.configure(text=f"  {len(items)} şarkı")

        for i, item in enumerate(items):
            var = tk.BooleanVar(value=True)
            self.check_vars.append(var)

            row = ctk.CTkFrame(
                self.scroll_frame,
                fg_color=C["glass_inner"] if i % 2 == 0 else "transparent",
                corner_radius=12,
                border_width=0,
            )
            row.grid(row=i, column=0, sticky="ew", pady=2, padx=4)
            row.grid_columnconfigure(2, weight=1)

            ctk.CTkLabel(
                row, text=f"{item['id']:02d}",
                font=(F_MONO, 9), text_color=C["text3"],
                width=32, anchor="center",
            ).grid(row=0, column=0, padx=(8, 4), pady=8)

            ctk.CTkCheckBox(
                row, text="",
                variable=var,
                fg_color=C["accent"], hover_color=C["accent_hover"],
                border_color=C["glass_border"], checkmark_color=C["text_inv"],
                corner_radius=4, width=18, height=18,
                checkbox_width=18, checkbox_height=18,
                command=self._update_select_all_state,
            ).grid(row=0, column=1, padx=(0, 10), pady=8)

            ctk.CTkLabel(
                row, text=item["title"],
                font=(F, 11), text_color=C["text"], anchor="w",
            ).grid(row=0, column=2, sticky="ew", padx=(0, 8), pady=8)

            ctk.CTkLabel(
                row, text=item["channel"],
                font=(F, 9), text_color=C["text3"], width=110, anchor="e",
            ).grid(row=0, column=3, padx=(0, 8), pady=8, sticky="e")

            ctk.CTkLabel(
                row, text=item["duration"],
                font=(F_MONO, 9), text_color=C["text2"],
                width=48, anchor="center",
            ).grid(row=0, column=4, padx=(0, 4), pady=8)

            sl = ctk.CTkLabel(row, text="", font=(F, 12),
                              text_color=C["text2"],
                              width=22, anchor="center")
            sl.grid(row=0, column=5, padx=(0, 8), pady=8)
            self.row_status_labels.append(sl)

    # ─────────────────────────────────────────────────────────────
    # 6  Progress + aksiyonlar — tek cam kart
    # ─────────────────────────────────────────────────────────────
    def _build_progress_section(self):
        card = self._glass_card(self)
        card.grid(row=6, column=0, sticky="ew", padx=28, pady=(10, 12))
        card.grid_columnconfigure(0, weight=1)

        wrap = ctk.CTkFrame(card, fg_color="transparent")
        wrap.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))
        wrap.grid_columnconfigure(0, weight=1)

        sr = ctk.CTkFrame(wrap, fg_color="transparent")
        sr.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        sr.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            sr, textvariable=self.status_var,
            font=(F, 10), text_color=C["text3"], anchor="w",
        )
        self.status_label.grid(row=0, column=0, sticky="w")

        self.pct_label = ctk.CTkLabel(
            sr, text="", font=(F_MONO, 10, "bold"),
            text_color=C["accent"],
        )
        self.pct_label.grid(row=0, column=1, sticky="e")

        self.progress_bar = ctk.CTkProgressBar(
            wrap,
            variable=self.progress_var,
            progress_color=C["accent"],
            fg_color=C["glass_inner"],
            corner_radius=4,
            height=4,
            border_width=0,
        )
        self.progress_bar.grid(row=1, column=0, sticky="ew")

        # Dock aksiyonları aynı kartta
        dock = ctk.CTkFrame(card, fg_color="transparent")
        dock.grid(row=1, column=0, sticky="ew", padx=16, pady=(4, 14))
        dock.grid_columnconfigure(1, weight=1)

        L = ctk.CTkFrame(dock, fg_color="transparent")
        L.grid(row=0, column=0, sticky="w")

        self.history_btn = ctk.CTkButton(
            L, text="Geçmiş",
            font=(F, 11),
            fg_color=C["glass_inner"], hover_color=C["glass2"],
            text_color=C["text2"],
            border_width=0,
            corner_radius=999, height=36, width=88,
            command=self._nav_gecmis,
        )
        self.history_btn.pack(side="left")

        self.selected_label = ctk.CTkLabel(
            L, text="", font=(F, 10), text_color=C["text3"],
        )
        self.selected_label.pack(side="left", padx=(10, 0))

        R = ctk.CTkFrame(dock, fg_color="transparent")
        R.grid(row=0, column=2, sticky="e")

        ctk.CTkButton(
            R, text="Temizle",
            font=(F, 11),
            fg_color=C["glass_inner"], hover_color=C["glass2"],
            text_color=C["text2"],
            border_width=0,
            corner_radius=999, height=40, width=96,
            command=self._clear_all,
        ).pack(side="left", padx=(0, 6))

        self.cancel_btn = ctk.CTkButton(
            R, text="Durdur",
            font=(F, 11, "bold"),
            fg_color=C["glass_inner"], hover_color=C["glass2"],
            text_color=C["error"],
            border_width=0,
            corner_radius=999, height=40, width=96,
            state="disabled",
            command=self._cancel_download,
        )
        self.cancel_btn.pack(side="left", padx=(0, 8))

        self.download_btn = ctk.CTkButton(
            R, text="\u0130ndir",
            font=(F, 13, "bold"),
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color=C["text_inv"],
            border_width=0,
            corner_radius=999, height=40, width=128,
            command=self._start_download,
        )
        self.download_btn.pack(side="left")

    def _build_action_section(self):
        """Eski ayrı dock — progress kartına taşındı (compat no-op)."""
        pass

    def _dropdown_group(self, *a, **kw): pass  # compat shim

    # ═══════════════════════════════════════════════════════════
    #  CALLBACK'LER
    # ═══════════════════════════════════════════════════════════

    def _fetch_playlist(self):
        url = self.url_var.get().strip()
        if not url:
            self._set_status("⚠  Lütfen geçerli bir URL girin.", color=C["warning"])
            return
        self._set_status("Playlist bilgileri alınıyor…")
        self.fetch_btn.configure(state="disabled", text="Yükleniyor…")
        self.progress_var.set(0.0)
        self.pct_label.configure(text="")

        def _worker():
            try:
                items = fetch_playlist_info(url)
                self.after(0, lambda it=items: self._on_fetch_done(it, None))
            except Exception as exc:
                self.after(0, lambda e=exc: self._on_fetch_done(None, e))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_fetch_done(self, items, error):
        self.fetch_btn.configure(state="normal", text="Getir")
        if error:
            self._set_status(f"✗  Hata: {error}", color=C["error"])
            return
        self._populate_playlist(items)
        self._refresh_selected_label()
        self._set_status(f"✓  {len(items)} video bulundu.", color=C["success"])
        # Thumbnail'leri arka planda indir
        threading.Thread(target=self._load_thumbnails, args=(items,), daemon=True).start()

    def _toggle_all(self):
        state = self.select_all_var.get()
        for v in self.check_vars:
            v.set(state)
        self._refresh_selected_label()

    def _update_select_all_state(self):
        total    = len(self.check_vars)
        selected = sum(v.get() for v in self.check_vars)
        self.select_all_var.set(selected == total)
        self._refresh_selected_label()

    def _refresh_selected_label(self):
        sel = sum(v.get() for v in self.check_vars)
        tot = len(self.check_vars)
        self.selected_label.configure(
            text=f"{sel} / {tot} seçili" if tot > 0 else ""
        )

    def _select_folder(self):
        path = filedialog.askdirectory(initialdir=self.download_path.get())
        if path:
            self.download_path.set(path)

    def _clear_all(self):
        self.url_var.set("")
        self.progress_var.set(0.0)
        self.pct_label.configure(text="")
        self._set_status("Temizlendi. Yeni bir URL girin.")
        self._populate_playlist([])
        self.selected_label.configure(text="")

    def _start_download(self):
        selected_indices = [i for i, v in enumerate(self.check_vars) if v.get()]
        if not selected_indices:
            self._set_status("⚠  En az bir video seçin!", color=C["warning"])
            return

        selected_items = [self.playlist_items[i] for i in selected_indices]
        total          = len(selected_items)

        # İndirme başlarken önceki hataları temizle
        self.row_errors = {}
        self._cancel_event.clear()
        self.download_btn.configure(state="disabled", text="İndiriliyor…")
        self.cancel_btn.configure(state="normal", fg_color="#2A0A0A")
        self.fetch_btn.configure(state="disabled")
        self.progress_var.set(0.0)
        self.pct_label.configure(text="0%")

        # Tamamlanan sayacı (thread-safe list)
        completed = [0]

        def _on_item_start(idx: int, title: str):
            ri = selected_indices[idx]
            def _ui(i=ri, t=title, n=idx):
                self._update_row_status(i, "⟳", C["warning"])
                self._set_status(f"İndiriliyor ({n+1}/{total}):  {t[:60]}…")
            self.after(0, _ui)

        def _on_item_progress(idx: int, pct: float, speed: str):
            overall = (completed[0] + pct) / total
            spd = f"  {speed}" if speed else ""
            def _ui(o=overall, s=spd):
                self.progress_var.set(o)
                self.pct_label.configure(text=f"{int(o * 100)}%{s}")
            self.after(0, _ui)

        def _on_item_done(idx: int, success: bool, error_msg: str = ""):
            completed[0] += 1
            ri    = selected_indices[idx]
            icon  = "✓" if success else "✗"
            color = C["success"] if success else C["error"]
            def _ui(i=ri, ic=icon, c=color, em=error_msg):
                self._update_row_status(i, ic, c)
                if not success and em:
                    self.row_errors[i] = em
                    self._bind_error_tooltip(i, em)
            self.after(0, _ui)

        def _worker():
            download_videos(
                items            = selected_items,
                output_dir       = self.download_path.get(),
                fmt              = self.format_var.get(),
                quality          = self.quality_var.get(),
                on_item_start    = _on_item_start,
                on_item_progress = _on_item_progress,
                on_item_done     = _on_item_done,
                cancel_event     = self._cancel_event,
            )
            self.after(0, lambda d=completed[0], t=total: self._on_download_done(d, t))

        self._dl_thread = threading.Thread(target=_worker, daemon=True)
        self._dl_thread.start()

    def _on_download_done(self, done: int, total: int):
        self.download_btn.configure(state="normal", text="\u0130ndir")
        self.cancel_btn.configure(state="disabled", fg_color=C["card"])
        self.fetch_btn.configure(state="normal")
        self.progress_var.set(1.0 if not self._cancel_event.is_set() else done / max(total, 1))
        self.pct_label.configure(text="")
        failed = total - done if not self._cancel_event.is_set() else 0
        if self._cancel_event.is_set():
            self._set_status(f"◼  Durduruldu  —  {done}/{total} video indirildi.", color=C["warning"])
            status = "cancelled"
        elif failed > 0:
            self._set_status(
                f"⚠  {done}/{total} video indirildi  —  {failed} indirilemedi"
                f"  (✗ simgesinin üzerine gelin → sebep)",
                color=C["warning"],
            )
            status = "partial"
        else:
            self._set_status(
                f"✓  {done}/{total} video indirildi  →  {self.download_path.get()}",
                color=C["success"],
            )
            status = "success"
        self._save_history_record(done, total, status)
        self._refresh_history_ui()

    def _cancel_download(self):
        self._cancel_event.set()
        self._set_status("Durduruluyor…", color=C["warning"])
        self.cancel_btn.configure(state="disabled")

    # ───────────────────────────────────────────────────────────
    # Hata Tooltip
    # ───────────────────────────────────────────────────────────
    def _bind_error_tooltip(self, row_idx: int, error_msg: str):
        """Hatalı satır durum etiketine hover tooltip bağlar."""
        if 0 <= row_idx < len(self.row_status_labels):
            lbl = self.row_status_labels[row_idx]
            lbl.configure(cursor="question_arrow")
            lbl.bind("<Enter>", lambda e, t=error_msg, w=lbl: self._show_tooltip(w, t))
            lbl.bind("<Leave>", lambda e: self._hide_tooltip())

    def _show_tooltip(self, widget, text: str):
        """Widget üzerine gelinince hata mesajı gösteren tooltip penceresi açar."""
        self._hide_tooltip()
        try:
            x = widget.winfo_rootx()
            y = widget.winfo_rooty() - 38
            self._tooltip_win = tk.Toplevel(self)
            self._tooltip_win.wm_overrideredirect(True)
            self._tooltip_win.wm_geometry(f"+{x}+{y}")
            self._tooltip_win.configure(bg=C["card2"])
            border = tk.Frame(self._tooltip_win, bg=C["error"], padx=1, pady=1)
            border.pack()
            inner = tk.Frame(border, bg="#1A0A0A")
            inner.pack()
            tk.Label(
                inner,
                text=f"✗  {text}",
                font=(F, 9),
                bg="#1A0A0A",
                fg=C["error"],
                padx=10, pady=6,
                wraplength=440,
                justify="left",
            ).pack()
        except Exception:
            pass

    def _hide_tooltip(self):
        """Aktif tooltip penceresini kapatır."""
        if self._tooltip_win:
            try:
                self._tooltip_win.destroy()
            except Exception:
                pass
            self._tooltip_win = None

    def _update_row_status(self, row_idx: int, icon: str, color: str):
        """Playlist satırındaki durum etiketini günceller (main thread'den çağrılmalı)."""
        if 0 <= row_idx < len(self.row_status_labels):
            self.row_status_labels[row_idx].configure(text=icon, text_color=color)

    # ───────────────────────────────────────────────────────────
    # FFmpeg Kontrol
    # ───────────────────────────────────────────────────────────
    def _build_ffmpeg_warning(self):
        """FFmpeg uyarı bandı (row=1). Başlangıçta gizli, FFmpeg yoksa görünür."""
        self._ffmpeg_banner = ctk.CTkFrame(
            self, fg_color="#251800", corner_radius=0,
        )
        inner = ctk.CTkFrame(self._ffmpeg_banner, fg_color="transparent")
        inner.pack(fill="x", padx=22, pady=9)

        ctk.CTkLabel(
            inner,
            text="⚠  FFmpeg bulunamadı  —  MP3 / FLAC / WAV / AAC dönüşümü çalışmayacak."
                 "  ffmpeg.org adresinden indirip sistem PATH'ine ekleyin.",
            font=(F, 10),
            text_color=C["warning"],
            anchor="w",
            wraplength=750,
            justify="left",
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            inner, text="✕",
            font=(F, 12, "bold"),
            fg_color="transparent",
            hover_color="#3A2200",
            text_color=C["text2"],
            width=28, height=28,
            corner_radius=6,
            command=self._ffmpeg_banner.grid_remove,
        ).pack(side="right", padx=(12, 0))

        self._ffmpeg_banner.grid(row=1, column=0, sticky="ew")
        self._ffmpeg_banner.grid_remove()   # başlangıçta gizli

    def _check_ffmpeg_bg(self):
        """Arka planda FFmpeg varlığını kontrol eder; yoksa uyarı bandını gösterir."""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            self._ffmpeg_ok = True
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            self._ffmpeg_ok = False
            self.after(0, self._ffmpeg_banner.grid)   # uyarıyı göster

    # ───────────────────────────────────────────────────────────
    # ANİMASYONLU ARKA PLAN
    # ───────────────────────────────────────────────────────────

    def _build_animated_background(self) -> None:
        """PIL gradyan animasyonu için tam pencere kaplayan canvas oluşturur."""
        if not PIL_OK:
            # Pillow yoksa bile ambient renk pulse çalışsın
            if getattr(self, "_anim_job", None) is None:
                self._bg_t = getattr(self, "_bg_t", 0.0)
                self._animate_bg()
            return

        # Önceki animasyonu durdur
        if getattr(self, "_anim_job", None):
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None

        # Önceki canvas'ı temizle
        if getattr(self, "_bg_canvas", None):
            try:
                self._bg_canvas.destroy()
            except Exception:
                pass

        self._bg_canvas = tk.Canvas(
            self,
            highlightthickness=0,
            bd=0,
            bg=C["bg"],
        )
        self._bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        # Canvas.lower() item API'sini override eder; widget sıralaması için Misc.lower
        tk.Misc.lower(self._bg_canvas)
        self._bg_photo = None
        self._animate_bg()

    def _theme_palette_rgbs(self) -> list:
        """Aktif temanın canlı swatch + vurgu renklerini RGB listesi olarak döner."""
        theme = THEMES.get(self.current_theme_name, THEMES[DEFAULT_THEME])
        colors = list(theme.get("_swatches", []))
        for key in ("accent", "accent_hover", "blue", "blue_hover"):
            colors.append(theme.get(key, C.get(key, "#ffffff")))
        # Tekrarları ayıkla; çok koyu (neredeyse bg) renkleri at — animasyon soluklaşmasın
        seen, out = set(), []
        for hex_c in colors:
            if not hex_c or hex_c in seen:
                continue
            seen.add(hex_c)
            try:
                rgb = _hex_to_rgb(hex_c)
            except Exception:
                continue
            lum = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
            if lum < 45:
                continue
            out.append(rgb)
        return out or [_hex_to_rgb(C["accent"]), _hex_to_rgb(C["blue"])]

    def _pulse_accent_widgets(self, accent_hex: str, accent_soft: str) -> None:
        """Tema vurgu rengini progress ve header aksanında canlı tutar."""
        try:
            if getattr(self, "progress_bar", None):
                self.progress_bar.configure(progress_color=accent_hex)
            if getattr(self, "pct_label", None):
                self.pct_label.configure(text_color=accent_hex)
            if getattr(self, "_header_accent", None):
                self._header_accent.configure(fg_color=accent_hex)
            if getattr(self, "_playlist_dot", None):
                self._playlist_dot.configure(fg_color=accent_soft)
        except Exception:
            pass

    def _bind_scroll_canvas_bg(self, color: str) -> None:
        """CTkScrollableFrame iç canvas'ını verilen renge zorla (siyah kutu engeli)."""
        sf = getattr(self, "scroll_frame", None)
        if not sf:
            return
        for attr in ("_parent_canvas", "_canvas", "_scrollbar_fg_color"):
            widget = getattr(sf, attr, None)
            if widget is None:
                continue
            try:
                if hasattr(widget, "configure") and attr != "_scrollbar_fg_color":
                    widget.configure(bg=color, highlightthickness=0)
            except Exception:
                pass
        # Bazı CTk sürümlerinde ek çerçeve
        for attr in ("_parent_frame", "_frame"):
            fr = getattr(sf, attr, None)
            if fr is None:
                continue
            try:
                fr.configure(fg_color=color)
            except Exception:
                pass

    def _animate_bg(self) -> None:
        """PulseTube tarzı soft orb / bg-flow arka plan + accent pulse."""
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        w = self.winfo_width()
        h = self.winfo_height()
        if w < 50 or h < 50:
            self._anim_job = self.after(120, self._animate_bg)
            return

        t = self._bg_t
        bg_rgb = _hex_to_rgb(C["bg"])
        ca = _hex_to_rgb(C["accent"])
        cah = _hex_to_rgb(C["accent_hover"])
        cb = _hex_to_rgb(C["blue"])
        palette = self._theme_palette_rgbs()
        n = len(palette)

        # Soft diagonal base (PulseTube linear-gradient hissi) — kök opak plaka yok
        try:
            self.configure(fg_color=C["bg"])
            if getattr(self, "_bg_canvas", None):
                self._bg_canvas.configure(bg=C["bg"])
        except Exception:
            pass

        pulse = (math.sin(t * 0.45) + 1) * 0.5
        accent_now = _rgb_to_hex(_lerp_rgb(ca, cah, pulse))
        accent_soft = _rgb_to_hex(_lerp_rgb(ca, cb, pulse))
        self._pulse_accent_widgets(accent_now, accent_soft)

        if PIL_OK and getattr(self, "_bg_canvas", None):
            rw = max(w // 4, 80)
            rh = max(h // 4, 60)

            # Base: bg + hafif accent/blue köşe glow
            img = PilImage.new("RGB", (rw, rh), bg_rgb)
            draw = ImageDraw.Draw(img)
            corner_a = _lerp_rgb(bg_rgb, ca, 0.35)
            corner_b = _lerp_rgb(bg_rgb, cb, 0.30)
            draw.ellipse([-rw // 3, -rh // 3, rw // 2, rh // 2], fill=corner_a)
            draw.ellipse([rw // 2, rh // 2, rw + rw // 3, rh + rh // 3], fill=corner_b)

            orb_specs = [
                (0.15, 0.20, 0.55, 0.18, 0.0),
                (0.82, 0.15, 0.48, 0.14, 1.5),
                (0.55, 0.75, 0.42, 0.16, 3.0),
                (0.20, 0.80, 0.50, 0.12, 2.2),
                (0.75, 0.65, 0.38, 0.15, 4.0),
            ]
            for i, (bx, by, br, spd, phase) in enumerate(orb_specs):
                c0 = palette[i % n]
                c1 = palette[(i + 1) % n]
                mix = (math.sin(t * 0.16 + phase) + 1) * 0.5
                rgb = _lerp_rgb(c0, c1, mix)
                cx = (bx + math.sin(t * spd + phase) * 0.10) * rw
                cy = (by + math.cos(t * spd * 0.8 + phase) * 0.10) * rh
                r = br * min(rw, rh)
                fill = _lerp_rgb(bg_rgb, rgb, 0.72)
                draw.ellipse(
                    [int(cx - r), int(cy - r), int(cx + r), int(cy + r)],
                    fill=fill,
                )

            img = img.filter(ImageFilter.GaussianBlur(radius=max(rw // 4, 14)))
            img = img.resize((w, h), PilImage.BILINEAR)

            self._bg_photo = PilImageTk.PhotoImage(img)
            try:
                self._bg_canvas.delete("bg")
                self._bg_canvas.create_image(
                    0, 0, anchor="nw", image=self._bg_photo, tags="bg",
                )
                tk.Misc.lower(self._bg_canvas)
            except Exception:
                pass

        self._bg_t += 0.018
        self._anim_job = self.after(48, self._animate_bg)
    # ───────────────────────────────────────────────────────────
    def _load_thumbnails(self, items: list):
        """Playlist öğelerinin küçük resimlerini arka planda indirir (PIL gerekli)."""
        if not PIL_OK:
            return
        for idx, item in enumerate(items):
            vid = item.get("video_id", "")
            if not vid:
                continue
            url = f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=6) as resp:
                    data = resp.read()
                img     = PilImage.open(io.BytesIO(data)).resize((72, 40), PilImage.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(72, 40))
                self.after(0, lambda i=idx, im=ctk_img: self._set_thumbnail(i, im))
            except Exception:
                pass

    def _set_thumbnail(self, idx: int, img):
        """Playlist satırının thumbnail etiketini günceller."""
        if 0 <= idx < len(self.thumb_labels):
            self.thumb_labels[idx].configure(image=img, fg_color="transparent")

    # ───────────────────────────────────────────────────────────
    # İndirme Geçmişi
    # ───────────────────────────────────────────────────────────
    def _build_history_section(self):
        """İndirme geçmişi — cam kart; başlangıçta gizli."""
        self._history_frame = self._glass_card(self)
        self._history_frame.grid(row=7, column=0, sticky="ew", padx=28, pady=(0, 18))
        self._history_frame.grid_columnconfigure(0, weight=1)
        self._history_frame.grid_remove()

        title_bar = ctk.CTkFrame(self._history_frame, fg_color="transparent")
        title_bar.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 6))
        title_bar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            title_bar, text="İNDİRME GEÇMİŞİ",
            font=(F, 9, "bold"), text_color=C["text3"],
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            title_bar, text="Temizle",
            font=(F, 9),
            fg_color="transparent",
            hover_color=C["glass2"],
            text_color=C["text3"],
            width=54, height=22,
            corner_radius=8,
            command=self._clear_history,
        ).grid(row=0, column=1, sticky="e")

        ctk.CTkFrame(
            self._history_frame, fg_color=C["glass_border"], height=1,
        ).grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 6))

        self._history_scroll = ctk.CTkScrollableFrame(
            self._history_frame,
            fg_color="transparent",
            scrollbar_button_color=C["glass_border"],
            scrollbar_button_hover_color=C["accent"],
            height=130,
        )
        self._history_scroll.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        self._history_scroll.grid_columnconfigure(0, weight=1)

        self._refresh_history_ui()

    def _toggle_history(self):
        if self._history_frame.winfo_ismapped():
            self._nav_indir()
        else:
            self._nav_gecmis()

    def _refresh_history_ui(self):
        """Geçmiş listesini history.json'dan okuyup UI'a yazar."""
        for w in self._history_scroll.winfo_children():
            w.destroy()

        records = self._load_history_records()

        if not records:
            ctk.CTkLabel(
                self._history_scroll,
                text="Henüz indirme geçmişi yok.",
                font=(F, 10), text_color=C["text3"],
            ).pack(pady=14)
            return

        STATUS_ICON  = {"success": "✓", "cancelled": "◼", "partial": "⚡"}
        STATUS_COLOR = {"success": C["success"], "cancelled": C["warning"], "partial": C["blue"]}

        for rec in records[:25]:
            st   = rec.get("status", "partial")
            icon = STATUS_ICON.get(st, "⚡")
            col  = STATUS_COLOR.get(st, C["blue"])

            row = ctk.CTkFrame(self._history_scroll, fg_color="transparent", corner_radius=0)
            row.pack(fill="x", pady=1)
            row.columnconfigure(1, weight=1)

            ctk.CTkLabel(
                row, text=icon,
                font=(F, 13, "bold"), text_color=col,
                width=28,
            ).grid(row=0, column=0, padx=(10, 6), pady=7)

            summary = (
                f"{rec.get('count','?')}/{rec.get('total','?')} video"
                f"  •  {rec.get('fmt','?')}"
                f"  →  {rec.get('path','')}"
            )
            ctk.CTkLabel(
                row, text=summary,
                font=(F, 10), text_color=C["text"],
                anchor="w",
            ).grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=7)

            ctk.CTkLabel(
                row, text=rec.get("date", ""),
                font=(F_MONO, 9), text_color=C["text3"],
                width=130, anchor="e",
            ).grid(row=0, column=2, padx=(0, 10), pady=7)

    @staticmethod
    def _load_history_records() -> list:
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as fh:
                    return json.load(fh)
            except Exception:
                return []
        return []

    def _save_history_record(self, done: int, total: int, status: str):
        records = self._load_history_records()
        records.insert(0, {
            "date":   datetime.now().strftime("%Y-%m-%d  %H:%M"),
            "count":  done,
            "total":  total,
            "fmt":    self.format_var.get(),
            "path":   self.download_path.get(),
            "status": status,
        })
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as fh:
                json.dump(records[:100], fh, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _clear_history(self):
        try:
            HISTORY_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        self._refresh_history_ui()

    def _set_status(self, msg: str, color: str = ""):
        self.status_var.set(msg)
        if color:
            self.status_label.configure(text_color=color)
        else:
            self.status_label.configure(text_color=C["text2"])


    # ═══════════════════════════════════════════════════════════
    #  TEMA MENÜSÜ
    # ═══════════════════════════════════════════════════════════

    def _open_theme_menu(self):
        """9 temayı gösteren modal seçim penceresi (animasyonlu)."""
        popup = ctk.CTkToplevel(self)
        popup.title("Tema Seç")
        popup.geometry("820x600")
        popup.resizable(False, False)
        popup.configure(fg_color=C["bg"])
        popup.transient(self)
        popup.grab_set()
        popup.focus_set()
        popup.wm_attributes("-alpha", 0.0)

        # ── Başlık çubuğu ───────────────────────────────────────
        hdr = ctk.CTkFrame(popup, fg_color=C["bg2"], corner_radius=0, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr, text="\U0001f3a8  Tema Seç",
            font=(F, 16, "bold"), text_color=C["text"],
        ).pack(side="left", padx=24)

        # Aktif tema badge
        badge_f = ctk.CTkFrame(hdr, fg_color=C["accent"], corner_radius=6)
        badge_f.pack(side="left", padx=(10, 0), pady=18)
        ctk.CTkLabel(
            badge_f, text=self.current_theme_name,
            font=(F, 10, "bold"), text_color=C["text_inv"],
        ).pack(padx=10, pady=5)

        ctk.CTkLabel(
            hdr, text="— Bir karta tıklayarak teması uygulayabilirsiniz",
            font=(F, 9), text_color=C["text3"],
        ).pack(side="left", padx=(14, 0))

        ctk.CTkButton(
            hdr, text="\u2715",
            font=(F, 14, "bold"),
            fg_color="transparent",
            hover_color=C["card"],
            text_color=C["text2"],
            width=36, height=36, corner_radius=8,
            command=popup.destroy,
        ).pack(side="right", padx=14)

        # ── Tema ızgarası ────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(
            popup,
            fg_color="transparent",
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["text3"],
        )
        scroll.pack(fill="both", expand=True, padx=18, pady=(14, 18))

        for col_i in range(3):
            scroll.grid_columnconfigure(col_i, weight=1, uniform="col")

        for idx, (theme_name, td) in enumerate(THEMES.items()):
            row_i     = idx // 3
            col_i     = idx % 3
            is_active = (theme_name == self.current_theme_name)

            card = ctk.CTkFrame(
                scroll,
                fg_color=td["card2"] if is_active else td["card"],
                border_color=td["accent"] if is_active else td["border"],
                border_width=2 if is_active else 1,
                corner_radius=14,
                cursor="arrow" if is_active else "hand2",
            )
            card.grid(row=row_i, column=col_i, padx=7, pady=7, sticky="nsew")

            # Kalın üst aksan şeridi
            strip = ctk.CTkFrame(
                card, fg_color=td["accent"],
                height=6, corner_radius=0,
            )
            strip.pack(fill="x")
            strip.pack_propagate(False)

            # Tema adı + aktif badge
            name_row = ctk.CTkFrame(card, fg_color="transparent")
            name_row.pack(fill="x", padx=12, pady=(10, 0))

            ctk.CTkLabel(
                name_row, text=theme_name,
                font=(F, 12, "bold"), text_color=td["text"], anchor="w",
            ).pack(side="left")

            if is_active:
                af = ctk.CTkFrame(name_row, fg_color=td["accent"], corner_radius=5)
                af.pack(side="right")
                ctk.CTkLabel(
                    af, text="\u2713",
                    font=(F, 9, "bold"), text_color=td["text_inv"],
                ).pack(padx=7, pady=2)

            # Renk swatchları (tam daire)
            srow = ctk.CTkFrame(card, fg_color="transparent")
            srow.pack(padx=12, pady=(8, 0), anchor="w")
            for color in td.get("_swatches", []):
                sw = ctk.CTkFrame(
                    srow, fg_color=color,
                    width=24, height=24, corner_radius=12,
                )
                sw.pack(side="left", padx=3)
                sw.pack_propagate(False)

            # Arka plan renk önizleme şeridi
            bg_bar = ctk.CTkFrame(
                card, fg_color=td["bg"], corner_radius=6, height=18,
            )
            bg_bar.pack(fill="x", padx=12, pady=(8, 0))
            bg_bar.pack_propagate(False)
            ctk.CTkLabel(
                bg_bar, text=td["bg"],
                font=(F_MONO, 8), text_color=td["text3"],
            ).place(relx=0.5, rely=0.5, anchor="center")

            # Alt aksiyon
            if is_active:
                ctk.CTkLabel(
                    card, text="\u25cf  Aktif Tema",
                    font=(F, 9, "bold"), text_color=td["accent"],
                ).pack(pady=(8, 12))
            else:
                def _make_cmd(tn=theme_name, p=popup):
                    def _cmd():
                        p.destroy()
                        self._apply_theme(tn)
                    return _cmd

                ctk.CTkButton(
                    card,
                    text="Uygula",
                    font=(F, 10, "bold"),
                    fg_color=td["accent"],
                    hover_color=td["accent_hover"],
                    text_color=td["text_inv"],
                    corner_radius=8, height=32,
                    command=_make_cmd(),
                ).pack(pady=(8, 12), padx=12, fill="x")

                self._bind_card_hover(card, td)

        # ── Popup fade-in (yukarıdan aşağıya kayış) animasyonu ─────────
        target_y = popup.winfo_y()

        def _popup_fadein(step: int = 0, steps: int = 12):
            t    = step / steps
            ease = t * t * (3.0 - 2.0 * t)   # smoothstep
            try:
                popup.wm_attributes("-alpha", ease)
                # Hafif yukarı-aşağı kayma
                offset = int((1.0 - ease) * 18)
                popup.geometry(f"+{popup.winfo_x()}+{target_y - offset}")
            except Exception:
                return
            if step < steps:
                popup.after(20, lambda: _popup_fadein(step + 1, steps))

        popup.after(60, _popup_fadein)

    def _apply_theme(self, theme_name: str):
        """Fade animasyonu eşliğinde teması değiştirir ve UI'yı yeniden oluşturur."""
        global C

        if self._dl_thread and self._dl_thread.is_alive():
            return

        checked_states  = [v.get() for v in self.check_vars]
        items_backup    = list(self.playlist_items)
        errors_backup   = dict(self.row_errors)
        ffmpeg_visible  = (
            hasattr(self, "_ffmpeg_banner") and self._ffmpeg_banner.winfo_ismapped()
        )
        history_visible = (
            hasattr(self, "_history_frame") and self._history_frame.winfo_ismapped()
        )

        def _rebuild():
            # Animasyonu durdur
            if getattr(self, "_anim_job", None):
                try:
                    self.after_cancel(self._anim_job)
                except Exception:
                    pass
                self._anim_job = None

            C.update(THEMES[theme_name])
            refresh_glass_tokens()
            self.current_theme_name = theme_name
            self.configure(fg_color=C["bg"])

            for w in self.winfo_children():
                w.destroy()

            self._nav_active = "indir"
            self._build_header()
            self._build_ffmpeg_warning()
            self._build_nav()
            self._build_url_section()
            self._build_options_section()
            self._build_playlist_section()
            self._build_progress_section()
            self._build_history_section()

            if items_backup:
                self._populate_playlist(items_backup)
                for i, state in enumerate(checked_states):
                    if i < len(self.check_vars):
                        self.check_vars[i].set(state)
                self.row_errors = errors_backup
                self._refresh_selected_label()

            if ffmpeg_visible:
                self._ffmpeg_banner.grid()
            if history_visible:
                self._nav_active = "gecmis"
                self._sync_nav_styles()
                self._history_frame.grid()

            threading.Thread(target=self._check_ffmpeg_bg, daemon=True).start()
            self._save_theme_preference(theme_name)

            # Animasyonlu arka planı yeniden başlat
            self._build_animated_background()

            # Fade-in ile geri göster
            self._animate_alpha(0.0, 1.0, 14, 18)

        # Önce fade-out, ardından rebuild
        self._animate_alpha(1.0, 0.0, 10, 18, on_done=_rebuild)

    def _animate_alpha(
        self,
        start: float,
        end: float,
        steps: int = 12,
        delay: int = 18,
        on_done: "callable | None" = None,
    ) -> None:
        """Ana pencerenin saydamlığını smoothstep easing ile animasyonlar."""
        def _step(i: int = 0):
            t     = i / steps
            ease  = t * t * (3.0 - 2.0 * t)
            alpha = start + (end - start) * ease
            try:
                self.wm_attributes("-alpha", max(0.0, min(1.0, alpha)))
            except Exception:
                pass
            if i < steps:
                self.after(delay, lambda: _step(i + 1))
            elif on_done:
                on_done()
        _step()

    @staticmethod
    def _bind_card_hover(card: ctk.CTkFrame, td: dict) -> None:
        """Tema kartı ve tüm alt widget'larına hover renk geçiş efekti bağlar."""
        def _enter(_e):
            card.configure(
                fg_color=td["card2"],
                border_color=td["accent"],
                border_width=2,
            )

        def _leave(e):
            try:
                px, py = e.widget.winfo_pointerxy()
                cx, cy = card.winfo_rootx(), card.winfo_rooty()
                cw, ch = card.winfo_width(), card.winfo_height()
                if not (cx <= px <= cx + cw and cy <= py <= cy + ch):
                    card.configure(
                        fg_color=td["card"],
                        border_color=td["border"],
                        border_width=1,
                    )
            except Exception:
                card.configure(
                    fg_color=td["card"],
                    border_color=td["border"],
                    border_width=1,
                )

        def _bind_recursive(w):
            w.bind("<Enter>", _enter, add="+")
            w.bind("<Leave>", _leave, add="+")
            for child in w.winfo_children():
                _bind_recursive(child)

        _bind_recursive(card)

    @staticmethod
    def _save_theme_preference(theme_name: str) -> None:
        """Tema tercihini settings.json dosyasına kaydeder."""
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
                json.dump({"theme": theme_name}, fh, ensure_ascii=False)
        except Exception:
            pass

    @staticmethod
    def _load_theme_preference() -> str:
        """settings.json'dan kayıtlı temayı okur; yoksa varsayılanı döner."""
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                name = data.get("theme", DEFAULT_THEME)
                if name in THEMES:
                    return name
        except Exception:
            pass
        return DEFAULT_THEME


# ═══════════════════════════════════════════════════════════════
#  BAŞLANGIÇ
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = MusicDownloaderApp()
    app.mainloop()
