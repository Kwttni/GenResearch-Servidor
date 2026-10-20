# Resultados - GenResearch-Servidor

Gerado em 2026-10-19T19:53:13 | rodadas: 3 | modo rapido: False

Ambiente em `ambiente.txt`; dados brutos (uma linha por execucao) em `brutos.csv`.
As tabelas mostram a **media das rodadas** de cada configuracao.


## C1/C2 - leitura convencional vs mmap

| exp | config | tempo_s | abertura_s | leitura_s | minflt | majflt | rchar | rss_mapeado_mb | vsz_mapeado_mb | rss_max_mb |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | pequeno_1MB|convencional|sequencial|fria | 0.001703 | 4.716e-06 | 0.001511 | 150.3 | 0 | 1.79e+07 | nan | nan | 81.3 |
| C1 | pequeno_1MB|convencional|sequencial|quente | 0.0006384 | 4.739e-06 | 0.0005006 | 225 | 0 | 1.895e+07 | nan | nan | 81 |
| C1 | pequeno_1MB|convencional|aleatorio|fria | 0.01438 | 6.966e-06 | 0.01419 | 0 | 0 | 8.25e+07 | nan | nan | 81 |
| C1 | pequeno_1MB|convencional|aleatorio|quente | 0.006324 | 4.495e-06 | 0.006202 | 0 | 0 | 1.03e+08 | nan | nan | 81 |
| C2 | pequeno_1MB|mmap|sequencial|fria | 0.001269 | 1.445e-05 | 0.001053 | 16 | 1 | 1.44e+08 | 82 | 2031 | 81 |
| C2 | pequeno_1MB|mmap|sequencial|quente | 0.0002647 | 1.338e-05 | 5.263e-05 | 17 | 0 | 1.44e+08 | 82 | 2031 | 81 |
| C2 | pequeno_1MB|mmap|aleatorio|fria | 0.002621 | 1.279e-05 | 0.002396 | 16 | 1 | 1.44e+08 | 82 | 2031 | 81 |
| C2 | pequeno_1MB|mmap|aleatorio|quente | 0.002686 | 1.235e-05 | 0.00235 | 17 | 0 | 1.44e+08 | 82 | 2031 | 81 |
| C1 | grande_512MB|convencional|sequencial|fria | 0.2273 | 6.545e-06 | 0.227 | 480 | 0 | 1.755e+09 | nan | nan | 81 |
| C1 | grande_512MB|convencional|sequencial|quente | 0.045 | 8.723e-06 | 0.04479 | 480 | 0 | 2.292e+09 | nan | nan | 81 |
| C1 | grande_512MB|convencional|aleatorio|fria | 0.5622 | 9.882e-06 | 0.5619 | 0 | 0 | 3.427e+09 | nan | nan | 81 |
| C1 | grande_512MB|convencional|aleatorio|quente | 0.0103 | 6.756e-06 | 0.01007 | 0 | 0 | 3.447e+09 | nan | nan | 81 |
| C2 | grande_512MB|mmap|sequencial|fria | 0.2468 | 2.006e-05 | 0.2445 | 2196 | 1 | 3.488e+09 | 593 | 2542 | 81 |
| C2 | grande_512MB|mmap|sequencial|quente | 0.009995 | 2.131e-05 | 0.008126 | 2195 | 0 | 3.488e+09 | 593 | 2542 | 81 |
| C2 | grande_512MB|mmap|aleatorio|fria | 0.5446 | 2.296e-05 | 0.5372 | 3720 | 187.3 | 3.488e+09 | 324.5 | 2542 | 81 |
| C2 | grande_512MB|mmap|aleatorio|quente | 0.02208 | 1.982e-05 | 0.01484 | 3901 | 0 | 3.488e+09 | 324.6 | 2542 | 81 |
| C1 | corpus_sqlite|convencional|sequencial|fria | 0.00243 | 3.34e-06 | 0.002291 | 469 | 0 | 3.495e+09 | nan | nan | 81.07 |
| C1 | corpus_sqlite|convencional|sequencial|quente | 0.00101 | 3.543e-06 | 0.0008997 | 463 | 0 | 3.497e+09 | nan | nan | 81.07 |
| C1 | corpus_sqlite|convencional|aleatorio|fria | 0.02133 | 5.657e-06 | 0.02107 | 0 | 0 | 3.563e+09 | nan | nan | 81.07 |
| C1 | corpus_sqlite|convencional|aleatorio|quente | 0.007107 | 4.455e-06 | 0.006823 | 0 | 0 | 3.583e+09 | nan | nan | 81.07 |
| C2 | corpus_sqlite|mmap|sequencial|fria | 0.001825 | 1.334e-05 | 0.001536 | 33 | 1 | 3.624e+09 | 83.14 | 2034 | 81.07 |
| C2 | corpus_sqlite|mmap|sequencial|quente | 0.0003379 | 1.287e-05 | 0.0001005 | 34 | 0 | 3.624e+09 | 83.14 | 2034 | 81.07 |
| C2 | corpus_sqlite|mmap|aleatorio|fria | 0.003429 | 1.178e-05 | 0.00318 | 33 | 1 | 3.624e+09 | 83.14 | 2034 | 81.07 |
| C2 | corpus_sqlite|mmap|aleatorio|quente | 0.00183 | 1.181e-05 | 0.001583 | 34 | 0 | 3.624e+09 | 83.14 | 2034 | 81.07 |
| C1 | indice_npy|convencional|sequencial|fria | 0.01481 | 3.41e-06 | 0.01458 | 474 | 0 | 3.699e+09 | nan | nan | 81.03 |
| C1 | indice_npy|convencional|sequencial|quente | 0.002733 | 4.939e-06 | 0.002573 | 480 | 0 | 3.724e+09 | nan | nan | 81.01 |
| C1 | indice_npy|convencional|aleatorio|fria | 0.1889 | 3.487e-06 | 0.1887 | 0 | 0 | 3.835e+09 | nan | nan | 81.01 |
| C1 | indice_npy|convencional|aleatorio|quente | 0.008445 | 5.186e-06 | 0.00832 | 0 | 0 | 3.855e+09 | nan | nan | 81.01 |
| C2 | indice_npy|mmap|sequencial|fria | 0.01679 | 1.345e-05 | 0.01622 | 241.3 | 1 | 3.896e+09 | 104.7 | 2054 | 81.01 |
| C2 | indice_npy|mmap|sequencial|quente | 0.0009468 | 2.186e-05 | 0.0005843 | 240.3 | 0 | 3.896e+09 | 104.7 | 2054 | 81.01 |
| C2 | indice_npy|mmap|aleatorio|fria | 0.02735 | 1.42e-05 | 0.0264 | 374 | 9 | 3.896e+09 | 104.7 | 2054 | 81.02 |
| C2 | indice_npy|mmap|aleatorio|quente | 0.004199 | 1.757e-05 | 0.003349 | 379 | 0 | 3.896e+09 | 104.7 | 2054 | 81.02 |
| C1 | indice_vetorial|np.load_convencional|fria | 0.1743 | 0.01378 | 0.1599 | 167 | 0 | 3.971e+09 | 105.4 | 2270 | 97.55 |
| C1 | indice_vetorial|np.load_convencional|quente | 0.1464 | 0.006018 | 0.1399 | 307 | 0 | 3.996e+09 | 105.4 | 2270 | 105.4 |
| C2 | indice_vetorial|np.load_mmap|fria | 0.1033 | 0.001062 | 0.1007 | 529.3 | 10.67 | 4.047e+09 | 129.2 | 2294 | 105.5 |
| C2 | indice_vetorial|np.load_mmap|quente | 0.0585 | 0.0002911 | 0.056 | 379 | 0 | 4.047e+09 | 129.2 | 2294 | 105.5 |


