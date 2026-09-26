# 06 — Runbook

## Kurulum
```bash
pip install "web3[tester]" requests     # Python ≥ 3.10
npm install                             # sadece kontratı yeniden derlemek için (solc 0.8.28)
cp .env.example .env                    # DEPLOYER_KEY doldur (faucet.monad.xyz'den MON)
```

## Temel komutlar
```bash
node compile.js                          # contracts/ → build/AIEscrow.json
python test_escrow.py                    # 7 test, internetsiz
python deploy.py --gen-judges            # deploy + judge1..3.env + dashboard/config.js
python deploy.py --judges A,B,C          # dış hakemlerle deploy
python demo.py setup                     # worker cüzdanı + gas parası
python judge.py --env judge1.env         # dürüst hakem
python judge.py --env judge3.env --corrupt --interval 0.5
cd dashboard && python -m http.server 8080
python demo.py run good|bad|inject
python demo.py status <id>
```

## Yerelde uçtan uca test (internetsiz, testnet gerekmez)
```bash
npx hardhat node                          # ayrı klasörde: npm i hardhat@2, hardfork: "cancun"
# .env: DEPLOYER_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
#       RPC_URL=http://127.0.0.1:8545
python deploy.py --gen-judges && python demo.py setup
# judgeN.env içinde PROVIDER=mock bırak, 3 hakemi başlat, demo.py run ...
```

## Sorun giderme
| Belirti | Sebep | Çözüm |
|---|---|---|
| Revert, veri `0x1cc3b37b` | `StakeTooLow` | Hakemin teminatı eksik. `judge.py` otomatik tamamlar, bakiyesi yetmiyorsa MON gönder. |
| Revert `0x5c975bda` | `BadStatus` | İş yanlış durumda (ör. teslimattan önce oy). |
| Revert `0x7c9a1cf9` | `AlreadyVoted` | Normal yarış durumu. judge.py sonraki turda geçer. |
| Deploy'da "invalid opcode" | EVM sürümü | `compile.js` → `evmVersion: "paris"`, sonra `node compile.js`. |
| 429 / rate limit | Public RPC | Hakemlere farklı `RPC_URL` ver, `--interval 3`. |
| Dashboard boş | `config.js` yok ya da eski | `deploy.py` yeniden üretir. Sayfayı demodan önce aç (son ~90 bloğu gösterir). |
| LLM 404 / model bulunamadı | Model adı eski | `judgeN.env` → `MODEL=<güncel ad>`. |
| `str | None` hatası | Python < 3.10 | Python'u güncelle. |
