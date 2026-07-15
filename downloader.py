"""
downloader.py  —  yt-dlp Wrapper Modülü
YouTube playlist bilgisi çekme ve video indirme işlemleri
"""

import threading
import yt_dlp


# ═══════════════════════════════════════════════════════════════
#  YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════

def _fmt_duration(seconds) -> str:
    """Saniyeyi MM:SS veya HH:MM:SS formatına çevirir."""
    if not seconds:
        return "--:--"
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


# ═══════════════════════════════════════════════════════════════
#  FORMAT & KALİTE EŞLEMELERİ
# ═══════════════════════════════════════════════════════════════

AUDIO_FORMATS = {"MP3", "FLAC", "WAV", "AAC", "OGG", "M4A (iOS)"}

FORMAT_CODEC = {
    "MP3":       "mp3",
    "FLAC":      "flac",
    "WAV":       "wav",
    "AAC":       "m4a",
    "OGG":       "vorbis",
    "M4A (iOS)": "m4a",   # iOS ile tam uyumlu — native AAC/M4A akışı
}

QUALITY_KBPS = {
    "En İyi":   "0",
    "320 kbps": "320",
    "256 kbps": "256",
    "192 kbps": "192",
    "128 kbps": "128",
}


# ═══════════════════════════════════════════════════════════════
#  PLAYLİST BİLGİSİ ÇEKME
# ═══════════════════════════════════════════════════════════════

def fetch_playlist_info(url: str) -> list:
    """
    Bir YouTube URL'sinden playlist/video bilgilerini çeker.
    İndirme yapmaz; yalnızca metadata (başlık, kanal, süre) döner.

    Returns:
        list[dict] — Her eleman: id, title, channel, duration, url, video_id
    Raises:
        ValueError — URL geçersizse veya bilgi alınamazsa
    """
    ydl_opts = {
        "quiet":         True,
        "no_warnings":   True,
        "extract_flat":  "in_playlist",
        "skip_download": True,
        "ignoreerrors":  True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if not info:
        raise ValueError("URL'den bilgi alınamadı. URL'yi kontrol edin.")

    entries = info.get("entries") or [info]
    result: list = []

    for i, entry in enumerate(entries, 1):
        if not entry:
            continue

        video_id = entry.get("id") or ""
        channel  = (
            entry.get("channel")
            or entry.get("uploader")
            or info.get("channel")
            or info.get("uploader")
            or "Bilinmiyor"
        )
        # Playlist flat extraction'da URL bazen sadece ID olabilir;
        # tam URL'yi güvenli biçimde oluştur.
        video_url = (
            entry.get("webpage_url")
            or (f"https://www.youtube.com/watch?v={video_id}" if video_id else "")
        )

        result.append({
            "id":       i,
            "title":    entry.get("title") or f"Video {i}",
            "channel":  channel,
            "duration": _fmt_duration(entry.get("duration")),
            "video_id": video_id,
            "url":      video_url,
        })

    if not result:
        raise ValueError("Playlist'te indirilebilir video bulunamadı.")

    return result


# ═══════════════════════════════════════════════════════════════
#  VİDEO İNDİRME
# ═══════════════════════════════════════════════════════════════

def download_videos(
    items:            list,
    output_dir:       str,
    fmt:              str,
    quality:          str,
    on_item_start:    callable,
    on_item_progress: callable,
    on_item_done:     callable,
    cancel_event:     threading.Event,
) -> None:
    """
    Verilen video listesini sırayla indirir.

    Callback imzaları:
        on_item_start(idx: int, title: str)
            — İndirme başladığında çağrılır.

        on_item_progress(idx: int, pct: float, speed: str)
            — İndirme ilerlemesi; pct: 0.0 – 1.0

        on_item_done(idx: int, success: bool, error_msg: str)
            — Video tamamlandığında veya hata oluştuğunda çağrılır.
              Hata durumunda error_msg dolu gelir.

    cancel_event.set() çağrısıyla indirme durdurulabilir.
    """
    is_audio = fmt in AUDIO_FORMATS
    codec    = FORMAT_CODEC.get(fmt, "mp3")
    q        = QUALITY_KBPS.get(quality, "0")
    tmpl     = f"{output_dir}/%(title)s.%(ext)s"

    for idx, item in enumerate(items):
        if cancel_event.is_set():
            break

        on_item_start(idx, item["title"])

        # Progress hook (her video için closure)
        def _make_hook(i: int):
            def hook(d: dict):
                if cancel_event.is_set():
                    raise yt_dlp.utils.DownloadError("Kullanıcı durdurdu")
                if d.get("status") == "downloading":
                    raw = d.get("_percent_str", "0%").strip().rstrip("%")
                    try:
                        pct = float(raw) / 100.0
                    except ValueError:
                        pct = 0.0
                    speed = d.get("_speed_str", "").strip()
                    on_item_progress(i, pct, speed)
            return hook

        ydl_opts: dict = {
            "quiet":          True,
            "no_warnings":    True,
            "outtmpl":        tmpl,
            "progress_hooks": [_make_hook(idx)],
            "noprogress":     False,
            "concurrent_fragment_downloads": 4,
        }

        if fmt == "M4A (iOS)":
            # YouTube'un native m4a/aac akışını al (yeniden kodlama olmaz → iOS uyumlu)
            ydl_opts["format"] = "bestaudio[ext=m4a]/bestaudio[acodec=aac]/bestaudio"
            ydl_opts["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": "m4a", "preferredquality": q},
                {"key": "FFmpegMetadata", "add_metadata": True},
            ]
        elif is_audio:
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [
                {
                    "key":              "FFmpegExtractAudio",
                    "preferredcodec":   codec,
                    "preferredquality": q,
                },
                {"key": "FFmpegMetadata", "add_metadata": True},
            ]
        else:  # MP4
            ydl_opts["format"] = (
                "bestvideo[ext=mp4]+bestaudio[ext=m4a]"
                "/bestvideo+bestaudio/best"
            )
            ydl_opts["merge_output_format"] = "mp4"

        try:
            url = item.get("url") or item.get("video_id") or ""
            if not url:
                raise ValueError(f"'{item['title']}' için URL bulunamadı.")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            on_item_done(idx, True, "")
        except Exception as exc:
            if cancel_event.is_set():
                break
            # Hata mesajını temizle; yt-dlp bazen çok uzun mesaj döner
            err = str(exc).strip().split("\n")[0][:150]
            on_item_done(idx, False, err)
