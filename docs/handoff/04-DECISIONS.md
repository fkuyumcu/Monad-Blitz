# 04 — Kararlar ve gerekçeleri

## PİVOT (12:30): AI hakemli emanet → Kurul (insan değerlendirici havuzu, puanlı)
Furkan'ın itirazı: "AI modelleri neden teminat koysun, kaybedecekleri ne?" Teminatı aslında modeli çalıştıran operatör koyuyor, ama bir LLM kötü niyetle değil rastgele hata yapıyor. Dürüst ama yanılan bir modeli cezalandırmak şans cezası oluyor. Teminat mekanizması, bilerek hile yapabilen insanlar için anlamlı.
Yeni fikir, Mercor benzeri bir freelance değerlendirme sistemi: bir işi tek amir yerine birbirinden bağımsız 3 değerlendirici kontrol ediyor, değerlendiriciler isabetli oldukça kazanıyor, sapınca kaybediyor.

**Furkan'ın vurgulamak istediği mimari karar:** Merkezi sistemlerde geri bildirimler bir sunucuda durur ve üst yönetim tarafından değiştirilebilir. Burada her puan ve yorum geri alınamaz bir işlemdir ve karar çoğunluğun uzlaşısıyla (medyan) uygulanır. Bu iddianın doğru olması için kontratta owner veya admin yok, upgradeable proxy yok, yorum da mühürün içinde (sonradan değiştirilemez). Yanlış bir karar kaydı düzeltilmez; ancak itiraz gibi yeni bir işlemle üstüne yazılabilir ve eski kayıt görünür kalır.

