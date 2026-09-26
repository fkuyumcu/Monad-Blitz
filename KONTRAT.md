# Kurul — Kontrat detayları

Tek kontrat: [`contracts/PeerReview.sol`](contracts/PeerReview.sol). Sahibi (owner/admin) yok, durdurulamaz, güncellenemez.
Para, değerlendirici seçimi, oy sayımı, medyan, ödeme ve ceza kontratın içinde hesaplanır.
Geliştirici referansı (fonksiyonlar, olaylar, hatalar, değişmezler): [`docs/handoff/03-CONTRACT.md`](docs/handoff/03-CONTRACT.md).

## Canlı deploy (Monad testnet)

| | |
|---|---|
| Ağ | Monad Testnet · chainId `10143` |
| RPC | `https://testnet-rpc.monad.xyz` |
| Kontrat | [`0x3495fc469BEb44b859C4cE09Ba9AaD65B25AB52D`](https://testnet.monadvision.com/address/0x3495fc469BEb44b859C4cE09Ba9AaD65B25AB52D) |
| Deploy eden / iş veren | [`0xbF86B103EB89E54DcE09Bc0Ec481b84267362771`](https://testnet.monadvision.com/address/0xbF86B103EB89E54DcE09Bc0Ec481b84267362771) |
| Deploy aracı | `panel/index.html` (kontrol paneli) |
| Derleyici | solc 0.8.28 · optimizer 200 · viaIR · evmVersion cancun |
| Explorer doğrulaması | Yapılmadı: explorer fonksiyon adlarını ve olayları ham hex gösterir. Okunur hali büyük ekranda. |

Deploy parametreleri (panelin varsayılanları):

| Parametre | Değer | Anlamı |
|---|---|---|
| `reviewerStake` | 0,002 MON | Havuza girmek için teminat |
| `slashAmount` | 0,001 MON | Her cezada teminattan kesilen |
| `feeBps` | 1000 (%10) | İş bedelinden değerlendiricilere ayrılan ücret |
| `commitWindow` | 60 sn | Mühürlü oy süresi |
| `revealWindow` | 45 sn | Oyları açma süresi |
| Sabitler | 3 değerlendirici · puan 1–10 · geçme puanı 8 · ceza sapması 3 | Kodda sabit, değiştirilemez |

## Bir işin yaşamı

1. **İş açılır** — `createJob(freelancer, şartname)`. İş veren ödemeyi gönderir, kontrat kilitler.
   %10'u değerlendirme ücreti olarak ayrılır. Freelancer adresi `0x0` ise iş herkese açıktır, ilk teslim eden freelancer olur.
2. **Teslim edilir** — `submit(id, metin)`. Kontrat havuzdan rastgele 3 değerlendirici seçer.
   İş veren ve freelancer seçilemez. Teminatı eşiğin altındaki seçilemez. Havuzda uygun 3 kişi yoksa teslim reddedilir.
3. **Mühürlü oy** — `commit(id, hash)`. Her değerlendirici puanını ve yorumunu gizli bir tuzla hash'leyip gönderir.
   Kimse diğerlerinin puanını göremez, sonradan da değiştiremez.
   `hash = keccak256(abi.encode(id, değerlendirici, puan, tuz, yorum))`
4. **Açma** — `reveal(id, puan, tuz, yorum)`. Üç mühür tamamlanınca ya da süre dolunca oylar açılır.
   Kontrat hash'in eşleştiğini kontrol eder.
5. **Sonuç** — son oy açılınca otomatik, süre dolarsa herkesin çağırabileceği `finalize(id)` ile.

## Para nasıl dağıtılır

- **Nihai puan** = açılan puanların **medyanı** (2 oy varsa ortalama, aşağı yuvarlanır).
- **Freelancer:** medyan ≥ 8 ise ödemenin tamamı, altındaysa `ödeme × medyan / 10`. Kalanı iş verene döner.
- **Ceza:** medyandan 3 ya da daha fazla sapan, mühür göndermeyen ya da mühürlediği oyu açmayan teminatından 0,001 MON kaybeder.
- **İsabet ağırlığı:** medyandan 0 sapma → 3, 1 sapma → 2, 2 sapma → 1.
- **Havuz = değerlendirme ücreti + kesilen cezalar.** Havuz isabetli değerlendiricilere ağırlıklarına göre bölünür.
  Bölmeden kalan küsurat iş verene döner. Kimse isabet etmediyse havuzun tamamı iş verene döner.
- En az 2 oy açılmadıysa karar çıkmaz: ödeme ve ücret iş verene iade edilir, oy vermeyenler ceza yer.

### Örnek: eksik teslimat (3/5 madde), tembel bot 10 veriyor

| | Puan | Sapma | Sonuç |
|---|---|---|---|
| Değerlendirici I (dürüst) | 6 | 0 | ağırlık 3 |
| Değerlendirici II (tembel) | 10 | 4 | **ceza −0,001 MON** |
| Değerlendirici III (dürüst) | 6 | 0 | ağırlık 3 |

İş veren 0,01 MON kilitledi → 0,009 ödeme + 0,001 ücret.

| Kalem | Hesap | MON |
|---|---|---|
| Medyan | 6, 6, 10 → | **6** |
| Freelancer | 0,009 × 6 / 10 | 0,0054 |
| İş verene iade | 0,009 − 0,0054 | 0,0036 |
| Havuz | 0,001 ücret + 0,001 ceza | 0,002 |
| Değerlendirici I | 0,002 × 3/6 (0,0005 ücret + 0,0005 ceza payı) | 0,001 |
| Değerlendirici III | 0,002 × 3/6 (0,0005 ücret + 0,0005 ceza payı) | 0,001 |

Giren 0,01 + 0,001 ceza = 0,011 MON · çıkan 0,0054 + 0,0036 + 0,002 = 0,011 MON.

## İtibar
Her değerlendiricinin kaydı zincirde, herkese açık: sonuçlanan iş sayısı, toplam ağırlık, kazanç ve ceza.
İsabet oranı = toplam ağırlık / (3 × iş sayısı). Büyük ekrandaki itibar tablosu buradan okunur.

## Güven modeli
- **Kontratta (kimse değiştiremez):** para, seçim, sayım, medyan, ödeme, ceza, itibar.
- **Zincir dışında:** değerlendiricinin kararı ve tuzu (telefonda ya da bot sekmesinde), arayüzler (GitHub Pages), RPC ve explorer.
  Bunlar sadece okur ya da işlem iletir. ABI açık ([`build/PeerReview.json`](build/PeerReview.json)); herkes kendi RPC'siyle aynı sonucu okuyabilir.
- **Demoda:** havuzdaki botların anahtarları organizatörün panelinde. Gerçek kullanımda havuz herkese açıktır.
  Çoğunluğu ele geçirmek büyük teminat ister, sapan her oy da ceza yer.

## Bilinen zayıflıklar
`prevrandao` tabanlı rastgelelik (gerçek sürümde VRF) · çoğunluk = doğruluk varsayımı (tuzak görev yok) · itiraz turu yok ·
push ödeme · yorumlar ve teslimatlar zincirde düz metin.
