"""Contrato da cópia reproduzível de julgamentos."""
import json

from scripts.copiar_julgamentos import main


def escrever(path, linhas):
    with path.open("w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in linhas))


def base(tmp_path):
    antiga, nova, saida = (tmp_path / nome for nome in ("antiga.jsonl", "nova.jsonl", "saida.jsonl"))
    linhas = [
        {"id": "E01", "tipo": "frase", "ordem": 1, "frase": "Primeira.", "julgamento": "S", "motivo": None, "nota": ""},
        {"id": "E01", "tipo": "frase", "ordem": 2, "frase": "Segunda.", "julgamento": "NS", "motivo": "SEM_BASE", "nota": "rever"},
        {"id": "E02", "tipo": "sem_evidencia", "julgamento_caso": "S"},
        {"id": "E20", "tipo": "nao_julgavel", "classe": "controle_local", "julgamento_controle": "S"},
    ]
    escrever(antiga, linhas)
    escrever(nova, [{**r, **({"julgamento": None, "motivo": None, "nota": ""} if r["tipo"] == "frase" else {"julgamento_caso": None} if r["tipo"] == "sem_evidencia" else {"julgamento_controle": None})} for r in linhas])
    return antiga, nova, saida, linhas


def test_copia_frases_recusa_controle_byte_a_byte(tmp_path):
    antiga, nova, saida, _ = base(tmp_path)
    assert main([str(antiga), str(nova), str(saida)]) == 0
    assert saida.read_bytes() == antiga.read_bytes()


def test_frase_diferente_para_sem_criar_saida(tmp_path, capsys):
    antiga, nova, saida, linhas = base(tmp_path)
    linhas[0]["frase"] = "Outra."
    escrever(nova, linhas)
    assert main([str(antiga), str(nova), str(saida)]) != 0
    assert "PARE" in capsys.readouterr().err
    assert not saida.exists()


def test_caso_ausente_para_sem_criar_saida(tmp_path, capsys):
    antiga, nova, saida, linhas = base(tmp_path)
    escrever(nova, linhas[:-1])
    assert main([str(antiga), str(nova), str(saida)]) != 0
    assert "PARE" in capsys.readouterr().err
    assert not saida.exists()


def test_saida_existente_recusa(tmp_path):
    antiga, nova, saida, _ = base(tmp_path)
    saida.write_text("intacto", encoding="utf-8")
    assert main([str(antiga), str(nova), str(saida)]) != 0
    assert saida.read_text(encoding="utf-8") == "intacto"


def test_ids_novos_sem_julgamento(tmp_path, capsys):
    antiga, nova, saida, linhas = base(tmp_path)
    linhas.append({"id": "E05", "tipo": "frase", "ordem": 1, "frase": "Nova.", "julgamento": None})
    escrever(nova, linhas)
    assert main([str(antiga), str(nova), str(saida)]) == 0
    assert "ids sem julgamento: E05" in capsys.readouterr().out
