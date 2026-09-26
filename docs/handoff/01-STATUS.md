# 01 — Durum (26 Eylül 2026, ~12:20)

## Özet
Çalışan bir MVP var: kontrat, 3 hakem node'u, deploy/demo script'leri ve canlı ekran.
Uçtan uca akış **yerel test zincirinde** (Hardhat, chainId 31337) doğrulandı.
**Monad testnet'te ve gerçek LLM'lerle henüz çalıştırılmadı.**

## Tamamlananlar
| Parça | Durum | Nasıl doğrulandı |
|---|---|---|
| `AIEscrow.sol` | bitti | `test_escrow.py` 7/7 geçiyor |
| 2/3 oy ile ödeme / iade | bitti | test + yerel e2e |
| Çoğunluğa ters oyda teminat kesme (hem önce hem geç gelen oy) | bitti | test + yerel e2e |
| Teminatı yetmeyen hakemin oyunu reddetme | bitti | test; e2e'de yakalandı, judge.py otomatik tamamlıyor |
| `judge.py` (mock sağlayıcı) | bitti | yerel e2e: good→ödeme, bad→iade+ceza, inject→red |
| `judge.py` anthropic/openai/gemini | yazıldı | **denenmedi** (API anahtarı yoktu) |
| `deploy.py --gen-judges` | bitti | yerel zincirde |
| `demo.py` | bitti | yerel zincirde |
| `dashboard/index.html` (editoryal "karar belgesi" tasarımı) | bitti | Playwright ekran görüntüsüyle kontrol edildi |
| GitHub | yüklendi | `main` dalı |

## Doğrulanmamış riskler (öncelik sırasıyla)
1. **Monad testnet deploy'u.** Kontrat `evmVersion: cancun` ile derlendi. Monad testnet'in bunu kabul ettiği varsayılıyor. Deploy hata verirse `compile.js` içinde `evmVersion` değerini `"paris"` yapıp yeniden derle.
2. **Gerçek LLM çağrıları.** Varsayılan model adları (`claude-haiku-4-5-20251001`, `gpt-4.1-mini`, `gemini-2.5-flash`) güncelliğini yitirmiş olabilir. Hata alınırsa `.env` içinde `MODEL=` ile değiştir.
3. **RPC limitleri.** Public RPC saniyede 20–50 istek. Dashboard 1 sn'de bir, 3 hakem 1,5 sn'de bir sorguluyor. Toplamda sınırda kalabilir. Gerekirse `--interval` değerini artır ya da hakemlere farklı RPC ver (Ankr, monadinfra).
4. **eth_getLogs aralığı.** Dashboard aralığı 90 bloklık parçalara bölerek tarıyor. Sayfa açıldığında yalnızca son ~90 bloğu gösteriyor.
5. **Faucet miktarı.** Varsayılan tutarlar küçük (teminat 0.01, ceza 0.005, iş 0.01, hakem başı 0.03 MON). Deploy cüzdanında en az ~0.15 MON olmalı.

## Test ortamında görülen ve düzeltilen hata
Rüşvetli hakemin teminatı kesildikten sonraki oyunda kontrat `StakeTooLow` ile reddetti. Bu doğru davranış. `judge.py` artık oy vermeden önce eksik teminatı otomatik tamamlıyor.

## Bilinçli olarak yapılmayanlar
- Hakem kaydı açık değil. 3 hakem deploy anında sabitleniyor.
- Zaman aşımı, itiraz ve hakem değişimi yok.
- Teslimat zincirde düz metin olarak tutuluyor (IPFS yok).
- Teminat çekme serbest, bekleme süresi yok.
- Kitleden QR ile teslimat gönderme arayüzü yok. Teslimatlar `demo.py` ile gönderiliyor.
