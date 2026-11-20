"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

DICAS DE IMPLEMENTAÇÃO:

- O pull é feito pelo cliente do LangSmith:

      from langsmith import Client
      client = Client()
      prompt = client.pull_prompt(
          "leonanluppi/bug_to_user_story_v1",
          dangerously_pull_public_prompt=True,
      )

- O parâmetro `dangerously_pull_public_prompt=True` é obrigatório sempre que o
  identificador tem dono explícito ("owner/nome"). O LangSmith bloqueia esse pull
  por padrão porque um prompt do Hub é um objeto LangChain serializado, que pode
  vir de terceiros. Aqui o prompt é o do desafio, então o risco é conhecido.

- O retorno é um ChatPromptTemplate. Para extrair o conteúdo das mensagens,
  use a serialização nativa do LangChain (`prompt.messages`, e o atributo
  `.prompt.template` de cada mensagem).

- Use `save_yaml` de utils.py para gravar o resultado no arquivo .yml.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts.chat import HumanMessagePromptTemplate, SystemMessagePromptTemplate
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


def pull_prompts_from_langsmith():
    try:
        client = Client()
        prompt = client.pull_prompt(
            "leonanluppi/bug_to_user_story_v1",
            dangerously_pull_public_prompt=True,
        )

        system_prompt, user_prompt = "", ""
        for msg in prompt.messages:
            if isinstance(msg, SystemMessagePromptTemplate):
                system_prompt = msg.prompt.template
            elif isinstance(msg, HumanMessagePromptTemplate):
                user_prompt = msg.prompt.template

        data = {
            "bug_to_user_story_v1": {
                "description": "Prompt para converter relatos de bugs em User Stories",
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "version": "v1",
                "tags": ["bug-analysis", "user-story", "product-management"],
            }
        }

        output_path = Path(__file__).resolve().parent.parent / "prompts" / "bug_to_user_story_v1.yml"
        if not save_yaml(data, str(output_path)):
            return False
        print(f"✅ Prompt salvo em {output_path}")
        return True

    except Exception as e:
        print(f"Error occurred while pulling prompts: {e}")
        return 1


def main():
    """Função principal"""
    # Verifica se as variáveis de ambiente necessárias estão definidas
    required_env_vars = ["LANGSMITH_API_KEY"]
    if check_env_vars(required_env_vars) == False:
        return 1
    print_section_header("Pulling prompts from LangSmith Prompt Hub")
    pull_prompts_from_langsmith()
    print("Prompts pulled and saved successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
