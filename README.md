# Metrom Nerede

İstanbul metro ve tramvay hatlarında **canlı sefer bilgisi** gösteren, açık kaynak mobil uygulama ve backend projesi.

![Platform](https://img.shields.io/badge/platform-iOS%20%7C%20Android-blue)
![React Native](https://img.shields.io/badge/React%20Native-0.73-61dafb)
![Backend](https://img.shields.io/badge/backend-Flask-000000)

---

## Özellikler

- **Metrolar:** M1A, M1B, M2, M3, M4, M5, M6, M7, M8, M9 hat listesi ve duraklar
- **Tramvaylar:** T1, T3, T4, T5 hat listesi ve duraklar
- **Canlı sefer:** Durağa tıklayınca o duraktan kalkan sonraki seferler (yön bazlı, dakika)
- **Sade arayüz:** Koyu tema, hızlı gezinme

Veri kaynağı: Metro İstanbul (canlı API) + proje içi hat/durak JSON'ları.

---

## Proje yapısı

```
├── MetroMNerede/          # React Native mobil uygulama (iOS & Android)
│   ├── src/
│   │   ├── screens/       # Ekranlar (Home, Lines, Stations, StationDepartures)
│   │   ├── api.ts         # Backend API client
│   │   └── navigation/
│   ├── ios/
│   └── android/
├── backend/               # Flask API sunucusu
│   ├── app.py             # Ana uygulama ve endpoint'ler
│   ├── live_metro.py      # Metro İstanbul canlı sefer istekleri
│   ├── veriler_loader.py  # Metro hat/durak verisi (metro-lines.json)
│   ├── tram_loader.py     # Tramvay hat/durak verisi (tram-lines.json)
│   └── requirements.txt
├── metro-lines.json       # Metro hat ve durak verisi
└── tram-lines.json        # Tramvay hat ve durak verisi
```

---

## Kurulum

### Gereksinimler

- **Node.js** ≥ 18
- **Python** 3.8+
- **iOS:** Xcode, CocoaPods
- **Android:** Android Studio, JDK 17

### 1. Backend'i çalıştırma

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

API varsayılan olarak **http://127.0.0.1:5000** adresinde çalışır.

### 2. Mobil uygulamayı çalıştırma

```bash
cd MetroMNerede
npm install
npm start
```

Başka bir terminalde:

- **iOS:** `npm run ios` (veya Xcode'dan çalıştır)
- **Android:** `npm run android`

**Gerçek cihazda test:** Telefon ve bilgisayar aynı Wi‑Fi'de olmalı. `MetroMNerede/src/api.ts` içinde `DEV_BACKEND_IP` değişkenini bilgisayarınızın yerel IP'siyle güncelleyin (örn. `192.168.1.42`). Android emülatörde backend `10.0.2.2:5000` olarak ayarlıdır.

---

## API özeti

| Endpoint | Açıklama |
|----------|----------|
| `GET /api/health` | Sağlık kontrolü |
| `GET /api/veriler/lines` | Metro hat listesi |
| `GET /api/veriler/lines/<code>/stations` | Metro hattı durakları |
| `GET /api/tram/lines` | Tramvay hat listesi |
| `GET /api/tram/lines/<code>/stations` | Tramvay hattı durakları |
| `GET /api/live/departures` | Durak için canlı seferler (query: `line`, `station`, `type=metro\|tram`) |

---

## Katkıda bulunma

1. Repoyu fork'layın.
2. Yeni bir branch açın: `git checkout -b feature/amazing`.
3. Değişikliklerinizi commit'leyin: `git commit -m 'feat: ...'`.
4. Branch'i push'layın: `git push origin feature/amazing`.
5. GitHub'da Pull Request açın.

Hata bildirimi ve özellik istekleri için **Issues** kullanabilirsiniz.

---

## Lisans

Bu proje açık kaynak olarak paylaşılmaktadır.

---

**Metrom Nerede** — İstanbul'da metro ve tramvay seferlerini hızlıca görmenin pratik yolu.
