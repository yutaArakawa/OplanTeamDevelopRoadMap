# frontend/CLAUDE.md

`frontend/` ディレクトリ内のReactコードを扱う際のガイドラインです。

---

## Django画面とReact画面の切り分け

このシステムはDjangoテンプレートによる既存画面とReactによる新画面が共存しています。

| 種別 | URLパターン | 例 |
|---|---|---|
| **React画面** | `/react/` で始まる | `/react/`、`/react/login`、`/react/accounts/user/list` |
| **Django画面** | `/react/` 以外 | `/accounts/login/`、`/inventory/orders/` |
| **Django API** | `/api/` で始まる | `/api/auth/login/`、`/api/accounts/user/list/` |

- ReactはDjango APIにaxiosでリクエストし、セッションベース認証（Cookie）を使用する
- Django側の既存テンプレート・ビュー・URLは引き続き動作する
- 新規画面はReactで実装し、既存Django画面はそのまま維持する

---

## ディレクトリ構成

```
frontend/src/
├── features/               # 画面単位のコンポーネント・API
│   ├── auth/               # ログイン・ログアウト
│   │   ├── LoginPage.jsx
│   │   ├── LoginPage.css
│   │   └── authApi.js
│   ├── dashboard/          # ホーム画面
│   │   ├── HomePage.jsx
│   │   ├── AdminHome.jsx
│   │   └── dashboardApi.js
│   └── accounts/           # ユーザー管理
│       ├── UserListPage.jsx
│       └── accountsApi.js
└── shared/                 # 複数画面で共有するもの
    ├── api/client.js       # axiosインスタンス（CSRFトークン付与）
    ├── components/
    │   ├── Layout.jsx      # ヘッダー・サイドバーを含む共通レイアウト
    │   ├── Layout.css
    │   └── Sidebar.jsx
    ├── hooks/useAuth.js    # ログインユーザー情報取得フック
    └── constants.js        # AUTHORITY_* 等の定数
```

**`features/` の命名規則：**
- 画面コンポーネント：`〇〇Page.jsx`
- API呼び出し：`〇〇Api.js`
- CSS：`〇〇Page.css`（そのページ専用のスタイルのみ）

---

## ルーティング（App.jsx）

React Router v6 を使用。`BrowserRouter basename="/react"` で `/react` 配下を管理する。

```jsx
<BrowserRouter basename="/react">
  <Routes>
    {/* ログイン画面（ヘッダー・サイドバーなし） */}
    <Route path="/login" element={<LoginPage />} />

    {/* 以降はヘッダー・サイドバーあり */}
    <Route element={<Layout><Outlet /></Layout>}>
      <Route path="/" element={<HomePage />} />
      <Route path="/accounts/user/list" element={<UserListPage />} />
    </Route>
  </Routes>
</BrowserRouter>
```

新しい画面を追加する場合は `<Route element={<Layout><Outlet /></Layout>}>` ブロック内に追記する。

---

## 認証

- セッションベース認証（JWT不使用）
- `useAuth()` フックで `/api/auth/me/` を呼び出してログインユーザー情報（`userInfo`）を取得する
- 未認証時（401レスポンス）は `client.js` のレスポンスインターセプターが自動で `/react/login` にリダイレクト
- CSRF：`CSRF_COOKIE_HTTPONLY = False`（settings.py）に設定し、Cookieの `csrftoken` を `X-CSRFToken` ヘッダーに付与する（`client.js` のリクエストインターセプターで処理）

---

## API呼び出し

- `shared/api/client.js` の `apiClient`（axiosインスタンス）を使用する
- `baseURL` は `/api` なので、各APIファイルのパスは `/auth/login/` のように `/api` を省略して記述する

```js
// 例：features/accounts/accountsApi.js
import apiClient from '../../shared/api/client'

export const getUserList = (filters = {}) => {
    return apiClient.get('/accounts/user/list/', { params: filters })
}
```

---

## 検索フィルターのパターン

検索フォームは**選択肢を変更した時点で即座に絞り込みを実行**する。検索ボタンは設置しない。

```jsx
const [filters, setFilters] = useState({ authority: '', shop: '' })

// filtersが変わるたびにAPIを呼び直す
useEffect(() => {
    const activeFilters = Object.fromEntries(
        Object.entries(filters).filter(([, v]) => v !== '')
    )
    fetchApi(activeFilters).then(res => setData(res.data))
}, [filters])

const handleFilterChange = (e) => {
    const { name, value } = e.target
    setFilters(prev => ({ ...prev, [name]: value }))
}
```

- フィルターの選択肢（セレクトボックスのoption）と絞り込み結果（一覧データ）は別々のstateで管理する
  - 選択肢は初回マウント時のみ取得（`useEffect(fetchOptions, [])`）
  - 結果は `useEffect(fetchResults, [filters])` で管理
  - 混在させると、フィルター変更のたびに選択肢が再レンダリングされてセレクトがリセットされる
- リセットボタンは設置してよい（`setFilters` で初期値に戻す）

**権限セレクトが所属店舗・倉庫セレクトを制御するパターン（`common.js` と同等の挙動）：**

```js
const handleFilterChange = (e) => {
    const { name, value } = e.target
    if (name === 'authority') {
        const isAdmin     = value == AUTHORITY_ADMIN
        const isShop      = value == AUTHORITY_SHOP
        const isWarehouse = value == AUTHORITY_WAREHOUSE
        setFilters(prev => ({
            ...prev,
            authority: value,
            shop:      (isAdmin || isWarehouse) ? '' : prev.shop,
            warehouse: (isAdmin || isShop)      ? '' : prev.warehouse,
        }))
    } else {
        setFilters(prev => ({ ...prev, [name]: value }))
    }
}
```

セレクトには `disabled` 属性で操作不可を表現する：

```jsx
<select
    name="shop"
    disabled={filters.authority == AUTHORITY_ADMIN || filters.authority == AUTHORITY_WAREHOUSE}
    ...
>
```

---

## スタイリング

- **Bootstrapを優先**：可能な限りBootstrapのユーティリティクラスを使用する
- **CSS**：ページ固有のCSSは `features/〇〇/〇〇Page.css` に記述し、JSXでimportする
  ```jsx
  import './LoginPage.css'
  ```
- Viteがビルド時にキャッシュバスティングを自動で処理する（ファイル名にハッシュ付与）
- インライン`style={{}}`は使用しない

---

## Django側のAPI実装規則

ReactからJSON APIとして呼び出されるDjango viewは以下の規則に従う：

- `django.views.View` を継承（DRF の `APIView` は使用しない）
- レスポンスは `JsonResponse` で返す
- 認証チェック：`request.user.is_authenticated` で確認し、未認証は401を返す
- エラーメッセージ・ステータスコードは `common/api_constants.py` の定数を使用する
- URLファイルはDjango既存の `urls.py` とは別に `api_〇〇_urls.py` として作成し、`config/urls.py` で `api/` プレフィックスで登録する
  - 例：`accounts/api_auth_urls.py` → `path('api/auth/', include('accounts.api_auth_urls'))`
  - 例：`accounts/api_accounts_urls.py` → `path('api/accounts/', include('accounts.api_accounts_urls'))`
- クエリセットをJSONで返す場合は `list(qs.values(...))` でシリアライズしてから `JsonResponse({'key': list})` に渡す
