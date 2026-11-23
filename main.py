import argparse
import asyncio

import spade

import relogio
from agents import AgenteCliente, Bar
from rotas import iniciar_painel

NUM_BARES = 3
PERFIS_CLIENTES = ["universitario"] * 50 + ["ponderado"] * 50


def ler_argumentos():
    p = argparse.ArgumentParser(description="Simulação de bares (SPADE)")
    p.add_argument("--dia", type=float, default=relogio.SEGUNDOS_REAIS_POR_DIA,
                   help="segundos reais por dia simulado (padrão: %(default)s; 2 = mês em 1 min)")
    p.add_argument("--dias", type=int, default=relogio.DIAS_SIMULACAO,
                   help="quantos dias simulados a simulação dura (padrão: %(default)s)")
    p.add_argument("--sair-ao-fim", action="store_true",
                   help="encerra o programa no fim da simulação (padrão: mantém o painel no ar)")
    return p.parse_args()


async def main(dias_simulacao, sair_ao_fim=False):
    bares = []
    clientes = []
    # o painel sobe primeiro e mostra os bares conforme eles vão entrando na lista
    painel = await iniciar_painel(bares, clientes)

    try:
        for i in range(1, NUM_BARES + 1):
            # nº de atendentes é sorteado dentro do Bar
            bar = Bar(f"bar{i}@localhost", "senha")
            await bar.start(auto_register=True)
            bares.append(bar)

        jids_bares = [str(b.jid) for b in bares]
        for b in bares:  # cada bar conhece os outros para comparar preços na revisão semanal
            b.concorrentes = [j for j in jids_bares if j != str(b.jid)]
        for i, perfil in enumerate(PERFIS_CLIENTES, start=1):
            cliente = AgenteCliente(f"cliente{i}@localhost", "senha", "asl/cliente.asl", jids_bares, perfil)
            await cliente.start(auto_register=True)
            clientes.append(cliente)

        # o relógio só começa quando todos os agentes já estão no ar
        relogio.iniciar()
        print(f"[Simulação] começou: {dias_simulacao} dias, 1 dia = {relogio.escala():g}s "
              f"(termina em ~{relogio.dias(dias_simulacao) / 60:.1f} min reais)")

        fim = dias_simulacao + relogio.HORA_INICIAL / 24  # o relógio não começa do zero
        while relogio.dias_passados() < fim and any(b.is_alive() for b in bares):
            await asyncio.sleep(min(1.0, relogio.dias(0.25)))

        relogio.encerrar()
        for b in bares:
            b.revisao.fechar_semana_parcial()  # a última semana (incompleta) também entra no relatório
        print(f"[Simulação] fim: {dias_simulacao} dias simulados")
        for b in bares:
            print(f"[Simulação] {b.jid.user}: faturamento final R$ {b.faturamento}")
        await asyncio.gather(*(a.stop() for a in clientes + bares if a.is_alive()))

        if not sair_ao_fim:
            # agentes parados, mas o painel continua mostrando o estado final
            print("[Painel] continua no ar com o resultado final: http://127.0.0.1:10000/painel "
                  "(Ctrl+C para sair)")
            await asyncio.Event().wait()
    finally:
        await asyncio.gather(*(a.stop() for a in clientes + bares if a.is_alive()))
        await painel.cleanup()


if __name__ == "__main__":
    args = ler_argumentos()
    relogio.configurar(args.dia)
    spade.run(main(args.dias, args.sair_ao_fim), embedded_xmpp_server=True)
