# Executa os experimentos e salva os resultados em CSV e Markdown.
# Exemplos: python3 experimentos.py ou python3 experimentos.py --rapido
import argparse
import csv
import datetime
import mmap
import multiprocessing as mp
import os
import shutil
import time
import numpy as np
import ambiente
import pandas as pd
import sinc_demo
import resource
from config import ARQ_DB, ARQ_IDX, ARQ_ANDAMENTO, ARQ_BRUTOS, ARQ_LOG, ARQ_ULTIMA_EXCE, PASTA_RESULTADOS
from metricas import Medicao, mem_info, status_proc
from servidor import Servidor, gera_consultas

TAM_PAG = 4096


class RegistraResultados:
    """
    Armazena os resultados dos experimentos e salva os dados em CSV.
    """

    def __init__(self, pasta_resul):
        self.pasta_resultados = pasta_resul
        self.linhas_resultados = []

    def adicionar_resul(self, experimento, config, num_rodada, **dados):
        """
        Adiciona os dados de uma execução ao registro de resultados.
        """
        linha_resul = {
            "exp": experimento,
            "config": config,
            "rodada": num_rodada,
            "hora": datetime.datetime.now().isoformat(timespec="seconds"),
        }

        linha_resul.update(dados)
        self.linhas_resultados.append(linha_resul)

    def salvar_resul(self):
        """
        Salva todas as execuções registradas em um arquivo CSV.
        """
        if not self.linhas_resultados:
            return

        nomes_colunas = []
        for linha_resul in self.linhas_resultados:
            for nome_coluna in linha_resul:
                if nome_coluna not in nomes_colunas:
                    nomes_colunas.append(nome_coluna)

        caminho_csv = os.path.join(self.pasta_resultados, ARQ_BRUTOS)

        with open(caminho_csv, "w", newline="", encoding="utf-8") as arquivo_csv:
            escritor_csv = csv.DictWriter(arquivo_csv, fieldnames=nomes_colunas)
            escritor_csv.writeheader()
            escritor_csv.writerows(self.linhas_resultados)


def registrar(mensagem):
    """
    Registra uma mensagem com data e hora no arquivo de andamento.
    """
    os.makedirs(PASTA_RESULTADOS, exist_ok=True)
    caminho_log = os.path.join(PASTA_RESULTADOS, ARQ_ANDAMENTO)

    with open(caminho_log, "a", encoding="utf-8") as arquivo_log:
        arquivo_log.write(f"{datetime.datetime.now().isoformat(timespec='seconds')} - {mensagem}\n")


def criar_arquivo(caminho_arqv, tam_mb):
    """
    Cria um arquivo binário de teste com o tamanho especificado em MB.
    """
    tam_bytes = tam_mb * 2 ** 20

    if os.path.exists(caminho_arqv) and os.path.getsize(caminho_arqv) == tam_bytes:
        return

    with open(caminho_arqv, "wb") as arqv:
        for _ in range(tam_mb):
            arqv.write(os.urandom(2 ** 20))

    os.sync()


def limpar_cache(caminho_arqv):
    """
    Solicita ao sistema operacional que descarte as páginas em cache do arquivo.
    """
    descritor_arqv = os.open(caminho_arqv, os.O_RDONLY)

    try:
        os.posix_fadvise(descritor_arqv, 0, 0, os.POSIX_FADV_DONTNEED)
    finally:
        os.close(descritor_arqv)


def ler_conv(caminho_arqv, padrao_leitura, desloc):
    """
    Mede a abertura e a leitura convencional de um arquivo.
    """
    inicio_operacao = time.perf_counter()
    descritor_arqv = os.open(caminho_arqv, os.O_RDONLY)
    tempo_abertura = time.perf_counter() - inicio_operacao
    checksum = 0
    inicio_leitura = time.perf_counter()

    if padrao_leitura == "sequencial":
        while True:
            bloco_bytes = os.read(descritor_arqv, 1 << 20)

            if not bloco_bytes:
                break

            checksum += int(np.frombuffer(bloco_bytes, dtype=np.uint8)[::TAM_PAG].sum())

    else:
        for d in desloc:
            bloco_bytes = os.pread(descritor_arqv, TAM_PAG, int(d))

            if bloco_bytes:
                checksum += bloco_bytes[0]

    tempo_leitura = time.perf_counter() - inicio_leitura
    os.close(descritor_arqv)

    return {"abertura_s": tempo_abertura, "leitura_s": tempo_leitura, "checksum": checksum}


