# Kurul — merkeziyetsiz freelance değerlendirme (Monad Blitz)

Freelancer'ın işini tek bir amir değil, **havuzdan rastgele seçilen, birbirinden habersiz 3 değerlendirici** puanlar.
Puanlar ve yorumlar zincire yazılır. **Hiçbir yönetici bunları değiştiremez ya da silemez**, çünkü kontratın sahibi yok ve kontrat güncellenemez.

1. **İş veren** ödemeyi kontrata kilitler. Ödemenin %10'u değerlendirme ücreti olarak ayrılır.
2. **Freelancer** işi teslim eder. Kontrat, teminat yatırmış değerlendiriciler havuzundan rastgele 3 kişi atar. İş veren ve freelancer atanamaz.
3. **Değerlendiriciler** 1–10 arası puan ve yorum verir. Oylama **mühürlüdür (commit-reveal)**: önce puanın hash'i gönderilir, üç mühür tamamlanınca açılır. Kimse başkasının puanını görüp kopyalayamaz.
4. **Nihai puan = medyan.** Puan 8 ve üstüyse freelancer tam ödeme alır, altındaysa puan oranında alır (6/10 → %60). Kalan tutar iş verene döner.
5. **Değerlendirici kazancı isabete bağlı.** Medyana tam isabet ●●●, 1 puan fark ●●, 2 puan fark ● ağırlık alır ve ücret bu ağırlıklara göre paylaşılır. **3 puan ya da daha fazla sapan** ya da süresinde oy vermeyenin teminatından kesilir. Kesilen tutar isabetli değerlendiricilere dağıtılır.
6. **İtibar zincirde:** Her değerlendiricinin isabet oranı, iş sayısı, kazancı ve cezası herkese açık.

Ajanlar için giriş noktası: [`AGENTS.md`](AGENTS.md)

```
contracts/PeerReview.sol   kontrat (owner yok, güncellenemez)
build/PeerReview.json      derlenmiş abi + bytecode
test_review.py             13 kontrat testi (internetsiz)
chain.py                   ortak zincir yardımcıları + mühür hash'i
deploy.py                  deploy + bot cüzdanları + sayfa ayarları
cards.py                   salona dağıtılacak, fonlanmış QR cüzdan kartları
reviewer_bot.py            otomatik değerlendirici (LLM / mock / tembel / rastgele)
demo.py                    iş veren ve freelancer komutları, havuz tablosu
app/                       telefon sayfası: değerlendirici + freelancer
dashboard/                 büyük ekran: dosya, 3 değerlendirici, hüküm, itibar tablosu, tutanak
vendor/                    ethers v6 (yerel, internetsiz çalışır)
```

## Kurulum

```bash
pip install "web3[tester]" requests qrcode     # Python ≥ 3.10
python test_review.py                          # 13 test geçmeli
cp .env.example .env                           # DEPLOYER_KEY (faucet.monad.xyz'den MON alınmış)
```

Kontratı değiştirirsen: `npm install && node compile.js`

## Demo kurulumu

```bash
python deploy.py --bots 3                 # kontrat + 3 bot cüzdanı (bots/botN.env)
python demo.py setup                      # freelancer cüzdanı
python cards.py 15 --url <app adresi>     # 15 fonlanmış QR kart → cards/cards.html
```

Botları başlat (havuzu doldurur, süresi dolan işleri ilerletir):
```bash
python reviewer_bot.py --env bots/bot1.env                 # PROVIDER=anthropic|openai|gemini|mock
python reviewer_bot.py --env bots/bot2.env
python reviewer_bot.py --env bots/bot3.env --mode lazy     # bakmadan hep 10 verir → ceza yer
```

Sayfaları yayınla (repo kökünden):
```bash
python -m http.server 8080
# büyük ekran: http://localhost:8080/dashboard/
# telefon:     http://<senin-IP>:8080/app/   (ya da GitHub Pages: .../app/)
```
Telefon sayfası statik. Kontrat adresi ve cüzdan anahtarı QR linkinin `#` kısmından okunur, sunucuya gitmez. Bu yüzden GitHub Pages'te barındırılabilir (Settings → Pages → main / root). `app/config.js` ve `dashboard/config.js` dosyalarını `deploy.py` yazar. Pages'te kullanacaksan bu iki dosyayı da commit'le, içinde anahtar yok.

## Demo akışı (3 dk)

1. **Sorun:** "Freelance platformlarında işini bir amir değerlendiriyor. Puan merkezi bir sunucuda duruyor ve üst yönetim değiştirebilir, silebilir."
2. **Çözüm:** Salondakiler QR ile değerlendirici olur. `python demo.py run good` çalışır, üç kişinin telefonuna görev düşer. Puanlar mühürlü gelir, ekranda "MÜHÜRLÜ" damgası görünür, sonra aynı anda açılır.
3. **Hüküm:** Medyan, freelancer ödemesi ve isabet ücretleri ekrana düşer. "Bu karar zincirde, hiçbir yönetici değiştiremez."
4. **Ceza:** `python demo.py run bad` çalışır. Tembel bot bakmadan 10 verir, medyan 3 olur, botun adının üstü çizilir ve teminatı kesilip isabetli olanlara dağıtılır. İtibar tablosunda kırmızıya döner.
5. **Kapanış:** "Değerlendiriciler isabetli oldukça kazanıyor, taraflı ya da tembel oldukça kaybediyor. İtibar kimsenin veritabanında değil, zincirde."

## Bilinen sınırlar

- Rastgelelik `prevrandao` ile sağlanıyor. Bu demo için yeterli, gerçek sistemde VRF gerekir.
- Mühürü açmak için gereken tuz telefonun tarayıcısında saklanıyor. Açma aşamasında sayfanın bir kez açılması gerekiyor, açılmazsa kişi ceza yer.
- Çoğunluk ≠ doğruluk. Herkes tembellik ederse sistem bunu yakalayamaz. Gerçek sistemde doğru cevabı bilinen tuzak görevler ve itiraz turu gerekir (bkz. `docs/handoff/05-NEXT-STEPS.md`).
- Ödemeler push ile yapılıyor. ETH kabul etmeyen bir kontrat adresi sonuçlandırmayı kilitleyebilir, gerçek sistemde pull-payment kullanılmalı.
