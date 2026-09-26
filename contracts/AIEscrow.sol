// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title AIEscrow — üç bağımsız AI hakemli emanet ödeme
/// @notice İş veren parayı kilitler, iş yapan teslim eder, 3 hakemden 2'si aynı oyu verince
///         para ya iş yapana ya da iş verene gider. Çoğunluğa ters oy veren hakemin teminatı kesilir.
contract AIEscrow {
    // ---------------------------------------------------------------- tipler
    enum Status { Open, Submitted, Paid, Refunded, Cancelled }

    struct Job {
        address client;       // iş veren
        address worker;       // iş yapan
        uint256 amount;       // kilitli ödeme (wei)
        Status status;
        uint8 approvals;      // "onay" oyu sayısı
        uint8 rejections;     // "red" oyu sayısı
        string spec;          // şartname (kısa metin ya da link)
        string deliverable;   // teslimat (kısa metin ya da link)
    }

    // ---------------------------------------------------------------- sabitler
    uint256 public constant JUDGE_COUNT = 3;
    uint256 public constant QUORUM = 2;        // 2/3 çoğunluk
    uint256 public immutable judgeStake;       // hakemin yatırması gereken teminat
    uint256 public immutable slashAmount;      // yanlış oyda kesilen miktar

    // ---------------------------------------------------------------- durum
    address[3] public judges;
    mapping(address => bool) public isJudge;
    mapping(address => uint256) public stakeOf;

    Job[] private _jobs;
    // jobId => hakem => 0: oy yok, 1: onay, 2: red
    mapping(uint256 => mapping(address => uint8)) public voteOf;

    // ---------------------------------------------------------------- olaylar
    event JudgeStaked(address indexed judge, uint256 total);
    event JudgeWithdrew(address indexed judge, uint256 amount);
    event JobCreated(uint256 indexed jobId, address indexed client, address indexed worker, uint256 amount, string spec);
    event Submitted(uint256 indexed jobId, address indexed worker, string deliverable);
    event Voted(uint256 indexed jobId, address indexed judge, bool approve, string reason);
    event Resolved(uint256 indexed jobId, bool approved, address indexed to, uint256 amount);
    event Slashed(uint256 indexed jobId, address indexed judge, address indexed to, uint256 amount);
    event Cancelled(uint256 indexed jobId);

    // ---------------------------------------------------------------- hatalar
    error NotJudge();
    error NotClient();
    error NotWorker();
    error BadStatus();
    error AlreadyVoted();
    error StakeTooLow();
    error ZeroAmount();
    error BadJudges();
    error TransferFailed();

    constructor(address[3] memory _judges, uint256 _judgeStake, uint256 _slashAmount) {
        if (_slashAmount > _judgeStake) revert BadJudges();
        for (uint256 i = 0; i < JUDGE_COUNT; i++) {
            address j = _judges[i];
            if (j == address(0) || isJudge[j]) revert BadJudges();
            judges[i] = j;
            isJudge[j] = true;
        }
        judgeStake = _judgeStake;
        slashAmount = _slashAmount;
    }

    // ================================================================ hakem teminatı

    /// @notice Hakem teminat yatırır. Teminatı yetmeyen hakem oy veremez.
    function stake() external payable {
        if (!isJudge[msg.sender]) revert NotJudge();
        stakeOf[msg.sender] += msg.value;
        emit JudgeStaked(msg.sender, stakeOf[msg.sender]);
    }

    /// @notice Hakem teminatını çeker (demo için serbest; gerçek sistemde bekleme süresi olmalı).
    function withdrawStake(uint256 amount) external {
        if (amount > stakeOf[msg.sender]) revert StakeTooLow();
        stakeOf[msg.sender] -= amount;
        _send(msg.sender, amount);
        emit JudgeWithdrew(msg.sender, amount);
    }

    // ================================================================ iş akışı

    /// @notice İş veren işi oluşturur ve ödemeyi kilitler.
    function createJob(address worker, string calldata spec) external payable returns (uint256 jobId) {
        if (msg.value == 0) revert ZeroAmount();
        jobId = _jobs.length;
        _jobs.push(Job({
            client: msg.sender,
            worker: worker,
            amount: msg.value,
            status: Status.Open,
            approvals: 0,
            rejections: 0,
            spec: spec,
            deliverable: ""
        }));
        emit JobCreated(jobId, msg.sender, worker, msg.value, spec);
    }

    /// @notice İş veren, teslimat gelmeden işi iptal edip parasını geri alabilir.
    function cancel(uint256 jobId) external {
        Job storage job = _jobs[jobId];
        if (msg.sender != job.client) revert NotClient();
        if (job.status != Status.Open) revert BadStatus();
        job.status = Status.Cancelled;
        _send(job.client, job.amount);
        emit Cancelled(jobId);
    }

    /// @notice İş yapan teslimatı gönderir; hakemler bu olayı dinler.
    function submit(uint256 jobId, string calldata deliverable) external {
        Job storage job = _jobs[jobId];
        if (msg.sender != job.worker) revert NotWorker();
        if (job.status != Status.Open) revert BadStatus();
        job.deliverable = deliverable;
        job.status = Status.Submitted;
        emit Submitted(jobId, msg.sender, deliverable);
    }

    /// @notice Hakem oyunu verir. 2 aynı oy gelince iş anında sonuçlanır.
    ///         Sonuçlandıktan sonra gelen oy da kaydedilir; çoğunluğa tersse teminat kesilir.
    function vote(uint256 jobId, bool approve, string calldata reason) external {
        if (!isJudge[msg.sender]) revert NotJudge();
        if (stakeOf[msg.sender] < judgeStake) revert StakeTooLow();
        Job storage job = _jobs[jobId];
        if (job.status == Status.Open || job.status == Status.Cancelled) revert BadStatus();
        if (voteOf[jobId][msg.sender] != 0) revert AlreadyVoted();

        voteOf[jobId][msg.sender] = approve ? 1 : 2;
        if (approve) job.approvals++; else job.rejections++;
        emit Voted(jobId, msg.sender, approve, reason);

        if (job.status == Status.Submitted) {
            // henüz sonuçlanmadı: çoğunluk oluştu mu?
            if (job.approvals >= QUORUM) {
                _resolve(jobId, job, true);
            } else if (job.rejections >= QUORUM) {
                _resolve(jobId, job, false);
            }
        } else {
            // geç gelen oy: sonuçla uyuşmuyorsa ceza
            bool outcome = job.status == Status.Paid;
            if (approve != outcome) _slash(jobId, job, msg.sender, outcome);
        }
    }

    // ================================================================ okuma

    function jobCount() external view returns (uint256) {
        return _jobs.length;
    }

    function getJob(uint256 jobId) external view returns (Job memory) {
        return _jobs[jobId];
    }

    function getJudges() external view returns (address[3] memory) {
        return judges;
    }

    // ================================================================ iç işler

    function _resolve(uint256 jobId, Job storage job, bool approved) internal {
        address to = approved ? job.worker : job.client;
        job.status = approved ? Status.Paid : Status.Refunded;
        uint256 amount = job.amount;

        // sonuç anında zaten çoğunluğa ters oy vermiş hakem varsa cezalandır
        for (uint256 i = 0; i < JUDGE_COUNT; i++) {
            address j = judges[i];
            uint8 v = voteOf[jobId][j];
            if (v != 0 && (v == 1) != approved) _slash(jobId, job, j, approved);
        }

        _send(to, amount);
        emit Resolved(jobId, approved, to, amount);
    }

    /// @dev Kesilen teminat, sonuçtan zarar görmemesi gereken tarafa (kazanan tarafa) gider.
    function _slash(uint256 jobId, Job storage job, address judge, bool outcome) internal {
        uint256 amount = stakeOf[judge] < slashAmount ? stakeOf[judge] : slashAmount;
        if (amount == 0) return;
        stakeOf[judge] -= amount;
        address to = outcome ? job.worker : job.client;
        _send(to, amount);
        emit Slashed(jobId, judge, to, amount);
    }

    function _send(address to, uint256 amount) internal {
        (bool ok, ) = payable(to).call{value: amount}("");
        if (!ok) revert TransferFailed();
    }
}
