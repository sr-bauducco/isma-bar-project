import json
from collections import deque

from spade.behaviour import CyclicBehaviour
from spade.message import Message

from behaviours.utils import responder

# VALORES PADROES DA ENTRADA
LIMITE_FILA_ENTRADA = 10   # quantos clientes cabem na fila da porta; além disso o bar recusa


def _boas_vindas(bar):
    return {
        "clientes": len(bar.clientes),
        "lotacao_maxima": bar.lotacao_maxima,
        "limpeza": round(bar.nivel_limpeza, 1),  # o cliente vê o estado do bar ao entrar
    }


async def chamar_fila(behaviour):
    """Enquanto houver vaga, chama o próximo da fila da porta (usada por qualquer behaviour do Bar).

    Envia: agree / entrar  (mesmo body da entrada direta)  -> cliente que estava na fila
    """
    bar = behaviour.agent
    while bar.fila_entrada and len(bar.clientes) < bar.lotacao_maxima:
        cliente = bar.fila_entrada.popleft()
        bar.clientes.add(cliente)
        msg = Message(to=cliente)
        msg.set_metadata("performative", "agree")
        msg.set_metadata("ontology", "entrar")
        msg.body = json.dumps(_boas_vindas(bar))
        await behaviour.send(msg)
        print(f"[{bar.jid.user}] vagou: {cliente.split('@')[0]} saiu da fila e entrou "
              f"({len(bar.clientes)}/{bar.lotacao_maxima})")


class ReceberEntrada(CyclicBehaviour):
    """Behaviour do Bar: cliente pede para entrar.

    Recebe:   request / entrar   (body vazio)
    Responde: agree  / entrar   {"clientes": n, "lotacao_maxima": m, "limpeza": 0-10}
              inform / entrar   {"posicao": n}  -> lotado: ficou na fila da porta; o agree vem
                                                   depois, quando abrir vaga (chamar_fila)
              refuse / entrar   {"motivo": "fechado" | "lotado"}  (lotado = fila da porta cheia)
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
            if cliente not in bar.fila_entrada:
                bar.recusas_lotado += 1  # chegou com o bar lotado (entrando na fila ou não)
                if len(bar.fila_entrada) >= LIMITE_FILA_ENTRADA:
                    await responder(self, msg, "refuse", {"motivo": "lotado"})
                    print(f"[{bar.jid.user}] recusei {msg.sender.user}: lotado")
                    return
                bar.fila_entrada.append(cliente)
            posicao = bar.fila_entrada.index(cliente) + 1
            await responder(self, msg, "inform", {"posicao": posicao})
            print(f"[{bar.jid.user}] {msg.sender.user} ficou na fila da porta (posição {posicao})")
            return

        bar.clientes.add(cliente)  # entrar de novo estando dentro não dá erro
        await responder(self, msg, "agree", _boas_vindas(bar))
        print(f"[{bar.jid.user}] {msg.sender.user} entrou ({len(bar.clientes)}/{bar.lotacao_maxima})")


class ReceberSaida(CyclicBehaviour):
    """Behaviour do Bar: cliente avisa que saiu do bar (ou desistiu da fila da porta).

    Recebe: inform / sair  (body vazio). Não há resposta.
    """

    async def run(self):
        msg = await self.receive(timeout=10)
        if not msg:
            return

        bar = self.agent
        cliente = str(msg.sender.bare)
        if cliente in bar.fila_entrada:
            bar.fila_entrada.remove(cliente)
            print(f"[{bar.jid.user}] {msg.sender.user} desistiu da fila da porta")
        bar.clientes.discard(cliente)
        # quem sai sem esperar a entrega tem os pedidos da fila cancelados (o que já está em preparo segue)
        bar.fila_pedidos = deque(p for p in bar.fila_pedidos if p["cliente"] != cliente)
        print(f"[{bar.jid.user}] {msg.sender.user} saiu ({len(bar.clientes)}/{bar.lotacao_maxima})")
        await chamar_fila(self)  # abriu vaga: entra o próximo da porta
