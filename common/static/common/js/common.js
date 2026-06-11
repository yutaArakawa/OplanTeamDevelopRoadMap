// 権限セレクトの change イベントを監視
const authoritySelect          = document.getElementById('authority-select');
const belongingSelect          = document.getElementById('belonging-select');
const belongingSelectShop      = document.getElementById('belonging-select-shop');
const belongingSelectWarehouse = document.getElementById('belonging-select-warehouse');
if (authoritySelect) {
    authoritySelect.addEventListener('change', function () {
        const isAdmin     = this.value == AUTHORITY_ADMIN;     // 管理者: '1'
        const isShop      = this.value == AUTHORITY_SHOP;      // 店舗スタッフ: '2'
        const isWarehouse = this.value == AUTHORITY_WAREHOUSE; // 倉庫スタッフ: '3'

        // 検索フォームが所属の場合はこっち
        if (belongingSelect) {
            // 所属セレクトを無効化 & 値をリセット
            belongingSelect.disabled = isAdmin;
            if (isAdmin) belongingSelect.value = '';
        }

        // 検索フォームの所属が店舗と倉庫で分かれてる場合はこっち
        if (belongingSelectShop && belongingSelectWarehouse) {

            //　無効化フラグを権限ごとに設定
            const disableShop      = isAdmin || isWarehouse; // 管理者と倉庫スタッフは店舗セレクトを無効化
            const disableWarehouse = isAdmin || isShop;  // 管理者と店舗スタッフは倉庫セレクトを無効化

            //　値のリセット
            if (disableShop)      belongingSelectShop.value      = '';
            if (disableWarehouse) belongingSelectWarehouse.value = '';

            // 有効無効の設定
            belongingSelectShop.disabled      = disableShop;
            belongingSelectWarehouse.disabled = disableWarehouse;

        }
    });

    // ページロード時に change イベントを発火させて初期状態を設定
    document.addEventListener('DOMContentLoaded', function () {
        const event = new Event('change');
        authoritySelect.dispatchEvent(event);
    })
}

document.addEventListener('DOMContentLoaded', function() {
    const deleteModal = document.getElementById('deleteModal');
    if (deleteModal) {
        deleteModal.addEventListener('show.bs.modal', function(event) {
            const btn = event.relatedTarget;
            const url = btn.getAttribute('data-delete-url');
            document.getElementById('deleteForm').action = url;
        })
    }
})
