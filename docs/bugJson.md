# Histórico de Debug: Erro de Extração de JSON do Gemini 2.0 no TinyTroupeLiteLLM

## Data: 31 de Julho de 2025

## Problema Inicial

O sistema TinyTroupeLiteLLM, após integração com o modelo Gemini 2.0 (via `vertex_ai` e `litellm`), começou a apresentar erros de análise de JSON na saída do modelo. Os erros mais comuns eram:

*   `Error occurred while extracting JSON: Extra data: line 1 column XXX (char YYY)`
*   `KeyError: 'cognitive_state'` (ocorrido em `tinytroupe/agent/tiny_person.py`, linha 448, dentro da função `aux_act_once`).
*   Ocasionalmente, `Error occurred while extracting JSON: Invalid \escape: line 1 column XXX (char YYY)`. 
*   Em alguns casos, a `Extraction raw result message` mostrava `{'role': 'assistant', 'content': '```json\nnull\n```'}` ou `{'role': 'assistant', 'content': '```json\n{}\n```'}`, seguido por `Error occurred while extracting JSON: Expecting value: line 1 column 1 (char 0)`.

## Análise da Causa Raiz

A análise do problema revelou que o modelo Gemini 2.0, embora estivesse gerando JSON válido, frequentemente incluía texto adicional antes ou depois do bloco JSON, ou até mesmo sequências de escape inválidas dentro do JSON. A função `extract_json` em `tinytroupe/utils/json.py` não era robusta o suficiente para lidar com essas variações.

O `KeyError: 'cognitive_state'` era um sintoma da falha na análise do JSON. Se o JSON não fosse extraído corretamente, o dicionário `content` estaria vazio ou malformado, levando à ausência da chave `cognitive_state` esperada pela lógica do agente.

## Tentativas de Correção e Reflexões

### Tentativa 1: Lidar com "Extra data" (Primeira Iteração)

*   **Observação:** O erro "Extra data" sugeria que a regex `re.search(r'\{.*\}', text, re.DOTALL)` era muito "gananciosa", capturando texto além do JSON.
*   **Ação:** Modificado `extract_json` para usar `json.JSONDecoder().raw_decode()` a partir do primeiro `{` encontrado, permitindo que o `raw_decode` lidasse com o "extra data" no final.
*   **Resultado:** Reduziu a frequência de "Extra data", mas introduziu ou revelou o erro "Invalid \escape".

### Tentativa 2: Corrigir "Invalid \escape"