def ler_mapeado(caminho_arqv, padrao_leitura, desloc):
    """
    Mede a abertura, a leitura e o consumo de memória usando mmap.
    """
    inicio_op = time.perf_counter()
    descritor_arqv = os.open(caminho_arqv, os.O_RDONLY)
    arqv_mapeado = mmap.mmap(descritor_arqv, 0, access=mmap.ACCESS_READ)
    tempo_abertura = time.perf_counter() - inicio_op
    checksum = 0
    inicio_leitura = time.perf_counter()

    if padrao_leitura == "sequencial":
        vetor_bytes = np.frombuffer(arqv_mapeado, dtype=np.uint8)
        checksum = int(vetor_bytes[::TAM_PAG].sum())
        del vetor_bytes

    else:
        for d in desloc:
            checksum += arqv_mapeado[int(d):int(d) + TAM_PAG][0]

    tempo_leitura = time.perf_counter() - inicio_leitura
    mem_processo = status_proc()
    arqv_mapeado.close()

    os.close(descritor_arqv)

    return {
        "abertura_s": tempo_abertura,
        "leitura_s": tempo_leitura,
        "checksum": checksum,
        "rss_mapeado_mb": mem_processo["rss"],
        "vsz_mapeado_mb": mem_processo["vsz"],
    }


def executar_c1_c2(registro, argumentos):
    """
    Compara leitura convencional e mmap em arquivos de diferentes tamanhos.
    """
    registrar("== C1/C2: leitura convencional vs mmap")

    pasta_dados_teste = "dados_teste"
    os.makedirs(pasta_dados_teste, exist_ok=True)

    arqv_pequeno = os.path.join(pasta_dados_teste, "pequeno_1MB.bin")
    arqv_grande = os.path.join(pasta_dados_teste, f"grande_{argumentos.tam_grande_mb}MB.bin")

    criar_arquivo(arqv_pequeno, 1)
    criar_arquivo(arqv_grande, argumentos.tam_grande_mb)

    arqv_teste = [
        ("pequeno_1MB", arqv_pequeno),
        (f"grande_{argumentos.tam_grande_mb}MB", arqv_grande),
    ]

    for nome_arqv, caminho_arqv in (("corpus_sqlite", ARQ_DB), ("indice_npy", ARQ_IDX)):
        if os.path.exists(caminho_arqv):
            arqv_teste.append((nome_arqv, caminho_arqv))

    quant_leituras_aleatorias = 500 if argumentos.rapido else 5000

    for nome_arqv, caminho_arqv in arqv_teste:
        tam_arquivo = os.path.getsize(caminho_arqv)
        metodos_leitura = (
            ("convencional", ler_conv, "C1"),
            ("mmap", ler_mapeado, "C2"),
        )

        for nome_metodo, funcao_leitura, experimento in metodos_leitura:
            for padrao_leitura in ("sequencial", "aleatorio"):
                for numero_rodada in range(1, argumentos.rodadas + 1):
                    desloc = np.random.default_rng(numero_rodada).integers(
                        0, max(1, tam_arquivo - TAM_PAG), quant_leituras_aleatorias
                    )

                    limpar_cache(caminho_arqv)

                    for temp_cache in ("fria", "quente"):
                        with Medicao() as medicao:
                            res_leitura = funcao_leitura(caminho_arqv, padrao_leitura, desloc)

                        registro.adicionar_resul(
                            experimento, f"{nome_arqv}|{nome_metodo}|{padrao_leitura}|{temp_cache}",
                            numero_rodada, arquivo=nome_arqv, tam_arquivo_mb=tam_arquivo / 2 ** 20,
                            modo=nome_metodo, padrao=padrao_leitura, temperatura=temp_cache,
                            **res_leitura, **medicao.resultado,
                        )

                registrar(f"   {nome_arqv} {nome_metodo} {padrao_leitura} ok")

    if os.path.exists(ARQ_IDX):
        for modo_map in (None, "r"):
            for numero_rodada in range(1, argumentos.rodadas + 1):
                limpar_cache(ARQ_IDX)
                for temp_cache in ("fria", "quente"):
                    with Medicao() as medicao:
                        inicio_carregamento = time.perf_counter()
                        matriz_vetores = np.load(ARQ_IDX, mmap_mode=modo_map)
                        tempo_carregamento = time.perf_counter() - inicio_carregamento
                        vetor_consulta = np.random.default_rng(numero_rodada).random(
                            matriz_vetores.shape[1], dtype=np.float32
                        )

                        inicio_consultas = time.perf_counter()

                        for _ in range(50):
                            np.argpartition(-(matriz_vetores @ vetor_consulta), 3)[:3]

                        tempo_consultas = time.perf_counter() - inicio_consultas
                        memoria_processo = status_proc()
                        del matriz_vetores

                    nome_metodo = "mmap" if modo_map else "convencional"

                    registro.adicionar_resul(
                        "C2" if modo_map else "C1",
                        f"indice_vetorial|np.load_{nome_metodo}|{temp_cache}",
                        numero_rodada, arquivo="indice_vetorial", modo=nome_metodo,
                        padrao="50_consultas_cosseno", temperatura=temp_cache,
                        abertura_s=tempo_carregamento, leitura_s=tempo_consultas,
                        rss_mapeado_mb=memoria_processo["rss"], vsz_mapeado_mb=memoria_processo["vsz"],
                        **medicao.resultado,
                    )


