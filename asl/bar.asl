// Crenças base do bar
caracteristica(limpeza, 9.0).
caracteristica(preco, 7.0).
caracteristica(temperatura, 6.0).
caracteristica(decoracao, 8.0).

reputacao_global(9.0).  // R_t-1 inicial
taxa_aprendizado(0.3).  // Alpha

!abrir_bar.

+!abrir_bar : true <-
    .print("[BAR ASL] Portas abertas! Aguardando clientes...").

// GATILHO: Quando recebe a avaliação do cliente via XMPP
+avaliacao_cliente(Nota)[source(Cliente)] <-
    .print("[BAR ASL] ALERTA! O cliente ", Cliente, " me deu nota: ", Nota);
    
    // 1. Consulta as variáveis na memória
    ?reputacao_global(RepAtual);
    ?taxa_aprendizado(Alpha);
    
    // 2. O AgentSpeak resolve a álgebra nativamente!
    NovaRep = ((1.0 - Alpha) * RepAtual) + (Alpha * Nota);
    
    // 3. O operador -+ atualiza a crença na base de conhecimento
    -+reputacao_global(NovaRep);
    
    .print("[BAR ASL] Matematica concluida internamente!");
    .print("[BAR ASL] Minha nova reputacao publica e: ", NovaRep).