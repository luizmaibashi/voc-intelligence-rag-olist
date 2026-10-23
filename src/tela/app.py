"""Tela local da demonstração; executar com python -m streamlit run."""

import streamlit as st

from src.demo import (CACHE_VETORES, LIMITES, RAIZ, REGISTRO_PADRAO,
                      _criar_gerador, carregar_corpus, carregar_modelo,
                      quantificar, responder_cli)
from src.rag import liberacao
from src.tela.logica import (PERGUNTAS_DEMO, ROTULOS_PERGUNTAS, argumentos_responder,
                            argumentos_trilha, caso_por_rotulo, chave_entrada,
                            contagem_citacoes_aprovadas, descricao_recorte,
                            hash_confere, hash_envio_trilha,
                            inteiro_pt, mensagem_status, percentual_pt,
                            posicoes_citacoes, resumo_execucoes, situacao_legivel)


@st.cache_resource
def recursos():
    return carregar_corpus(RAIZ / "data/processed/corpus_reviews.parquet"), carregar_modelo()


def aplicar_preset():
    caso = next((c for c in PERGUNTAS_DEMO if c["id"] == st.session_state["preset"]), None)
    if caso is None:
        return
    for campo in ("pergunta", "nota_min", "nota_max", "situacao", "categoria",
                  "compra_de", "compra_ate", "k"):
        valor = caso[campo]
        st.session_state[campo] = "" if valor is None and campo in {
            "categoria", "compra_de", "compra_ate"} else valor


def cartao_fonte(fonte, posicao=None):
    with st.container(border=True):
        titulo = f"{posicao}. {fonte.get('review_id', 'Sem ID')}" if posicao else fonte.get("review_id", "Sem ID")
        st.markdown(f"**{titulo}**")
        if posicao:
            score = fonte.get("score")
            score_texto = f"{score:.3f}" if isinstance(score, (int, float)) else "—"
            st.caption(f"Nota: {fonte.get('nota', '—')} · Situação: {fonte.get('situacao_entrega', '—')} · Score: {score_texto}")
        st.write(fonte.get("texto", ""))


def mostrar_resultado(saida):
    resposta = saida.get("resposta", {})
    status = resposta.get("status", "sem_status")
    aviso = mensagem_status(status)
    if status == "respondida":
        st.success(aviso)
    elif status == "sem_evidencia":
        st.warning(aviso)
    else:
        st.error(aviso)
    st.markdown("**Texto da resposta**")
    st.write(resposta.get("texto", ""))
    st.markdown("**Fontes citadas**")
    if not saida.get("fontes_citadas"):
        st.write("Nenhuma fonte citada.")
    for fonte in saida.get("fontes_citadas", []):
        cartao_fonte(fonte)
    st.warning("Citação válida não prova suporte; confira as fontes.")


