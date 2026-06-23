const sidebarEl = document.querySelector('#offcanvasSidebar');
const sidebar = new bootstrap.Offcanvas(sidebarEl)

document.addEventListener('mousemove', (e) => {
    // マウスのX座標が左端から20px以内に入ったら発火
    if (e.clientX <= 20) {
        sidebar.show();
    }
});
// サイドバーからマウスが離れたら閉じる
sidebarEl.addEventListener('mouseleave', () => {
    sidebar.hide();
});