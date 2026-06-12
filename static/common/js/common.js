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

// オートコンプリート機能
// クリアボタンの初期化
function initClearBtn(clearBtnId, nameInputId, idInputId) {
    const clearBtn = document.querySelector(clearBtnId);
    if (!clearBtn) return;

    clearBtn.addEventListener('click', function() {
        document.querySelector(nameInputId).value = '';
        const idInput = document.querySelector(idInputId);
        if (idInput) {
            idInput.value = '';
        }
    });
}

// オートコンプリートの初期化
function initAutocomplete(nameInputId, dropdownId, apiUrl, idInputId) {
    const nameInput = document.querySelector(nameInputId);
    const dropdown = document.querySelector(dropdownId);
    if (!nameInput || !dropdown) return;

    let selectedFromDropdown = false;

    async function showSuggestions(query) {
        const res = await fetch(`${apiUrl}?q=${query}`);
        const data = await res.json();

        dropdown.innerHTML = '';
        data.forEach(item => {
            const li = document.createElement('li');
            li.className = 'list-group-item list-group-item-action';
            li.textContent = item.name;
            li.addEventListener('click', () => {
                nameInput.value = item.name;
                const idInput = document.querySelector(idInputId);
                if (idInput) {
                    idInput.value = item.id;
                }
                dropdown.innerHTML = '';
                selectedFromDropdown = true;
            });
            dropdown.appendChild(li);
        });
    }

    nameInput.addEventListener('input', async function() {
        await showSuggestions(nameInput.value);
    });

    // フォーム欄クリック時にドロップダウンを表示する
    nameInput.addEventListener('focus', async function() {
        if (selectedFromDropdown) {
            selectedFromDropdown = false;
            return;
        }
        await showSuggestions(nameInput.value);
    });

    // フォーム欄外クリック時にドロップダウンを閉じる
    nameInput.addEventListener('blur', function() {
        dropdown.innerHTML = '';
        selectedFromDropdown = false;
    });

    // liクリック時にblurが先に発火してドロップダウンが消えるのを防ぐ
    dropdown.addEventListener('mousedown', function(e) {
        e.preventDefault();
    });
}

// 店舗名
initClearBtn('#shop-clear-btn', '#shop-name-input', '#shop-id-input');
initAutocomplete('#shop-name-input', '#shop-name-dropdown', '/common/api/shops/autocomplete/', '#shop-id-input');

// 倉庫名
initClearBtn('#warehouse-clear-btn', '#warehouse-name-input', '#warehouse-id-input');
initAutocomplete('#warehouse-name-input', '#warehouse-name-dropdown', '/common/api/warehouses/autocomplete/', '#warehouse-id-input');