*   **Observação:** O erro "Invalid \escape" indicava que o JSON gerado pelo modelo continha barras invertidas (`\`) que não eram parte de sequências de escape JSON válidas (e.g., `\n`, `\t`, `\"`).
*   **Ação:** Adicionada uma etapa de pré-processamento na função auxiliar `_clean_and_load_json` (introduzida para encapsular a lógica de limpeza e carregamento) para substituir barras invertidas soltas por barras invertidas duplas (`\\`) usando `re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', json_string)`.
*   **Resultado:** O erro "Invalid \escape" foi resolvido. No entanto, "Extra data" e `KeyError: 'cognitive_state'` ainda persistiam, e ocasionalmente o JSON extraído era `null` ou `{}`.

### Tentativa 3: Robustez na Extração e Priorização (Primeira Abordagem)

*   **Observação:** A função `extract_json` precisava ser mais inteligente para encontrar o JSON correto, especialmente quando o modelo retornava múltiplos objetos JSON ou texto confuso. A priorização de `cognitive_state` foi considerada crucial.
*   **Ação:** Refatorada `extract_json` para:
    *   Primeiro, tentar extrair de blocos de código Markdown (```json ... ```) com uma regex mais flexível.
    *   Se falhasse ou não contivesse `cognitive_state`, usar `re.findall(r'\{.*?\}', text, re.DOTALL)` para encontrar todos os candidatos a JSON.
    *   Iterar sobre esses candidatos, tentando decodificar cada um.
    *   Priorizar: Se um JSON válido fosse encontrado e contivesse `cognitive_state`, retorná-lo imediatamente.
    *   Fallback: Se nenhum JSON com `cognitive_state` fosse encontrado, mas um JSON válido (sem `cognitive_state`) fosse encontrado, armazená-lo como `fallback_json` e retorná-lo no final.
    *   Lidar com `null` explicitamente.
*   **Resultado:** Os erros "Extra data" e `KeyError: 'cognitive_state'` ainda apareciam. A `Extraction raw result message` ocasionalmente mostrava JSONs válidos (como `{"ad_copy": "..."}`) que não continham `cognitive_state`, mas eram importantes para outras partes do código. Isso levou à reflexão de que a priorização de `cognitive_state` dentro de `extract_json` poderia estar causando a perda de informações relevantes em outros contextos.

### Tentativa 4: Extração Genérica de JSON (Removendo Priorização de cognitive_state)

*   **Observação:** A reflexão da Tentativa 3 sugeriu que `extract_json` deveria ser uma utilidade genérica, retornando o primeiro JSON válido encontrado, e que a lógica de validação de chaves específicas (`cognitive_state`, `ad_copy`) deveria ser movida para as funções que chamam `extract_json`.
*   **Ação:** Modificada `extract_json` para remover toda a priorização de `cognitive_state`. A função simplesmente retornaria o primeiro dicionário JSON válido que encontrasse, seja de um bloco Markdown ou de uma busca geral.
*   **Resultado:** Os erros "Extra data" e `KeyError: 'cognitive_state'` voltaram a ser proeminentes. Isso confirmou que a função `aux_act_once` em `tinytroupe/agent/tiny_person.py` realmente depende da presença de `cognitive_state` no JSON retornado por `extract_json`. A remoção da priorização fez com que JSONs sem `cognitive_state` fossem retornados, causando o `KeyError`.

### Tentativa 5: Re-reintrodução da Priorização de `cognitive_state` de forma mais inteligente (Estado Atual)

*   **Observação:** A lição aprendida é que a função `extract_json` *precisa* ser inteligente sobre o contexto em que é chamada. No contexto de `aux_act_once`, a chave `cognitive_state` é essencial.
*   **Ação:** A função `extract_json` foi atualizada para:
    1.  Manter `_clean_and_load_json` para lidar com sequências de escape e valores `null`.
    2.  Priorizar a extração de blocos Markdown.
    3.  Usar `re.findall` para encontrar *todos* os candidatos a JSON.
    4.  **Lógica de Priorização e Fallback Aprimorada:**
        *   Se um JSON válido for encontrado *e* contiver `cognitive_state`, ele será retornado imediatamente.
        *   Se um JSON válido for encontrado, mas *não* contiver `cognitive_state`, ele será armazenado como um `fallback_json`.
        *   Se, após verificar todos os candidatos, nenhum JSON com `cognitive_state` for encontrado, mas um `fallback_json` existir, ele será retornado.
        *   Se nenhum JSON válido for encontrado, um `ValueError` será levantado.
*   **Resultado:** Os erros `Extra data` e `KeyError: 'cognitive_state'` ainda persistem. A `Extraction raw result message` mostra `{'role': 'assistant', 'content': '```json\n{"ad_copy": null}\n```'}`. Isso indica que, embora a função `extract_json` esteja tentando priorizar `cognitive_state`, o modelo não está gerando consistentemente JSON com essa chave no contexto esperado, ou o JSON gerado é tão malformado que mesmo a lógica robusta não consegue extraí-lo corretamente.

### Tentativa 6: Robustez de `aux_act_once` para `cognitive_state` e `action` (Estado Atual)

*   **Observação:** O `KeyError: 'cognitive_state'` em `aux_act_once` é o ponto de falha. Embora o prompt em `tiny_person.mustache` peça explicitamente por `cognitive_state`, o modelo não está garantindo sua presença em todas as respostas, ou a `extract_json` ainda não está conseguindo extraí-lo em todos os cenários.
*   **Ação:** Modificada `aux_act_once` em `tinytroupe/agent/tiny_person.py` para:
    *   Usar `content.get("cognitive_state")` para acessar a chave, fornecendo um valor padrão se ausente.
    *   Usar `content.get("action")` para acessar a chave, levantando um `ValueError` se `action` estiver ausente (pois é uma chave crítica).
*   **Resultado:** Os erros `Extra data` e `KeyError: 'cognitive_state'` foram mitigados dentro de `aux_act_once`. No entanto, o problema de `ad_copy: null` na `Extraction raw result message` persiste, indicando que o problema agora está na geração de conteúdo pelo modelo para o `ResultsExtractor`.

### Tentativa 7: Aprimoramento do Prompt de Extração (`interaction_results_extractor.mustache`) (Estado Atual)

*   **Observação:** O problema de `ad_copy: null` sugere que o prompt para o `ResultsExtractor` não está sendo interpretado corretamente pelo modelo, ou que o modelo não está gerando o conteúdo esperado para `ad_copy`.
*   **Ação:** Modificado `tinytroupe/extraction/prompts/interaction_results_extractor.mustache` para:
    *   Fortalecer a instrução para `fields_hints`: Em vez de "Restrição adicional", torná-la uma instrução direta para "Extrair as seguintes informações para o campo `{{0}}`: {{1}}".
    *   Adicionar uma nota sobre a geração de conteúdo se não for encontrado explicitamente: Incluir uma instrução geral de que, se a informação não estiver explicitamente presente, o LLM deve *inferir* ou *resumir* com base no contexto, em vez de apenas retornar `null`.
    *   Remover o exemplo `{"choice": null}`.
*   **Resultado:** O `ad_copy` agora está sendo preenchido com conteúdo. No entanto, o `ValueError: [PERSON_1] 'action' not found in LLM response.` e `Error occurred while extracting JSON: Extra data: line 1 column XXX (char YYY)` reapareceram. Isso indica que, embora o prompt de extração esteja funcionando melhor, a saída do LLM para as ações do agente ainda é inconsistente ou malformada, levando a falhas na extração de `action` e `cognitive_state` em `aux_act_once`.

### Tentativa 8: Aprimoramento de `extract_json` com Priorização Multi-nível (Estado Atual)

*   **Observação:** O problema parece ter voltado para a robustez da função `extract_json` e a forma como ela lida com a saída do LLM para as ações do agente. Embora `aux_act_once` tenha sido mitigada para `cognitive_state`, a ausência de `action` ainda causa um erro crítico.
*   **Ação:** Implementada uma lógica de priorização multi-nível em `extract_json`:
    *   Prioridade 1: JSON com `action` E `cognitive_state`.
    *   Prioridade 2: JSON com apenas `action`.
    *   Prioridade 3: JSON com apenas `cognitive_state`.
    *   Prioridade 4: Qualquer JSON válido (dicionário).
*   **Resultado:** Os erros `Extra data` e `ValueError: [PERSON_1] 'action' not found in LLM response.` ainda persistem. Isso sugere que a lógica de extração de JSON, mesmo com priorização, ainda não está conseguindo isolar o JSON correto da saída do LLM, ou que a saída do LLM é tão inconsistente que a extração é inerentemente difícil.

### Tentativa 9: Implementação de Extração de JSON Baseada em Pilha (Stack-based JSON Extraction) (Estado Atual)

*   **Observação:** O problema parece estar na dificuldade de `extract_json` em lidar com a complexidade da saída do LLM, que pode incluir texto extra e JSONs incompletos ou malformados. A abordagem atual de `re.findall` e `json.loads` pode não ser suficiente para todos os cenários.
*   **Ação:** Implementada uma lógica de extração de JSON baseada em pilha em `extract_json` para encontrar objetos JSON balanceados. A lógica de priorização multi-nível foi mantida.
*   **Resultado:** Os erros `Extra data` e `ValueError: [PERSON_1] 'action' not found in LLM response.` ainda persistem. Isso indica que, mesmo com uma extração mais robusta, a saída do LLM ainda é problemática, ou que a lógica de priorização precisa ser ainda mais refinada para lidar com a ordem em que os JSONs são encontrados.

## Novos Erros Observados (Após Tentativa 9)

Os erros mais recentes são:

*   `Error occurred while extracting JSON: Extra data: line 1 column XXX (char YYY)`
*   `ValueError: [PERSON_1] 'action' not found in LLM response.`

## Próximos Passos

O problema parece estar na dificuldade de `extract_json` em lidar com a complexidade da saída do LLM, que pode incluir texto extra e JSONs incompletos ou malformados. A abordagem atual de `re.findall` e `json.loads` pode não ser suficiente para todos os cenários.

**Ações Propostas:**

1.  **Revisar a Lógica de Priorização em `extract_json`:** A lógica de priorização atual pode estar falhando em cenários onde o JSON com `action` e `cognitive_state` não é o primeiro JSON balanceado encontrado. Pode ser necessário garantir que a busca por JSONs com `action` e `cognitive_state` seja feita em *todos* os JSONs balanceados encontrados, e não apenas no primeiro.
2.  **Adicionar mais exemplos ao Prompt do LLM para Geração de Ações:** Se o LLM ainda está gerando JSONs inconsistentes, adicionar mais exemplos de saída JSON esperada no prompt de `tiny_person.mustache` pode ajudar a guiar o modelo.
3.  **Considerar um Parser de JSON Mais Tolerante a Erros:** Se o problema persistir, pode ser necessário usar uma biblioteca de parsing de JSON que seja mais tolerante a erros e que possa tentar corrigir JSONs malformados.

Vou começar revisando a lógica de priorização em `extract_json` em `tinytroupe/utils/json.py` para garantir que ela esteja verificando todos os JSONs balanceados encontrados.

```
```
```
```