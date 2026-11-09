// Crenças e desejos iniciais para teste de sintaxe
peso(limpeza, 0.3).
peso(preco, 0.4).
peso(temperatura, 0.2).
peso(decoracao, 0.1).

reputacao(bar1, 5.0).
reputacao(bar2, 5.0).
reputacao(bar3, 5.0).

!sair_para_beber.

+!sair_para_beber : true <-
    .print("Analisando a reputacao dos bares para decidir onde ir...").