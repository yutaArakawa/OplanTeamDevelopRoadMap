class ApiStatus:
    OK    = 'ok'
    ERROR = 'error'

class ApiErrorMsg:
    REQUIRED_FIELDS_LOGIN = 'ユーザー名とパスワードを入力してください'
    ACCOUNT_INVALID = 'ユーザー名またはパスワードが違います'
    ACCOUNT_DELETED = 'このアカウントは削除されています'
    UNAUTHORIZED    = '認証が必要です'

class ApiResponseStatus:
    OK                    = 200 # 成功
    BAD_REQUEST           = 400 # リクエストが不正。必須項目未入力など形式がおかしい場合。
    UNAUTHORIZED          = 401 # 認証失敗。
    FORBIDDEN             = 403 # 認証はできているが権限がない。
    NOT_FOUND             = 404 # リソースが存在しない。
    INTERNAL_SERVER_ERROR = 500 # サーバー側の予期しないエラー。
