import spade
from agents.Atendente import Atendente
from spade.behaviour import OneShotBehaviour, CyclicBehaviour

# VALORES PADROES PARA O BAR
NUM_ATENDENTES = 1

class Bar(spade.agent.Agent):

    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.atendentes = []
        self.is_open = True
        self.pontuacao = {
            "limpeza": 10,
            "decoracao": 10,
            "atendimento": 10, # tempo de espera dos atendentes
            "preco": 10
        }
        self.avaliacoes = {criterio: [] for criterio in self.pontuacao}

    def registrar_nota(self, criterio, nota):
        self.avaliacoes[criterio].append(nota)
        notas = self.avaliacoes[criterio]
        self.pontuacao[criterio] = sum(notas) / len(notas)   # média só deste critério
        return self.pontuacao[criterio]

    class Encerrar(OneShotBehaviour):
        async def run(self):
            await self.agent.stop()

    class ReceberAvaliacao(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)
            if msg:
                try:
                    avaliacao = msg.body.split(":")
                    criterio = avaliacao[0]
                    nota = int(avaliacao[1])
                    media = self.agent.registrar_nota(criterio, nota)
                    print(f"[Bar] recebi avaliacao: {criterio} = {nota} (média: {media:.2f})")
                except Exception as e:
                    print(f"[Bar] erro ao processar avaliacao: {e}\nInforme no formato 'criterio:nota' (ex: limpeza:8)")

    async def setup(self):
        print(f"Hello! Bar agent {self.jid} is starting...")

        self.add_behaviour(self.ReceberAvaliacao())

        # Cada bar nasce com seus próprios atendentes: bar1 -> bar1_atendente1..3
        for i in range(1, NUM_ATENDENTES + 1):
            atendente_jid = f"{self.jid.user}_atendente{i}@{self.jid.domain}"
            atendente = Atendente(atendente_jid, "senha", str(self.jid))
            await atendente.start(auto_register=True)
            self.atendentes.append(atendente)
