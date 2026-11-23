"""Teste offline (sem XMPP): todo cliente tenta ir a um bar em todo horário de pico.
Rode: python teste_pico.py
"""
import random

from agents.Cliente import HORARIO_PICO_HORAS, INTERVALO_VISITA_HORAS, horas_ate_proxima_visita

DIAS = 30
inicio, fim = HORARIO_PICO_HORAS

for semente in range(200):
    rng = random.Random(semente)
    agora, picos = 0.0, set()   # 1ª tentativa na hora 0, como na simulação
    while agora < DIAS * 24:
        if inicio <= agora % 24 <= fim:
            picos.add(int(agora // 24))
        descanso = horas_ate_proxima_visita(agora, rng)
        assert 0 < descanso <= max(INTERVALO_VISITA_HORAS[1], 24 + fim - inicio), descanso
        agora += descanso
    assert picos == set(range(DIAS)), f"semente {semente}: pulou o pico dos dias {set(range(DIAS)) - picos}"

print(f"ok: {DIAS} dias x 200 clientes, nenhum pico pulado")
