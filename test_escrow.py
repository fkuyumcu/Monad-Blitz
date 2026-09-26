"""Kontrat testleri — yerel sahte zincirde (eth-tester) çalışır, internet gerekmez.

Çalıştırma:  python test_escrow.py
"""
from web3 import Web3, EthereumTesterProvider
from eth_account import Account

import chain

E = Web3.to_wei


def setup():
    w3 = Web3(EthereumTesterProvider())
    funder = w3.eth.accounts[0]
    accts = [Account.create() for _ in range(6)]
    for a in accts:
        w3.eth.send_transaction({"from": funder, "to": a.address, "value": E(100, "ether")})
    client, worker, j1, j2, j3, stranger = accts
    Deployer = w3.eth.contract(abi=chain.ARTIFACT["abi"], bytecode=chain.ARTIFACT["bytecode"])
    r = chain.send(w3, client, deploy_tx=Deployer.constructor(
        [j1.address, j2.address, j3.address], E(1, "ether"), E(0.5, "ether")))
    c = chain.escrow(w3, r.contractAddress)
    for j in (j1, j2, j3):
        chain.send(w3, j, c.functions.stake(), value=E(1, "ether"))
    return w3, c, client, worker, (j1, j2, j3), stranger


def bal(w3, a):
    return w3.eth.get_balance(a.address)


def expect_revert(fn):
    try:
        fn()
    except Exception:
        return
    raise AssertionError("revert bekleniyordu")


def new_job(w3, c, client, worker, amount=E(2, "ether")):
    chain.send(w3, client, c.functions.createJob(worker.address, "Fişten toplam tutarı çıkar"), value=amount)
    jid = c.functions.jobCount().call() - 1
    chain.send(w3, worker, c.functions.submit(jid, "TOPLAM: 142,50 TL"))
    return jid


def test_approve_pays_worker():
    w3, c, client, worker, (j1, j2, j3), _ = setup()
    jid = new_job(w3, c, client, worker)
    before = bal(w3, worker)
    chain.send(w3, j1, c.functions.vote(jid, True, "tutar doğru"))
    assert c.functions.getJob(jid).call()[3] == 1  # hâlâ Submitted
    chain.send(w3, j2, c.functions.vote(jid, True, "doğru"))
    job = c.functions.getJob(jid).call()
    assert job[3] == 2, "Paid olmalı"
    assert bal(w3, worker) - before == E(2, "ether")
    assert w3.eth.get_balance(c.address) == E(3, "ether")  # sadece teminatlar kaldı


def test_reject_refunds_client():
    w3, c, client, worker, (j1, j2, j3), _ = setup()
    jid = new_job(w3, c, client, worker)
    before = bal(w3, client)
    chain.send(w3, j1, c.functions.vote(jid, False, "tutar yanlış"))
    chain.send(w3, j3, c.functions.vote(jid, False, "yanlış"))
    assert c.functions.getJob(jid).call()[3] == 3  # Refunded
    assert bal(w3, client) - before == E(2, "ether")


def test_corrupt_judge_slashed_when_outvoted_first():
    """Rüşvetli hakem önce oy verir, sonra diğer ikisi tersini söyler → sonuçta kesilir."""
    w3, c, client, worker, (j1, j2, j3), _ = setup()
    jid = new_job(w3, c, client, worker)
    cb = bal(w3, client)
    chain.send(w3, j3, c.functions.vote(jid, True, "harika iş"))       # rüşvetli
    chain.send(w3, j1, c.functions.vote(jid, False, "yanlış"))
    chain.send(w3, j2, c.functions.vote(jid, False, "yanlış"))
    assert c.functions.getJob(jid).call()[3] == 3
    assert c.functions.stakeOf(j3.address).call() == E(0.5, "ether")
    assert bal(w3, client) - cb == E(2.5, "ether")  # iade + kesilen teminat
    logs = c.events.Slashed().get_logs(from_block=0)
    assert len(logs) == 1 and logs[0].args.judge == j3.address


def test_late_dissent_slashed():
    """Sonuç çıktıktan sonra ters oy veren hakem de kesilir."""
    w3, c, client, worker, (j1, j2, j3), _ = setup()
    jid = new_job(w3, c, client, worker)
    chain.send(w3, j1, c.functions.vote(jid, True, "ok"))
    chain.send(w3, j2, c.functions.vote(jid, True, "ok"))
    wb = bal(w3, worker)
    chain.send(w3, j3, c.functions.vote(jid, False, "rüşvet"))
    assert c.functions.stakeOf(j3.address).call() == E(0.5, "ether")
    assert bal(w3, worker) - wb == E(0.5, "ether")


def test_late_agreeing_vote_not_slashed():
    w3, c, client, worker, (j1, j2, j3), _ = setup()
    jid = new_job(w3, c, client, worker)
    for j in (j1, j2, j3):
        chain.send(w3, j, c.functions.vote(jid, True, "ok"))
    assert all(c.functions.stakeOf(j.address).call() == E(1, "ether") for j in (j1, j2, j3))


def test_guards():
    w3, c, client, worker, (j1, j2, j3), stranger = setup()
    chain.send(w3, client, c.functions.createJob(worker.address, "x"), value=E(1, "ether"))
    # teslimattan önce oy yok
    expect_revert(lambda: chain.send(w3, j1, c.functions.vote(0, True, "")))
    # başkası teslim edemez
    expect_revert(lambda: chain.send(w3, stranger, c.functions.submit(0, "x")))
    chain.send(w3, worker, c.functions.submit(0, "y"))
    # hakem olmayan oy veremez, aynı hakem iki kez oy veremez
    expect_revert(lambda: chain.send(w3, stranger, c.functions.vote(0, True, "")))
    chain.send(w3, j1, c.functions.vote(0, True, ""))
    expect_revert(lambda: chain.send(w3, j1, c.functions.vote(0, True, "")))
    # teslimattan sonra iptal yok, sıfır tutarla iş yok
    expect_revert(lambda: chain.send(w3, client, c.functions.cancel(0)))
    expect_revert(lambda: chain.send(w3, client, c.functions.createJob(worker.address, "x")))


def test_unstaked_judge_cannot_vote_and_cancel_refunds():
    w3, c, client, worker, (j1, j2, j3), _ = setup()
    chain.send(w3, j1, c.functions.withdrawStake(E(1, "ether")))
    chain.send(w3, client, c.functions.createJob(worker.address, "x"), value=E(1, "ether"))
    cb = bal(w3, client)
    chain.send(w3, client, c.functions.cancel(0))
    assert bal(w3, client) > cb  # gas düşülse de iade geldi
    jid = new_job(w3, c, client, worker)
    expect_revert(lambda: chain.send(w3, j1, c.functions.vote(jid, True, "")))


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print("✓", t.__name__)
    print(f"{len(tests)} test geçti")
