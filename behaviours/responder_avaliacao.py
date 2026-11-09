import json

from spade.behaviour import CyclicBehaviour


class ResponderAvaliacao(CyclicBehaviour):
    """Behaviour do Bar: responde quem pergunta a avaliação dele (protocolo FIPA Query).

    Recebe:  query-ref / avaliacao  (body vazio)
    Responde: inform / avaliacao    body JSON:
        {"bar": "bar1@localhost", "nota_geral": 8.25,
         "pontuacao": {"limpeza": 10.0, ...}, "num_avaliacoes": 7}
    """

    async def run(self):
        msg = await self.receive(timeout=10)
        if not msg:
            return

        bar = self.agent
        resp = msg.make_reply()
        resp.set_metadata("performative", "inform")
        resp.set_metadata("ontology", "avaliacao")
        resp.body = json.dumps({
            "bar": str(bar.jid),
            "nota_geral": round(bar.nota_geral, 2),
            "pontuacao": {c: round(v, 2) for c, v in bar.pontuacao.items()},
            "num_avaliacoes": sum(len(notas) for notas in bar.avaliacoes.values()),
        })
        await self.send(resp)
        print(f"[{bar.jid.user}] {msg.sender.user} pediu minha avaliação: {bar.nota_geral:.2f}")
