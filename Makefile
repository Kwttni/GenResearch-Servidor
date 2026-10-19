LOTE ?= 5000

.PHONY: tudo deps ambiente preparar sintetico testar rapido graficos monitorar c5-limitado evidencias-so limpar

tudo: ambiente preparar testar graficos

deps:
	python3 -m pip install -r requirements.txt

ambiente:
	mkdir -p resultados
	python3 ambiente.py

preparar:
	python3 ingestao.py --limite $(LOTE)

sintetico:
	python3 ingestao.py --sintetico 3000

testar:
	python3 experimentos.py

rapido:
	python3 experimentos.py --rapido

graficos:
	python3 graficos.py

# Guarda as medidas do sistema durante os experimentos.
monitorar:
	mkdir -p resultados
	free -h > resultados/free_antes.txt
	(vmstat -t 1 > resultados/vmstat.txt & echo $$! > .vmstat.pid)
	(iostat -xz 1 > resultados/iostat.txt 2>/dev/null & echo $$! > .iostat.pid) || true
	python3 experimentos.py; \
	kill `cat .vmstat.pid` 2>/dev/null; kill `cat .iostat.pid` 2>/dev/null; rm -f .vmstat.pid .iostat.pid; \
	free -h > resultados/free_depois.txt
	cp resultados/vmstat.txt resultados/free_*.txt resultados/iostat.txt "$$(cat resultados/ULTIMA_EXECUCAO.txt)/" 2>/dev/null || true

# Executa C5 com um limite de memória aplicado pelo systemd.
c5-limitado:
	systemd-run --user --scope -p MemoryMax=1G -p MemorySwapMax=1G python3 experimentos.py --so c5 --limite-mem-mb 1400

# Salva informações sobre threads, processo e chamadas de sistema.
evidencias-so:
	mkdir -p resultados
	python3 demo_servidor.py --trabalhadores 4 --n 400 --custo 0.05 --saida resultados/demo_saida.json & \
	PID=$$!; sleep 4; \
	ps -L -p $$PID -o pid,tid,comm,stat,pcpu,pmem,nlwp > resultados/threads_ps.txt; \
	top -H -b -n 1 -p $$PID > resultados/threads_top.txt; \
	grep -E 'Threads|VmRSS|VmSize|voluntary' /proc/$$PID/status > resultados/proc_status.txt; \
	wait $$PID
	-strace -f -c -o resultados/strace_resumo.txt python3 demo_servidor.py --trabalhadores 4 --n 100 --custo 0.01 --saida resultados/demo_strace.json

limpar:
	rm -rf genresearch.db vetores.npy meta.json genresearch.log dados_teste .vmstat.pid .iostat.pid __pycache__ resultados
