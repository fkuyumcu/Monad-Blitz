# 03 — Kontrat referansı: `PeerReview.sol`

Solidity ^0.8.24 · solc 0.8.28 · optimizer 200 · **viaIR** · cancun. Dış bağımlılık yok, owner yok.

## Parametreler
| Ad | Tür | Varsayılan (deploy.py) |
|---|---|---|
| `MAX_SCORE` / `PASS_SCORE` / `SLASH_DEV` / `REVIEWERS` | sabit | 10 / 8 / 3 / 3 |
| `reviewerStake` | immutable | 0.002 MON |
| `slashAmount` | immutable (≤ stake) | 0.001 MON |
| `feeBps` | immutable (≤ 5000) | 1000 (%10) |
| `commitWindow` / `revealWindow` | immutable, sn | 150 / 90 |

## Veri
`Status: Open(0) Committing(1) Revealing(2) Finalized(3) Cancelled(4)`

`Job { client, worker, amount, fee, status, commitCount, revealCount, finalScore, commitDeadline, revealDeadline, reviewers[3], commits[3], scores[3] (0 = açılmadı), spec, deliverable }`

`Reviewer { registered, reviews, weightSum (her iş 0..3), open, stake, earned, slashed }`. İsabet oranı = `weightSum / (3·reviews)`.

## Fonksiyonlar
| Fonksiyon | Kim | Koşul | Etki |
|---|---|---|---|
| `register()` payable | herkes | kayıtlı değil, value ≥ stake | havuza girer |
| `topUp()` payable | kayıtlı | | teminat artar |
| `withdrawStake(a)` | herkes | açık ataması varsa kalan ≥ stake | çeker |
| `createJob(worker, spec)` payable | herkes | value > 0 | ücret ayrılır, iş açılır |
| `cancel(id)` | iş veren | Open | ödeme ve ücret iade |
| `submit(id, text)` | freelancer (ya da açık işte herkes, iş veren hariç) | Open, ≥3 uygun değerlendirici | 3 atama, Committing |
| `commit(id, hash)` | atanmış | Committing, süre içinde, ilk kez | 3. mühürde Revealing |
| `reveal(id, score, salt, comment)` | atanmış | Revealing (ya da mühür süresi dolmuş ve ≥2 mühür), 1 ≤ score ≤ 10, hash eşleşiyor | hepsi açılınca sonuçlanır |
| `finalize(id)` | herkes | süre dolmuş | açma aşamasını başlatır ya da sonuçlandırır |
| `commitHash(...)` | pure | | `keccak256(abi.encode(id, reviewer, score, salt, comment))` |
| `jobCount`, `getJob`, `poolSize`, `getPool`, `reviewerInfo` | view | | |

## Sonuçlandırma kuralları
- En az 2 açık oy yoksa: freelancer 0 alır, tüm tutar ve ücret (ve varsa cezalar) iş verene döner.
- Oy vermeyen ceza yer: mühür göndermeyen her zaman, mühür gönderip açmayan ise açma aşaması başlamışsa.
- Oy veren için `dev = |puan − medyan|`. `dev ≥ 3` ise ceza, değilse ağırlık `3 − dev`.
- Freelancer: `medyan ≥ 8` ise tamamı, değilse `amount × medyan / 10`.
- Havuz = ücret + tüm cezalar. Ağırlıklara göre dağıtılır, küsurat ve kalan iş verene gider.

## Olaylar
`ReviewerRegistered, StakeChanged, JobCreated, Submitted(…, reviewers[3], commitDeadline), Committed, RevealPhase, Revealed(id, reviewer, score, comment), Slashed, ReviewerPaid(id, reviewer, weight, reward), Finalized(id, finalScore, workerPayout, clientRefund), Cancelled`

## Hatalar
`BadParams AlreadyRegistered NotRegistered StakeTooLow StakeLocked ZeroAmount NotClient NotWorker BadStatus NotAssigned AlreadyDone TooLate TooEarly BadReveal BadScore NotEnoughReviewers TransferFailed`

## Değişmezler (testlerle)
- Sonuçlanan işin puanı ve yorumları değişmez. Durum Finalized olduktan sonra hiçbir fonksiyon işi değiştiremez.
- Tüm işler sonuçlandıktan sonra kontrat bakiyesi = toplam teminat.
- İş veren ve freelancer kendi işlerine atanamaz.
- Ceza hiçbir zaman teminatı aşmaz. Teminatı eşiğin altına düşen, tamamlayana kadar atanamaz.
- Durum değişikliği para gönderiminden önce yapılır.

## Zayıflıklar (bilinçli)
`prevrandao` rastgeleliği · push ödeme (DoS riski) · çoğunluk = doğruluk varsayımı (tuzak görev yok) · itiraz turu yok · değerlendirici aynı anda çok işe atanabilir · yorumlar zincirde düz metin.