def investigar(corpus, modelo):
    if "preset" not in st.session_state:
        st.session_state["preset"] = "E-A"
        aplicar_preset()
    st.subheader("1. Pergunta")
    st.selectbox("Pergunta", [c["id"] for c in PERGUNTAS_DEMO] + ["Pergunta livre"],
                 key="preset", on_change=aplicar_preset)
    pergunta = st.text_input("Texto da pergunta", key="pergunta")
    col1, col2, col3 = st.columns(3)
    formato_nota = lambda x: "Sem filtro" if x is None else str(x)
    nota_min = col1.selectbox("Nota mínima", [None, 1, 2, 3, 4, 5], key="nota_min", format_func=formato_nota)
    nota_max = col2.selectbox("Nota máxima", [None, 1, 2, 3, 4, 5], key="nota_max", format_func=formato_nota)
    situacao = col3.selectbox("Situação da entrega", [None, "atrasado", "no_prazo", "nao_entregue"],
                              key="situacao", format_func=lambda x: x or "Todos")
    with st.expander("Avançado"):
        categoria = st.text_input("Categoria exata (opcional)", key="categoria")
        c1, c2 = st.columns(2)
        compra_de = c1.text_input("Compra de (AAAA-MM-DD)", key="compra_de")
        compra_ate = c2.text_input("Compra até (AAAA-MM-DD)", key="compra_ate")
        k = st.number_input("k", min_value=1, step=1, key="k")
        gerador = st.selectbox("Gerador", ["gemini", "falso"])
    try:
        args = argumentos_responder(pergunta, k, nota_min, nota_max, situacao,
                                    categoria, compra_de, compra_ate)
    except ValueError:
        st.error("Informe datas no formato AAAA-MM-DD.")
        return
    chave = chave_entrada(args)
    if st.session_state.get("chave_previa") != chave:
        for campo in ("previa", "chave_previa", "resultado", "erro_envio"):
            st.session_state.pop(campo, None)
    comuns = {"registro": REGISTRO_PADRAO, "cache_vetores": CACHE_VETORES}
    st.subheader("2. Prévia")
    if st.button("Gerar prévia", disabled=not pergunta.strip()):
        try:
            previa = responder_cli(corpus, modelo=modelo, **args, executar=False,
                                  gerador="gemini", **comuns)
            st.session_state["previa"] = previa
            st.session_state["chave_previa"] = chave
        except (OSError, ValueError, KeyError, TypeError) as erro:
            st.error(f"Falha local: confira corpus, entrada e pesos MiniLM. {erro}")
    previa = st.session_state.get("previa")
    if previa:
        st.code(previa.get("hash", "Sem hash: contexto vazio"))
        caso = next((c for c in PERGUNTAS_DEMO if c["id"] == st.session_state["preset"]), None)
        if caso:
            if previa.get("hash") == caso["hash"]:
                st.success("Mesmo contexto liberado em 23/10")
            else:
                st.warning("Entrada diferente da liberada: leia o contexto antes de enviar")
        st.info("Nada foi enviado. Leia o contexto; o alerta de PII não substitui sua revisão.")
        alertas = previa.get("alertas_pii", [])
        if alertas:
            st.warning(f"Alertas automáticos de PII: {alertas}")
        else:
            st.info("Nenhum alerta automático (não substitui a leitura)")
        for posicao, fonte in enumerate(previa["contexto"], 1):
            cartao_fonte(fonte, posicao)
        st.subheader("3. Leitura e liberação")
        hash_colado = st.text_input("Cole o hash da prévia")
        revisado = st.checkbox("Li o contexto e nada identifica o cliente")
        if hash_colado:
            if hash_confere(hash_colado, previa.get("hash", "")):
                st.success("hash confere com a prévia")
            else:
                st.warning("hash diferente da prévia")
        st.write(f"Chamadas restantes hoje: {previa.get('chamadas_restantes_hoje', 0)} de {liberacao.TETO_DIARIO}")
    else:
        hash_colado, revisado = "", False
    st.subheader("4. Resposta")
    if gerador == "falso":
        if st.button("Simular", disabled=not pergunta.strip()):
            try:
                st.session_state["resultado"] = responder_cli(corpus, modelo=modelo,
                    **args, gerador="falso", **comuns)
                st.session_state.pop("erro_envio", None)
            except (OSError, ValueError, KeyError, TypeError) as erro:
                st.error(f"Falha local: confira corpus, entrada e pesos MiniLM. {erro}")
    else:
        habilitado = bool(previa and previa.get("hash") and revisado and hash_colado)
        if st.button("Enviar ao Gemini", disabled=not habilitado):
            st.session_state.pop("resultado", None)
            try:
                st.session_state["resultado"] = responder_cli(corpus, modelo=modelo,
                    **args, executar=True, aprovacao_sha256=hash_colado,
                    gerador="gemini", criar_gerador=_criar_gerador, **comuns)
                st.session_state.pop("erro_envio", None)
            except liberacao.EnvioBloqueado as erro:
                st.session_state["erro_envio"] = f"Envio bloqueado: {erro}. Nenhuma API de geração chamada."
            except (OSError, ValueError, KeyError, TypeError) as erro:
                st.error(f"Falha local: confira corpus, entrada, pesos MiniLM e credencial. {erro}")
    if st.session_state.get("erro_envio"):
        st.error(st.session_state["erro_envio"])
    if st.session_state.get("resultado"):
        if st.session_state["resultado"].get("modo") == "simulado":
            st.success("Simulado: nenhuma chamada ao Gemini")
        mostrar_resultado(st.session_state["resultado"])


