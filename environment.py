"""Ambiente compartilhado ("Páginas Amarelas") dos agentes.

Como todos os agentes rodam no mesmo processo (main.py), este módulo faz o
papel de ambiente: os bares publicam atributos e reputação; os clientes
consultam e registram visitas.
"""
import os
import time

DOMINIO = os.getenv("XMPP_DOMAIN", "localhost")


def jid(nome):
    return f"{nome}@{DOMINIO}"


# Atributos 0-10, maior = melhor. Em 'preco', maior = mais barato.
_BASE = {
    "bar1_premium":  {"limpeza": 9.5, "preco": 3.0, "temperatura": 8.0, "decoracao": 9.0},
    "bar2_coposujo": {"limpeza": 4.0, "preco": 9.5, "temperatura": 9.0, "decoracao": 3.0},
    "bar3_modinha":  {"limpeza": 8.0, "preco": 5.0, "temperatura": 7.5, "decoracao": 8.5},
}

REGISTRO_BARES = {
    jid(nome): {**attrs, "preco_base": attrs["preco"],
                "reputacao": 5.0, "visitas": 0, "lucro": 0.0}
    for nome, attrs in _BASE.items()
}

LIMITE_PRECO = 4.0  # quanto o bar pode se afastar do preço base (em pontos)


_VISITAS_RECENTES = {j: [] for j in REGISTRO_BARES}  # timestamps por bar


def lotacao(jid_bar, janela, agora=None):
    """Quantos clientes chegaram ao bar nos últimos `janela` segundos."""
    agora = time.monotonic() if agora is None else agora
    return sum(1 for t in _VISITAS_RECENTES[jid_bar] if agora - t <= janela)


def registrar_visita(jid_bar, agora=None):
    agora = time.monotonic() if agora is None else agora
    _VISITAS_RECENTES[jid_bar].append(agora)
    bar = REGISTRO_BARES[jid_bar]
    bar["visitas"] += 1
    bar["lucro"] += 1.0 + (10.0 - bar["preco"])  # preço mais alto => mais margem


def fluxo(jid_bar):
    """Fluxo relativo na escala 0-10 (5 = igual à média dos bares)."""
    visitas = [b["visitas"] for b in REGISTRO_BARES.values()]
    media = sum(visitas) / len(visitas)
    if media == 0:
        return 5.0
    return min(10.0, 5.0 * REGISTRO_BARES[jid_bar]["visitas"] / media)


def ajustar_preco(jid_bar, delta):
    bar = REGISTRO_BARES[jid_bar]
    base = bar["preco_base"]
    novo = max(base - LIMITE_PRECO, min(base + LIMITE_PRECO, bar["preco"] + delta))
    bar["preco"] = max(0.0, min(10.0, novo))
    return bar["preco"]


def resumo():
    linhas = ["", "=== Resultado final ==="]
    for j, b in sorted(REGISTRO_BARES.items(), key=lambda kv: -kv[1]["visitas"]):
        linhas.append(f"{j:28s} visitas={b['visitas']:3d} reputacao={b['reputacao']:.2f} "
                      f"preco(score)={b['preco']:.2f} lucro={b['lucro']:.1f}")
    return "\n".join(linhas)
