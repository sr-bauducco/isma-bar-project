caracteristica(limpeza, 9.0).
caracteristica(preco, 7.0).
caracteristica(temperatura, 6.0).
caracteristica(decoracao, 8.0).

!abrir_bar.

+!abrir_bar : true <-
    .print("[BAR ASL] Portas abertas! Aguardando clientes...").

// GATILHO DE REDE: Reage imediatamente quando recebe a crença 'avaliacao_cliente' de qualquer agente.
+avaliacao_cliente(Nota)[source(Cliente)] <-
    .print("[BAR ASL] ALERTA DE FEEDBACK!");
    .print("[BAR ASL] O cliente ", Cliente, " acabou de me avaliar com nota: ", Nota).