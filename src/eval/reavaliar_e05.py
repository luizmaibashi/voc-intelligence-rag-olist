"""Reavaliação isolada do E05 revisado na rodada 04 (spec 0006).

Prévia sem API por padrão; não permite alterar lote, modelo ou repetição.
"""
import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from src.eval import avaliar_geracao as lote
from src.rag.responder import Resposta, responder
from src.rag.tentativas import GeradorComTentativas

HASH_ORIGEM = "8953bffc2db35a5ff48371763c97238bf04eb16ad4424564f30ba7c6afc9ccd0"


def previa(manifesto: dict) -> dict:
    # Validar/congelar o lote inteiro antes de selecionar, sem contornar contrato.
    lote.validar_manifesto(manifesto)
    congelado = json.loads(lote._canonico(manifesto))
    digest = lote.hash_lote(congelado, repetir_transitorios=True)
    if digest != HASH_ORIGEM:
        raise ValueError("Payload/configuração divergem da rodada revisada.")
    return {"tipo": "previa_e05", "hash_lote_origem": digest,
            "configuracao": lote.configuracao_execucao(repetir_transitorios=True),
            "caso": next(c for c in congelado["casos"] if c["id"] == "E05")}


def digests_codigo() -> dict:
    raiz = Path(__file__).resolve().parents[1]
    caminhos = ("eval/reavaliar_e05.py", "eval/avaliar_geracao.py",
                "rag/provedor_gemini.py", "rag/responder.py", "rag/tentativas.py")
    return {f"src/{p}": hashlib.sha256((raiz / p).read_bytes()).hexdigest()
            for p in caminhos}


def executar(manifesto: dict, *, aprovacao_sha256: str, previsao: int,
             saida: Path, gerar=None) -> None:
    revisado = previa(manifesto)
    if aprovacao_sha256 != HASH_ORIGEM:
        raise ValueError("Hash informado não corresponde ao lote revisado.")
    if type(previsao) is not int or previsao not in (0, 1):
        raise ValueError("Previsão deve ser 0 ou 1.")
    if gerar is not None and not callable(gerar):
        raise ValueError("Gerador inválido.")
    caso = revisado["caso"]
    client = None
    with Path(saida).open("x", encoding="utf-8") as arquivo:
        def registrar(evento):
            arquivo.write(lote._canonico(evento) + "\n")
            arquivo.flush()
        registrar({**revisado, "tipo": "cabecalho_e05", "previsao": previsao,
                   "codigo_sha256": digests_codigo(),
                   "utc": datetime.now(timezone.utc).isoformat(),
                   "gate_demo": "bloqueado", "julgamento_semantico": "pendente"})
        try:
            if gerar is None:
                try:
                    gerar, client = lote._criar_gerador()
                except Exception as erro:
                    registrar({"tipo": "erro_setup", **lote._erro_seguro(erro, "cliente")})
                    raise ValueError("Não foi possível criar o cliente.") from None
            falha_registro = []
            captura = {"saida_provedor": None, "erro_integracao": None}

            def registrar_tentativa(evento):
                try:
                    registrar({"tipo": "tentativa", "id": "E05", **evento})
                except Exception as erro:
                    falha_registro.append(erro)
                    raise

            controlador = GeradorComTentativas(gerar, registrar_tentativa)

            def capturar(pergunta, evidencias):
                try:
                    resultado = controlador(pergunta, evidencias)
                    captura["saida_provedor"] = lote._saida_serializavel(resultado)
                    return resultado
                except Exception as erro:
                    if not falha_registro:
                        captura["erro_integracao"] = lote._erro_seguro(erro, "gerador")
                    raise

            try:
                resposta = responder(caso["pergunta"], caso["evidencias"], capturar)
            except Exception as erro:
                captura["erro_integracao"] = lote._erro_seguro(erro, "validacao_aplicacao")
                resposta = Resposta("erro_geracao", "Saída inválida do modelo.")
            if falha_registro:
                raise falha_registro[0]
            registrar({"tipo": "caso", "id": "E05", **captura,
                       "resposta_aplicacao": asdict(resposta),
                       "status_esperado_compativel": resposta.status in caso["status_esperados"],
                       "tentativa": controlador.tentativas,
                       "julgamento_semantico": "pendente"})
            registrar({"tipo": "fim", "casos_registrados": 1,
                       "chamadas_externas": controlador.tentativas,
                       "gate_demo": "bloqueado"})
        finally:
            if client is not None:
                client.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifesto", type=Path, required=True)
    parser.add_argument("--executar", action="store_true")
    parser.add_argument("--aprovacao-sha256")
    parser.add_argument("--previsao", type=int)
    parser.add_argument("--saida", type=Path)
    args = parser.parse_args(argv)
    try:
        manifesto = lote.carregar_manifesto(args.manifesto)
        if args.executar:
            if args.saida is None:
                raise ValueError("Informe arquivo novo de saída.")
            executar(manifesto, aprovacao_sha256=args.aprovacao_sha256,
                     previsao=args.previsao, saida=args.saida)
        else:
            print(json.dumps(previa(manifesto), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError):
        print("Falha: confira ambiente, contrato, hash, previsão e saída.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
