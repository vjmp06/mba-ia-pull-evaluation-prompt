# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Projeto do desafio do MBA em IA (Full Cycle). Ele faz o pull de um prompt de baixa qualidade do LangSmith Prompt Hub, otimiza o prompt com técnicas de Prompt Engineering, publica a nova versão e avalia o resultado com 5 métricas (Helpfulness, Correctness, F1-Score, Clarity e Precision). Para ser aprovado, o prompt precisa de nota **≥ 0.8 em todas** as métricas.

O prompt converte **relatos de bugs em User Stories** com critérios de aceitação.

> Enunciado original do desafio: https://github.com/devfullcycle/mba-ia-pull-evaluation-prompt

---

## Técnicas Aplicadas (Fase 2)

O prompt otimizado está em [`prompts/bug_to_user_story_v2.yml`](prompts/bug_to_user_story_v2.yml) e usa duas técnicas, declaradas em `techniques_applied`.

### 1. Role Prompting

**Por que escolhi:** o v1 dizia só "Você é um assistente que ajuda...". Uma persona genérica gera histórias genéricas. Escrever uma boa User Story exige o olhar de quem conhece produto: separar o *sintoma* (o bug) do *valor* para o usuário, escolher a persona certa e escrever critérios que o QA consiga testar. Uma persona com experiência definida passa esse repertório para o modelo e dá o tom (objetivo, orientado a valor, voltado para dev e QA).

**Como apliquei:**

```text
Você é um Product Owner sênior com mais de 10 anos de experiência em produtos digitais
(e-commerce, SaaS B2B, aplicativos mobile e ERPs). Sua especialidade é traduzir relatos
de bugs — muitas vezes curtos, informais ou muito técnicos — em User Stories claras e
acionáveis [...]. Quem lê o que você escreve é o time de desenvolvimento e QA [...]
```

A persona também sustenta a Regra 6: *"como PO sênior, você complementa o relato com boas práticas de mercado"*. É isso que permite ao modelo sugerir critérios de acessibilidade, prevenção e solução técnica sem contradizer o relato.

### 2. Few-shot Learning

**Por que escolhi:** é obrigatória no desafio e também a técnica mais eficaz para esta tarefa. O formato esperado tem muitos detalhes, como `Dado que / Quando / Então / E`, os blocos `=== ... ===` e as tasks no formato `[ÁREA]`, e descrever tudo isso só em texto é frágil. Os exemplos mostram o formato pronto e o modelo copia o padrão.

**Como apliquei:** são 3 exemplos de entrada e saída, um para cada nível de complexidade do formato de saída. Os exemplos foram criados do zero, sem copiar itens do dataset, para não entregar o gabarito ao modelo:

| Exemplo | Nível | Bug de exemplo | O que ensina |
|---|---|---|---|
| 1 | Simples | Botão "Salvar rascunho" não funciona | História + critérios de aceitação |
| 2 | Médio | Upload de avatar retorna HTTP 413 acima de 2MB | + Critérios Técnicos + Contexto Técnico com "Solução sugerida" |
| 3 | Complexo | App de delivery com 3 falhas (rastreamento, cobrança dupla, push) | Blocos A/B/C + Critérios Técnicos, Contexto do Bug, Tasks e Métricas de Sucesso |

### Outras práticas do prompt

- **Separação entre system e user prompt:** as instruções ficam no `system_prompt` e o `{bug_report}` aparece **só** no `user_prompt`. No v1 ele estava duplicado nos dois.
- **Regras explícitas:** são 7 regras numeradas, cobrindo idioma, modelo da história, persona concreta, quantidade de linhas por critério, preservação literal dos dados técnicos, completude sem contradizer o relato e ausência de texto fora do formato.
- **Formato de saída em 3 níveis:** a estrutura da resposta muda conforme a complexidade do bug. No nível 2 há um bloco complementar escolhido pelo tipo do bug (Acessibilidade, Prevenção, Admins, Exemplo de Cálculo ou Critérios Técnicos).
- **Edge cases:** relato vago, relato que já traz a solução, bugs de segurança, bugs que só ocorrem em um ambiente, vários problemas num mesmo relato e relato em outro idioma.

---

## Resultados Finais

### Evidências no LangSmith

- **Dataset de avaliação público (15 exemplos + experimentos):** https://smith.langchain.com/public/39eddc57-eac5-4a57-b7a8-7dcfb20b7e77/d
- **Prompt publicado no Hub:** `vjmp06/bug_to_user_story_v2`

### Notas por iteração

| Métrica | v1 (referência do enunciado) | v2, iteração 1 | **v2, iteração 2 (final)** |
|---|---|---|---|
| Helpfulness | 0.45 | 0.93 | **0.95 ✓** |
| Correctness | 0.52 | 0.86 | **0.94 ✓** |
| F1-Score | 0.48 | 0.76 ✗ | **0.92 ✓** |
| Clarity | 0.50 | 0.91 | **0.93 ✓** |
| Precision | 0.46 | 0.95 | **0.96 ✓** |
| **Média** | 0.48 | 0.88 | **0.94** |

Status final: ✅ **APROVADO**, com todas as métricas ≥ 0.8.

Modelos usados: `gemini-2.5-flash` para gerar as respostas e também para avaliar (`LLM_PROVIDER=google`).

### Screenshots

