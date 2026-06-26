// @ts-nocheck
(function () {
    const sidebar  = document.getElementById('appSidebar');
    const overlay  = document.getElementById('sidebarOverlay');
    const toggle   = document.getElementById('sidebarToggle');

    if (!sidebar) return;

    function openSidebar() {
        sidebar.classList.add('sidebar-open');
        overlay && overlay.classList.add('show');
    }
    function closeSidebar() {
        sidebar.classList.remove('sidebar-open');
        overlay && overlay.classList.remove('show');
    }

    toggle  && toggle.addEventListener('click', openSidebar);
    overlay && overlay.addEventListener('click', closeSidebar);

    // PC幅に戻ったらモバイル用クラスをリセット
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 992) closeSidebar();
    });

    // 現在のURLに対応するナビリンクをアクティブに
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('sidebar-link-active');
        }
    });
})();