def executar_c3(registro, args):
    """
    Avalia concorrência entre trabalhadores e diferentes capacidades de fila.
    """
    registrar("== C3: concorrencia e fila (trabalhadores 1/2/4 e capacidade da fila)")

    quant_consultas = 40 if args.rapido else 200
    custo_resposta = 0.005 if args.rapido else 0.02
    consultas = gera_consultas(quant_consultas, "distintas")

    for quant_consumidores in (1, 2, 4):
        for num_rodada in range(1, args.rodadas + 1):
            resultado = Servidor(
                n_trab=quant_consumidores, cap_fila=50, cap_cache=0, custo_resp=custo_resposta
            ).consultar(consultas, n_prod=2)

            registro.adicionar_resul("C3", f"trabalhadores={quant_consumidores}", num_rodada, **resultado)

        registrar(f"   trabalhadores={quant_consumidores} ok")

    for capacidade_fila in (2, 8, 50):
        for num_rodada in range(1, args.rodadas + 1):
            resultado = Servidor(
                n_trab=2, cap_fila=capacidade_fila, cap_cache=0, custo_resp=custo_resposta
            ).consultar(consultas, n_prod=4)

            registro.adicionar_resul("C3", f"fila_cap={capacidade_fila}", num_rodada, **resultado)

        registrar(f"   fila cap={capacidade_fila} ok")


def executar_c4(registro, args):
    """
    Avalia o cache compartilhado com diferentes capacidades e políticas.
    """
    registrar("== C4: cache compartilhado (tamanho, politica, tipo de consulta)")

    quantidade_consultas = 30 if args.rapido else 60
    custo_resp = 0.005 if args.rapido else 0.03

    config_cache = [(0, "LRU")] + [
        (capacidade_cache, politica_cache)
        for capacidade_cache in (8, 64)
        for politica_cache in ("LRU", "FIFO")
    ]

    for tipo_carga in ("repetidas", "mista", "distintas", "parafrases"):
        consultas = gera_consultas(quantidade_consultas, tipo_carga, 0.5)
        for capacidade_cache, politica_cache in config_cache:
            for num_rodada in range(1, args.rodadas + 1):
                res = Servidor(
                    n_trab=1, cap_cache=capacidade_cache, pol=politica_cache, custo_resp=custo_resp
                ).consultar(consultas, n_prod=1)

                registro.adicionar_resul(
                    "C4", f"{tipo_carga}|cache={capacidade_cache}|{politica_cache}",
                    num_rodada, carga=tipo_carga, **res,
                )

        registrar(f"   carga {tipo_carga} ok")

    consultas_repetidas = gera_consultas(quantidade_consultas, "repetidas")

    for num_rodada in range(1, args.rodadas + 1):
        res = Servidor(n_trab=4, cap_cache=64, custo_resp=custo_resp).consultar(
            consultas_repetidas, n_prod=1
        )

        registro.adicionar_resul(
            "C4", "repetidas|cache=64|LRU|4_trabalhadores", num_rodada,
            carga="repetidas", **res,
        )