def aplicar_preset_gestor():
    caso = caso_por_rotulo(st.session_state["g_preset"])
    if caso is None:
        st.session_state["g_pergunta"] = ""
        st.session_state["g_nota_min"] = None
        st.session_state["g_nota_max"] = None
        st.session_state["g_situacao"] = None
        return
    st.session_state["g_pergunta"] = caso["pergunta"]
    st.session_state["g_nota_min"] = caso["nota_min"]
    st.session_state["g_nota_max"] = caso["nota_max"]
    st.session_state["g_situacao"] = caso["situacao"]


def cartao_relato_gestor(fonte, posicao):
    with st.container(border=True):
        situacao = situacao_legivel(fonte.get("situacao_entrega"))
        st.markdown(f"**{posicao} · nota {fonte.get('nota', '—')} · {situacao}**")
        st.write(fonte.get("texto", ""))
        st.caption(f"ID: {fonte.get('review_id', '—')}")


def perguntar(corpus, modelo):
    if "g_preset" not in st.session_state:
        st.session_state["g_preset"] = "Relatos de atraso"
        aplicar_preset_gestor()
    st.subheader("1. Pergunta")
    st.selectbox("O que deseja investigar?", list(ROTULOS_PERGUNTAS) +
                 ["Escrever minha pergunta"], key="g_preset", on_change=aplicar_preset_gestor)
    pergunta = st.text_input("Pergunta", key="g_pergunta")
    with st.expander("Ajustar recorte"):
        cols = st.columns(3)
        formato_nota = lambda x: "Sem filtro" if x is None else str(x)
        nota_min = cols[0].selectbox("Nota mínima", [None, 1, 2, 3, 4, 5],
                                     key="g_nota_min", format_func=formato_nota)
        nota_max = cols[1].selectbox("Nota máxima", [None, 1, 2, 3, 4, 5],
                                     key="g_nota_max", format_func=formato_nota)
        situacao = cols[2].selectbox("Situação da entrega",
                    [None, "atrasado", "no_prazo", "nao_entregue"],
                    key="g_situacao", format_func=lambda x: situacao_legivel(x))
    st.write(descricao_recorte(nota_min, nota_max, situacao))
    args = argumentos_trilha(pergunta, nota_min, nota_max, situacao)
    chave = chave_entrada(args)
    if st.session_state.get("g_chave_previa") != chave:
        for campo in ("g_previa", "g_chave_previa", "g_resultado", "g_erro_envio"):
            st.session_state.pop(campo, None)
        st.session_state["g_revisado"] = False
    comuns = {"registro": REGISTRO_PADRAO, "cache_vetores": CACHE_VETORES}
    if st.button("Buscar relatos", disabled=not pergunta.strip()):
        st.session_state.pop("g_resultado", None)
        st.session_state.pop("g_erro_envio", None)
        st.session_state.pop("g_previa", None)
        st.session_state["g_revisado"] = False
        try:
            st.session_state["g_previa"] = responder_cli(corpus, modelo=modelo,
                **args, executar=False, gerador="gemini", **comuns)
            st.session_state["g_chave_previa"] = chave
        except (OSError, ValueError, KeyError, TypeError) as erro:
            st.error(f"Falha local: confira corpus, entrada e pesos MiniLM. {erro}")
    previa = st.session_state.get("g_previa")
    if not previa:
        return

    contexto = previa.get("contexto", [])
    st.subheader("2. Relatos encontrados")
    st.markdown(f"**{inteiro_pt(len(contexto))} relatos encontrados**")
    st.write("Os mais próximos da pergunta pelo sentido. Leia antes de seguir.")
    if not contexto:
        st.info("Nenhum relato neste recorte")
        return
    for posicao, fonte in enumerate(contexto[:3], 1):
        cartao_relato_gestor(fonte, posicao)
    if len(contexto) > 3:
        with st.expander(f"Mostrar os outros {inteiro_pt(len(contexto) - 3)}"):
            for posicao, fonte in enumerate(contexto[3:], 4):
                cartao_relato_gestor(fonte, posicao)

    st.subheader("3. Aprovar o envio")
    alertas = previa.get("alertas_pii", [])
    if alertas:
        st.warning(f"Alertas automáticos de dados pessoais: {alertas}")
    else:
        st.info("Alerta automático de dados pessoais: nenhum. O alerta não substitui a sua leitura.")
    caso = caso_por_rotulo(st.session_state["g_preset"])
    if caso:
        if previa.get("hash") == caso["hash"]:
            st.success("Mesmo contexto liberado em 23/10")
        else:
            st.warning("Entrada diferente da liberada: leia o contexto antes de enviar")
    revisado = st.checkbox("Li os relatos e nada identifica o cliente", key="g_revisado")
    hash_aprovado = hash_envio_trilha(previa, revisado, chave,
                                     st.session_state.get("g_chave_previa"))
    selo = previa.get("hash", "")[:8]
    st.caption(f"selo {selo}… · {previa.get('chamadas_restantes_hoje', 0)} de {liberacao.TETO_DIARIO} chamadas restantes hoje")
    if st.button("Aprovar e gerar resposta", type="primary", disabled=hash_aprovado is None):
        st.session_state.pop("g_resultado", None)
        try:
            st.session_state["g_resultado"] = responder_cli(corpus, modelo=modelo,
                **args, executar=True, aprovacao_sha256=hash_aprovado,
                gerador="gemini", criar_gerador=_criar_gerador, **comuns)
            st.session_state.pop("g_erro_envio", None)
        except liberacao.EnvioBloqueado as erro:
            st.session_state["g_erro_envio"] = str(erro)
        except (OSError, ValueError, KeyError, TypeError) as erro:
            st.error(f"Falha local: confira corpus, entrada, pesos MiniLM e credencial. {erro}")
    if st.button("Simular (sem chamar o Gemini)"):
        try:
            st.session_state["g_resultado"] = responder_cli(corpus, modelo=modelo,
                **args, gerador="falso", **comuns)
            st.session_state.pop("g_erro_envio", None)
        except (OSError, ValueError, KeyError, TypeError) as erro:
            st.error(f"Falha local: confira corpus, entrada e pesos MiniLM. {erro}")
    if st.session_state.get("g_erro_envio"):
        st.error("Envio bloqueado: o contexto mudou desde a leitura ou o limite do dia acabou. Nenhuma chamada foi feita.")
        st.caption(st.session_state["g_erro_envio"])
    saida = st.session_state.get("g_resultado")
    if not saida:
        return

    st.subheader("4. Resposta")
    if saida.get("modo") == "simulado":
        st.info("Simulado: nenhuma chamada ao Gemini")
    resposta = saida.get("resposta", {})
    status = resposta.get("status", "sem_status")
    if status == "respondida":
        st.success(mensagem_status(status))
    elif status == "sem_evidencia":
        st.warning(mensagem_status(status))
    else:
        st.error(mensagem_status(status))
    st.markdown("**Resposta**")
    st.write(resposta.get("texto", ""))
    posicoes = posicoes_citacoes(contexto, resposta.get("review_ids", []))
    if posicoes:
        st.write("Cita os relatos " + ", ".join(str(posicao) for posicao in posicoes))
    else:
        st.write("Nenhum relato citado.")
    with st.expander("Ver relatos citados"):
        for fonte in saida.get("fontes_citadas", []):
            posicao = posicoes_citacoes(contexto, [fonte["review_id"]])[0]
            cartao_relato_gestor(fonte, posicao)

    st.subheader("5. Conferência e tamanho do problema")
    dentro, total = contagem_citacoes_aprovadas(posicoes)
    st.write(f"{inteiro_pt(dentro)} de {inteiro_pt(total)} citações estão entre os relatos aprovados")
    if situacao in (None, "atrasado"):
        dados = quantificar(corpus)["resultado"]
        st.metric("Das entregas atrasaram", percentual_pt(dados["proporcao"]))
        st.write(f"{inteiro_pt(dados['atrasadas'])} de {inteiro_pt(dados['entregues'])} · "
                 f"IC95% {percentual_pt(dados['ic95_inf'])} a {percentual_pt(dados['ic95_sup'])}")
        st.caption("A resposta mostra exemplos; o tamanho do problema vem da contagem, não da IA.")


