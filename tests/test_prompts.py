"""
Testes automatizados para validação de prompts.
"""
import re
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt():
    data = load_prompts(PROMPT_FILE)
    assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' não encontrada no YAML"
    return data[PROMPT_KEY]


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt
        assert prompt["system_prompt"].strip()

    def test_prompt_has_role_definition(self, prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        assert re.search(r"Você é (um|uma) ", prompt["system_prompt"]), \
            "O system_prompt deve definir uma persona com 'Você é um/uma ...'"

    def test_prompt_mentions_format(self, prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        text = prompt["system_prompt"].lower()
        assert "markdown" in text or "user story" in text
        assert "como um" in text and "eu quero" in text and "para que" in text, \
            "O formato padrão de User Story deve estar descrito"

    def test_prompt_has_few_shot_examples(self, prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        text = prompt["system_prompt"]
        assert len(re.findall(r"### Exemplo \d+", text)) >= 2, "Mínimo de 2 exemplos"
        assert text.count("Entrada:") >= 2
        assert text.count("Saída:") >= 2

    def test_prompt_no_todos(self, prompt):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        full_text = yaml.safe_dump(prompt, allow_unicode=True)
        assert "TODO" not in full_text

    def test_minimum_techniques(self, prompt):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt.get("techniques_applied", [])
        assert len(techniques) >= 2
        is_valid, errors = validate_prompt_structure(prompt)
        assert is_valid, errors

    def test_bug_report_only_in_user_prompt(self, prompt):
        """Garante que {bug_report} está só no user_prompt (problema do v1)."""
        assert "{bug_report}" in prompt["user_prompt"]
        assert "{bug_report}" not in prompt["system_prompt"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
