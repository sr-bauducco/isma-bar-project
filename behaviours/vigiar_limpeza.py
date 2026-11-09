from spade.behaviour import PeriodicBehaviour
from spade.message import Message

import relogio

# VALORES PADROES DA VIGILANCIA (em tempo simulado)
PERIODO_VIGIAR_MINUTOS = 30   # o bar confere a limpeza a cada 30 min simulados
LIMITE_LIMPEZA = 6.0          # abaixo disso o bar chama uma faxineira


class VigiarLimpeza(PeriodicBehaviour):
    """Behaviour do Bar: se o nível de limpeza estiver baixo, chama uma faxineira livre.

    "Livre" é decidido pelo próprio bar (agent.chamados_pendentes): uma faxineira que já
    foi chamada e ainda não respondeu "limpeza_feita" não é chamada de novo.
    """

    def __init__(self, period=None, limite=LIMITE_LIMPEZA, **kwargs):
        if period is None:
            period = relogio.periodo(relogio.minutos(PERIODO_VIGIAR_MINUTOS))
        super().__init__(period=period, **kwargs)
        self.limite = limite

    async def run(self):
        bar = self.agent
        if bar.nivel_limpeza >= self.limite:
            return

        livre = next(
            (f for f in bar.faxineiras if str(f.jid) not in bar.chamados_pendentes),
            None,
        )
        if livre is None:
            return

        msg = Message(to=str(livre.jid))
        msg.set_metadata("performative", "request")
        msg.set_metadata("ontology", "limpar")
        await self.send(msg)

        bar.chamados_pendentes.add(str(livre.jid))
        print(f"[{bar.jid.user}] limpeza em {bar.nivel_limpeza:.1f}, chamei {livre.jid.user}")