def main():
    st.set_page_config(page_title="VoC Intelligence", layout="wide")
    st.title("VoC Intelligence — tela local")
    try:
        corpus, modelo = recursos()
    except (OSError, ValueError, KeyError, TypeError):
        st.error("Falha local: confira corpus, entrada, pesos MiniLM e credencial.")
        return
    tab_perguntar, tab_numeros, tab_execucoes, tab_tecnico = st.tabs(
        ["Perguntar", "Números", "Execuções", "Modo técnico"])
    with tab_perguntar:
        perguntar(corpus, modelo)
    with tab_numeros:
        saida = quantificar(corpus)
        dados = saida["resultado"]
        cols = st.columns(3)
        cols[0].metric("Atrasadas", inteiro_pt(dados["atrasadas"]))
        cols[1].metric("População", inteiro_pt(dados["entregues"]))
        cols[2].metric("Proporção", percentual_pt(dados["proporcao"]))
        st.write(f"IC95% de Wilson: {percentual_pt(dados['ic95_inf'])} a "
                 f"{percentual_pt(dados['ic95_sup'])}; n = {inteiro_pt(dados['entregues'])}")
        st.write(f"Entregas atrasadas: {inteiro_pt(dados['atrasadas'])} de "
                 f"{inteiro_pt(dados['entregues'])} avaliações com comentário de pedidos "
                 f"entregues. Compras de {dados['inicio']} a {dados['fim']}.")
        st.caption(LIMITES)
        with st.expander("Detalhes"):
            st.json(dados)
    with tab_execucoes:
        try:
            linhas = liberacao._ler_registro(REGISTRO_PADRAO)
            if not linhas:
                st.info("Nenhuma execução registrada")
            else:
                resumo = resumo_execucoes(linhas)
                cols = st.columns(4)
                cols[0].metric("Tentativas (n)", inteiro_pt(resumo["tentativas"]))
                cols[1].metric("Erros de integração", inteiro_pt(resumo["erros_integracao"]))
                taxa = resumo["taxa_erro"]
                cols[2].metric("Taxa de erro", percentual_pt(taxa, 1) if taxa is not None else "—")
                mediana = resumo["mediana_duracao_ms_sem_erro"]
                cols[3].metric("Mediana sem erro", f"{inteiro_pt(round(mediana))} ms" if mediana is not None else "—")
                inf, sup = resumo["ic95_wilson"]
                if taxa is not None:
                    st.write(f"Erros de integração: {inteiro_pt(resumo['erros_integracao'])}/"
                             f"{inteiro_pt(resumo['tentativas'])} tentativas; "
                             f"IC95% de Wilson: {percentual_pt(inf, 1)} a {percentual_pt(sup, 1)}.")
                else:
                    st.write("Taxa sem tentativas para estimar (n = 0).")
                st.write("Resultados por status")
                st.dataframe([{"Status": nome, "Total": inteiro_pt(total)} for nome, total in
                              resumo["resultados_por_status"].items()], use_container_width=True)
                st.caption(f"Linhas de outro formato: {inteiro_pt(resumo['linhas_outro_formato'])}")
                with st.expander("Últimas execuções"):
                    st.dataframe(linhas[-20:][::-1], use_container_width=True)
        except ValueError as erro:
            st.error(str(erro))
    with tab_tecnico:
        investigar(corpus, modelo)


if __name__ == "__main__":
    main()
