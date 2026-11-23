"""Teste offline (sem XMPP/BDI) com relógio virtual: perfis, manada e competição.
Rode: python teste_fuzzy.py [semente]
"""
import random
import sys
from collections import Counter

import avaliacao
import decisao
import environment
import estrategia_bar

PERIODO = 6
JANELA = PERIODO / 2
PERFIS = ["universitario"] * 3 + ["ponderado"] * 3
RODADAS = 40
random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 1)

print("--- Satisfação (sem ruído) por perfil ---")
for perfil in avaliacao.PERFIS:
    linha = [f"{j.split('@')[0]}={avaliacao.avaliar(b, perfil)[0]:.2f}"
             for j, b in environment.REGISTRO_BARES.items()]
    print(f"{perfil:14s}", "  ".join(linha))

eventos = []
for perfil in PERFIS:
    off = random.uniform(1, PERIODO)
    eventos += [(off + k * PERIODO, "cliente", perfil) for k in range(RODADAS)]
for j in environment.REGISTRO_BARES:
    off = random.uniform(2, PERIODO)
    eventos += [(off + k * PERIODO, "bar", j) for k in range(RODADAS)]
eventos.sort()

modos = Counter()
por_perfil = {p: Counter() for p in avaliacao.PERFIS}
por_modo = {m: Counter() for m in ("individual", "manada")}
for t, tipo, x in eventos:
    if tipo == "bar":
        b = environment.REGISTRO_BARES[x]
        d = estrategia_bar.fuzzy_estrategia(b["reputacao"], environment.fluxo(x))
        environment.ajustar_preco(x, 0.3 * d)
        continue
    lot = {j: environment.lotacao(j, JANELA, t) for j in environment.REGISTRO_BARES}
    j, modo, _ = decisao.escolher_bar(x, environment.REGISTRO_BARES, lot)
    bar = environment.REGISTRO_BARES[j]
    nota, _, _ = avaliacao.avaliar(avaliacao.experiencia(bar), x)
    environment.registrar_visita(j, t)
    bar["reputacao"] = estrategia_bar.fuzzy_reputacao(nota, bar["reputacao"])
    nome = j.split("@")[0]
    modos[modo] += 1
    por_perfil[x][nome] += 1
    por_modo[modo][nome] += 1

total = sum(modos.values())
print("\n--- Modos: " + ", ".join(f"{m}={n} ({100*n/total:.0f}%)" for m, n in modos.items()))
for p, c in por_perfil.items():
    print(f"{p:14s} visitas por bar:", dict(c))
for m, c in por_modo.items():
    print(f"modo {m:10s} visitas por bar:", dict(c))
print(environment.resumo())