def executar_c5(registro, args):
    """
    Avalia o impacto do crescimento do corpus de vetores sobre a memória.
    """
    registrar("== C5: pressao de memoria (corpus de vetores crescendo)")

    info_mem_inicial = mem_info()
    mem_disp_mb = info_mem_inicial.get("MemAvailable", 2048)
    limite_mem_mb = args.limite_mem_mb or min(0.45 * mem_disp_mb, 4096)

    registrar(
        f"   MemAvailable={mem_disp_mb:.0f}MB; limite de alocacao={limite_mem_mb:.0f}MB (mude com --limite-mem-mb)")

    dim_vetores = 512
    quant_consultas = 10 if args.rapido else 30
    vetor_consulta = np.random.default_rng(0).random(dim_vetores, dtype=np.float32)

    for fracao_memoria in (0.1, 0.25, 0.5, 1.0):
        tam_corpus_mb = max(8, int(limite_mem_mb * fracao_memoria))
        quant_vetores = tam_corpus_mb * 2 ** 20 // (dim_vetores * 4)
        for num_rodada in range(1, args.rodadas + 1):
            mem_disp_mb = mem_info().get("MemAvailable", 1e9)
            memoria_total_mb = info_mem_inicial.get("MemTotal", 0)

            if mem_disp_mb < tam_corpus_mb + 0.15 * memoria_total_mb:
                registrar(f"   [seguranca] pulando {tam_corpus_mb}MB: pouca memoria disponivel")
                registro.adicionar_resul("C5", f"corpus={tam_corpus_mb}MB", num_rodada,
                                         corpus_mb=tam_corpus_mb, abortado_por_seguranca=1,
                                         )
                continue

            latencias_consulta = []
            with Medicao() as medicao:
                inicio_aloc = time.perf_counter()
                matriz_vetores = np.full((quant_vetores, dim_vetores), 1.0, dtype=np.float32)
                tempo_aloc = time.perf_counter() - inicio_aloc

                for _ in range(quant_consultas):
                    inicio_consulta = time.perf_counter()
                    similaridades = matriz_vetores @ vetor_consulta
                    np.argpartition(-similaridades, 3)[:3]
                    latencias_consulta.append(time.perf_counter() - inicio_consulta)

                del matriz_vetores

            registro.adicionar_resul(
                "C5", f"corpus={tam_corpus_mb}MB", num_rodada,
                corpus_mb=tam_corpus_mb, n_vetores=quant_vetores, alocacao_s=tempo_aloc,
                lat_consulta_media_s=float(np.mean(latencias_consulta)),
                lat_consulta_p95_s=float(np.percentile(latencias_consulta, 95)),
                lat_consulta_max_s=float(np.max(latencias_consulta)), **medicao.resultado,
            )

        registrar(f"   corpus={tam_corpus_mb}MB ok")


