"""Motor nebuloso mínimo (Mamdani e Sugeno), sem dependências externas.

Tudo vive na escala 0-10, a mesma de environment.py.
"""
from dataclasses import dataclass


def trap(x, a, b, c, d):
    """Função de pertinência trapezoidal (a<=b<=c<=d)."""
    if x < a or x > d:
        return 0.0
    if x < b:
        return (x - a) / (b - a) if b != a else 1.0
    if x <= c:
        return 1.0
    return (d - x) / (d - c) if d != c else 1.0


def tri(x, a, b, c):
    """Função de pertinência triangular."""
    return trap(x, a, b, b, c)


class Variavel:
    """Variável linguística: nome do conjunto -> função de pertinência."""

    def __init__(self, conjuntos):
        self.conjuntos = conjuntos

    def fuzzificar(self, x):
        return {nome: f(x) for nome, f in self.conjuntos.items()}

    def rotular(self, x):
        graus = self.fuzzificar(x)
        return max(graus, key=graus.get), graus


@dataclass
class Regra:
    se: dict        # {variavel: conjunto}, antecedentes ligados por E (mínimo)
    entao: object   # Mamdani: nome do conjunto de saída | Sugeno: número


ESCALA = [i / 10 for i in range(101)]  # 0.0 ... 10.0


def _forca(regra, graus):
    return min(graus[v][c] for v, c in regra.se.items())


def inferir_mamdani(regras, graus, saida, peso=None):
    """Mamdani com agregação por máximo e defuzzificação por centroide.

    graus: {variavel: {conjunto: grau}}
    peso:  função opcional regra -> fator em [0,1] (perfil do cliente)
    Devolve (valor_nítido, ativação_por_conjunto_de_saída).
    """
    ativ = {}
    for r in regras:
        f = _forca(r, graus) * (peso(r) if peso else 1.0)
        ativ[r.entao] = max(ativ.get(r.entao, 0.0), f)
    num = den = 0.0
    for x in ESCALA:
        mu = max((min(a, saida.conjuntos[c](x)) for c, a in ativ.items()), default=0.0)
        num += x * mu
        den += mu
    return (num / den if den > 1e-9 else 5.0), ativ


def inferir_sugeno(regras, graus, padrao=0.0):
    """Sugeno de ordem zero: média ponderada das saídas constantes."""
    num = den = 0.0
    for r in regras:
        f = _forca(r, graus)
        num += f * r.entao
        den += f
    return num / den if den > 1e-9 else padrao
