from statistics import mean

from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message

import relogio
from behaviours.entrada import chamar_fila
from behaviours.utils import ler_json, responder

# VALORES PADROES DA GESTAO SEMANAL DO BAR
PERIODO_REVISAO_HORAS = 1    # de quanto em quanto tempo o bar confere se a semana virou
QUEDA_FATURAMENTO = 0.9      # faturou menos que 90% da semana anterior -> "estou perdendo dinheiro"
TIMEOUT_RIVAIS = 2           # s reais esperando o preço de cada concorrente (polling, não escala)
ESPERA_ALTA_MINUTOS = 20     # espera média da semana acima disso -> contrata atendente
MAX_ATENDENTES_BAR = 6
RECUSAS_ALTAS = 30           # clientes que chegaram com o bar lotado na semana acima disso -> mais cadeiras
CADEIRAS_POR_REFORMA = 5
LOTACAO_LIMITE = 30
REPUTACAO_BAIXA = 5.0        # abaixo disso o bar faz promoção
REPUTACAO_ALTA = 7.0         # acima disso o bar encarece
PASSO_PRECO = 0.10           # cada mudança mexe 10% do preço base
FATOR_PRECO_MIN = 0.5        # o preço fica entre 50% e 150% do preço base
FATOR_PRECO_MAX = 1.5


def decidir(espera_media, recusas, reputacao, num_atendentes, lotacao, fator_preco,
            preco_medio=None, preco_rivais=None):
    """Tudo o que a semana pede, como lista (vazia = não muda nada) de
    "atendente" | "cadeiras" | "baixar_preco" | "subir_preco". No máximo um movimento de preço.

    preco_rivais (preço médio do cardápio dos concorrentes) só é informado quando o faturamento
    caiu; aí o preço segue a comparação: mais caro que eles -> baixa, mais barato -> sobe.
    Sem isso (ou com preço igual), o preço segue a reputação.
    """
    acoes = []
    if espera_media > ESPERA_ALTA_MINUTOS and num_atendentes < MAX_ATENDENTES_BAR:
        acoes.append("atendente")
    if recusas > RECUSAS_ALTAS and lotacao < LOTACAO_LIMITE:
        acoes.append("cadeiras")

    pode_baixar, pode_subir = fator_preco > FATOR_PRECO_MIN, fator_preco < FATOR_PRECO_MAX
    preco = None
    if preco_rivais is not None:
        if preco_medio - preco_rivais > 0.01 and pode_baixar:
            preco = "baixar_preco"
        elif preco_rivais - preco_medio > 0.01 and pode_subir:
            preco = "subir_preco"
    if preco is None:
        if reputacao < REPUTACAO_BAIXA and pode_baixar:
            preco = "baixar_preco"
        elif reputacao > REPUTACAO_ALTA and pode_subir:
            preco = "subir_preco"
    if preco:
        acoes.append(preco)
    return acoes


class ResponderPrecos(CyclicBehaviour):
    """Behaviour do Bar: informa o cardápio a quem perguntar (o preço é público).

    Recebe:   query-ref / precos  (body vazio)
    Responde: inform / precos     {"bar": "bar1@localhost", "cardapio": {"cerveja": 12, ...}}
    """

    async def run(self):
        msg = await self.receive(timeout=10)
        if not msg:
            return
        bar = self.agent
        await responder(self, msg, "inform", {"bar": str(bar.jid), "cardapio": bar.cardapio})


