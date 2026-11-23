#!/usr/bin/env bash
# Cria (ou recria) as contas dos agentes no Prosody local.
# Uso: bash scripts/criar_contas.sh        (variáveis opcionais: XMPP_DOMAIN, XMPP_SENHA, N_CLIENTES)
set -euo pipefail

DOMINIO="${XMPP_DOMAIN:-localhost}"
SENHA="${XMPP_SENHA:-senha123}"
N="${N_CLIENTES:-6}"   # deve ser igual ao tamanho de PERFIS_CLIENTES em main.py

contas=(bar1_premium bar2_coposujo bar3_modinha)
for i in $(seq 1 "$N"); do contas+=("cliente$i"); done

for c in "${contas[@]}"; do
  sudo prosodyctl deluser "$c@$DOMINIO" >/dev/null 2>&1 || true
  sudo prosodyctl register "$c" "$DOMINIO" "$SENHA"
  echo "conta criada: $c@$DOMINIO"
done
