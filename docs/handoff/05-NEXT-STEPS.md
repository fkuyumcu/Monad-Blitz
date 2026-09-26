# 05 — Sıradaki adımlar

## P0 — Demodan önce (bugün)
- [ ] Monad testnet'e deploy et: `python deploy.py --bots 3 --commit 60 --reveal 45`. Hata verirse `evmVersion: "paris"`.
- [ ] Gas maliyetini gör (deploy çıktısında gasPrice var). `python cards.py 10 --url ...` için bakiye yetiyor mu kontrol et.
- [ ] Telefon sayfasını yayınla: GitHub Pages (main/root). `app/config.js` ve `dashboard/config.js` dosyalarını commit'le (anahtar içermez). Kart linki: `https://fkuyumcu.github.io/Monad-Blitz/app/`.
- [ ] Botları başlat (2 dürüst + 1 lazy). Mümkünse bir dürüst botu gerçek bir LLM ile çalıştır.
- [ ] Kendi telefonunla bir kartı okut ve tam bir tur dene: katıl → görev → puan → mühür → açılış → isabet.
- [ ] `run good` ve `run bad` ile iki kez prova yap.

## P1 — Vakit kalırsa
- [ ] Dashboard'a salondakilerin okutacağı büyük bir "Değerlendirici ol" QR'ı ekle (sıradaki kartı gösteren kiosk modu).
- [ ] Freelancer tarafında teslimattan sonra canlı durum göstergesi.
- [ ] Telefonda açma aşaması gelince titreşim veya bildirim (`navigator.vibrate`).

## P2 — Metropolis (13 Ekim)
- [ ] **Tuzak görevler:** Doğru puanı bilinen gizli işler. Tembel ya da taraflı değerlendiriciyi yakalar. Çoğunluk ≠ doğruluk sorununun asıl çözümü.
- [ ] **İtiraz turu:** Freelancer ya da iş veren teminat koyup 5 kişilik ikinci tura götürebilir. İlk turda yanlış karar verenler daha ağır ceza yer.
- [ ] VRF ile atama. Teminat ve itibar ağırlıklı seçim.
- [ ] Rubrik: birden çok kriter (doğruluk, biçim, zamanında teslim), kriter başına medyan.
- [ ] Pull-payment, değerlendirici başına eşzamanlı iş sınırı, teminat kilidi süresi.
- [ ] Teslimat için IPFS ve hash. Yorumlar da istenirse şifreli tutulabilir.
- [ ] Taşınabilir itibar: başka platformların okuyabileceği bir arayüz.
- [ ] Foundry'ye geçiş, fuzz ve invariant testleri.
