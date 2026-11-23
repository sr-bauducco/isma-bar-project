+visita(Bar) <-
    .print("cliente: enviando 4 testes para ", Bar);
    .send(Bar, tell, t1(655, 2, 1));
    .send(Bar, tell, t2(655, 2, 1));
    .send(Bar, tell, t3(655, 2, 1));
    .send(Bar, tell, t4(655, 2, 1)).
