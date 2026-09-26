"""PeerReview kontrat testleri — yerel sahte zincirde (eth-tester), internet gerekmez.

Çalıştırma:  python test_review.py
"""
import os

from eth_account import Account
from web3 import EthereumTesterProvider, Web3

import chain

E = lambda x: Web3.to_wei(x, "ether")
STAKE, SLASH, FEE_BPS, COMMIT_W, REVEAL_W = E(1), E(0.5), 1000, 300, 300


class Env:
    def __init__(self, n_reviewers=5, register=True):
        self.w3 = w3 = Web3(EthereumTesterProvider())
        self.tester = w3.provider.ethereum_tester
        funder = w3.eth.accounts[0]
        self.client, self.worker, self.other = (Account.create() for _ in range(3))
        self.revs = [Account.create() for _ in range(n_reviewers)]
        for a in [self.client, self.worker, self.other, *self.revs]:
            w3.eth.send_transaction({"from": funder, "to": a.address, "value": E(1000)})
        D = w3.eth.contract(abi=chain.ARTIFACT["abi"], bytecode=chain.ARTIFACT["bytecode"])
        r = chain.send(w3, self.client, deploy_tx=D.constructor(STAKE, SLASH, FEE_BPS, COMMIT_W, REVEAL_W))
        self.c = chain.contract(w3, r.contractAddress)
        if register:
            for a in self.revs:
                chain.send(w3, a, self.c.functions.register(), value=STAKE)
        self.by_addr = {a.address: a for a in [self.client, self.worker, self.other, *self.revs]}
        self.salts = {}

    def tx(self, acct, fn, value=0):
        return chain.send(self.w3, acct, fn, value=value)

    def job(self, value=E(11), worker=None, spec="şartname"):
        w = worker if worker is not None else self.worker.address
        self.tx(self.client, self.c.functions.createJob(w, spec), value)
        return self.c.functions.jobCount().call() - 1

    def submit(self, jid, who=None, text="teslimat"):
        self.tx(who or self.worker, self.c.functions.submit(jid, text))
        return [self.by_addr[a] for a in self.get(jid)["reviewers"]]

    def commit(self, jid, acct, score, comment="yorum"):
        salt = os.urandom(32)
        self.tx(acct, self.c.functions.commit(jid, chain.commit_hash(jid, acct.address, score, salt, comment)))
        self.salts[(jid, acct.address)] = (score, salt, comment)  # yalnızca başarılı mühürden sonra

    def reveal(self, jid, acct):
        score, salt, comment = self.salts[(jid, acct.address)]
        return self.tx(acct, self.c.functions.reveal(jid, score, salt, comment))

    def get(self, jid):
        j = self.c.functions.getJob(jid).call()
        keys = ["client", "worker", "amount", "fee", "status", "commitCount", "revealCount", "finalScore",
                "commitDeadline", "revealDeadline", "reviewers", "commits", "scores", "spec", "deliverable"]
        return dict(zip(keys, j))

    def info(self, a):
        keys = ["registered", "reviews", "weightSum", "open", "stake", "earned", "slashed"]
        return dict(zip(keys, self.c.functions.reviewerInfo(a.address).call()))

    def bal(self, a):
        return self.w3.eth.get_balance(a.address)

    def travel(self, seconds):
        ts = self.w3.eth.get_block("latest")["timestamp"]
        self.tester.time_travel(ts + seconds)

    def full_round(self, scores):
        jid = self.job()
        revs = self.submit(jid)
        for a, s in zip(revs, scores):
            self.commit(jid, a, s)
        for a in revs:
            self.reveal(jid, a)
        return jid, revs


def expect_revert(fn, name=None):
    try:
        fn()
    except Exception as e:
        if name:
            sel = Web3.keccak(text=f"{name}()")[:4]
            msg = str(e)
            assert name in msg or sel.hex() in msg or str(bytes(sel)) in msg, f"{name} bekleniyordu, gelen: {e}"
        return
    raise AssertionError(f"revert bekleniyordu ({name})")


