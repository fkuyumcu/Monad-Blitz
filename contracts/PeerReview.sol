// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title PeerReview — üç bağımsız değerlendiricili, puanlı freelance emanet
/// @notice İş veren ödemeyi ve değerlendirme ücretini kilitler. Freelancer teslim eder.
///         Havuzdan rastgele 3 değerlendirici atanır; birbirini görmeden (commit-reveal) 1–10 puan
///         ve yorum verir. Nihai puan medyandır. Freelancer puana göre ödeme alır; değerlendiriciler
///         medyana yakınlıklarına göre ücret paylaşır, çok sapan cezalandırılır.
/// @dev Yönetici (owner) yok, güncellenemez: kayıtlar ve kurallar deploy'dan sonra değiştirilemez.
contract PeerReview {
    // ================================================================ sabitler
    uint8 public constant MAX_SCORE = 10;
    uint8 public constant PASS_SCORE = 8;   // bu puan ve üstü: tam ödeme
    uint8 public constant SLASH_DEV = 3;    // medyandan bu kadar ve fazla sapma: ceza
    uint256 public constant REVIEWERS = 3;

    uint256 public immutable reviewerStake; // havuza girmek için asgari teminat
    uint256 public immutable slashAmount;   // ceza başına kesinti (≤ reviewerStake)
    uint256 public immutable feeBps;        // ödemeden ayrılan değerlendirme ücreti (1000 = %10)
    uint256 public immutable commitWindow;  // saniye
    uint256 public immutable revealWindow;  // saniye

    enum Status { Open, Committing, Revealing, Finalized, Cancelled }

    struct Job {
        address client;
        address worker;          // 0 ise ilk teslim eden freelancer olur
        uint256 amount;          // freelancer'a ayrılan tutar
        uint256 fee;             // değerlendirici ücret havuzu
        Status status;
        uint8 commitCount;
        uint8 revealCount;
        uint8 finalScore;
        uint64 commitDeadline;
        uint64 revealDeadline;
        address[3] reviewers;
        bytes32[3] commits;
        uint8[3] scores;         // 0 = açıklanmadı
        string spec;
        string deliverable;
    }

    struct Reviewer {
        bool registered;
        uint32 reviews;          // sonuçlanan atama sayısı
        uint32 weightSum;        // toplam isabet ağırlığı (her iş 0..3)
        uint32 open;             // sonuçlanmamış atama sayısı
        uint256 stake;
        uint256 earned;          // toplam kazanç
        uint256 slashed;         // toplam ceza
    }

    Job[] private _jobs;
    mapping(address => Reviewer) public reviewerInfo;
    address[] private _pool;

    // ================================================================ olaylar
    event ReviewerRegistered(address indexed reviewer, uint256 stake);
    event StakeChanged(address indexed reviewer, uint256 stake);
    event JobCreated(uint256 indexed jobId, address indexed client, address indexed worker, uint256 amount, uint256 fee, string spec);
    event Submitted(uint256 indexed jobId, address indexed worker, string deliverable, address[3] reviewers, uint64 commitDeadline);
    event Committed(uint256 indexed jobId, address indexed reviewer);
    event RevealPhase(uint256 indexed jobId, uint64 revealDeadline);
    event Revealed(uint256 indexed jobId, address indexed reviewer, uint8 score, string comment);
    event Slashed(uint256 indexed jobId, address indexed reviewer, uint256 amount);
    event ReviewerPaid(uint256 indexed jobId, address indexed reviewer, uint8 weight, uint256 reward);
    event Finalized(uint256 indexed jobId, uint8 finalScore, uint256 workerPayout, uint256 clientRefund);
    event Cancelled(uint256 indexed jobId);

    // ================================================================ hatalar
    error BadParams();
    error AlreadyRegistered();
    error NotRegistered();
    error StakeTooLow();
    error StakeLocked();
    error ZeroAmount();
    error NotClient();
    error NotWorker();
    error BadStatus();
    error NotAssigned();
    error AlreadyDone();
    error TooLate();
    error TooEarly();
    error BadReveal();
    error BadScore();
    error NotEnoughReviewers();
    error TransferFailed();

    constructor(uint256 _reviewerStake, uint256 _slashAmount, uint256 _feeBps, uint256 _commitWindow, uint256 _revealWindow) {
        if (_slashAmount > _reviewerStake || _feeBps > 5000 || _commitWindow == 0 || _revealWindow == 0) revert BadParams();
        reviewerStake = _reviewerStake;
        slashAmount = _slashAmount;
        feeBps = _feeBps;
        commitWindow = _commitWindow;
        revealWindow = _revealWindow;
    }

    // ================================================================ değerlendirici havuzu

    function register() external payable {
        Reviewer storage r = reviewerInfo[msg.sender];
        if (r.registered) revert AlreadyRegistered();
        if (msg.value < reviewerStake) revert StakeTooLow();
        r.registered = true;
        r.stake = msg.value;
        _pool.push(msg.sender);
        emit ReviewerRegistered(msg.sender, msg.value);
    }

    function topUp() external payable {
        Reviewer storage r = reviewerInfo[msg.sender];
        if (!r.registered) revert NotRegistered();
        r.stake += msg.value;
        emit StakeChanged(msg.sender, r.stake);
    }

    /// @notice Açık ataması varken teminat asgari seviyenin altına çekilemez.
    function withdrawStake(uint256 amount) external {
        Reviewer storage r = reviewerInfo[msg.sender];
        if (amount > r.stake) revert StakeTooLow();
        if (r.open > 0 && r.stake - amount < reviewerStake) revert StakeLocked();
        r.stake -= amount;
        _send(msg.sender, amount);
        emit StakeChanged(msg.sender, r.stake);
    }

    // ================================================================ iş akışı

    /// @notice msg.value = ödeme + ücret. Ücret feeBps oranında ayrılır.
    ///         worker = address(0) verilirse iş herkese açıktır; ilk teslim eden freelancer olur.
    function createJob(address worker, string calldata spec) external payable returns (uint256 jobId) {
        if (msg.value == 0) revert ZeroAmount();
        uint256 fee = (msg.value * feeBps) / 10_000;
        jobId = _jobs.length;
        Job storage j = _jobs.push();
        j.client = msg.sender;
        j.worker = worker;
        j.amount = msg.value - fee;
        j.fee = fee;
        j.spec = spec;
        emit JobCreated(jobId, msg.sender, worker, j.amount, fee, spec);
    }

    function cancel(uint256 jobId) external {
        Job storage j = _jobs[jobId];
        if (msg.sender != j.client) revert NotClient();
        if (j.status != Status.Open) revert BadStatus();
        j.status = Status.Cancelled;
        _send(j.client, j.amount + j.fee);
        emit Cancelled(jobId);
    }

    /// @notice Teslimat; havuzdan rastgele 3 değerlendirici atanır ve mühürlü oy süresi başlar.
    function submit(uint256 jobId, string calldata deliverable) external {
        Job storage j = _jobs[jobId];
        if (j.status != Status.Open) revert BadStatus();
        if (j.worker == address(0)) {
            if (msg.sender == j.client) revert NotWorker();
            j.worker = msg.sender;
        } else if (msg.sender != j.worker) {
            revert NotWorker();
        }
        j.deliverable = deliverable;
        j.reviewers = _pick(jobId, j.client, j.worker);
        for (uint256 i = 0; i < REVIEWERS; i++) reviewerInfo[j.reviewers[i]].open++;
        j.status = Status.Committing;
        j.commitDeadline = uint64(block.timestamp + commitWindow);
        emit Submitted(jobId, j.worker, deliverable, j.reviewers, j.commitDeadline);
    }

    /// @notice Mühürlü oy: commitHash(jobId, msg.sender, score, salt, comment)
    function commit(uint256 jobId, bytes32 hash) external {
        Job storage j = _jobs[jobId];
        if (j.status != Status.Committing) revert BadStatus();
        if (block.timestamp > j.commitDeadline) revert TooLate();
        uint256 i = _slot(j, msg.sender);
        if (j.commits[i] != bytes32(0)) revert AlreadyDone();
        j.commits[i] = hash;
        j.commitCount++;
        emit Committed(jobId, msg.sender);
        if (j.commitCount == REVIEWERS) _startReveal(jobId, j);
    }

    /// @notice Oyu açar. Üç mühür de gelince (ya da süre dolup en az ikisi gelmişse) açılabilir.
    function reveal(uint256 jobId, uint8 score, bytes32 salt, string calldata comment) external {
        Job storage j = _jobs[jobId];
        if (j.status == Status.Committing) {
            if (block.timestamp <= j.commitDeadline || j.commitCount < 2) revert TooEarly();
            _startReveal(jobId, j);
        }
        if (j.status != Status.Revealing) revert BadStatus();
        if (block.timestamp > j.revealDeadline) revert TooLate();
        if (score == 0 || score > MAX_SCORE) revert BadScore();
        uint256 i = _slot(j, msg.sender);
        if (j.scores[i] != 0) revert AlreadyDone();
        if (j.commits[i] != commitHash(jobId, msg.sender, score, salt, comment)) revert BadReveal();
        j.scores[i] = score;
        j.revealCount++;
        emit Revealed(jobId, msg.sender, score, comment);
        if (j.revealCount == j.commitCount) _finalize(jobId, j);
    }

    /// @notice Süresi dolan işi herkes ilerletebilir: mühür süresi dolduğunda en az 2 mühür varsa
    ///         açma aşaması başlar; yoksa ya da açma süresi de dolduysa iş sonuçlanır
    ///         (oy vermeyenler cezalandırılır).
    function finalize(uint256 jobId) external {
        Job storage j = _jobs[jobId];
        if (j.status == Status.Committing) {
            if (block.timestamp <= j.commitDeadline) revert TooEarly();
            if (j.commitCount >= 2) {
                _startReveal(jobId, j);
                return;
            }
        } else if (j.status == Status.Revealing) {
            if (block.timestamp <= j.revealDeadline) revert TooEarly();
        } else {
            revert BadStatus();
        }
        _finalize(jobId, j);
    }

    // ================================================================ okuma

    function commitHash(uint256 jobId, address reviewer, uint8 score, bytes32 salt, string calldata comment)
        public pure returns (bytes32)
    {
        return keccak256(abi.encode(jobId, reviewer, score, salt, comment));
    }

    function jobCount() external view returns (uint256) { return _jobs.length; }
    function getJob(uint256 jobId) external view returns (Job memory) { return _jobs[jobId]; }
    function poolSize() external view returns (uint256) { return _pool.length; }
    function getPool() external view returns (address[] memory) { return _pool; }

    // ================================================================ iç işler

    function _slot(Job storage j, address who) internal view returns (uint256) {
        for (uint256 i = 0; i < REVIEWERS; i++) if (j.reviewers[i] == who) return i;
        revert NotAssigned();
    }

    function _startReveal(uint256 jobId, Job storage j) internal {
        j.status = Status.Revealing;
        j.revealDeadline = uint64(block.timestamp + revealWindow);
        emit RevealPhase(jobId, j.revealDeadline);
    }

    function _eligible(address a, address client, address worker) internal view returns (bool) {
        Reviewer storage r = reviewerInfo[a];
        return a != client && a != worker && r.stake >= reviewerStake;
    }

    /// @dev Zayıf rastgelelik (prevrandao): demo için yeterli, gerçek sistemde VRF kullanılmalı.
    function _pick(uint256 jobId, address client, address worker) internal view returns (address[3] memory out) {
        uint256 n = _pool.length;
        uint256 seed = uint256(keccak256(abi.encode(block.prevrandao, block.timestamp, jobId, worker)));
        for (uint256 k = 0; k < REVIEWERS; k++) {
            uint256 start = uint256(keccak256(abi.encode(seed, k))) % (n == 0 ? 1 : n);
            bool found;
            for (uint256 s = 0; s < n; s++) {
                address a = _pool[(start + s) % n];
                if (!_eligible(a, client, worker)) continue;
                if ((k > 0 && out[0] == a) || (k > 1 && out[1] == a)) continue;
                out[k] = a;
                found = true;
                break;
            }
            if (!found) revert NotEnoughReviewers();
        }
    }

    function _median(Job storage j) internal view returns (uint8) {
        uint8[3] memory s;
        uint256 c;
        for (uint256 i = 0; i < REVIEWERS; i++) if (j.scores[i] != 0) s[c++] = j.scores[i];
        if (c == 2) return uint8((uint256(s[0]) + s[1]) / 2);
        // c == 3: ortanca
        uint8 a = s[0]; uint8 b = s[1]; uint8 d = s[2];
        if (a > b) (a, b) = (b, a);
        if (b > d) (b, d) = (d, b);
        if (a > b) (a, b) = (b, a);
        return b;
    }

    function _takeSlash(uint256 jobId, address who) internal returns (uint256 cut) {
        Reviewer storage r = reviewerInfo[who];
        cut = r.stake < slashAmount ? r.stake : slashAmount;
        if (cut == 0) return 0;
        r.stake -= cut;
        r.slashed += cut;
        emit Slashed(jobId, who, cut);
    }

    function _finalize(uint256 jobId, Job storage j) internal {
        j.status = Status.Finalized; // önce durum (reentrancy'ye karşı)
        uint256 pot = j.fee;
        bool decided = j.revealCount >= 2;
        uint8 fin = decided ? _median(j) : 0;
        j.finalScore = fin;

        // 1) ağırlıklar ve cezalar
        uint8[3] memory w;
        uint256 sumW;
        bool revealPhase = j.revealDeadline != 0;
        for (uint256 i = 0; i < REVIEWERS; i++) {
            address a = j.reviewers[i];
            Reviewer storage r = reviewerInfo[a];
            r.open--;
            r.reviews++;
            uint8 s = j.scores[i];
            if (s == 0) {
                // mühür göndermedi ya da açma aşaması başladığı hâlde açmadı → ceza
                if (j.commits[i] == bytes32(0) || revealPhase) pot += _takeSlash(jobId, a);
                continue;
            }
            if (!decided) continue;
            uint8 dev = s > fin ? s - fin : fin - s;
            if (dev >= SLASH_DEV) {
                pot += _takeSlash(jobId, a);
            } else {
                w[i] = SLASH_DEV - dev;         // 3, 2, 1
                sumW += w[i];
                r.weightSum += w[i];
            }
        }

        // 2) freelancer ve iş veren
        uint256 workerPay;
        if (decided) workerPay = fin >= PASS_SCORE ? j.amount : (j.amount * fin) / MAX_SCORE;
        uint256 refund = j.amount - workerPay;

        // 3) değerlendirici payları (isabet ağırlıklı)
        uint256 distributed;
        if (sumW > 0) {
            for (uint256 i = 0; i < REVIEWERS; i++) {
                if (w[i] == 0) continue;
                uint256 share = (pot * w[i]) / sumW;
                distributed += share;
                reviewerInfo[j.reviewers[i]].earned += share;
                _send(j.reviewers[i], share);
                emit ReviewerPaid(jobId, j.reviewers[i], w[i], share);
            }
        }
        refund += pot - distributed; // kimse isabet etmediyse ya da küsurat → iş verene

        if (workerPay > 0) _send(j.worker, workerPay);
        if (refund > 0) _send(j.client, refund);
        emit Finalized(jobId, fin, workerPay, refund);
    }

    function _send(address to, uint256 amount) internal {
        (bool ok, ) = payable(to).call{value: amount}("");
        if (!ok) revert TransferFailed();
    }
}
