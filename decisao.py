"""Como o cliente escolhe o bar (músculo em Python puro, testável sem XMPP).

- Modo INDIVIDUAL: segue o próprio perfil
    universitario -> quase só preço (percepção nebulosa) + 10% reputação
    ponderado     -> preço e temperatura (nebuloso, 70%) + reputação (30%)
- Modo MANADA: se algum bar teve MAIS de LIMITE_MANADA clientes na janela
  recente, o cliente ignora o perfil e pondera só preço e reputação (50/50),
  com escolha quase determinística -> todos tendem ao mesmo bar.
"""
import math
import random

import avaliacao

LIMITE_MANADA = 2      # "mais de 2" clientes no mesmo bar ativa a manada
PESO_PRECO_MANADA = 0.5
TEMP_INDIVIDUAL = 1.0  # temperatura do softmax: menor = mais determinístico
TEMP_MANADA = 0.4


def valor_individual(perfil, bar):
    perc, _, _ = avaliacao.avaliar(bar, perfil)
    w = avaliacao.PERFIS[perfil]["peso_reputacao"]
    return (1 - w) * perc + w * bar["reputacao"]


def valor_manada(bar):
    return PESO_PRECO_MANADA * bar["preco"] + (1 - PESO_PRECO_MANADA) * bar["reputacao"]


def modo_de(lotacoes, limite=LIMITE_MANADA):
    return "manada" if lotacoes and max(lotacoes.values()) > limite else "individual"


def escolher_bar(perfil, bares, lotacoes, limite=LIMITE_MANADA, rng=random):
    """Devolve (jid_escolhido, modo, valores_por_bar)."""
    modo = modo_de(lotacoes, limite)
    if modo == "manada":
        valores = {j: valor_manada(b) for j, b in bares.items()}
        temp = TEMP_MANADA
    else:
        valores = {j: valor_individual(perfil, b) for j, b in bares.items()}
        temp = TEMP_INDIVIDUAL
    pesos = {j: math.exp(v / temp) for j, v in valores.items()}
    r, acum = rng.uniform(0, sum(pesos.values())), 0.0
    for j, p in pesos.items():
        acum += p
        if r <= acum:
            break
    return j, modo, valores
