import itertools
import json
import random
from collections import deque

import spade
from agents.Atendente import Atendente
from agents.Faxineira import Faxineira
from behaviours import (
    Sujar, VigiarLimpeza, ResponderAvaliacao,
    ReceberEntrada, ReceberSaida,
    ReceberPedido, DistribuirPedidos, ReceberPedidoPronto,
    template,
)
from spade.behaviour import OneShotBehaviour, CyclicBehaviour

# VALORES PADROES PARA O BAR
MIN_ATENDENTES = 1
MAX_ATENDENTES = 4
NUM_FAXINEIRAS = 1
LOTACAO_MAXIMA = 20
CARDAPIO = {  # item -> preço
    "cerveja": 12,
    "refrigerante": 6,
    "drink": 25,
    "porcao": 30,
}


class Bar(spade.agent.Agent):
    def __init__(self, jid, password, num_atendentes=None, num_faxineiras=NUM_FAXINEIRAS):
        super().__init__(jid, password)
        self.num_atendentes = num_atendentes or random.randint(MIN_ATENDENTES, MAX_ATENDENTES)
        self.num_faxineiras = num_faxineiras
        self.atendentes = []
        self.faxineiras = []
        self.chamados_pendentes = set()  
        self.clientes = set()  
        self.lotacao_maxima = LOTACAO_MAXIMA
        self.cardapio = dict(CARDAPIO)
        self.fila_pedidos = deque()    
        self.pedidos_em_preparo = {}   
        self.proximo_pedido_id = itertools.count(1)
        self.tempos_espera = []       
        self.is_open = True
        self.nivel_limpeza = 10.0
        self.pontuacao = {
            "limpeza": 10,
            "decoracao": 10,
            "atendimento": 10,
            "preco": 10
        }
        self.avaliacoes = {criterio: [] for criterio in self.pontuacao}

    @property
    def nota_geral(self):
        return sum(self.pontuacao.values()) / len(self.pontuacao)

    async def stop(self):
        # o bar encerra a própria equipe antes de fechar
        for agente in self.atendentes + self.faxineiras:
            if agente.is_alive():
                await agente.stop()
        await super().stop()

    @property
    def espera_media(self):
        """Espera média dos pedidos, em minutos simulados."""
        return sum(self.tempos_espera) / len(self.tempos_espera) if self.tempos_espera else 0.0


    def registrar_nota(self, criterio, nota):
        if criterio not in self.avaliacoes:
            raise ValueError(f"critério inválido: {criterio}")
        if not 0 <= nota <= 10:
            raise ValueError("nota deve estar entre 0 e 10")
        self.avaliacoes[criterio].append(nota)
        notas = self.avaliacoes[criterio]
        self.pontuacao[criterio] = sum(notas) / len(notas)
        return self.pontuacao[criterio]


    class Encerrar(OneShotBehaviour):
        async def run(self):
            await self.agent.stop()


    class ReceberAvaliacao(CyclicBehaviour):
        """Recebe só mensagens inform/avaliacao, body 'criterio:nota'."""
        async def run(self):
            nome = self.agent.jid.user
            msg = await self.receive(timeout=5)
            if msg:
                try:
                    avaliacao = msg.body.split(":")
                    criterio = avaliacao[0]
                    nota = int(avaliacao[1])
                    media = self.agent.registrar_nota(criterio, nota)
                    print(f"[{nome}] recebi avaliacao: {criterio} = {nota} (média: {media:.2f})")
                except Exception as e:
                    print(f"[{nome}] erro ao processar avaliacao: {e}\nInforme no formato 'criterio:nota' (ex: limpeza:8)")
            else:
                # nota atual
                print(f"[{nome}] nota atual: {self.agent.nota_geral:.2f}")


    class ReceberLimpeza(CyclicBehaviour):
        """Recebe inform/limpeza_feita da faxineira, body {"quantidade": x}."""
        async def run(self):
            msg = await self.receive(timeout=10)
            if not msg:
                return
            bar = self.agent
            try:
                quantidade = float(json.loads(msg.body)["quantidade"])
            except Exception as e:
                print(f"[{bar.jid.user}] limpeza_feita inválida de {msg.sender}: {e}")
                return
            bar.nivel_limpeza = min(10.0, bar.nivel_limpeza + quantidade)
            bar.chamados_pendentes.discard(str(msg.sender.bare))
            print(f"[{bar.jid.user}] {msg.sender.user} limpou +{quantidade}, limpeza agora {bar.nivel_limpeza:.1f}")


    async def setup(self):
        print(f"Hello! Bar agent {self.jid} is starting...")

        # cada behaviour só recebe as mensagens do seu tipo (filtro por ontology)
        self.add_behaviour(self.ReceberAvaliacao(), template("inform", "avaliacao"))
        self.add_behaviour(self.ReceberLimpeza(), template("inform", "limpeza_feita"))
        self.add_behaviour(ResponderAvaliacao(), template("query-ref", "avaliacao"))
        self.add_behaviour(ReceberEntrada(), template("request", "entrar"))
        self.add_behaviour(ReceberSaida(), template("inform", "sair"))
        self.add_behaviour(ReceberPedido(), template("request", "pedido"))
        self.add_behaviour(ReceberPedidoPronto(), template("inform", "pedido_pronto"))
        self.add_behaviour(DistribuirPedidos())
        self.add_behaviour(Sujar())
        self.add_behaviour(VigiarLimpeza())


        # Cada bar nasce com seus próprios
        #  atendentes: bar1 -> bar1_atendente1..N
        print(f"[{self.jid.user}] criando {self.num_atendentes} atendente(s)")
        for i in range(1, self.num_atendentes + 1):
            atendente_jid = f"{self.jid.user}_atendente{i}@{self.jid.domain}"
            atendente = Atendente(atendente_jid, "senha", str(self.jid))
            await atendente.start(auto_register=True)
            self.atendentes.append(atendente)

        #  faxineiras: bar1 -> bar1_faxineira1..N
        print(f"[{self.jid.user}] criando {self.num_faxineiras} faxineira(s)")
        for i in range(1, self.num_faxineiras + 1):
            faxineira_jid = f"{self.jid.user}_faxineira{i}@{self.jid.domain}"
            faxineira = Faxineira(faxineira_jid, "senha", str(self.jid))
            await faxineira.start(auto_register=True)
            self.faxineiras.append(faxineira)
