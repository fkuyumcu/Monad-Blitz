# 05 — Sıradaki adımlar

## P0 — Demodan önce (bugün)
- [ ] Monad testnet'e deploy et (`python deploy.py --gen-judges`). Hata verirse `evmVersion: "paris"` ile yeniden derle.
- [ ] En az bir hakemi gerçek bir LLM ile çalıştır, mümkünse üç farklı sağlayıcıyla. `good`, `bad` ve `inject` senaryolarının üçünü de dene.
- [ ] Dashboard'u testnet adresiyle aç ve projektör çözünürlüğünde kontrol et.
- [ ] `inject` senaryosunda gerçek LLM'lerin reddettiğini doğrula. Onaylayan olursa `SYSTEM_PROMPT`'u sertleştir.
- [ ] Mümkünse 1–2 hakemi salondaki başka kişilere çalıştırt (`deploy.py --judges a,b,c` ile yeni deploy).
- [ ] Demoyu iki kez prova et (akış README'de).

## P1 — Vakit kalırsa (bugün)
- [ ] **Kitleden teslimat:** QR ile açılan mobil sayfa. Tarayıcıda burner cüzdan oluşturur, `submit` gönderir. Gas için bir faucet fonksiyonu ya da deployer'dan otomatik fonlama gerekir.
- [ ] Dashboard'da "Düşünüyor" kartına geçen süre sayacı ekle.
- [ ] `demo.py run` için özel metin: `demo.py run custom "metin"`.

## P2 — Metropolis'e taşınırsa (13 Ekim teslim)
- [ ] Açık hakem kaydı ve her iş için rastgele 3 hakem seçimi (VRF ya da blockhash tabanlı commit-reveal).
- [ ] **Commit-reveal oylama:** Hakemler birbirinin oyunu görüp kopyalamasın.
- [ ] Deadline ve zaman aşımında iade, askıda kalan işler için hakem değişimi.
- [ ] Pull-payment (`withdraw`) ile DoS riskini kaldır.
- [ ] Teminat kilidi: oy verilen işler kapanmadan teminat çekilemesin.
- [ ] Teslimat için IPFS/CID ve zincirde sadece hash.
- [ ] İtibar: hakemin çoğunlukla uyum oranı zincirde tutulsun.
- [ ] Ajanlar arası mikro görevler (x402 ile entegrasyon) konumlandırması.
- [ ] Foundry'ye geçiş, fuzz testleri, `nonReentrant`.
