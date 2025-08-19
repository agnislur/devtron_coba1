FROM curlimages/curl:latest

# Langsung salin dan berikan izin eksekusi dalam satu perintah
COPY --chmod=755 run.sh /app/run.sh

CMD ["/app/run.sh"]
