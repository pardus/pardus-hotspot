[🇹🇷](./README_TR.md) [🇬🇧](./README.md)

# Pardus Kablosuz Erişim Noktası

## Giriş
Bu uygulama, Linux sistemleri için tasarlanmış olup, kullanıcıların Wi-Fi hotspot'u kolayca oluşturmasını ve yönetmesini sağlar.
Grafiksel bir arayüze sahip olup, ağ ayarlarının konfigürasyonunu ve yönetimini kolaylaştırır.

## Kurulum

### Önkoşullar
- Sisteminizde NetworkManager ve Python 3.x'in yüklü olduğundan emin olun.
- Uygulamanın NetworkManager ile etkileşimde bulunabilmesi için D-Bus Python bağlantıları gereklidir.

### Kullanım
- Depoyu klonlayın:

    ```
    git clone https://git.pardus.net.tr/emel.ozturk/pardus-hotspot-app.git
    ```

- Uygulamayı başlatmak için şunu çalıştırın:
    `python3 Main.py`

### Arayüz

Hotspot aktif değilken:

<img src="screenshots/disable.png" alt="Hotspot Devre Dışı" width="500" height="auto"/>

Hotspot aktifken:

<img src="screenshots/enable.png" alt="Hotspot Etkin" width="500" height="auto"/>

Ayarların konfigürasyonu:

<img src="screenshots/settings.png" alt="Hotspot Ayarları" width="500" height="auto"/>

### Hotspot Konfigürasyonu
- Arayüz, SSID, bağlantı adı, parola ve diğer ağla ilgili konfigürasyonları ayarlamanıza olanak tanır.

## Geliştirici Notları
`MainWindow.py`, uygulamanın giriş noktası olarak hareket eder. Sistemin ağ yönetimiyle etkileşimde bulunmak için `hotspot.py`'ı kullanır.
`network_utils.py`, bilgisayarda bulunan Wi-Fi kartlarını listeleme ve Wi-Fi durumunu alma gibi işlemler için kullanılır.

___
## Yapılacaklar
- [x] Ağ arayüzlerinin dinamik olarak alınması
- [x] Önemli hatalar için stack sayfası
- [x] Farklı şifreleme yöntemleri için destek ekleme
- [x] Hata yönetimi ve kullanıcı geri bildirimlerini geliştirme
- [ ] Uygulamanın sanal makinede çalışıp çalışmadığını kontrol etme
- [x] Wi-Fi'nin açık olup olmadığını kontrol etme
- [x] iPhone'lar için bağlantıyı etkinleştirme
- [x] Wi-Fi sinyali kaybolduğunda bağlantıyı otomatik olarak devre dışı bırakma
- [x] Kullanıcı, hotspot penceresini kapatmak istediğinde bağlantıyı kaldırma
- [x] Tam ekran modunu devre dışı bırakma
- [x] Hakkında ve ayarlar butonları arasında geçiş yaparken oluşan donma
  sorununu düzeltme
- [ ] Uygulamanın sanal makinede çalışıp çalışmadığını kontrol etme
- [ ] Hotspota bağlı cihaz sayısını kontrol etme
- [ ] Bağlı cihaz bilgilerini gösterme
- [ ] Gizli parametre ekleme (sadece belirli cihazlara hotspot bağlantısını gösterme)
- [ ] QR özelliği ekleme

__NOT :__ GitHub'a uygulama eklenirken __Yapılacaklar__ kısmını silelim,
__URL__'i güncelleyelim.
