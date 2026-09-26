# 06 — Runbook

## Kurulum
```bash
pip install "web3[tester]" requests qrcode     # Python ≥ 3.10
npm install                                    # sadece kontratı yeniden derlemek için
cp .env.example .env                           # DEPLOYER_KEY
```

## Terminalsiz yol: kontrol paneli (`panel/`)
```bash
python3 -m http.server 8080        # repo kökünden
# tarayıcı: http://localhost:8080/panel/
```
Private key yapıştır → Cüzdanı bağla → Deploy → 3 bot kur → Senaryolar → QR kart. Botlar panel sekmesinde çalışır
(sekme açık kalmalı). Anahtarlar (ana cüzdan, bot, freelancer, kart) sadece o tarayıcının localStorage'ında durur.
Büyük ekran ve telefon linkleri kontratı `#c=` ile taşır, `config.js` gerekmez.

## Komutlar
```bash
node compile.js                                # contracts/ → build/
python test_review.py                          # 13 test
python deploy.py --bots 3 [--commit 60 --reveal 45 --stake 0.002 --slash 0.001 --fee-bps 1000]
python demo.py setup                           # freelancer cüzdanı
python cards.py 10 --url https://fkuyumcu.github.io/Monad-Blitz/app/
python reviewer_bot.py --env bots/bot1.env [--mode honest|lazy|random] [--provider ...]
python -m http.server 8080                     # repo kökünden: /dashboard/ ve /app/
python demo.py post [--open] [--spec ...] [--amount 0.01]
python demo.py run good|ok|bad|inject
python demo.py submit <id> "metin" · status <id> · tick <id> · pool
```

## Yerel uçtan uca test (testnet gerekmez)
```bash
# ayrı klasörde: npm i hardhat@2 && npx hardhat node   (hardfork: cancun)
curl -X POST localhost:8545 -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"evm_setIntervalMining","params":[1000]}'   # süreler için blok üretimi
# .env: DEPLOYER_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80  RPC_URL=http://127.0.0.1:8545
python deploy.py --bots 2 --commit 45 --reveal 30 && python demo.py setup
python cards.py 1 --url http://localhost:8080/app/      # linki tarayıcıda aç
```
Kart linkine `&r=<rpc>` eklenir (RPC varsayılandan farklıysa).

## Sorun giderme
| Belirti | Sebep / çözüm |
|---|---|
| `NotEnoughReviewers` | Havuzda iş veren ve freelancer dışında teminatı yeterli en az 3 kişi yok. Botları başlat ya da kart dağıt. |
| `TooEarly` (reveal) | Üç mühür tamamlanmadı ve süre dolmadı. Bekle. |
| `BadReveal` | Tuz, puan ya da yorum mühürdekiyle aynı değil. Telefonda farklı tarayıcı veya gizli sekme kullanılmışsa tuz kaybolur. |
| `StakeTooLow` / `StakeLocked` | Teminat eşiğin altında ya da açık atama varken çekilmeye çalışılıyor. |
| Değerlendirici oy açmadı | Açma aşamasında telefon sayfası açık değildi. Sayfa açılınca otomatik açar, süre dolduysa ceza kesilir. |
| İş takıldı | Süre dolduysa `python demo.py tick <id>` ya da telefonda "Süreyi ilerlet". Botlar da otomatik ilerletir. |
| 429 / rate limit | RPC'yi değiştir (`RPC_URL`, kart linkinde `&r=`) ya da bot `--interval` değerini artır. |
| Deploy'da "invalid opcode" | `compile.js` → `evmVersion: "paris"`. |
| Kart bakiyesi yetmiyor | `cards.py --actions 8` ya da faucet'ten MON al. |
