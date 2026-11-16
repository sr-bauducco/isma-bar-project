"""Avaliação nebulosa que o CLIENTE faz de um bar (Mamdani).

Entradas: limpeza, preco, temperatura, decoracao (0-10, maior = melhor;
em 'preco', maior = mais barato). Saída: satisfação 0-10 com rótulo
linguístico (ruim / regular / boa / otima).
Cada perfil de cliente tem o seu próprio conjunto de regras.
"""
import random
from fuzzy import Variavel, Regra, trap, tri, inferir_mamdani

NIVEIS = ("ruim", "regular", "boa", "otima")  # código numérico = posição
ATRIBUTOS = ("limpeza", "preco", "temperatura", "decoracao")

ENTRADA = Variavel({
    "baixo": lambda x: trap(x, -1, 0, 2.5, 5),
    "medio": lambda x: tri(x, 2.5, 5, 7.5),
    "alto":  lambda x: trap(x, 5, 7.5, 10, 11),
})

SATISFACAO = Variavel({
    "ruim":    lambda x: trap(x, 0, 0, 1.5, 4),
    "regular": lambda x: tri(x, 2.5, 5, 7.5),
    "boa":     lambda x: tri(x, 5, 7, 9),
    "otima":   lambda x: trap(x, 7.5, 9, 10, 10),
})

# Universitário: só o preço importa (maior = mais barato).
REGRAS_UNIVERSITARIO = [
    Regra({"preco": "alto"}, "otima"),
    Regra({"preco": "medio"}, "regular"),
    Regra({"preco": "baixo"}, "ruim"),
]

# Ponderado: preço e temperatura da bebida.
REGRAS_PONDERADO = [
    Regra({"preco": "alto", "temperatura": "alto"}, "otima"),
    Regra({"preco": "alto", "temperatura": "medio"}, "boa"),
    Regra({"preco": "medio", "temperatura": "alto"}, "boa"),
    Regra({"preco": "medio", "temperatura": "medio"}, "regular"),
    Regra({"preco": "baixo", "temperatura": "alto"}, "regular"),
    Regra({"preco": "baixo", "temperatura": "medio"}, "ruim"),
    Regra({"preco": "alto", "temperatura": "baixo"}, "regular"),
    Regra({"preco": "medio", "temperatura": "baixo"}, "ruim"),
    Regra({"preco": "baixo", "temperatura": "baixo"}, "ruim"),
]

# peso_reputacao: quanto a reputação publicada do bar pesa na ESCOLHA (o resto é a
# percepção nebulosa dos atributos).
PERFIS = {
    "universitario": {"regras": REGRAS_UNIVERSITARIO, "peso_reputacao": 0.1},
    "ponderado":     {"regras": REGRAS_PONDERADO,     "peso_reputacao": 0.3},
}


def avaliar(attrs, perfil):
    """Satisfação nebulosa -> (nota 0-10, rótulo, graus por rótulo)."""
    graus = {v: ENTRADA.fuzzificar(max(0.0, min(10.0, attrs[v]))) for v in ATRIBUTOS}
    nota, ativ = inferir_mamdani(PERFIS[perfil]["regras"], graus, SATISFACAO)
    rotulo, _ = SATISFACAO.rotular(nota)
    return nota, rotulo, ativ


def experiencia(attrs, ruido=0.7):
    """O que o cliente realmente sente na visita: atributos + variação aleatória."""
    return {k: max(0.0, min(10.0, v + random.gauss(0, ruido)))
            for k, v in attrs.items() if k in ATRIBUTOS}
