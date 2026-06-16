const escapeBtn = document.querySelector('#escape-link');
let timer = null;
let hideTimer = null;

document.addEventListener('mousemove', (e) => {
    const isBottomRight =
        e.clientX >= window.innerWidth - 40 &&
        e.clientY >= window.innerHeight - 40;

    if (isBottomRight) {
        if (timer) return;

        timer = setTimeout(() => {
            showEscapeBtn();

            hideTimer = setTimeout(() => {
                hideEscapeBtn();
            }, 5000);
        }, 5000);

    } else {
        clearTimeout(timer);
        timer = null;
    }
});

function showEscapeBtn() {
    escapeBtn.classList.add('show');
}

function hideEscapeBtn() {
    escapeBtn.classList.remove('show');
}