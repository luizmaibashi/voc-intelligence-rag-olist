"""Tela local da demonstração; executar com python -m streamlit run."""

from datetime import date

import streamlit as st

from src.demo import (CACHE_VETORES, LIMITES, RAIZ, REGISTRO_PADRAO,
                      _criar_gerador, carregar_corpus, carregar_modelo,
                      quantificar, responder_cli)
from src.rag import liberacao
from src.tela.logica import argumentos_responder, chave_entrada, resumo_execucoes


@st.cache_resource
def recursos():
    return carregar_corpus(RAIZ / "data/processed/corpus_reviews.parquet"), carregar_modelo()


def mostrar_resultado(saida):
    resposta = saida.get("resposta", {})
    st.subheader(resposta.get("status", "Resultado"))
    st.write(resposta.get("texto", ""))
    st.write("IDs citados:", resposta.get("review_ids", []))
    for fonte in saida.get("fontes_citadas", []):
        st.markdown(f"**{fonte['review_id']}**")
        st.write(fonte["texto"])
    st.warning("Citação válida não prova suporte; confira as fontes.")


def investigar(corpus, modelo):
    pergunta = st.text_input("Pergunta")
    col1, col2, col3 = st.columns(3)
    nota_min = col1.selectbox("Nota mínima", [None, 1, 2, 3, 4, 5], format_func=lambda x: "Sem filtro" if x is None else str(x))
    nota_max = col2.selectbox("Nota máxima", [None, 1, 2, 3, 4, 5], format_func=lambda x: "Sem filtro" if x is None else str(x))
    situacao = col3.selectbox("Situação da entrega", [None, "atrasado", "no_prazo", "nao_entregue"], format_func=lambda x: x or "Todos")
    categoria = st.text_input("Categoria exata (opcional)")
    c1, c2 = st.columns(2)
    compra_de = c1.text_input("Compra de (AAAA-MM-DD)")
    compra_ate = c2.text_input("Compra até (AAAA-MM-DD)")
    k = st.number_input("k", min_value=1, value=10, step=1)
    gerador = st.selectbox("Gerador", ["gemini", "falso"])
    try:
        args = argumentos_responder(pergunta, k, nota_min, nota_max, situacao,
                                    categoria, compra_de, compra_ate)
    except ValueError:
        st.error("Informe datas no formato AAAA-MM-DD.")
        return
    chave = chave_entrada(args)
    if st.session_state.get("chave_previa") != chave:
        st.session_state.pop("previa", None)
        st.session_state.pop("chave_previa", None)
    comuns = {"registro": REGISTRO_PADRAO, "cache_vetores": CACHE_VETORES}
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
        st.subheader("Contexto da prévia")
        st.dataframe([{"ID": f.get("review_id"), "Texto": f.get("texto"),
                       "Nota": f.get("nota"), "Situação": f.get("situacao_entrega"),
                       "Score": f.get("score")} for f in previa["contexto"]],
                     use_container_width=True)
        st.write("Alertas de PII:", previa.get("alertas_pii", []))
        st.write("Chamadas restantes hoje:", previa.get("chamadas_restantes_hoje"))
        st.code(previa.get("hash", "Sem hash: contexto vazio"))
        st.info("Nada foi enviado. Leia o contexto; o alerta de PII não substitui sua revisão.")
    if gerador == "falso":
        if st.button("Simular", disabled=not pergunta.strip()):
            try:
                saida = responder_cli(corpus, modelo=modelo, **args, gerador="falso", **comuns)
                st.success("Simulado: nenhuma chamada ao Gemini")
                mostrar_resultado(saida)
            except (OSError, ValueError, KeyError, TypeError) as erro:
                st.error(f"Falha local: confira corpus, entrada e pesos MiniLM. {erro}")
    else:
        hash_colado = st.text_input("Cole o hash da prévia")
        revisado = st.checkbox("Li o contexto e nada identifica o cliente")
        habilitado = bool(previa and previa.get("hash") and revisado and hash_colado)
        if st.button("Enviar ao Gemini", disabled=not habilitado):
            try:
                saida = responder_cli(corpus, modelo=modelo, **args, executar=True,
                                      aprovacao_sha256=hash_colado, gerador="gemini",
                                      criar_gerador=_criar_gerador, **comuns)
                mostrar_resultado(saida)
            except liberacao.EnvioBloqueado as erro:
                st.error(f"Envio bloqueado: {erro}. Nenhuma API de geração chamada.")
            except (OSError, ValueError, KeyError, TypeError) as erro:
                st.error(f"Falha local: confira corpus, entrada, pesos MiniLM e credencial. {erro}")


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
        st.write(saida["resumo"])
        st.json(saida["resultado"])
        st.caption(LIMITES)
    with tab_execucoes:
        try:
            linhas = liberacao._ler_registro(REGISTRO_PADRAO)
            st.json(resumo_execucoes(linhas))
            st.dataframe(linhas[-20:][::-1], use_container_width=True)
        except ValueError as erro:
            st.error(str(erro))


if __name__ == "__main__":
    main()
