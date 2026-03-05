# Ahtabyte Mobile - Günlük Rapor Görüntüleyici

Flutter ile geliştirilmiş, **günlük rapor PDF görüntüleyici ve not alma** uygulaması.

## Özellikler

- **Yüksek kalitede UI/UX**
  - Koyu tema, gradient arkaplan, cam efekti (glassmorphism) hissi
  - Günler arasında hızlı geçiş için yatay kaydırmalı tarih çipleri
- **PDF görüntüleme**
  - Her gün için ayrı PDF rapor
  - Pinch-to-zoom ve kaydırma desteği (`pdfx` paketi ile)
  - Önceki / sonraki sayfa kısayol butonları
- **Günlük notlar**
  - Her gün için ayrı not alanı
  - Otomatik kaydediliyormuş gibi akan UI (in-memory)

## Kurulum

1. Proje klasöründe bağımlılıkları kur:

```bash
flutter pub get
```

2. PDF dosyalarını ekle:

- `assets/reports/` klasörünü oluştur.
- Dosya isimlerini şu formatta ekle:
  - `report_YYYY-MM-DD.pdf` (örn. `report_2026-03-05.pdf`)
- `pubspec.yaml` içinde zaten şu tanım mevcut:

```yaml
flutter:
  uses-material-design: true
  assets:
    - assets/reports/
```

3. Uygulamayı çalıştır:

```bash
flutter run
```

## Notlar

- Örnek olarak son 7 gün için sahte rapor kayıtları oluşturuluyor.
- Gerçek API / backend entegrasyonu için:
  - `DailyReport` modelini genişletip
  - PDF dosya yollarını ve notları servis üzerinden besleyebilirsin.

