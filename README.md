# Music Downloader

YouTube video / playlist indirici — Windows masaüstü uygulaması (cam UI + temalar).

## Hızlı başlangıç

| Yol | Nasıl |
|---|---|
| Geliştirme | `run.bat` veya `python main.py` |
| Hazır exe | `dist\MusicDownloader.exe` |

> Exe Windows Akıllı Uygulama Denetimi (SAC) tarafından engellenebilir (imzasız). O zaman `run.bat` kullan.

## Kullanım kılavuzu

1. **Linki getir** — YouTube video veya playlist linkini yapıştır → **Getir**
2. **Ayarları seç** — Format (MP3, M4A…), kalite ve kayıt klasörü
3. **İndir** — Parçaları işaretle → **İndir**. İstersen **Durdur** / **Devam Et**
4. **Bittiğinde** — Klasörü açmak isteyip istemediğin sorulur
5. **İpuçları** — Panoya YouTube linki kopyalarsan ekleme sorusu çıkar; Tema paneli görünümü değiştirir; ayarlar otomatik kaydolur

Uygulama içinde de aynı anlatım vardır: menüden **Kılavuz**.

## Gereksinimler

- Python 3 + `requirements.txt` (geliştirme için)
- **FFmpeg** (ses dönüşümü için PATH’te olmalı)

## Ayarlar nerede?

Tema, klasör, format ve geçmiş:

`%APPDATA%\MusicDownloader\`

## Exe derleme

```bash
python build.py
```

Çıktı: `dist\MusicDownloader.exe`

## Not

Bu uygulama yalnızca kendine ait içeriği veya izinli materyali indirmek için kullanılmalıdır.
