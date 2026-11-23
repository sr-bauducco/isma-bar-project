"""Teste offline (sem XMPP) das decisões semanais do bar.
Rode: python teste_gestao.py
"""
from behaviours.gestao import (
    FATOR_PRECO_MAX, FATOR_PRECO_MIN, LOTACAO_LIMITE, MAX_ATENDENTES_BAR, decidir,
)

base = dict(espera_media=10, recusas=0, reputacao=6, num_atendentes=2, lotacao=10, fator_preco=1.0)

assert decidir(**base) == []
assert decidir(**{**base, "espera_media": 30}) == ["atendente"]
assert decidir(**{**base, "recusas": 50}) == ["cadeiras"]
assert decidir(**{**base, "reputacao": 4}) == ["baixar_preco"]
assert decidir(**{**base, "reputacao": 8}) == ["subir_preco"]
# várias decisões na mesma semana
assert decidir(**{**base, "espera_media": 30, "recusas": 50, "reputacao": 4}) == ["atendente", "cadeiras", "baixar_preco"]
# no limite, aquela opção não entra
assert decidir(**{**base, "espera_media": 30, "num_atendentes": MAX_ATENDENTES_BAR, "recusas": 50}) == ["cadeiras"]
assert decidir(**{**base, "recusas": 50, "lotacao": LOTACAO_LIMITE}) == []
assert decidir(**{**base, "reputacao": 4, "fator_preco": FATOR_PRECO_MIN}) == []
assert decidir(**{**base, "reputacao": 8, "fator_preco": FATOR_PRECO_MAX}) == []

# faturamento caiu (preco_rivais informado): o preço segue a comparação com os concorrentes
perdendo = {**base, "reputacao": 8, "preco_medio": 18.25}
assert decidir(**{**perdendo, "preco_rivais": 16.0}) == ["baixar_preco"]   # mais caro que eles, apesar da reputação alta
assert decidir(**{**perdendo, "preco_rivais": 20.0}) == ["subir_preco"]
assert decidir(**{**perdendo, "preco_rivais": 18.25, "reputacao": 4}) == ["baixar_preco"]  # preço igual: vale a reputação
assert decidir(**{**perdendo, "preco_rivais": 16.0, "espera_media": 30}) == ["atendente", "baixar_preco"]

print("ok: decisões semanais do bar")
