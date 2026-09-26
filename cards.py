"""Salona dağıtılacak, önceden fonlanmış cüzdan kartları üretir.

Her kart bir QR kod: telefonla okutunca değerlendirici/freelancer sayfası kendi cüzdanıyla açılır.
Özel anahtar URL'nin # kısmında durur (sunucuya gitmez). Test ağı anahtarlarıdır; gerçek değeri yoktur.

  python cards.py 15 --url https://fkuyumcu.github.io/monad-blitz/app/
  → cards/cards.html (yazdır ya da ekranda göster), cards/keys.csv
"""
import argparse
import csv
import io
import os

import qrcode
import qrcode.image.svg
from eth_account import Account

import chain
from deploy import gas_budget


def qr_svg(data: str) -> str:
    img = qrcode.make(data, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=1)
    buf = io.BytesIO()
    img.save(buf)
    svg = buf.getvalue().decode()
    return svg[svg.index("<svg"):]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("count", type=int)
    ap.add_argument("--url", default=os.environ.get("APP_URL", "http://localhost:8080/app/"),
                    help="telefon sayfasının adresi (GitHub Pages, Vercel ya da yerel ağ)")
    ap.add_argument("--actions", type=int, default=15, help="kart başına gas bütçesi (işlem sayısı)")
    args = ap.parse_args()

    chain.load_env()
    w3 = chain.connect()
    c = chain.contract(w3)
    deployer = Account.from_key(os.environ["DEPLOYER_KEY"])
    stake = c.functions.reviewerStake().call()
    fund = stake * 2 + gas_budget(w3, args.actions)
    total = fund * args.count
    bal = w3.eth.get_balance(deployer.address)
    print(f"Kart başı {w3.from_wei(fund, 'ether')} MON, toplam {w3.from_wei(total, 'ether')} MON "
          f"(bakiye {w3.from_wei(bal, 'ether')} MON)")
    if total > bal:
        raise SystemExit("Bakiye yetmiyor: --actions ya da kart sayısını düşür, ya da faucet'ten MON al.")

    rpc = os.environ.get("RPC_URL", chain.MONAD_TESTNET_RPC)
    extra = "" if rpc == chain.MONAD_TESTNET_RPC else f"&r={rpc}"
    out = chain.ROOT / "cards"
    out.mkdir(exist_ok=True)
    rows, cards = [], []
    for i in range(1, args.count + 1):
        a = Account.create()
        chain.transfer(w3, deployer, a.address, fund)
        link = f"{args.url}#c={c.address}&k={chain.hexkey(a)}{extra}"
        rows.append([i, a.address, chain.hexkey(a), link])
        cards.append(f'<div class="card"><div class="no">Kart {i:02d}</div>{qr_svg(link)}'
                     f'<div class="addr">{a.address[:8]}…{a.address[-6:]}</div></div>')
        print(f"  kart {i}: {a.address}")

    with open(out / "keys.csv", "w", newline="") as f:
        csv.writer(f).writerows([["no", "adres", "anahtar", "link"], *rows])
    (out / "cards.html").write_text(f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<title>Değerlendirici kartları</title><style>
body{{margin:0;background:#f3eee3;color:#16130f;font-family:Georgia,serif}}
h1{{font-size:28px;margin:18px 22px 4px}} p{{margin:0 22px 14px;font:14px monospace}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:0;border-top:1px solid #16130f}}
.card{{border-right:1px solid #16130f;border-bottom:1px solid #16130f;padding:14px;text-align:center;break-inside:avoid}}
.card svg{{width:170px;height:170px}} .no{{font:600 13px monospace;letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px}}
.addr{{font:12px monospace;color:#5c554a;margin-top:4px}}
</style></head><body><h1>Değerlendirici ol</h1>
<p>Okut → teminatını yatır → sana atanan teslimatı puanla. İsabetli puan kazandırır, sapma teminattan keser.</p>
<div class="grid">{''.join(cards)}</div></body></html>""")
    print(f"✓ cards/cards.html ve cards/keys.csv yazıldı ({args.count} kart). Bu klasör git'e girmez.")


if __name__ == "__main__":
    main()
