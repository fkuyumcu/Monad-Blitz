# 02 — Mimari

## Bileşenler
```
                ┌──────────── zincir dışı ─────────────┐
 İş veren ──createJob(+MON)──▶ ┌──────────────────────┐
 (demo.py)                    │   AIEscrow (Monad)   │◀── stake() / vote() ── Hakem I   (judge.py, cüzdan A, LLM x)
 İş yapan ──submit(metin)───▶ │  - işler & para      │◀── stake() / vote() ── Hakem II  (judge.py, cüzdan B, LLM y)
 (demo.py)                    │  - oy sayımı (2/3)   │◀── stake() / vote() ── Hakem III (judge.py, cüzdan C, LLM z)
                              │  - ödeme / iade      │
                              │  - teminat kesme     │── olaylar ──▶ dashboard/index.html (salt okunur)
                              └──────────────────────┘
```

**Güven sınırı:** Para, oy sayımı ve ceza zincirde. Zincir dışında sadece iki şey var: LLM'in kararı ve bu kararı imzalayan hakemin anahtarı. Hiçbir sunucu parayı tutmuyor, oy da saymıyor.

## Akış
1. **İş aç:** `createJob(worker, spec)` payable → `JobCreated`. Durum: `Open`.
2. **Teslim:** yalnızca `worker`, `submit(jobId, deliverable)` çağırabilir → `Submitted`. Durum: `Submitted`.
3. **Değerlendirme (her hakem, bağımsız):**
   - `judge.py` her `interval` saniyede `jobCount()` ve `getJob()` ile durumu okur (olay yerine durum sorgusu kullanılıyor, getLogs sınırlarından kaçınmak için).
   - `Submitted` durumunda olup henüz oy vermediği işi LLM'e sorar.
   - Prompt'ta şartname ve teslimat, her çağrıda rastgele üretilen etiketler (`<TESLIMAT_{hex}>`) arasında veri olarak verilir. Sistem mesajı, teslimattaki talimatları hile sayıp reddetmesini söyler. Çıktı katı JSON: `{"approve": bool, "reason": str}`.
   - Gerekçenin başına `[model]` eklenir (dashboard kart başlığı olarak kullanır). Rüşvetli hakem de kendi model adını gösterir.
   - Teminatı eksikse önce tamamlar, sonra `vote(jobId, approve, reason)` gönderir.
4. **Sonuç:** 2 aynı oy geldiği anda kontrat `_resolve` ile ödeme ya da iade yapar → `Resolved`. O ana kadar ters oy vermiş hakem varsa cezalandırılır → `Slashed`.
5. **Geç oy:** Sonuçtan sonra gelen 3. oy da kabul edilir. Sonuçla uyuşmuyorsa ceza kesilir.
6. **Dashboard:** `getLogs` ile olayları 90 bloklık parçalar halinde biriktirir, seçili dosyayı `getJob` ve `stakeOf` ile çizer. Yazma işlemi yapmaz.

## Rüşvetli hakem senaryosu (demo çekirdeği)
`judge.py --corrupt --interval 0.5`: LLM'e sormaz, her şeye hemen "onay" verir. Hızlı olduğu için ilk oyu hep o verir. Diğer iki hakem "red" verince iş iade edilir ve rüşvetçinin teminatından `slashAmount` kesilip haklı çıkan tarafa (iş verene) gönderilir. Kontrat daha sonra onun teminatı tamamlanana kadar oy vermesine izin vermez.

## Ayarlar
| Dosya | Anahtarlar |
|---|---|
| `.env` | `DEPLOYER_KEY`, `RPC_URL`, `CONTRACT` (deploy yazar), `WORKER_KEY` (demo setup yazar), opsiyonel `CLIENT_KEY` |
| `judgeN.env` | `JUDGE_KEY`, `CONTRACT`, `RPC_URL`, `PROVIDER`, opsiyonel `MODEL`, `CORRUPT`, sağlayıcı API anahtarı, `OPENAI_BASE_URL` |
| `dashboard/config.js` | `contract`, `rpc`, `explorer` (deploy yazar, commit'lenmez) |

Ağ: Monad testnet, chainId 10143. RPC: `https://testnet-rpc.monad.xyz` (yedekler: `https://rpc.ankr.com/monad_testnet`, `https://rpc-testnet.monadinfra.com`). Explorer: `https://testnet.monadvision.com`. Faucet: `https://faucet.monad.xyz`.
