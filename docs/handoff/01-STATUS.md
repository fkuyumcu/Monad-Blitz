# 01 — Durum (26 Eylül 2026, ~13:00)

## Özet
Kurul çalışır durumda: kontrat, telefon sayfası, büyük ekran, bot değerlendiriciler, QR kart üretimi.
Uçtan uca akış **yerel test zincirinde** (Hardhat, 1 sn blok) doğrulandı, **Monad testnet'te henüz çalıştırılmadı.**

## Doğrulananlar
| Parça | Nasıl |
|---|---|
| `PeerReview.sol` | `test_review.py` 13/13: tam/kısmi ödeme, ağırlıklı ücret, sapana ceza, mühür korumaları, zaman aşımı yolları, oy vermeyene ceza, teminat kilidi, iptal, cezalı değerlendiricinin havuz dışı kalması, iş veren/freelancer'ın atanmaması, açık iş |
| Telefon sayfası | Playwright (390px): kart linkiyle açıldı → teminat yatırdı → görev geldi → 9 puan + yorum → mühürledi → otomatik açtı → "İSABET" |
| Büyük ekran | Doğru teslimat (9/9/9 → tam ödeme) ve yanlış teslimat + tembel bot (10/3/3 → medyan 3, %30 ödeme, bot −0,001 MON) senaryoları |
| Botlar | mock sağlayıcı, honest ve lazy modları, teminat tamamlama |
| `deploy.py`, `demo.py`, `cards.py` | yerel zincirde |

## Doğrulanmayanlar (risk sırasıyla)
1. **Monad testnet deploy'u** (viaIR + cancun). Hata verirse `compile.js` içinde `evmVersion: "paris"`.
2. **Gas maliyeti / faucet.** `deploy.py` ve `cards.py` kart başına bütçeyi `gasPrice × 350k × işlem × 1.3` olarak hesaplıyor. Testnet gas fiyatına göre kart başı tutar büyüyebilir. Bakiye yetmezse `--actions` değerini düşür.
3. **Gerçek LLM'ler** (`PROVIDER=anthropic|openai|gemini`) denenmedi. Model adları eskiyebilir, `MODEL=` ile değiştirilebilir.
4. **Public RPC limitleri.** Telefonlar 2,5 sn, ekran 1,2 sn, botlar 2 sn aralıkla sorguluyor. Çok katılımcıda 429 gelebilir. Gerekirse aralıkları artır ya da farklı RPC kullan.
5. **Telefon sayfasının barındırılması.** Salon Wi-Fi'ı cihazları birbirinden yalıtıyorsa yerel IP çalışmaz. GitHub Pages önerilir.
6. **Süreler.** Varsayılan mühür 150 sn, açma 90 sn. Demo için kısaltılabilir (`deploy.py --commit 60 --reveal 45`).

## Bilinen küçük sorunlar
- Hardhat'ta telefon sayfası bir kez "nonce too low" verdi. Nonce artık her işlemde `pending` olarak açıkça alınıyor. Sayfa hatayı yakalayıp bir sonraki turda tekrar denediği için akışı bozmadı.
- `reviewer_bot.py` web3'ün "MismatchedABI" uyarısını basıyor (aynı makbuzdaki başka olay). Zararsız.
