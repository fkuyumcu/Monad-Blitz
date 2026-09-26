"""Zincir yardımcıları: bağlantı, kontrat yükleme, işlem gönderme, mühürlü oy hash'i.

Monad notu: gas, kullanılan miktara göre değil verilen gas limitine göre ücretlendirilir.
Bu yüzden her işlemde gas'ı önce tahmin edip küçük bir pay ekleyerek açıkça veriyoruz.
"""
import json
import os
from pathlib import Path

from eth_abi import encode as abi_encode
from web3 import Web3

ROOT = Path(__file__).parent
ARTIFACT = json.loads((ROOT / "build" / "PeerReview.json").read_text())

MONAD_TESTNET_RPC = "https://testnet-rpc.monad.xyz"
EXPLORER = "https://testnet.monadvision.com"
STATUS = ["Açık", "Mühürlü oylama", "Açıklama", "Sonuçlandı", "İptal"]


def load_env(path: Path = ROOT / ".env") -> None:
    """Basit .env okuyucu (ekstra paket gerektirmesin diye)."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def set_env(key: str, value: str, path: Path = ROOT / ".env") -> None:
    """.env içinde anahtarı ekler ya da günceller."""
    lines = path.read_text().splitlines() if path.exists() else []
    lines = [l for l in lines if not l.strip().startswith(f"{key}=")]
    lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n")
    os.environ[key] = value


def connect(rpc: str | None = None) -> Web3:
    w3 = Web3(Web3.HTTPProvider(rpc or os.environ.get("RPC_URL", MONAD_TESTNET_RPC)))
    if not w3.is_connected():
        raise SystemExit(f"RPC'ye bağlanılamadı: {rpc}")
    return w3


def contract(w3: Web3, address: str | None = None):
    address = address or os.environ["CONTRACT"]
    return w3.eth.contract(address=Web3.to_checksum_address(address), abi=ARTIFACT["abi"])


def hexkey(acct) -> str:
    k = acct.key.hex()
    return k if k.startswith("0x") else "0x" + k


def commit_hash(job_id: int, reviewer: str, score: int, salt: bytes, comment: str) -> bytes:
    """Kontrattaki commitHash ile birebir aynı: keccak256(abi.encode(...))."""
    return Web3.keccak(abi_encode(["uint256", "address", "uint8", "bytes32", "string"],
                                  [job_id, Web3.to_checksum_address(reviewer), score, salt, comment]))


def send(w3: Web3, account, fn=None, *, value: int = 0, deploy_tx=None):
    """fn: kontrat fonksiyon çağrısı (ör. c.functions.commit(...)). Makbuzu döndürür."""
    base = {"from": account.address, "value": value, "chainId": w3.eth.chain_id,
            "nonce": w3.eth.get_transaction_count(account.address)}
    tx = deploy_tx.build_transaction(base) if deploy_tx is not None else fn.build_transaction(base)
    tx["gas"] = int(w3.eth.estimate_gas({k: v for k, v in tx.items() if k != "gas"}) * 1.15) + 5_000
    return _sign_send(w3, account, tx)


def transfer(w3: Web3, account, to: str, value: int):
    tx = {"from": account.address, "to": Web3.to_checksum_address(to), "value": value,
          "nonce": w3.eth.get_transaction_count(account.address), "chainId": w3.eth.chain_id,
          "gas": 21_000, "gasPrice": w3.eth.gas_price}
    return _sign_send(w3, account, tx)


def _sign_send(w3, account, tx):
    signed = account.sign_transaction(tx)
    h = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(h, timeout=60)
    if receipt.status != 1:
        raise RuntimeError(f"İşlem geri çevrildi: {h.hex()}")
    return receipt


def tx_link(receipt) -> str:
    h = receipt.transactionHash.hex()
    return f"{EXPLORER}/tx/{h if h.startswith('0x') else '0x' + h}"