class RevisarSemana(PeriodicBehaviour):
    """Behaviour do Bar: quando a semana vira, olha os números dela e toma as decisões que
    ela pedir (contratar atendente, pôr mais cadeiras, baixar ou subir o preço), todas na mesma semana.

    Se o faturamento caiu em relação à semana anterior, antes de decidir ele pergunta o preço
    aos concorrentes (bar.concorrentes). Registrar com template inform / precos.
    """

    def __init__(self, period=None, **kwargs):
        if period is None:
            period = relogio.periodo(relogio.horas(PERIODO_REVISAO_HORAS))
        super().__init__(period=period, **kwargs)
        self._semana = None
        self._esperas_vistas = 0   # quanto de tempos_espera / recusas_lotado / faturamento já foi analisado
        self._recusas_vistas = 0
        self._faturamento_visto = 0
        self._faturamento_anterior = None  # faturamento da semana passada (None na 1ª semana)

    async def precos_dos_rivais(self):
        """Pergunta o cardápio a cada concorrente -> preço médio entre eles (None se ninguém respondeu).

        Envia:  query-ref / precos  -> cada bar de bar.concorrentes
        Recebe: inform / precos     {"cardapio": {...}}
        """
        bar = self.agent
        for jid in bar.concorrentes:
            msg = Message(to=jid)
            msg.set_metadata("performative", "query-ref")
            msg.set_metadata("ontology", "precos")
            await self.send(msg)
        medias = []
        for _ in bar.concorrentes:
            resp = await self.receive(timeout=TIMEOUT_RIVAIS)
            if resp is None:
                break
            try:
                medias.append(mean(ler_json(resp)["cardapio"].values()))
            except Exception as e:
                print(f"[{bar.jid.user}] preços inválidos de {resp.sender}: {e}")
        return mean(medias) if medias else None

    def numeros_da_semana(self):
        """Números da semana em curso (desde a última revisão) e a situação do bar durante ela."""
        bar = self.agent
        esperas = bar.tempos_espera[self._esperas_vistas:]
        return {
            "semana": self._semana,
            "faturamento": round(bar.faturamento - self._faturamento_visto, 2),
            "entregues": len(esperas),
            "espera": mean(esperas) if esperas else 0.0,
            "recusas": bar.recusas_lotado - self._recusas_vistas,
            "reputacao": bar.reputacao,
            "atendentes": len(bar.atendentes),
            "lotacao": bar.lotacao_maxima,
            "fator_preco": bar.fator_preco,
        }

    def registrar_semana(self, numeros, acao):
        """Guarda a semana no relatório do bar (bar.decisoes) e recomeça a contagem."""
        bar = self.agent
        bar.decisoes.append({**numeros, "acao": acao})
        self._esperas_vistas = len(bar.tempos_espera)
        self._recusas_vistas = bar.recusas_lotado
        self._faturamento_visto = bar.faturamento
        self._faturamento_anterior = numeros["faturamento"]

    def fechar_semana_parcial(self):
        """Chamado pelo main.py no fim da simulação: registra a semana que ficou incompleta."""
        if self._semana is not None:
            self.registrar_semana(self.numeros_da_semana(), "simulação encerrada (semana incompleta)")

    async def run(self):
        if not relogio.rodando():
            return
        bar = self.agent
        # este behaviour roda a cada hora simulada: aproveita para amostrar a ocupação por hora do dia
        amostra = bar.ocupacao_por_hora.setdefault(relogio.hora_do_dia(), [0, 0, 0])
        amostra[0] += 1
        amostra[1] += len(bar.clientes)
        amostra[2] += len(bar.fila_entrada)
        semana = relogio.semana_atual()
        if self._semana is None:
            self._semana = semana
        if semana == self._semana:
            return

        numeros = self.numeros_da_semana()
        espera, recusas, faturamento = numeros["espera"], numeros["recusas"], numeros["faturamento"]
        anterior = self._faturamento_anterior
        perdendo = anterior is not None and faturamento < QUEDA_FATURAMENTO * anterior

        preco_medio = mean(bar.cardapio.values())
        preco_rivais = await self.precos_dos_rivais() if perdendo else None
        acoes = decidir(espera, recusas, numeros["reputacao"], len(bar.atendentes), bar.lotacao_maxima,
                        bar.fator_preco, preco_medio, preco_rivais)

        bar.tendencia_preco = 0
        feitos = []
        for acao in acoes:
            if acao == "atendente":
                novo = await bar.contratar_atendente()
                feitos.append(f"contratou {novo.jid.user.split('_')[-1]} (espera média de {espera:.0f} min)")
            elif acao == "cadeiras":
                bar.lotacao_maxima = min(LOTACAO_LIMITE, bar.lotacao_maxima + CADEIRAS_POR_REFORMA)
                feitos.append(f"aumentou para {bar.lotacao_maxima} cadeiras "
                              f"({recusas} clientes chegaram com o bar lotado)")
                await chamar_fila(self)  # as cadeiras novas já servem quem está na porta
            else:
                bar.ajustar_preco(-PASSO_PRECO if acao == "baixar_preco" else PASSO_PRECO)
                if preco_rivais is not None and abs(preco_medio - preco_rivais) > 0.01:
                    motivo = (f"faturamento caiu de R$ {anterior:.0f} para R$ {faturamento:.0f}; preço médio "
                              f"era R$ {preco_medio:.2f} contra R$ {preco_rivais:.2f} dos concorrentes")
                else:
                    motivo = f"reputação {numeros['reputacao']:.1f}"
                feitos.append(f"{'baixou' if acao == 'baixar_preco' else 'subiu'} o preço para "
                              f"{bar.fator_preco:.0%} do base ({motivo})")
        texto = "; ".join(feitos) or "manteve tudo como está"

        self.registrar_semana(numeros, texto)
        print(f"[{bar.jid.user}] fim da semana {self._semana}: {texto}")
        self._semana = semana