Tasarım seçimleri:
- **Evet/hayır yerine 1–10 puan** (Furkan onayladı). Freelance işte ikili karar kaba kalıyor.
- **Medyan:** Tek sapkın puana dayanıklı.
- **Değerlendirici ödemesi medyana yakınlıkla ağırlıklı** (Furkan'ın önerisi): ağırlık 3/2/1, ≥3 sapmada ceza. Kesinti isabetlilere gider, böylece dürüstlük doğrudan kazandırır.
- **Commit-reveal:** Bağımsızlık iddiası için şart, yoksa ikinci oy veren ilkini kopyalar.
- **Rastgele atama, iş veren ve freelancer hariç:** Tarafların kendi değerlendiricisini seçip anlaşmasını zorlaştırır.
- **Açık iş (`worker = 0`):** Salondan biri freelancer olabilsin diye.
- **Fonlanmış QR kartlar:** Katılımcı cüzdanına gas dağıtmak için faucet sunucusu yerine önceden fonlanmış burner anahtarlar. Anahtar URL'nin `#` kısmında durduğu için sunucuya gitmiyor ve sayfa statik barındırılabiliyor.
- **Botlar kalıyor:** AI artık hakem değil, havuzdaki değerlendiricilerden biri (ve bekçi). Az katılımcıda havuzu dolduruyor. Tembel bot, ceza mekanizmasını canlı göstermek için kullanılıyor.
- **Çözülmemiş sorun (dürüstçe söylenmeli):** Çoğunluk doğruluk demek değil. Herkes tembelce 10 verirse sistem bunu yakalayamaz. Çözüm: doğru cevabı bilinen tuzak görevler ve itiraz turu (yol haritasında).

---
Aşağısı pivot öncesi (AIEscrow) kararları, tarihçe olarak duruyor.

## Fikrin evrimi (neden bu fikir)
1. **Marina (İskele):** Bluetooth mesh ile haberleşen pedestallar ve zincirde ödeme. Donanım gerektirdiği için bir güne sığmadı, Furkan da Blitz için başka bir fikir aradı.
2. **Canlılık kanıtlı insan kimliği ve ajan yetkisi:** Furkan'ın kimlik doğrulama (openMRZ, NFC, yüz eşleme) geçmişine uyuyordu. Ancak ajan ve zk-passport kavramları karışık bulundu. "Doğrulayıcıları neden tek node'da tutmayalım?" sorusuna tatmin edici bir cevap bir güne sığmadı.
3. **Deprem sinyali / sensör ağı:** Monad'ın hızını gerçekten kullanıyordu, ama Furkan finansal bir fikir istedi.
4. **Hile yapılamayan arkadaş bahsi:** Furkan "saçma" buldu. Benzer bir proje London Blitz'te de yapılmıştı.
5. **AI hakemli emanet ← SEÇİLDİ.** Furkan'ın koşulu: Monad'a özgü olması şart değil, EVM kullanımının mantıklı olması yeterli.

## Neden blockchain burada zorlama değil
- Birbirine güvenmeyen iki taraf var ve parayı tutacak güvenilir bir aracı yok. Kontrat emanetçi görevini görüyor.
- Karar tek bir hakeme bağlı değil. Oy sayımı ve ceza zincirde herkesin görebileceği şekilde yapılıyor. Tek bir hakem satın alınsa bile sonuç değişmiyor.
- Dürüst sınır: Üç hakemi tek bir kişi çalıştırırsa merkeziyetsizlik sahte olur. Demoda hakemleri salondan farklı kişilere çalıştırmak bu yüzden önerildi (`deploy.py --judges`).

## Başka bir AI'ın önerileri ve verilen cevaplar
| Öneri | Karar | Gerekçe |
|---|---|---|
| Kontrat "aptal" kalsın, tek yetkili adres ödeme yapsın, oylama zincir dışında sayılsın | **Reddedildi** | Tek güven noktası yaratır, fikrin özünü yok eder. Onun yerine her hakem kendi oyunu yazıyor, sayım zincirde (~40 satır). |
| 3 hakeme farklı roller (format / kalite / güvenlik) | **Reddedildi** | Aynı soruya oy vermeyince 2/3 çoğunluk anlamsızlaşır. Onun yerine aynı soru, farklı sağlayıcılar. |
| Rastgele etiketlerle çevrili teslimat + katı JSON çıktı | **Kabul edildi** | `judge.py` içinde uygulandı. |
| Regex ile injection filtresi | Kısmen | Kolay atlatılır. Sadece mock hakemde var, asıl savunma sistem prompt'u. |
| Demo görsel olarak sönük kalır | **Kabul edildi** | Büyük ekran dashboard'u yapıldı. |
| Alternatif: mempool'da AI radarı / front-running koruması | **Reddedildi** | LLM gecikmesi 0,4 sn'lik bloktan uzun, başkasının işlemi iptal edilemez, front-running etik açıdan tartışmalı. |

## Teknik seçimler
- **Solidity + Python + solc-js.** Foundry kurulumu çalışma ortamında engellendi. Furkan Python'a alışkın. Rust gerekmiyor (Monad EVM uyumlu).
- **Durum sorgusu (hakemlerde) / parçalı getLogs (dashboard'da).** Public RPC'lerin getLogs aralık sınırlarına takılmamak için.
- **Açık gas limiti.** Monad gas'ı verilen limite göre kestiği için tahmin × 1.15 + 5000.
- **Kesilen teminat haklı çıkan tarafa gider.** Demoda "rüşvetçinin parası iş verene geçti" diye anlatılabiliyor.
- **Geç gelen ters oy da cezalandırılıyor.** Aksi halde bir hakem hep son sırada oy verip riskten kaçabilirdi.
- **Demo görevi nesnel seçildi:** fişten toplam tutar (doğru cevap 57,50 TL). Öznel işlerde AI kararı tartışmalı olur.

## Tasarım dili (dashboard)
Editoryal "resmî karar belgesi": krem kâğıt zemin, Fraunces serif başlıklar, IBM Plex Mono ile veri, sıfır köşe yuvarlaması, çizgilerle ayrılan bölümler, KABUL / RET mühürleri, cezalı hakemin adının üstü çizili.
Gerekçe: "AI yapmış" görüntüsünün tersi (mor gradyan, Inter, 16px yuvarlak kartlar yok), hakem ve karar konseptine oturuyor, projeksiyonda açık zemin daha iyi okunuyor.
Elenenler: glassmorphism ve claymorphism (AI şablonu dili), neobrutalizm (fazla yaygınlaştı), terminal (klişe riski), bento (bu kadar az bilgiye fazla).
