# AGENTS.md — bu repoda çalışacak ajan için giriş noktası

Bu dosyayı ilk sen oku. Sonra sırasıyla `docs/handoff/` altındaki dosyalara geç.

## Proje tek cümlede
**AI hakemli emanet (escrow):** iş veren parayı akıllı kontrata kilitler, iş yapan teslimatı gönderir,
birbirinden bağımsız 3 AI hakem teslimatı şartnameye göre değerlendirip oyunu kendi cüzdanıyla zincire yazar.
2/3 çoğunluk parayı ya iş yapana gönderir ya da iş verene iade eder. Çoğunluğa ters oy veren hakemin teminatı kesilir.

Bağlam: Monad Blitz İstanbul (26 Eylül 2026), tek günlük hackathon, katılımcı oylaması, slaytsız canlı demo.
Geliştirici: Furkan (AI + gömülü sistemler geçmişi, web3'te yeni). Konuşma dili Türkçe.

## Okuma sırası
1. `docs/handoff/01-STATUS.md` — ne bitti, ne doğrulandı, ne doğrulanmadı
2. `docs/handoff/02-ARCHITECTURE.md` — bileşenler ve veri akışı
3. `docs/handoff/03-CONTRACT.md` — kontratın tam referansı ve değişmezleri
4. `docs/handoff/04-DECISIONS.md` — neden bu fikir, neden bu tasarım, neler reddedildi
5. `docs/handoff/05-NEXT-STEPS.md` — öncelikli yapılacaklar
6. `docs/handoff/06-RUNBOOK.md` — komutlar ve sorun giderme

## Dosya haritası
```
contracts/AIEscrow.sol   Solidity 0.8.28 kontrat (tek kontrat)
build/AIEscrow.json      derlenmiş abi + bytecode (commit'li; kontrat değişirse yeniden üret)
compile.js               solc-js ile derleme → build/AIEscrow.json
chain.py                 web3.py yardımcıları (bağlantı, gas'lı gönderim, .env okuma/yazma)
deploy.py                deploy + 3 hakem cüzdanı üretme/fonlama + dashboard/config.js üretme
judge.py                 hakem node'u (anthropic | openai | gemini | mock, --corrupt)
demo.py                  CLI: setup / run good|bad|inject / create / submit / status
dashboard/index.html     büyük ekran (ethers v6 UMD yerel dosya, config.js deploy'da üretilir)
test_escrow.py           kontrat testleri (eth-tester, internetsiz)
docs/                    handoff paketi + mimari PDF
```

## Kesin kurallar
- **Gizli anahtarları asla commit etme.** `.env`, `judge*.env` gitignore'da. Yalnızca `.env.example` repoda.
- Kontratı değiştirirsen: `node compile.js` → `python test_escrow.py` (7/7 geçmeli) → gerekirse test ekle.
- Kontrat değişince ABI değişirse `dashboard/index.html` içindeki insan-okur ABI dizisini de güncelle.
- Oylama sayımı **zincirde** kalmalı. Oyları zincir dışında sayıp tek yetkili adresten ödeme yapan bir tasarıma geçme; fikrin tüm gerekçesi bu (bkz. 04-DECISIONS.md).
- Monad gas'ı verilen **limite** göre keser: işlemleri `chain.send()` üzerinden gönder (tahmin × 1.15).
- Python ≥ 3.10 (`str | None` sözdizimi kullanılıyor).
- Arayüz metinleri Türkçe; kod tanımlayıcıları İngilizce.

## Hızlı doğrulama
```bash
pip install "web3[tester]" requests
python test_escrow.py          # 7 test geçti
```
