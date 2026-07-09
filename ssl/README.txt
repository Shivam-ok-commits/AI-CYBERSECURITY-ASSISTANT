Place your SSL certificate and key files here:

  - cert.pem  (SSL certificate)
  - key.pem   (SSL private key)

For development, generate a self-signed certificate:
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem -out ssl/cert.pem \
    -subj "/CN=localhost"

For production, use Let's Encrypt or a commercial CA.