## C3 - concorrencia e fila

| exp | config | tempo_total_s | vazao_req_s | latencia_mediana | latencia_p95 | espera_media | fila_media | fila_max | utilizacao_trabalhadores | bloqueio_produtores_s | perdidos | duplicados | violacoes_fifo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C3 | trabalhadores=1 | 5.137 | 38.93 | 1.306 | 1.319 | 1.12 | 43.91 | 50 | 0.9989 | 6.345 | 0 | 0 | 0 |
| C3 | trabalhadores=2 | 2.611 | 76.6 | 0.6752 | 0.6839 | 0.5672 | 43.92 | 50 | 0.9979 | 3.189 | 0 | 0 | 0 |
| C3 | trabalhadores=4 | 1.329 | 150.5 | 0.3479 | 0.3699 | 0.2851 | 43.93 | 50 | 0.9909 | 1.64 | 0 | 0 | 0 |
| C3 | fila_cap=2 | 2.615 | 76.49 | 0.05152 | 0.05497 | 0.02551 | 1.975 | 2 | 0.9963 | 10.02 | 0 | 0 | 0 |
| C3 | fila_cap=8 | 2.619 | 76.36 | 0.1303 | 0.1345 | 0.1016 | 7.842 | 8 | 0.9961 | 9.535 | 0 | 0 | 0 |
| C3 | fila_cap=50 | 2.612 | 76.58 | 0.6728 | 0.6832 | 0.5674 | 43.93 | 50 | 0.9977 | 5.714 | 0 | 0 | 0 |


## C4 - cache compartilhado