def tentar_alocar_memoria(fila_res, mem_extra_mb, tam_aloc_mb):
    """
    Tenta alocar memória em um processo filho com limite RLIMIT_AS.
    """
    mem_virt_mb = status_proc()["vsz"]
    lim_mem_bytes = int((mem_virt_mb + mem_extra_mb) * 2 ** 20)

    resource.setrlimit(resource.RLIMIT_AS, (lim_mem_bytes, lim_mem_bytes))

    try:
        vetor_aloc = np.ones(tam_aloc_mb * 2 ** 20 // 8)
        fila_res.put({"memoryerror": 0, "alocado_mb": vetor_aloc.nbytes / 2 ** 20})
    except MemoryError:
        fila_res.put({"memoryerror": 1, "alocado_mb": 0})


def executar_c6(registro, argumentos):
    """
    Avalia falhas controladas de banco, índice, fila, geração e memória.
    """
    registrar("== C6: falhas controladas")

    consultas = gera_consultas(20 if argumentos.rapido else 30, "mista")
    custo_resp = 0.005 if argumentos.rapido else 0.03

    for numero_rodada in range(1, argumentos.rodadas + 1):
        res = Servidor(db="banco_inexistente.db", cap_cache=8, custo_resp=custo_resp).consultar(consultas)
        registro.adicionar_resul("C6", "banco_ausente", numero_rodada, **res)

        res = Servidor(idx="indice_inexistente.npy", cap_cache=8, custo_resp=custo_resp).consultar(consultas)
        registro.adicionar_resul("C6", "indice_ausente(fallback_lexical)", numero_rodada, **res)

        res = Servidor(
            n_trab=1, cap_fila=2, timeout_put=0.02, tent_put=1, cap_cache=0, custo_resp=0.05
        ).consultar(gera_consultas(40, "distintas"), n_prod=4)

        registro.adicionar_resul("C6", "fila_saturada(cap=2)", numero_rodada, **res)

        res = Servidor(p_falha=0.35, tentativas=2, cap_cache=8, custo_resp=custo_resp).consultar(consultas)
        registro.adicionar_resul("C6", "servico_geracao_falhando(35%)", numero_rodada, **res)

        contexto_multiproces = mp.get_context("fork")
        fila_res = contexto_multiproces.Queue()
        proces_aloc = contexto_multiproces.Process(target=tentar_alocar_memoria, args=(fila_res, 200, 800))
        proces_aloc.start()
        proces_aloc.join(timeout=30)
        res_aloc = fila_res.get() if not fila_res.empty() else {"memoryerror": -1}

        registro.adicionar_resul("C6", "limite_memoria(RLIMIT_AS)", numero_rodada, limite_extra_mb=200,
                                 tentativa_mb=800, **res_aloc)
        fila_res.close()

    registrar("   C6 ok")


def executar_parte_d(registro, args):
    """
    Executa os testes de sincronização com e sem mecanismos de proteção.
    """
    registrar("== Parte D: sincronizacao (corrida sem lock vs com lock)")

    for numero_rodada in range(1, args.rodadas + 1):
        for config, res in sinc_demo.roda_tudo():
            registro.adicionar_resul("D", config, numero_rodada, **res)


def gerar_tabela_markdown(dataframe, nomes_colunas, casas_decimais=4):
    """
    Converte as colunas selecionadas de um DataFrame em uma tabela Markdown.
    """
    cabecalho = "| " + " | ".join(nomes_colunas) + " |\n|" + "---|" * len(nomes_colunas) + "\n"

    linhas_tabela = []
    for _, linha_res in dataframe.iterrows():
        celulas = []
        for nome_coluna in nomes_colunas:
            valor = linha_res[nome_coluna]
            celulas.append(f"{valor:.{casas_decimais}g}" if isinstance(valor, (float, np.floating)) else str(valor))

        linhas_tabela.append("| " + " | ".join(celulas) + " |")

    return cabecalho + "\n".join(linhas_tabela) + "\n"


def gerar_relatorio(registro, pasta_res, args):
    """
    Gera o relatório Markdown com a média das métricas por configuração.
    """
    df_res = pd.DataFrame(registro.linhas_resultados)

    secoes_relatorio = {
        "C1": ("C1/C2 - leitura convencional vs mmap", [
            "tempo_s", "abertura_s", "leitura_s", "minflt", "majflt", "rchar",
            "rss_mapeado_mb", "vsz_mapeado_mb", "rss_max_mb",
        ]),
        "C3": ("C3 - concorrencia e fila", [
            "tempo_total_s", "vazao_req_s", "latencia_mediana", "latencia_p95",
            "espera_media", "fila_media", "fila_max", "utilizacao_trabalhadores",
            "bloqueio_produtores_s", "perdidos", "duplicados", "violacoes_fifo",
        ]),
        "C4": ("C4 - cache compartilhado", [
            "cache_hits", "cache_misses", "taxa_acerto", "cache_substituicoes",
            "cache_tamanho", "tempo_economizado_s", "geracoes_repetidas", "tempo_total_s",
        ]),
        "C5": ("C5 - pressao de memoria", [
            "alocacao_s", "lat_consulta_media_s", "lat_consulta_p95_s", "rss_max_mb",
            "vsz_max_mb", "memavail_min_mb", "swap_max_mb", "minflt", "majflt",
            "swap_in_pag", "swap_out_pag",
        ]),
        "C6": ("C6 - falhas controladas", [
            "falhas", "retentativas", "falhas_geracao", "respostas_degradadas",
            "rejeitadas", "put_timeouts", "processadas", "perdidos", "memoryerror",
        ]),
        "D": ("Parte D - sincronizacao", [
            "atualizacoes_perdidas", "computacoes_duplicadas", "linhas_corrompidas",
            "tempo_s", "perdidos", "fila_max", "produtores_bloqueados_s",
            "consumidor_bloqueado_vazio_s", "deadlock_detectado", "recuperado",
        ]),
    }

    conteudo_relatorio = [
        "# Resultados - GenResearch-Servidor\n\n"
        f"Gerado em {datetime.datetime.now().isoformat(timespec='seconds')} | "
        f"rodadas: {args.rodadas} | modo rapido: {args.rapido}\n\n"
        f"Ambiente em `ambiente.txt`; dados brutos (uma linha por execucao) em `{ARQ_BRUTOS}`.\n"
        "As tabelas mostram a **media das rodadas** de cada configuracao.\n"
    ]

    for codigo_exp in ("C1", "C3", "C4", "C5", "C6", "D"):
        codigos_incluidos = ["C1", "C2"] if codigo_exp == "C1" else [codigo_exp]
        res_exp = df_res[df_res["exp"].isin(codigos_incluidos)]

        if res_exp.empty:
            continue

        titulo_secao, colunas_metricas = secoes_relatorio[codigo_exp]
        colunas_metricas = [nome_coluna for nome_coluna in colunas_metricas if nome_coluna in res_exp.columns]
        medias_config = res_exp.groupby(["exp", "config"], sort=False)[colunas_metricas].mean(
            numeric_only=True).reset_index()
        conteudo_relatorio.append(f"\n## {titulo_secao}\n\n" + gerar_tabela_markdown(medias_config, ["exp", "config"] +
                                                                                     colunas_metricas))

    arqv_relatorio = os.path.join(pasta_res, "relatorio.md")

    with open(arqv_relatorio, "w", encoding="utf-8") as arquivo_relatorio:
        arquivo_relatorio.write("\n".join(conteudo_relatorio))


def main():
    """
    Interpreta os argumentos, executa os experimentos e salva os resultados.
    """
    analisador = argparse.ArgumentParser()
    analisador.add_argument("--rodadas", type=int, default=3)
    analisador.add_argument("--rapido", action="store_true")
    analisador.add_argument("--so", default="c1c2,c3,c4,c5,c6,d")
    analisador.add_argument("--tam-grande-mb", type=int, default=None)
    analisador.add_argument("--limite-mem-mb", type=int, default=None)
    analisador.add_argument("--saida", default=None)

    args = analisador.parse_args()

    if args.tam_grande_mb is None:
        args.tam_grande_mb = 32 if args.rapido else 512

    exp_escolhidos = set(args.so.split(","))

    if not os.path.exists(ARQ_DB) and exp_escolhidos & {"c3", "c4", "c6"}:
        registrar("Banco não encontrado. Execute a preparação dos dados antes dos experimentos.")
        raise SystemExit(1)

    os.makedirs("dados_teste", exist_ok=True)

    pasta_res = args.saida or os.path.join(
        str(PASTA_RESULTADOS), datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    )

    os.makedirs(pasta_res, exist_ok=True)
    os.makedirs(PASTA_RESULTADOS, exist_ok=True)

    arqv_ultima_exec = os.path.join(str(PASTA_RESULTADOS), ARQ_ULTIMA_EXCE)

    with open(arqv_ultima_exec, "w", encoding="utf-8") as arquivo_ultima_execucao:
        arquivo_ultima_execucao.write(pasta_res)

    ambiente.coletar_ambiente(pasta_res)
    registro = RegistraResultados(pasta_res)

    funcoes_experimentos = (
        ("c1c2", executar_c1_c2),
        ("c3", executar_c3),
        ("c4", executar_c4),
        ("c5", executar_c5),
        ("c6", executar_c6),
        ("d", executar_parte_d),
    )

    try:
        for nome_exp, funcao_exp in funcoes_experimentos:
            if nome_exp in exp_escolhidos:
                funcao_exp(registro, args)
    finally:
        registro.salvar_resul()

    gerar_relatorio(registro, pasta_res, args)

    if os.path.exists(ARQ_LOG):
        shutil.copy(ARQ_LOG, os.path.join(pasta_res, ARQ_LOG))

    registrar(f"\n[OK] resultados em {pasta_res}/ ({ARQ_BRUTOS}, relatorio.md, ambiente.txt). "
              "Rode 'python3 graficos.py' pros graficos.")


if __name__ == "__main__":
    main()