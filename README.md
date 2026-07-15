# Music Downloader

YouTube video ve playlist indirici — Windows masaüstü uygulaması.

## Nasıl çalıştırılır?

1. [Python](https://www.python.org/downloads/) kur (Windows için “Add python.exe to PATH” işaretli olsun).
2. Bu projeyi indir veya klonla.
3. Proje klasöründe `run.bat` dosyasına çift tıkla.

İlk açılışta eksik paketler varsa:

```bash
pip install -r requirements.txt
```

## FFmpeg (gerekli)

Ses formatları (MP3, M4A vb.) için FFmpeg gerekir.

1. İndir: [FFmpeg Windows builds](https://www.gyan.dev/ffmpeg/builds/) → **ffmpeg-release-essentials.zip**
2. Kutuyu aç, içindeki `bin` klasörünü PATH’e ekle  
   veya [kurulum rehberi](https://www.gyan.dev/ffmpeg/builds/#release-builds) adımlarını izle.
3. Uygulamayı yeniden başlat.

Resmi site: [ffmpeg.org/download.html](https://ffmpeg.org/download.html)

## Kullanım

1. YouTube video veya playlist linkini yapıştır → **Getir**
2. Format, kalite ve klasörü seç
3. Parçaları işaretle → **İndir**
4. İstersen **Durdur** / **Devam Et**
5. Bittiğinde klasörü açmak isteyip istemediğin sorulur

Daha kısa anlatım uygulama içinde: menü → **Kılavuz**.

## Not

Yalnızca kendi içeriğinizi veya indirme izniniz olan materyali kullanın.
