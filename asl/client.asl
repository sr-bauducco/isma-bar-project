!sair_para_beber.

+!sair_para_beber : true <-
    .print("[ASL] Quero beber! Aguardando meu cerebro Python avaliar as opcoes...").

+vencedor(Bar) : true <-
    .print("[ASL] O bar escolhido para hoje foi o: ", Bar);
    !consumir(Bar).

+!consumir(Bar) : true <-
    .print("[ASL] Indo fisicamente para o ", Bar, "...");
    
    // Simula o consumo da cerveja
    .print("[ASL] Bebendo e avaliando a experiencia...");
    
    // O comando .send(Destinatario, AtoComuniativo, Conteudo) envia a mensagem XMPP.
    // Estamos enviando a crença 'avaliacao_cliente(8.5)' para a mente do Bar.
    .send(Bar, tell, avaliacao_cliente(8.5));
    
    .print("[ASL] Avaliacao enviada ao bar com sucesso!").