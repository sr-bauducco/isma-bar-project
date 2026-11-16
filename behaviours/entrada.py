from spade.behaviour import CyclicBehaviour

from behaviours.utils import responder


class ReceberEntrada(CyclicBehaviour):
    """Behaviour do Bar: cliente pede para entrar.

    Recebe:   request / entrar   (body vazio)
    Responde: agree  / entrar   {"clientes": n, "lotacao_maxima": m, "limpeza": 0-10}
              refuse / entrar   {"motivo": "fechado" | "lotado"}
    """

    async def run(self):
        msg = await self.receive(timeout=10)
        if not msg:
            return

        bar = self.agent
        cliente = str(msg.sender.bare)

        if not bar.is_open:
            await responder(self, msg, "refuse", {"motivo": "fechado"})
            print(f"[{bar.jid.user}] recusei {msg.sender.user}: fechado")
            return

        if cliente not in bar.clientes and len(bar.clientes) >= bar.lotacao_maxima:
            await responder(self, msg, "refuse", {"motivo": "lotado"})
            print(f"[{bar.jid.user}] recusei {msg.sender.user}: lotado")
            return

        bar.clientes.add(cliente)  # entrar de novo estando dentro não dá erro
        await responder(self, msg, "agree", {
            "clientes": len(bar.clientes),
            "lotacao_maxima": bar.lotacao_maxima,
            "limpeza": round(bar.nivel_limpeza, 1),  # o cliente vê o estado do bar ao entrar
        })
        print(f"[{bar.jid.user}] {msg.sender.user} entrou ({len(bar.clientes)}/{bar.lotacao_maxima})")


class ReceberSaida(CyclicBehaviour):
    """Behaviour do Bar: cliente avisa que saiu.

    Recebe: inform / sair  (body vazio). Não há resposta.
    """

    async def run(self):
        msg = await self.receive(timeout=10)
        if not msg:
            return

        bar = self.agent
        bar.clientes.discard(str(msg.sender.bare))
        print(f"[{bar.jid.user}] {msg.sender.user} saiu ({len(bar.clientes)}/{bar.lotacao_maxima})")
