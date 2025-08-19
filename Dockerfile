# Menggunakan image dasar yang sudah memiliki curl
FROM curlimages/curl:latest

# Salin script ke dalam image
COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh

# Perintah default saat container dijalankan
CMD ["/app/run.sh"]
