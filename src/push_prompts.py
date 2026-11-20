"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        username = os.getenv("USERNAME_LANGSMITH_HUB")
        full_name = f"{username}/{prompt_name}"

        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_data["system_prompt"]),
            ("user", prompt_data.get("user_prompt", "{bug_report}")),
        ])

        techniques = prompt_data.get("techniques_applied", [])
        tags = list(dict.fromkeys(prompt_data.get("tags", []) + techniques))
        description = prompt_data.get("description", "")
        if techniques:
            description = f"{description} | Técnicas: {', '.join(techniques)}"

        client = Client()
        url = client.push_prompt(
            full_name,
            object=prompt,
            is_public=True,
            description=description,
            tags=tags,
        )
        print(f"✅ Push realizado: {full_name}")
        print(f"   {url}")
        return True

    except Exception as e:
        if "nothing to commit" in str(e).lower():
            print(f"ℹ️  {prompt_name} já está atualizado no Hub (nenhuma alteração).")
            return True
        print(f"❌ Erro ao fazer push de {prompt_name}: {e}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []
    for field in ("description", "system_prompt", "user_prompt", "version"):
        if not str(prompt_data.get(field, "")).strip():
            errors.append(f"Campo obrigatório vazio ou ausente: {field}")

    full_text = f"{prompt_data.get('system_prompt', '')}\n{prompt_data.get('user_prompt', '')}"
    if "TODO" in full_text:
        errors.append("Prompt ainda contém TODOs")
    if "{bug_report}" not in prompt_data.get("user_prompt", ""):
        errors.append("user_prompt precisa conter a variável {bug_report}")
    if "{bug_report}" in prompt_data.get("system_prompt", ""):
        errors.append("{bug_report} não deve estar no system_prompt")
    if len(prompt_data.get("techniques_applied", [])) < 2:
        errors.append("Mínimo de 2 técnicas em techniques_applied")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    print_section_header("Push de prompts otimizados para o LangSmith Hub")

    yaml_path = Path(__file__).resolve().parent.parent / "prompts" / "bug_to_user_story_v2.yml"
    data = load_yaml(str(yaml_path))
    if not data:
        return 1

    success = True
    for prompt_name, prompt_data in data.items():
        is_valid, errors = validate_prompt(prompt_data)
        if not is_valid:
            print(f"❌ {prompt_name} inválido:")
            for err in errors:
                print(f"   - {err}")
            success = False
            continue
        success = push_prompt_to_langsmith(prompt_name, prompt_data) and success

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
