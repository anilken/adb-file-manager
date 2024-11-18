# ADB File Manager

Emulatör için geliştirilmiş özel bir dosya yönetim aracıdır. ADB (Android Debug Bridge) üzerinden Emülatör instancelarına dosya aktarımı, silme ve yönetim işlemlerini kolaylaştırır.

## Özellikler

- Bağlı Adb instancelarını otomatik tespit etme
- Dosya aktarımı (PC -> Emülatör)
- Emülatördeki dosyaları listeleme
- Dosya silme
- Dosya indirme (Emülatör -> PC)
- Sürükle-bırak desteği
- Gelişmiş dosya izinleri görüntüleme

## Gereksinimler

- Python 3.8 veya üzeri
- PyQt6
- ADB (Android Debug Bridge)

## Kurulum

1. Repository'yi klonlayın:
```bash
git clone https://github.com/anilken/adb-file-manager.git
cd adb-file-manager
```

2. Gerekli Python paketlerini yükleyin:
```bash
pip install -r requirements.txt
```

3. ADB'nin sisteminizde kurulu olduğundan emin olun ve PATH'e ekleyin.

## Kullanım

1. Programı başlatın:
```bash
python main.py
```

2. Program başladığında otomatik olarak bağlı Adb instancelarını tarayacaktır.

3. İşlemler:
   - PC'den dosya yüklemek için "Dosya Seç" butonunu kullanın
   - Hedef klasörü belirtin (varsayılan: /storage/emulated/0/)
   - Bağlı cihazlar listesinden bir cihaz seçin
   - "Seçili Dosyayı Aktar" butonuna tıklayın
   - Dosyaları silmek veya PC'ye indirmek için sağ tık menüsünü kullanın

## Hata Ayıklama

Yaygın hatalar ve çözümleri:

1. ADB bağlantı hatası:
   - ADB doğru kurulu olduğunu kontrol edin
   - Emulatör çalışır durumda olduğundan emin olun
   - USB hata ayıklama modunun açık olduğunu kontrol edin

2. Dosya aktarım hatası:
   - Hedef klasörün var olduğundan emin olun
   - Yazma izinlerinin doğru olduğunu kontrol edin

## Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/NewFeature`)
3. Değişikliklerinizi commit edin (`git commit -am 'Add new feature'`)
4. Branch'inizi push edin (`git push origin feature/NewFeature`)
5. Pull Request oluşturun

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.