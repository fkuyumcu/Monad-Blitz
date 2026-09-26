# 02 — Mimari

```
 İş veren (demo.py) ─ createJob(+MON) ─▶ ┌─────────────────────────────┐
                                         │ PeerReview (Monad)          │
 Freelancer (app / demo.py) ─ submit ──▶ │ · emanet + %10 ücret havuzu │ ── olaylar ──▶ dashboard (salt okunur)
                                         │ · değerlendirici havuzu     │
 Değerlendirici × N (app / bot)          │ · rastgele 3 atama          │
   register(+teminat) ───────────────▶   │ · commit → reveal           │
   commit(hash) / reveal(puan,tuz,yorum) │ · medyan, ödeme, ücret, ceza│
                                         │ · itibar sayaçları          │
                                         └─────────────────────────────┘
```

**Güven sınırı:** Para, atama, oy sayımı, medyan, ödeme, ceza ve itibar zincirde. Zincir dışında sadece değerlendiricinin kararı ve tuzu (telefonda ya da botun `.bot-state/` klasöründe) var. Kontratın owner'ı yok.

## Akış
1. `createJob(worker, spec)` payable → `fee = value × feeBps / 10000`, `amount = value − fee`. `worker = 0` ise iş açıktır, ilk teslim eden freelancer olur.
2. `submit(id, deliverable)` → `_pick`, havuzdan uygun 3 kişi seçer: teminatı ≥ eşik, iş veren ya da freelancer değil, tekrarsız. Rastgelelik `keccak(prevrandao, timestamp, id, worker)` ile başlangıç noktası seçilip havuzda dolaşılarak sağlanıyor. Durum `Committing` olur, `commitDeadline = now + commitWindow`.
3. `commit(id, hash)` → üçüncü mühürde durum `Revealing` olur, `revealDeadline` başlar.
4. `reveal(id, score, salt, comment)` → hash kontrol edilir. Mühür gönderenlerin hepsi açınca `_finalize` otomatik çalışır.
5. Süre dolarsa `finalize(id)` herkes tarafından çağrılabilir. `Committing` durumunda ve en az 2 mühür varsa açma aşamasını başlatır, yoksa sonuçlandırır. `Revealing` durumunda sonuçlandırır. Botlar bunu "bekçi" olarak otomatik yapar, telefonda da "Süreyi ilerlet" düğmesi var.
6. `_finalize`: medyan (2 oyda ortalama, aşağı yuvarlanır) → oy vermeyene ve ≥3 sapana ceza → freelancer ödemesi (≥8 tam, altı orantılı) → ücret + cezalar ağırlıklara göre isabetlilere → küsurat ve kalan iş verene. En az 2 açık oy yoksa her şey iş verene iade edilir.

## İstemciler
- **Telefon (`app/`)**: Anahtar `#k=` ile gelir ya da tarayıcıda üretilir. `localStorage` erişilemezse yalnızca bellekte tutulur. Sekmeler: Görevler (puanla, mühürle, sonuç), İş al (açık işe teslimat), Profil (itibar). Tuz `localStorage`'da saklanır, açma aşaması gelince oy otomatik açılır.
- **Büyük ekran (`dashboard/`)**: Olayları 90 bloklık parçalarla `getLogs` ile toplar. Seçili dosya, 3 değerlendirici kartı (İnceliyor → MÜHÜRLÜ → puan ve yorum → isabet ya da ceza), hüküm, itibar tablosu ve tutanak gösterir.
- **Bot (`reviewer_bot.py`)**: Modlar honest (LLM ya da mock), lazy (hep 10) ve random. Teminatı eksikse tamamlar, süresi dolan işleri ilerletir.

## Ayar dosyaları
| Dosya | İçerik |
|---|---|
| `.env` | `DEPLOYER_KEY`, `RPC_URL`, `CONTRACT`, `WORKER_KEY`, opsiyonel `CLIENT_KEY` |
| `bots/botN.env` | `BOT_KEY`, `CONTRACT`, `RPC_URL`, `PROVIDER`, `MODE`, opsiyonel `MODEL`, API anahtarı |
| `app/config.js`, `dashboard/config.js` | `window.PR_CONFIG = { contract, rpc, explorer, chainId }` (anahtar içermez) |

Ağ: Monad testnet, chainId 10143, RPC `https://testnet-rpc.monad.xyz`, explorer `https://testnet.monadvision.com`, faucet `https://faucet.monad.xyz`.