# ------------------------------------------------------------------ testler

def test_commit_hash_matches_contract():
    t = Env(n_reviewers=0, register=False)
    salt = os.urandom(32)
    a = t.revs[0].address if t.revs else t.other.address
    assert t.c.functions.commitHash(7, a, 9, salt, "güzel iş").call() == chain.commit_hash(7, a, 9, salt, "güzel iş")


def test_pass_score_pays_full_and_weights():
    t = Env()
    wb, cb = t.bal(t.worker), t.bal(t.client)
    jid = t.job()
    cb = t.bal(t.client)  # iş açıldıktan sonra
    revs = t.submit(jid)
    before = {a.address: t.bal(a) for a in revs}
    for a, s in zip(revs, [9, 8, 8]):
        t.commit(jid, a, s)
    gas_spent = {}
    for a in revs:
        r = t.reveal(jid, a)
    j = t.get(jid)
    assert j["status"] == 3 and j["finalScore"] == 8
    assert t.bal(t.worker) - wb > E(9.89)  # tam ödeme (9.9) eksi submit gas'ı
    assert t.bal(t.client) == cb           # iade yok
    ws = [t.info(a)["weightSum"] for a in revs]
    assert ws == [2, 3, 3], ws
    earned = [t.info(a)["earned"] for a in revs]
    assert sum(earned) == E(1.1) and earned[1] == earned[2] > earned[0]
    assert all(t.info(a)["open"] == 0 and t.info(a)["reviews"] == 1 for a in revs)


def test_partial_pay_and_slash_outlier():
    t = Env()
    jid = t.job()
    cb = t.bal(t.client)
    revs = t.submit(jid)
    for a, s in zip(revs, [6, 5, 2]):
        t.commit(jid, a, s)
    for a in revs:
        t.reveal(jid, a)
    j = t.get(jid)
    assert j["finalScore"] == 5
    assert t.bal(t.client) - cb == E(9.9) // 2       # %50 iade
    out = t.info(revs[2])
    assert out["stake"] == STAKE - SLASH and out["slashed"] == SLASH and out["weightSum"] == 0
    pot = E(1.1) + SLASH
    e0, e1 = t.info(revs[0])["earned"], t.info(revs[1])["earned"]
    assert e0 == pot * 2 // 5 and e1 == pot * 3 // 5
    # kontratta sadece teminatlar kalır (küsurat iş verene gider)
    stakes = sum(t.info(a)["stake"] for a in t.revs)
    assert t.w3.eth.get_balance(t.c.address) == stakes


def test_commit_reveal_guards():
    t = Env()
    jid = t.job()
    revs = t.submit(jid)
    outsider = next(a for a in t.revs if a not in revs)
    expect_revert(lambda: t.commit(jid, outsider, 5), "NotAssigned")
    t.commit(jid, revs[0], 7)
    expect_revert(lambda: t.commit(jid, revs[0], 7), "AlreadyDone")
    expect_revert(lambda: t.reveal(jid, revs[0]), "TooEarly")         # üçü mühürlemeden açılamaz
    t.commit(jid, revs[1], 7)
    t.commit(jid, revs[2], 7)
    s, salt, c = t.salts[(jid, revs[0].address)]
    expect_revert(lambda: t.tx(revs[0], t.c.functions.reveal(jid, s, os.urandom(32), c)), "BadReveal")
    expect_revert(lambda: t.tx(revs[0], t.c.functions.reveal(jid, s, salt, "değişmiş yorum")), "BadReveal")
    t.reveal(jid, revs[0])
    expect_revert(lambda: t.reveal(jid, revs[0]), "AlreadyDone")


def test_client_and_worker_never_assigned():
    t = Env(n_reviewers=3)
    chain.send(t.w3, t.worker, t.c.functions.register(), value=STAKE)
    chain.send(t.w3, t.client, t.c.functions.register(), value=STAKE)
    for _ in range(6):
        jid = t.job()
        revs = t.submit(jid)
        assert {a.address for a in revs} == {a.address for a in t.revs}
        for a in revs:
            t.commit(jid, a, 8)
        for a in revs:
            t.reveal(jid, a)


