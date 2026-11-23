#!/usr/bin/env bash
# Instala e configura um servidor XMPP (Prosody) local para o ISMA Bar Project.
# Uso: bash scripts/instalar_prosody.sh
set -euo pipefail

sudo apt update
sudo apt install -y prosody openssl

# Certificado autoassinado (o SPADE aceita, pois não verifica certificado por padrão)
sudo mkdir -p /etc/prosody/certs
if [ ! -f /etc/prosody/certs/localhost.crt ]; then
  sudo openssl req -new -x509 -days 365 -nodes -newkey rsa:2048 \
    -subj "/CN=localhost" \
    -keyout /etc/prosody/certs/localhost.key \
    -out /etc/prosody/certs/localhost.crt
  sudo chown root:prosody /etc/prosody/certs/localhost.key /etc/prosody/certs/localhost.crt
  sudo chmod 640 /etc/prosody/certs/localhost.key
fi

[ -f /etc/prosody/prosody.cfg.lua.bak ] || sudo cp /etc/prosody/prosody.cfg.lua /etc/prosody/prosody.cfg.lua.bak

sudo tee /etc/prosody/prosody.cfg.lua >/dev/null <<'LUA'
-- Prosody para uso LOCAL (ISMA Bar Project). Escuta apenas em 127.0.0.1.
admins = { }
interfaces = { "127.0.0.1" }

modules_enabled = {
  "roster"; "saslauth"; "tls"; "disco"; "private"; "vcard_legacy";
  "version"; "uptime"; "time"; "ping"; "register";
}
modules_disabled = { "s2s" }  -- sem comunicação com servidores externos

allow_registration = true
c2s_require_encryption = false
authentication = "internal_hashed"
storage = "internal"
certificates = "certs"

pidfile = "/run/prosody/prosody.pid"
log = {
  info = "/var/log/prosody/prosody.log";
  error = "/var/log/prosody/prosody.err";
}

VirtualHost "localhost"
LUA

sudo prosodyctl check config || true
sudo systemctl enable prosody
sudo systemctl restart prosody
sleep 2
systemctl is-active prosody && echo "Prosody rodando em localhost:5222"
