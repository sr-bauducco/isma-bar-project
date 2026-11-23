"""Lógica nebulosa do BAR (Sugeno).

1) fuzzy_reputacao: taxa de aprendizado adaptativa da média móvel. Quanto
   mais a nota "surpreende" a reputação atual, mais ela pesa (alfa maior).
2) fuzzy_estrategia: decide ajuste de preço com base em reputação e fluxo
   de clientes (promoção quando está vazio, reajuste quando está cheio).
"""
from fuzzy import Variavel, Regra, trap, tri, inferir_sugeno

SURPRESA = Variavel({
    "pequena": lambda x: trap(x, -1, 0, 1, 3),
    "media":   lambda x: tri(x, 1, 3, 5),
    "grande":  lambda x: trap(x, 3, 5, 10, 11),
})

NIVEL = Variavel({
    "baixo": lambda x: trap(x, -1, 0, 2.5, 5),
    "medio": lambda x: tri(x, 2.5, 5, 7.5),
    "alto":  lambda x: trap(x, 5, 7.5, 10, 11),
})

REGRAS_ALFA = [
    Regra({"surpresa": "pequena"}, 0.15),
    Regra({"surpresa": "media"}, 0.30),
    Regra({"surpresa": "grande"}, 0.50),
]

# saída: variação do "score" de preço (positivo = ficar mais barato)
REGRAS_PRECO = [
    Regra({"reputacao": "baixo", "fluxo": "baixo"}, +1.0),
    Regra({"reputacao": "baixo", "fluxo": "medio"}, +0.4),
    Regra({"reputacao": "baixo", "fluxo": "alto"}, 0.0),
    Regra({"reputacao": "medio", "fluxo": "baixo"}, +0.6),
    Regra({"reputacao": "medio", "fluxo": "medio"}, 0.0),
    Regra({"reputacao": "medio", "fluxo": "alto"}, -0.3),
    Regra({"reputacao": "alto", "fluxo": "baixo"}, +0.3),
    Regra({"reputacao": "alto", "fluxo": "medio"}, -0.3),
    Regra({"reputacao": "alto", "fluxo": "alto"}, -0.8),
]


def fuzzy_reputacao(nota, reputacao_atual):
    """Nova reputação (0-10) via EMA com alfa nebuloso."""
    graus = {"surpresa": SURPRESA.fuzzificar(abs(nota - reputacao_atual))}
    alfa = inferir_sugeno(REGRAS_ALFA, graus, padrao=0.3)
    return alfa * nota + (1 - alfa) * reputacao_atual


def fuzzy_estrategia(reputacao, fluxo):
    """Delta de preço em pontos de score; fluxo já na escala 0-10 (5 = média)."""
    graus = {"reputacao": NIVEL.fuzzificar(reputacao), "fluxo": NIVEL.fuzzificar(fluxo)}
    return inferir_sugeno(REGRAS_PRECO, graus)
