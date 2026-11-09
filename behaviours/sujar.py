from spade.behaviour import PeriodicBehaviour

import relogio

# VALORES PADROES DA SUJEIRA (em tempo simulado)
PERIODO_SUJAR_HORAS = 1     # a cada ~1 hora simulada o bar suja
SUJEIRA_BASE = 0.1          # queda por hora, mesmo vazio (10 -> 0 em ~4 dias)
SUJEIRA_POR_CLIENTE = 0.02  # queda extra por hora para cada cliente presente
LOG_A_CADA_HORAS = 6        # imprime o nível de limpeza a cada 6 horas simuladas


class Sujar(PeriodicBehaviour):
    """O bar fica mais sujo com o tempo; quanto mais clientes, mais rápido.

    queda = (base + por_cliente * nº de clientes) * horas simuladas desde a última execução.
    Usar as horas que realmente passaram (e não "1 execução = 1 hora") deixa o resultado
    igual em qualquer escala do relógio. Não faz nada antes do relógio começar.
    """

    def __init__(self, period=None, base=SUJEIRA_BASE, por_cliente=SUJEIRA_POR_CLIENTE, **kwargs):
        if period is None:
            period = relogio.periodo(relogio.horas(PERIODO_SUJAR_HORAS))
        super().__init__(period=period, **kwargs)
        self.base = base
        self.por_cliente = por_cliente
        self._ultima_hora = None  # hora simulada da última execução
        self._ultimo_log = None

    def taxa(self):
        """Queda de limpeza por hora simulada."""
        return self.base + self.por_cliente * len(self.agent.clientes)

    async def run(self):
        if not relogio.rodando():
            return

        agora = relogio.dias_passados() * 24
        if self._ultima_hora is None:
            self._ultima_hora = self._ultimo_log = agora
            return

        horas = agora - self._ultima_hora
        self._ultima_hora = agora
        bar = self.agent
        bar.nivel_limpeza = max(0.0, bar.nivel_limpeza - self.taxa() * horas)

        if agora - self._ultimo_log >= LOG_A_CADA_HORAS:
            self._ultimo_log = agora
            print(
                f"[{bar.jid.user}] dia {relogio.dia_atual()} {relogio.hora_do_dia():02d}h "
                f"nível de limpeza: {bar.nivel_limpeza:.1f} "
                f"(-{self.taxa():.2f}/h, {len(bar.clientes)} clientes)"
            )
