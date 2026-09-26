# 03 — Kontrat referansı: `AIEscrow.sol`

Solidity ^0.8.24, derleyici 0.8.28, optimizer 200, `evmVersion: cancun`. Dış bağımlılık yok.

## Durum
| Değişken | Tip | Anlamı |
|---|---|---|
| `JUDGE_COUNT` | const 3 | hakem sayısı |
| `QUORUM` | const 2 | sonuç için gereken aynı oy |
| `judgeStake` | immutable uint | oy verebilmek için gereken asgari teminat |
| `slashAmount` | immutable uint | ters oy başına kesinti (≤ judgeStake) |
| `judges` | address[3] | sabit hakem listesi |
| `isJudge` | mapping(address⇒bool) | |
| `stakeOf` | mapping(address⇒uint) | hakem teminatı |
| `_jobs` | Job[] | işler (id = dizi indeksi) |
| `voteOf` | mapping(jobId⇒mapping(address⇒uint8)) | 0 yok, 1 onay, 2 red |

`Job { client, worker, amount, status, approvals, rejections, spec, deliverable }`
`Status: Open(0), Submitted(1), Paid(2), Refunded(3), Cancelled(4)`

## Fonksiyonlar
| Fonksiyon | Kim | Ön koşul | Etki |
|---|---|---|---|
| `constructor(address[3] judges, uint judgeStake, uint slashAmount)` | deployer | adresler sıfır değil ve tekrarsız, `slash ≤ stake` | hakemleri sabitler |
| `stake()` payable | hakem | `isJudge` | `stakeOf += value` → `JudgeStaked` |
| `withdrawStake(amount)` | herkes (fiilen hakem) | `amount ≤ stakeOf` | geri öder → `JudgeWithdrew` |
| `createJob(worker, spec)` payable | herkes | `value > 0` | yeni iş, `Open` → `JobCreated` |
| `cancel(jobId)` | iş veren | `Open` | iade, `Cancelled` → `Cancelled` |
| `submit(jobId, deliverable)` | iş yapan | `Open` | `Submitted` → `Submitted` |
| `vote(jobId, approve, reason)` | hakem | `stakeOf ≥ judgeStake`, durum Submitted/Paid/Refunded, daha önce oy yok | aşağıya bak |
| `jobCount()`, `getJob(id)`, `getJudges()` | view | | |

### `vote` mantığı
```
oyu kaydet; approvals/rejections++; emit Voted
if status == Submitted:
    approvals ≥ 2  → _resolve(approved=true)
    rejections ≥ 2 → _resolve(approved=false)
else (Paid/Refunded — geç oy):
    oy ≠ sonuç → _slash
```
`_resolve`: durumu Paid/Refunded yapar. O ana kadar sonuca ters oy vermiş hakemleri `_slash` eder, parayı `to` adresine (worker ya da client) gönderir → `Resolved`.
`_slash`: `min(stakeOf, slashAmount)` keser ve **kazanan tarafa** gönderir → `Slashed`.

## Olaylar
`JudgeStaked(judge,total)`, `JudgeWithdrew(judge,amount)`, `JobCreated(jobId,client,worker,amount,spec)`,
`Submitted(jobId,worker,deliverable)`, `Voted(jobId,judge,approve,reason)`, `Resolved(jobId,approved,to,amount)`,
`Slashed(jobId,judge,to,amount)`, `Cancelled(jobId)`. `jobId` ve adresler indexed.

## Hatalar (4 baytlık seçiciler hata ayıklamak için)
`NotJudge`, `NotClient`, `NotWorker`, `BadStatus` (0x5c975bda), `AlreadyVoted` (0x7c9a1cf9),
`StakeTooLow` (0x1cc3b37b), `ZeroAmount`, `BadJudges`, `TransferFailed`.

## Değişmezler (testlerle korunuyor)
- Bir iş en fazla bir kez sonuçlanır. Sonuçtan sonra para hareketi yalnızca ceza olabilir.
- Bir hakem bir işe en fazla bir kez oy verir.
- Kontrat bakiyesi = açık/teslim edilmiş işlerin tutarları + tüm teminatlar.
- Ceza hiçbir zaman hakemin teminatını aşmaz.

## Bilinen zayıflıklar (bilinçli, demo kapsamı)
- **DoS:** `worker` ya da `client`, ETH kabul etmeyen bir kontratsa `_send` revert eder ve iş kilitlenir. Çözüm: pull-payment deseni (`withdraw()`).
- **Askıda iş:** 2 hakem oy vermezse `Submitted` durumu sonsuza kadar sürer. Çözüm: deadline + `client` için iade.
- **Teminat çekme serbest:** Hakem kötü oy vermeden önce teminatını çekebilir. `_slash` o zaman 0 keser. Çözüm: kilit süresi ya da oy başına teminat ayırma.
- **Sabit hakemler:** Rastgele seçim ve açık kayıt yok. Metropolis aşaması için yol haritasında.
- **Reentrancy:** Tüm durum değişiklikleri `_send`'den önce yapılıyor. Hakemler ödeme almadığı için `vote` üzerinden reentrancy yolu yok. Yine de ileride `nonReentrant` eklenebilir.
