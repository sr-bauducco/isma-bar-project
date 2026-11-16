// Cérebro do cliente: registra a experiência vivida na visita.
// (a avaliação ao bar segue por mensagem XMPP, enviada pelo músculo em Python)
+visita(R, Bar, Nota, Rotulo) <-
    .print("Rodada ", R, ": fui ao bar ", Bar, ", achei ", Rotulo, " (nota ", Nota, ")").
