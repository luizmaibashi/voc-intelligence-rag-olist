"""Tela local da demonstração; executar com python -m streamlit run."""

import streamlit as st

from src.demo import (CACHE_VETORES, LIMITES, RAIZ, REGISTRO_PADRAO,
                      _criar_gerador, carregar_corpus, carregar_modelo,
                      quantificar, responder_cli)
from src.rag import liberacao
from src.tela.logica import (PERGUNTAS_DEMO, argumentos_responder, chave_entrada,
                            hash_confere, mensagem_status, resumo_execucoes)


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
        k = st.number_input("k", min_value=1, value=10, step=1, key="k")
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


def main():
    st.set_page_config(page_title="VoC Intelligence", layout="wide")
    st.title("VoC Intelligence — tela local")
    try:
        corpus, modelo = recursos()
    except (OSError, ValueError, KeyError, TypeError):
        st.error("Falha local: confira corpus, entrada, pesos MiniLM e credencial.")
        return
    tab_investigar, tab_contagem, tab_execucoes = st.tabs(["Investigar", "Contagem", "Execuções"])
    with tab_investigar:
        investigar(corpus, modelo)
    with tab_contagem:
        saida = quantificar(corpus)
        dados = saida["resultado"]
        cols = st.columns(3)
        cols[0].metric("Atrasadas", f"{dados['atrasadas']:,}")
        cols[1].metric("População", f"{dados['entregues']:,}")
        cols[2].metric("Proporção", f"{dados['proporcao']:.2%}")
        st.write(f"IC95% de Wilson: {dados['ic95_inf']:.2%} a {dados['ic95_sup']:.2%}; n = {dados['entregues']:,}")
        st.write(saida["resumo"])
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
                cols[0].metric("Tentativas (n)", resumo["tentativas"])
                cols[1].metric("Erros de integração", resumo["erros_integracao"])
                taxa = resumo["taxa_erro"]
                cols[2].metric("Taxa de erro", f"{taxa:.1%}" if taxa is not None else "—")
                mediana = resumo["mediana_duracao_ms_sem_erro"]
                cols[3].metric("Mediana sem erro", f"{mediana:.0f} ms" if mediana is not None else "—")
                inf, sup = resumo["ic95_wilson"]
                if taxa is not None:
                    st.write(f"Erros de integração: {resumo['erros_integracao']}/{resumo['tentativas']} tentativas; IC95% de Wilson: {inf:.1%} a {sup:.1%}.")
                else:
                    st.write("Taxa sem tentativas para estimar (n = 0).")
                st.write("Resultados por status")
                st.dataframe([{"Status": nome, "Total": total} for nome, total in
                              resumo["resultados_por_status"].items()], use_container_width=True)
                st.caption(f"Linhas de outro formato: {resumo['linhas_outro_formato']}")
                with st.expander("Últimas execuções"):
                    st.dataframe(linhas[-20:][::-1], use_container_width=True)
        except ValueError as erro:
            st.error(str(erro))


if __name__ == "__main__":
    main()
