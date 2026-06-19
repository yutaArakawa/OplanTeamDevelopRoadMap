# envsubst：テンプレート（nginx.conf）の $BASIC を環境変数の値に置換して本番用に保存し、Nginxをフォアグラウンドで起動
envsubst '$BASIC $STATIC_CACHE_CONTROL $STATIC_DIR $REACT_LOCATION' < /etc/nginx/temp/nginx.conf > /etc/nginx/conf.d/nginx.conf && nginx -g 'daemon off;'
