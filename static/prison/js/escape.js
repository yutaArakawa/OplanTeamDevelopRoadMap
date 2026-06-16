(function () {
    'use strict';

    // --- Config ---
    const DASH_SPEED = 0.667;          // px per frame while dashing
    const GRACE_PERIOD_MS = 300;       // ms player has to stop after guard turns around
    const PRISONER_START_RATIO = 0.70; // start position: 70% from left
    const GOAL_X = 60;                 // px from left edge = goal

    // 難易度設定（進捗0%→100%で変化）
    const GUARD_AWAY_MAX_EASY   = 5000;
    const GUARD_AWAY_MAX_HARD   = 1800;
    const GUARD_AWAY_MIN_EASY   = 2500;
    const GUARD_AWAY_MIN_HARD   = 800;
    const GUARD_WATCH_MAX_EASY  = 3500;
    const GUARD_WATCH_MAX_HARD  = 1500;
    const GUARD_WATCH_MIN_EASY  = 2000;
    const GUARD_WATCH_MIN_HARD  = 800;
    // フェイント確率（進捗0%→100%で変化）
    const FEINT_CHANCE_EASY = 0.0;   // 序盤はフェイントなし
    const FEINT_CHANCE_HARD = 0.55;  // 終盤は55%でフェイント
    const FEINT_DURATION_MIN = 300;  // フェイントで後ろを向く時間(ms)
    const FEINT_DURATION_MAX = 700;

    // --- State ---
    let prisonerX = 0;
    let dashing = false;
    let guardWatching = true;
    let gameOver = false;
    let caught = false;
    let guardTurnedAt = 0;
    let catchTimer = null;
    let guardCycleTimer = null;
    let guardChaseInterval = null;
    let animFrame = null;

    // --- DOM ---
    const container   = document.getElementById('game-container');
    const bg          = document.getElementById('background');
    const prisoner    = document.getElementById('prisoner');
    const guard       = document.getElementById('guard');
    const guardStatus = document.getElementById('guard-status');
    const progressBar = document.getElementById('progress-bar');
    const statusText  = document.getElementById('status-text');
    const dashBtn     = document.getElementById('dash-btn');
    const overlay     = document.getElementById('overlay');
    const overlayTitle = document.getElementById('overlay-title');
    const failImage   = document.getElementById('fail-image');
    const retryBtn      = document.getElementById('retry-btn');
    const goalReturnBtn = document.getElementById('goal-return-btn');

    const imgGuardFront   = document.getElementById('img-guard-front').src;
    const imgGuardBack    = document.getElementById('img-guard-back').src;
    const imgPrisonerIdle = document.getElementById('img-prisoner-idle').src;
    const imgPrisonerRun  = document.getElementById('img-prisoner-run').src;
    const imgFailSrc      = document.getElementById('img-fail') ? document.getElementById('img-fail').src : null;

    function containerWidth() { return container.offsetWidth; }

    function init() {
        prisonerX = containerWidth() * PRISONER_START_RATIO;
        dashing = false;
        guardWatching = true;
        gameOver = false;
        caught = false;
        guardTurnedAt = 0;

        if (catchTimer)       clearTimeout(catchTimer);
        if (guardCycleTimer)  clearTimeout(guardCycleTimer);
        if (guardChaseInterval) clearInterval(guardChaseInterval);
        if (animFrame)        cancelAnimationFrame(animFrame);

        overlay.classList.remove('show');
        dashBtn.textContent = 'DASH';
        dashBtn.disabled = false;
        dashBtn.onclick = null;
        dashBtn.classList.remove('pressed');
        goalReturnBtn.classList.remove('show');

        guard.src = imgGuardFront;
        guard.style.right = '5px';
        guard.style.left = '';

        prisoner.src = imgPrisonerIdle;
        prisoner.style.left = prisonerX + 'px';

        updateGuardStatus();
        updateProgressBar();

        setTimeout(scheduleGuardTurn, 1000);
        animFrame = requestAnimationFrame(gameLoop);
    }

    function getProgress() {
        const total = containerWidth() * PRISONER_START_RATIO - GOAL_X;
        const remaining = prisonerX - GOAL_X;
        return Math.max(0, Math.min(1, 1 - remaining / total));
    }

    function lerp(a, b, t) { return a + (b - a) * t; }

    function getDifficulty() {
        return getProgress(); // 0.0〜1.0
    }

    function scheduleGuardTurn() {
        if (gameOver) return;
        const d = getDifficulty();

        if (guardWatching) {
            const delay = rand(
                Math.round(lerp(GUARD_WATCH_MIN_EASY, GUARD_WATCH_MIN_HARD, d)),
                Math.round(lerp(GUARD_WATCH_MAX_EASY, GUARD_WATCH_MAX_HARD, d))
            );
            guardCycleTimer = setTimeout(() => guardLookAway(), delay);
        } else {
            const delay = rand(
                Math.round(lerp(GUARD_AWAY_MIN_EASY, GUARD_AWAY_MIN_HARD, d)),
                Math.round(lerp(GUARD_AWAY_MAX_EASY, GUARD_AWAY_MAX_HARD, d))
            );
            guardCycleTimer = setTimeout(() => guardLookForward(), delay);
        }
    }

    function guardLookAway() {
        if (gameOver) return;
        const d = getDifficulty();
        const feintChance = lerp(FEINT_CHANCE_EASY, FEINT_CHANCE_HARD, d);

        // フェイント：後ろを向いた直後にすぐ正面に戻る
        if (Math.random() < feintChance) {
            guardWatching = false;
            guard.src = imgGuardBack;
            updateGuardStatus();
            const feintDuration = rand(FEINT_DURATION_MIN, FEINT_DURATION_MAX);
            guardCycleTimer = setTimeout(() => guardLookForward(), feintDuration);
        } else {
            guardWatching = false;
            guard.src = imgGuardBack;
            updateGuardStatus();
            scheduleGuardTurn();
        }
    }

    function guardLookForward() {
        if (gameOver) return;
        guardWatching = true;
        guardTurnedAt = performance.now();
        guard.src = imgGuardFront;
        updateGuardStatus();

        if (dashing) {
            catchTimer = setTimeout(() => {
                if (dashing && !gameOver) triggerFail();
            }, GRACE_PERIOD_MS);
        }
        scheduleGuardTurn();
    }

    function gameLoop() {
        if (!gameOver) {
            if (dashing && !guardWatching) {
                prisonerX = Math.max(GOAL_X, prisonerX - DASH_SPEED);
                prisoner.style.left = prisonerX + 'px';
                updateProgressBar();

                if (prisonerX <= GOAL_X) {
                    triggerGoal();
                    return;
                }
            }
        }
        animFrame = requestAnimationFrame(gameLoop);
    }

    function updateProgressBar() {
        const total = containerWidth() * PRISONER_START_RATIO - GOAL_X;
        const remaining = prisonerX - GOAL_X;
        const pct = Math.max(0, Math.min(100, (1 - remaining / total) * 100));
        progressBar.style.width = pct + '%';
    }

    function updateGuardStatus() {
        if (guardWatching) {
            guardStatus.textContent = '👁 WATCHING';
            guardStatus.className = 'watching';
            statusText.textContent = '⚠ 止まれ！';
        } else {
            guardStatus.textContent = '🔙 AWAY';
            guardStatus.className = 'away';
            statusText.textContent = '✅ 今だ！SPACEを長押し！';
        }
    }

    function triggerGoal() {
        gameOver = true;
        dashing = false;
        prisoner.src = imgPrisonerIdle;
        dashBtn.disabled = true;
        dashBtn.textContent = 'DASH';
        if (guardCycleTimer) clearTimeout(guardCycleTimer);
        if (catchTimer)      clearTimeout(catchTimer);

        overlayTitle.textContent = 'PRISON BREAK!!';
        overlayTitle.className = 'goal';
        failImage.style.display = 'none';
        goalReturnBtn.classList.add('show');
        overlay.classList.add('show');
    }

    function triggerFail() {
        if (gameOver) return;
        gameOver = true;
        caught = true;
        dashing = false;
        dashBtn.disabled = true;
        if (guardCycleTimer)    clearTimeout(guardCycleTimer);
        if (catchTimer)         clearTimeout(catchTimer);

        prisoner.src = imgPrisonerIdle;
        guard.src = imgGuardFront;

        // Guard chases from right → left toward prisoner
        const guardEl = guard;
        const cw = containerWidth();
        const guardStartRight = 5; // CSSのright値に合わせる
        const guardStartLeft = cw - guardStartRight - guardEl.offsetWidth;
        const targetLeft = prisonerX - 10;

        let step = 0;
        guardEl.style.right = '';
        guardEl.style.left = guardStartLeft + 'px';

        guardChaseInterval = setInterval(() => {
            step += 4;
            const ratio = Math.min(step / 100, 1);
            const currentLeft = guardStartLeft + (targetLeft - guardStartLeft) * ratio;
            guardEl.style.left = currentLeft + 'px';

            if (ratio >= 1) {
                clearInterval(guardChaseInterval);
                showFailScreen();
            }
        }, 20);
    }

    function showFailScreen() {
        overlayTitle.textContent = 'FAIL...';
        overlayTitle.className = 'fail';
        if (imgFailSrc) {
            failImage.src = imgFailSrc;
            failImage.style.display = 'block';
        }
        overlay.classList.add('show');

        // DASHボタンをRETRYボタンに変える
        dashBtn.textContent = 'RETRY';
        dashBtn.disabled = false;
        dashBtn.classList.remove('pressed');
        dashBtn.onclick = () => {
            dashBtn.textContent = 'DASH';
            dashBtn.onclick = null;
            init();
        };
    }

    // --- Space key ---
    document.addEventListener('keydown', (e) => {
        if (e.code !== 'Space' || e.repeat) return;
        e.preventDefault();
        if (gameOver && caught) {
            dashBtn.click();
        } else {
            onDashStart();
        }
    });
    document.addEventListener('keyup', (e) => {
        if (e.code === 'Space') {
            e.preventDefault();
            onDashEnd();
        }
    });

    // --- Button events (touch / click) ---
    dashBtn.addEventListener('mousedown',  (e) => { e.preventDefault(); onDashStart(); });
    dashBtn.addEventListener('mouseup',    (e) => { e.preventDefault(); onDashEnd(); });
    dashBtn.addEventListener('mouseleave', (e) => { onDashEnd(); });
    dashBtn.addEventListener('touchstart', (e) => { e.preventDefault(); onDashStart(); }, { passive: false });
    dashBtn.addEventListener('touchend',   (e) => { e.preventDefault(); onDashEnd(); },   { passive: false });

    function onDashStart() {
        if (gameOver) return;
        dashing = true;
        dashBtn.classList.add('pressed');
        prisoner.src = imgPrisonerRun;

        if (guardWatching) {
            const elapsed = performance.now() - guardTurnedAt;
            if (elapsed > GRACE_PERIOD_MS) triggerFail();
        }
    }

    function onDashEnd() {
        if (gameOver) return;
        dashing = false;
        dashBtn.classList.remove('pressed');
        prisoner.src = imgPrisonerIdle;
        if (catchTimer) clearTimeout(catchTimer);
    }

    retryBtn.addEventListener('click', init);

    function rand(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    init();
})();
