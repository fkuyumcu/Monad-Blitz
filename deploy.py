"""Kontratı Monad testnet'e (ya da RPC_URL neyse oraya) deploy eder.

Önce .env içine DEPLOYER_KEY=0x... yaz (faucet'ten MON almış bir cüzdan).

  # 3 hakem cüzdanını otomatik üret, MON gönder (hepsini sen çalıştırırsın):
  python deploy.py --gen-judges

  # Hakemleri salondaki başka kişiler kendi cüzdanıyla çalıştıracaksa:
  python deploy.py --judges 0xAAA...,0xBBB...,0xCCC...
"""
import argparse
import os
from pathlib import Path

from eth_account import Account

import chain


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--judges", help="virgülle ayrılmış 3 hakem adresi")
    g.add_argument("--gen-judges", action="store_true", help="3 hakem cüzdanı üret ve fonla")
    ap.add_argument("--stake", default="0.01", help="hakem teminatı (MON)")
    ap.add_argument("--slash", default="0.005", help="yanlış oyda kesilecek miktar (MON)")
    ap.add_argument("--fund", default="0.03", help="--gen-judges ile her hakeme gönderilecek MON")
    ap.add_argument("--rpc")
    args = ap.parse_args()

    chain.load_env()
    w3 = chain.connect(args.rpc)
    deployer = Account.from_key(os.environ["DEPLOYER_KEY"])
    print(f"Ağ chainId={w3.eth.chain_id}, deployer={deployer.address}, "
          f"bakiye={w3.from_wei(w3.eth.get_balance(deployer.address), 'ether')} MON")

    judge_accts = None
    if args.gen_judges:
        judge_accts = [Account.create() for _ in range(3)]
        addrs = [a.address for a in judge_accts]
    else:
        addrs = [chain.Web3.to_checksum_address(a.strip()) for a in args.judges.split(",")]
        if len(addrs) != 3:
            raise SystemExit("Tam 3 hakem adresi gerekli.")

    stake, slash = w3.to_wei(args.stake, "ether"), w3.to_wei(args.slash, "ether")
    Deployer = w3.eth.contract(abi=chain.ARTIFACT["abi"], bytecode=chain.ARTIFACT["bytecode"])
    r = chain.send(w3, deployer, deploy_tx=Deployer.constructor(addrs, stake, slash))
    addr = r.contractAddress
    print(f"✓ AIEscrow deploy edildi: {addr}\n  {chain.EXPLORER}/address/{addr}")

    chain.set_env("CONTRACT", addr)
    rpc = args.rpc or os.environ.get("RPC_URL", chain.MONAD_TESTNET_RPC)

    # canlı ekranın ayarı
    (chain.ROOT / "dashboard").mkdir(exist_ok=True)
    (chain.ROOT / "dashboard" / "config.js").write_text(
        f'window.ESCROW_CONFIG = {{ contract: "{addr}", rpc: "{rpc}", explorer: "{chain.EXPLORER}" }};\n')

    if judge_accts:
        for i, a in enumerate(judge_accts, 1):
            tx = {"to": a.address, "value": w3.to_wei(args.fund, "ether"), "from": deployer.address,
                  "nonce": w3.eth.get_transaction_count(deployer.address), "chainId": w3.eth.chain_id,
                  "gas": 21000, "gasPrice": w3.eth.gas_price}
            h = w3.eth.send_raw_transaction(deployer.sign_transaction(tx).raw_transaction)
            w3.eth.wait_for_transaction_receipt(h)
            Path(chain.ROOT / f"judge{i}.env").write_text(
                f"JUDGE_KEY={a.key.hex() if a.key.hex().startswith('0x') else '0x' + a.key.hex()}\n"
                f"CONTRACT={addr}\nRPC_URL={rpc}\n"
                f"# PROVIDER: anthropic | openai | gemini | mock\nPROVIDER=mock\n")
            print(f"  hakem {i}: {a.address} → judge{i}.env ({args.fund} MON gönderildi)")
    else:
        print("Hakemler judge.py'yi çalıştırınca teminatlarını kendileri yatıracak "
              f"(her biri en az {args.stake} MON + gas gerekir).")


if __name__ == "__main__":
    main()
