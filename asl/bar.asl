// Cérebro do bar: reage a cada avaliação recebida. A reputação nebulosa (EMA com alfa
// adaptativo) já vem calculada pelo músculo em Python; o preço é revisado em EstrategiaBehaviour.
+avaliacao(R, Cliente, NotaCent, Nivel, NovaRep) <-
    .print("Feedback de ", Cliente, " (rodada ", R, "): nivel ", Nivel,
           ", nota x100 = ", NotaCent, " -> reputacao ", NovaRep).
