const escapeBtn = document.querySelector('#escape-link');
let timer = null;
let hideTimer = null;

document.addEventListener('mousemove', (e) => {
    const isBottomRight = 
        e.clientX >= window.innerWidth - 20 && 
        e.clientY >= window.innerHeight - 20;

    if (isBottomRight) {
        if (timer) return;

        timer = setTimeout(() => {
            escapeBtn.show();

            hideTimer = setTimeout(() => {
                escapeBtn.hide();
            }, 5000);
        }, 5000);

    } else {
        clearTimeout(timer);
        timer = null;
    }
});