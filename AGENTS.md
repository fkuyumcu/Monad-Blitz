# AGENTS.md — bu repoda çalışacak ajan için giriş noktası

Bu dosyayı ilk sen oku. Sonra sırasıyla `docs/handoff/` altındaki dosyalara geç.

## Proje tek cümlede
**Kurul — merkeziyetsiz freelance değerlendirme:** İş veren ödemeyi kontrata kilitler, freelancer teslim eder.
Teminat yatırmış havuzdan rastgele 3 değerlendirici, birbirini görmeden (commit-reveal) 1–10 puan ve yorum verir.
Nihai puan medyandır. Freelancer puana göre ödeme alır. Değerlendiriciler medyana yakınlıklarına göre ücret paylaşır,
3 puan ya da daha fazla sapan ceza yer. Kayıtlar zincirde; kontratın sahibi yok ve kontrat güncellenemez.

Bağlam: Monad Blitz İstanbul (26 Eylül 2026), tek günlük hackathon, katılımcı oylaması, canlı demo.
Geliştirici: Furkan (AI + gömülü sistemler geçmişi, web3'te yeni). Konuşma dili Türkçe.
Proje gün içinde "AI hakemli emanet"ten (AIEscrow) bu tasarıma **pivot** etti. Eski kod git geçmişinde duruyor (commit `e33960b`).

## Okuma sırası
1. `docs/handoff/01-STATUS.md` — ne bitti, ne doğrulandı, ne doğrulanmadı
2. `docs/handoff/02-ARCHITECTURE.md` — bileşenler ve veri akışı
3. `docs/handoff/03-CONTRACT.md` — kontratın tam referansı ve değişmezleri
4. `docs/handoff/04-DECISIONS.md` — neden bu fikir, neden bu tasarım, neler reddedildi
5. `docs/handoff/05-NEXT-STEPS.md` — öncelikli yapılacaklar
6. `docs/handoff/06-RUNBOOK.md` — komutlar ve sorun giderme

`docs/AI-Hakemli-Emanet-Mimari.pdf` **eski tasarıma** ait (AIEscrow). Yeni tasarım için güncellenmedi.

## Dosya haritası
```
KONTRAT.md                 kontratın sade anlatımı + canlı testnet deploy bilgileri (jüri/takım için)
contracts/PeerReview.sol   tek kontrat (Solidity 0.8.28, viaIR, cancun)
build/PeerReview.json      derlenmiş abi + bytecode (commit'li; kontrat değişirse yeniden üret)
compile.js                 contracts/*.sol → build/<Ad>.json
test_review.py             13 test (eth-tester, internetsiz)
chain.py                   web3.py yardımcıları, commit_hash, gas'lı gönderim, .env okuma/yazma
deploy.py                  deploy + bots/botN.env + app/config.js + dashboard/config.js
cards.py                   fonlanmış QR cüzdan kartları → cards/ (gitignore)
reviewer_bot.py            otomatik değerlendirici + süresi dolan işleri ilerleten bekçi
demo.py                    setup / post / run / submit / status / tick / pool
app/index.html             telefon sayfası (değerlendirici + freelancer), tarayıcıda burner cüzdan
dashboard/index.html       büyük ekran
panel/index.html           kontrol paneli: deploy, tarayıcı içi botlar, senaryolar, QR kartlar (terminalsiz demo)
vendor/ethers.umd.min.js   ethers v6
vendor/qrcode.js           qrcode-generator 1.4.4 (MIT)
```

## Kesin kurallar
- **Gizli anahtarları asla commit etme.** `.env`, `*.env` (bots dahil), `cards/`, `.bot-state/` gitignore'da.
- Kontratı değiştirirsen: `node compile.js` → `python test_review.py` (13/13) → gerekirse test ekle.
- ABI değişirse `app/index.html` ve `dashboard/index.html` içindeki insan-okur ABI dizilerini güncelle.
- Kontrata **owner, admin, pause ya da upgradeable proxy ekleme.** "Kimse değiştiremez" iddiası buna dayanıyor.
- Oylama sayımı, medyan, ödeme ve ceza **zincirde** kalmalı.
- Mühür hash'i: `keccak256(abi.encode(jobId, reviewer, score, salt, comment))`. `chain.commit_hash` ve app'teki JS aynı olmalı. Test bunu kontrol ediyor.
- Monad gas'ı verilen **limite** göre keser. Python'da `chain.send()`, JS'te `send()` (tahmin × 1.15) kullan.
- Python ≥ 3.10. Arayüz metinleri Türkçe, kod tanımlayıcıları İngilizce.
