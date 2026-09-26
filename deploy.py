"""PeerReview kontratını deploy eder ve demo ortamını hazırlar.

Önce .env içine DEPLOYER_KEY=0x... yaz (faucet'ten MON almış bir cüzdan; iş veren olarak da kullanılır).

  python deploy.py                    # sadece kontrat
  python deploy.py --bots 3           # + 3 otomatik değerlendirici cüzdanı (bots/botN.env), fonlanmış
  python deploy.py --stake 0.002 --commit 120 --reveal 90

Ardından: python cards.py 15   → salona dağıtılacak, fonlanmış QR cüzdan kartları
"""
import argparse
import os
from pathlib import Path

from eth_account import Account

import chain

GAS_PER_ACTION = 350_000  # register / commit / reveal(+sonuçlandırma) için cömert üst sınır


def gas_budget(w3, actions: int) -> int:
    """Monad gas'ı limite göre kestiği için tahmini gas bütçesi (cömert)."""
    return int(w3.eth.gas_price * GAS_PER_ACTION * actions * 1.3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stake", default="0.002", help="değerlendirici teminatı (MON)")
    ap.add_argument("--slash", default="0.001", help="ceza başına kesinti (MON)")
    ap.add_argument("--fee-bps", type=int, default=1000, help="değerlendirme ücreti, baz puan (1000 = %%10)")
    ap.add_argument("--commit", type=int, default=150, help="mühürlü oy süresi (sn)")
    ap.add_argument("--reveal", type=int, default=90, help="açma süresi (sn)")
    ap.add_argument("--bots", type=int, default=0, help="üretilecek otomatik değerlendirici sayısı")
    ap.add_argument("--bot-actions", type=int, default=40, help="bot başına gas bütçesi (işlem sayısı)")
    ap.add_argument("--rpc")
    args = ap.parse_args()

    chain.load_env()
    w3 = chain.connect(args.rpc)
    rpc = args.rpc or os.environ.get("RPC_URL", chain.MONAD_TESTNET_RPC)
    deployer = Account.from_key(os.environ["DEPLOYER_KEY"])
    bal = w3.eth.get_balance(deployer.address)
    print(f"Ağ chainId={w3.eth.chain_id}, deployer={deployer.address}, bakiye={w3.from_wei(bal, 'ether')} MON, "
          f"gasPrice={w3.from_wei(w3.eth.gas_price, 'gwei')} gwei")

    stake, slash = w3.to_wei(args.stake, "ether"), w3.to_wei(args.slash, "ether")
    D = w3.eth.contract(abi=chain.ARTIFACT["abi"], bytecode=chain.ARTIFACT["bytecode"])
    r = chain.send(w3, deployer, deploy_tx=D.constructor(stake, slash, args.fee_bps, args.commit, args.reveal))
    addr = r.contractAddress
    print(f"✓ PeerReview deploy edildi: {addr}\n  {chain.EXPLORER}/address/{addr}")
    chain.set_env("CONTRACT", addr)

    cfg = f'window.PR_CONFIG = {{ contract: "{addr}", rpc: "{rpc}", explorer: "{chain.EXPLORER}", chainId: {w3.eth.chain_id} }};\n'
    for d in ("dashboard", "app"):
        (chain.ROOT / d).mkdir(exist_ok=True)
        (chain.ROOT / d / "config.js").write_text(cfg)

    if args.bots:
        fund = stake * 2 + gas_budget(w3, args.bot_actions)
        (chain.ROOT / "bots").mkdir(exist_ok=True)
        for i in range(1, args.bots + 1):
            a = Account.create()
            chain.transfer(w3, deployer, a.address, fund)
            Path(chain.ROOT / "bots" / f"bot{i}.env").write_text(
                f"BOT_KEY={chain.hexkey(a)}\nCONTRACT={addr}\nRPC_URL={rpc}\n"
                f"# PROVIDER: anthropic | openai | gemini | mock   MODE: honest | lazy | random\n"
                f"PROVIDER=mock\nMODE=honest\n")
            print(f"  bot {i}: {a.address} → bots/bot{i}.env ({w3.from_wei(fund, 'ether')} MON)")
    print("Sonraki adım: python cards.py <kişi sayısı>  ·  python reviewer_bot.py --env bots/bot1.env")


if __name__ == "__main__":
    main()