def test_not_enough_reviewers():
    t = Env(n_reviewers=2)
    jid = t.job()
    expect_revert(lambda: t.submit(jid), "NotEnoughReviewers")


def test_open_job_first_submitter_becomes_worker():
    t = Env()
    jid = t.job(worker="0x" + "00" * 20)
    expect_revert(lambda: t.submit(jid, who=t.client), "NotWorker")
    t.submit(jid, who=t.other)
    assert t.get(jid)["worker"] == t.other.address


def test_timeout_two_commits_nonvoter_slashed():
    t = Env()
    jid = t.job()
    revs = t.submit(jid)
    t.commit(jid, revs[0], 8)
    t.commit(jid, revs[1], 9)
    expect_revert(lambda: t.tx(t.other, t.c.functions.finalize(jid)), "TooEarly")
    t.travel(COMMIT_W + 5)
    t.tx(t.other, t.c.functions.finalize(jid))   # 2 mühür var → açma aşaması başlar, sonuçlanmaz
    assert t.get(jid)["status"] == 2
    t.reveal(jid, revs[0])
    t.reveal(jid, revs[1])          # iki mühür de açıldı → sonuçlanır
    j = t.get(jid)
    assert j["status"] == 3 and j["finalScore"] == 8  # (8+9)//2
    assert t.info(revs[2])["slashed"] == SLASH


def test_timeout_reveal_path_via_reveal():
    t = Env()
    jid = t.job()
    revs = t.submit(jid)
    t.commit(jid, revs[0], 6)
    t.commit(jid, revs[1], 6)
    t.travel(COMMIT_W + 5)
    t.reveal(jid, revs[0])          # süre dolunca açma, reveal ile de başlatılabilir
    t.reveal(jid, revs[1])
    assert t.get(jid)["finalScore"] == 6


def test_nobody_votes_full_refund():
    t = Env()
    jid = t.job()
    cb = t.bal(t.client)
    revs = t.submit(jid)
    t.travel(COMMIT_W + 5)
    t.tx(t.other, t.c.functions.finalize(jid))
    assert t.get(jid)["status"] == 3
    assert t.bal(t.client) - cb == E(11) + 3 * SLASH  # ödeme + ücret + 3 ceza
    assert all(t.info(a)["slashed"] == SLASH for a in revs)


def test_reveal_timeout_non_revealer_slashed():
    t = Env()
    jid = t.job()
    revs = t.submit(jid)
    for a, s in zip(revs, [8, 8, 9]):
        t.commit(jid, a, s)
    t.reveal(jid, revs[0])
    t.reveal(jid, revs[1])
    t.travel(REVEAL_W + 5)
    t.tx(t.other, t.c.functions.finalize(jid))
    assert t.get(jid)["finalScore"] == 8
    assert t.info(revs[2])["slashed"] == SLASH


def test_stake_lock_and_cancel():
    t = Env()
    jid = t.job()
    revs = t.submit(jid)
    expect_revert(lambda: t.tx(revs[0], t.c.functions.withdrawStake(STAKE)), "StakeLocked")
    j2 = t.job()
    cb = t.bal(t.client)
    t.tx(t.client, t.c.functions.cancel(j2))
    assert t.bal(t.client) > cb
    expect_revert(lambda: t.tx(t.client, t.c.functions.cancel(jid)), "BadStatus")


def test_slashed_reviewer_excluded_until_topup():
    t = Env(n_reviewers=3)
    jid, revs = t.full_round([8, 8, 1])     # üçüncü ceza yer, teminatı eşiğin altına düşer
    bad = revs[2]
    assert t.info(bad)["stake"] < STAKE
    j2 = t.job()
    expect_revert(lambda: t.submit(j2), "NotEnoughReviewers")
    t.tx(bad, t.c.functions.topUp(), value=SLASH)
    t.submit(j2)


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for fn in tests:
        fn()
        print("✓", fn.__name__)
    print(f"{len(tests)} test geçti")
