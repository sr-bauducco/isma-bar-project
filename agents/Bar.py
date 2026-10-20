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
        self.estado = {
            "limpeza": 10,
        }
        self.mesas = [f"mesa_{i}" for i in range(1, 6)]
        self.mesas_ocupadas = 0

        self.avaliacoes = {criterio: [] for criterio in self.pontuacao}

    @property
    def nota_geral(self):
        return sum(self.pontuacao.values()) / len(self.pontuacao)


    def registrar_nota(self, criterio, nota):
        if criterio not in self.avaliacoes:
            raise ValueError(f"critério inválido: {criterio}")
        if not 0 <= nota <= 10:
            raise ValueError("nota deve estar entre 0 e 10")
        self.avaliacoes[criterio].append(nota)
        notas = self.avaliacoes[criterio]
        self.pontuacao[criterio] = sum(notas) / len(notas)
        return self.pontuacao[criterio]


    def status(self):
        """Retorna o status atual do bar."""
        return {
            "is_open": self.is_open,
            "pontuacao": self.pontuacao,
            "nota_geral": self.nota_geral,
            "limpeza": self.estado["limpeza"],
            "mesas_ocupadas": self.mesas_ocupadas,
            "mesas": self.mesas,
        }

    class ReceberCliente(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)
            if msg and self.agent.mesas_ocupadas < len(self.agent.mesas):
                print(f"[Bar] recebi cliente: {msg.body}")
                self.agent.mesas_ocupadas += 1
                print(f"[Bar] mesas ocupadas: {self.agent.mesas_ocupadas}/{len(self.agent.mesas)}")
            else:
                print(f"[Bar] aguardando clientes... Mesas ocupadas: {self.agent.mesas_ocupadas}/{len(self.agent.mesas)}")

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
            else:
                # nota atual
                print(f"[Bar] nota atual: {self.agent.nota_geral:.2f}")


    async def setup(self):
        print(f"Hello! Bar agent {self.jid} is starting...")

        self.add_behaviour(self.ReceberAvaliacao())

        # Cada bar nasce com seus próprios atendentes: bar1 -> bar1_atendente1..3
        for i in range(1, NUM_ATENDENTES + 1):
            atendente_jid = f"{self.jid.user}_atendente{i}@{self.jid.domain}"
            atendente = Atendente(atendente_jid, "senha", str(self.jid))
            await atendente.start(auto_register=True)
            self.atendentes.append(atendente)

        print(f"[Bar] {len(self.atendentes)} atendentes registrados: {[a.jid for a in self.atendentes]}")
        print(f"[Bar] status inicial: {self.status()}")
