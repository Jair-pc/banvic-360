FROM n8nio/n8n:1.70.3

USER root

# psql (para executar SQL files via Execute Command nodes)
# python3 + pip (para rodar scripts do projeto)
RUN apk add --no-cache \
    postgresql15-client \
    python3 \
    py3-pip \
    bash \
 && pip3 install --no-cache-dir --break-system-packages psycopg2-binary pandas

USER node