<!-- Adicione as imagens em docs/screenshots/ e ajuste os caminhos abaixo -->
- Resultado do `evaluate.py` com todas as métricas ≥ 0.8: `docs/screenshots/evaluate-aprovado.png`
- Experimento no dashboard do LangSmith: `docs/screenshots/langsmith-experimento.png`
- Tracing detalhado de 3 exemplos: `docs/screenshots/tracing-1.png`, `tracing-2.png`, `tracing-3.png`

### Processo de iteração

**Iteração 1 (F1 = 0.76):** a primeira versão restringia demais a saída, com "use apenas estas seções" e "4 a 6 linhas por bloco", para proteger a Precision. A Precision ficou alta (0.95), mas o recall caiu. Analisando o F1 de cada exemplo no LangSmith:

- bugs **simples**: F1 entre 0.82 e 1.00;
- bugs **médios e complexos**: F1 entre 0.52 e 0.78. Os comentários do avaliador apontavam a ausência de "Critérios Técnicos", "Tasks Técnicas Sugeridas", "Métricas de Sucesso", critérios de acessibilidade e da solução técnica sugerida.

Comparando com as respostas esperadas do dataset, vi que elas ficam bem mais ricas à medida que o bug fica mais complexo.

**Iteração 2 (F1 = 0.92):**

- Critérios de aceitação passaram a ter de 5 a 7 linhas, incluindo o retorno ao usuário e o caso de erro.
- Nova regra: todo dado técnico do relato precisa aparecer na resposta, e o PO pode complementar com boas práticas.
- O nível 2 ganhou um bloco complementar escolhido pelo tipo do bug e uma "Solução sugerida" no contexto.
- O nível 3 ganhou `CRITÉRIOS TÉCNICOS`, `CONTEXTO DO BUG`, `TASKS TÉCNICAS SUGERIDAS` e `MÉTRICAS DE SUCESSO`.
- Os exemplos 2 e 3 foram reescritos para mostrar esse formato completo.

O F1 subiu para 0.92 e a Precision se manteve (0.96), mesmo com respostas mais longas.

### Comparação v1 × v2

| Aspecto | v1 | v2 |
|---|---|---|
| Persona | "assistente que ajuda..." (genérica) | Product Owner sênior com domínio e público definidos |
| `{bug_report}` | Duplicado no system e no user prompt | Só no user prompt |
| Instruções | "Analise e crie uma user story" | Tarefa, 7 regras explícitas e casos especiais |
| Formato de saída | Não definido | Modelo "Como um / eu quero / para que" + Dado/Quando/Então, em 3 níveis de complexidade |
| Exemplos | Nenhum | 3 exemplos de entrada e saída (simples, médio e complexo) |
| Edge cases | Nenhum | 6 casos tratados |
| Dados técnicos | Podiam ser perdidos | Precisam ser preservados literalmente |

---

## Como Executar

### Pré-requisitos

- Python 3.10+
- Conta no [LangSmith](https://smith.langchain.com) com API key e **handle público** do Hub criado (veja `.env.example`)
- API key de um provedor de LLM: Google Gemini ou OpenAI

> **Atenção à cota do Gemini:** o plano gratuito permite apenas 20 requisições por dia por modelo, e cada avaliação completa faz cerca de 60 chamadas (15 de geração + 45 dos juízes). Para iterar, ative o faturamento no projeto da chave pelo Google AI Studio.

### Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # preencha as variáveis
```

Variáveis principais do `.env`:

| Variável | Exemplo | Observação |
|---|---|---|
| `LANGSMITH_API_KEY` | `lsv2_...` | |
| `LANGSMITH_PROJECT` | `mba-ia-pull-evaluation-prompt` | Também define o nome do dataset (`<projeto>-eval`) |
| `USERNAME_LANGSMITH_HUB` | `vjmp06` | Só o handle, **não** a URL |
| `LLM_PROVIDER` | `google` | `google` ou `openai` |
| `LLM_MODEL` / `EVAL_MODEL` | `gemini-2.5-flash` | Confira os modelos disponíveis na documentação do provedor |
| `GOOGLE_API_KEY` ou `OPENAI_API_KEY` | | De acordo com o provedor |

### Fases do projeto

```bash
# 1. Pull do prompt original (v1) do LangSmith Hub → prompts/bug_to_user_story_v1.yml
python src/pull_prompts.py

# 2. Otimização: edite prompts/bug_to_user_story_v2.yml

# 3. Testes de validação do prompt (estrutura, persona, formato, few-shot, TODOs, técnicas)
pytest tests/test_prompts.py -v

# 4. Push do prompt otimizado (público, com descrição, tags e técnicas)
python src/push_prompts.py

# 5. Avaliação: cria um experimento no LangSmith e imprime as 5 métricas
python src/evaluate.py
```

Repita os passos 2 a 5 até todas as métricas ficarem ≥ 0.8. Use o tracing do LangSmith para ver, exemplo a exemplo, as respostas e os comentários do avaliador.

### Estrutura

```
├── prompts/
│   ├── bug_to_user_story_v1.yml   # prompt original (pull)
│   └── bug_to_user_story_v2.yml   # prompt otimizado
├── datasets/bug_to_user_story.jsonl  # 15 bugs (5 simples, 7 médios, 3 complexos)
├── src/
│   ├── pull_prompts.py   # pull do Hub → YAML
│   ├── push_prompts.py   # validação + push público ao Hub
│   ├── evaluate.py       # avaliação (fornecido)
│   ├── metrics.py        # métricas (fornecido)
│   └── utils.py          # utilitários (fornecido)
└── tests/test_prompts.py # 7 testes de validação do prompt
```