| exp | config | cache_hits | cache_misses | taxa_acerto | cache_substituicoes | tempo_economizado_s | geracoes_repetidas | tempo_total_s |
|---|---|---|---|---|---|---|---|---|
| C4 | repetidas|cache=0|LRU | 0 | 60 | 0 | 0 | 0 | 55 | 2.19 |
| C4 | repetidas|cache=8|LRU | 55 | 5 | 0.9167 | 0 | 2.009 | 0 | 0.1843 |
| C4 | repetidas|cache=8|FIFO | 55 | 5 | 0.9167 | 0 | 2.009 | 0 | 0.1841 |
| C4 | repetidas|cache=64|LRU | 55 | 5 | 0.9167 | 0 | 2.011 | 0 | 0.1844 |
| C4 | repetidas|cache=64|FIFO | 55 | 5 | 0.9167 | 0 | 2.01 | 0 | 0.1843 |
| C4 | mista|cache=0|LRU | 0 | 60 | 0 | 0 | 0 | 32 | 2.177 |
| C4 | mista|cache=8|LRU | 20 | 40 | 0.3333 | 32 | 0.7194 | 12 | 1.441 |
| C4 | mista|cache=8|FIFO | 20 | 40 | 0.3333 | 32 | 0.7202 | 12 | 1.443 |
| C4 | mista|cache=64|LRU | 32 | 28 | 0.5333 | 0 | 1.146 | 0 | 1.005 |
| C4 | mista|cache=64|FIFO | 32 | 28 | 0.5333 | 0 | 1.148 | 0 | 1.007 |
| C4 | distintas|cache=0|LRU | 0 | 60 | 0 | 0 | 0 | 0 | 2.143 |
| C4 | distintas|cache=8|LRU | 0 | 60 | 0 | 52 | 0 | 0 | 2.147 |
| C4 | distintas|cache=8|FIFO | 0 | 60 | 0 | 52 | 0 | 0 | 2.144 |
| C4 | distintas|cache=64|LRU | 0 | 60 | 0 | 0 | 0 | 0 | 2.145 |
| C4 | distintas|cache=64|FIFO | 0 | 60 | 0 | 0 | 0 | 0 | 2.145 |
| C4 | parafrases|cache=0|LRU | 0 | 60 | 0 | 0 | 0 | 0 | 2.165 |
| C4 | parafrases|cache=8|LRU | 0 | 60 | 0 | 52 | 0 | 0 | 2.165 |
| C4 | parafrases|cache=8|FIFO | 0 | 60 | 0 | 52 | 0 | 0 | 2.163 |
| C4 | parafrases|cache=64|LRU | 0 | 60 | 0 | 0 | 0 | 0 | 2.162 |
| C4 | parafrases|cache=64|FIFO | 0 | 60 | 0 | 0 | 0 | 0 | 2.163 |
| C4 | repetidas|cache=64|LRU|4_trabalhadores | 51.67 | 8.333 | 0.8611 | 0 | 1.989 | 3.333 | 0.09216 |


## C5 - pressao de memoria

| exp | config | alocacao_s | lat_consulta_media_s | lat_consulta_p95_s | rss_max_mb | vsz_max_mb | minflt | majflt |
|---|---|---|---|---|---|---|---|---|
| C5 | corpus=315MB | 0.1308 | 0.02176 | 0.02402 | 113.2 | 3073 | 2.274e+04 | 0 |
| C5 | corpus=789MB | 0.3834 | 0.05538 | 0.06193 | 113.2 | 3073 | 3.847e+04 | 0 |
| C5 | corpus=1578MB | 0.5902 | 0.1045 | 0.108 | 113.2 | 3073 | 5.257e+04 | 0 |
| C5 | corpus=3157MB | 1.325 | 0.2118 | 0.2224 | 117.2 | 3077 | 1.206e+05 | 0 |


## C6 - falhas controladas

| exp | config | falhas | retentativas | falhas_geracao | rejeitadas | put_timeouts | processadas | perdidos | memoryerror |
|---|---|---|---|---|---|---|---|---|---|
| C6 | banco_ausente | 3 | 2 | 0 | 0 | 0 | 30 | 0 | nan |
| C6 | indice_ausente(fallback_lexical) | 3 | 2 | 0 | 0 | 0 | 30 | 0 | nan |
| C6 | fila_saturada(cap=2) | 0 | 0 | 0 | 30 | 63 | 10 | 30 | nan |
| C6 | servico_geracao_falhando(35%) | 0 | 9.667 | 10.67 | 0 | 0 | 30 | 0 | nan |
| C6 | limite_memoria(RLIMIT_AS) | nan | nan | nan | nan | nan | nan | nan | 1 |


## Parte D - sincronizacao

| exp | config | atualizacoes_perdidas | tempo_s | perdidos | fila_max | deadlock_detectado | recuperado |
|---|---|---|---|---|---|---|---|
| D | atualizacao_sem_bloqueio | 3e+04 | 0.08225 | nan | nan | nan | nan |
| D | atualizacao_com_bloqueio | 0 | 0.006203 | nan | nan | nan | nan |
| D | fila_limitada | nan | 2.024e-05 | nan | 2 | 1 | 1 |
