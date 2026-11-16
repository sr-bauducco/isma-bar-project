// Quatro planos de dificuldade crescente, cada um com seu próprio gatilho.
reputacao_global(5.0).

+t1(A, B, C) <- .print("T1 OK (sem anotacao, sem contexto): ", A, " ", B, " ", C).
+t2(A, B, C)[source(S)] <- .print("T2 OK (com [source]): ", S).
+t3(A, B, C) : reputacao_global(R) <- .print("T3 OK (com contexto reputacao_global): ", R).
+t4(A, B, C) : reputacao_global(R) <- X = .fuzzy_reputacao(A, R); .print("T4 OK (funcao fuzzy): ", X).
