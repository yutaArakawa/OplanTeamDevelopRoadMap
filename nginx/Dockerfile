FROM nginx:1.20.2
RUN rm -f /etc/nginx/conf.d/*
RUN apt-get update \
  && apt-get install -y apt-transport-https vim \
  && apt-get clean
COPY gen_htpasswd /etc/nginx
RUN apt install -y openssl
RUN chmod 777 /etc/nginx/gen_htpasswd
RUN /etc/nginx/gen_htpasswd
ADD /script/entrypoint.sh /app/script/entrypoint.sh
ENTRYPOINT ["sh", "/app/script/entrypoint.sh"]