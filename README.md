# Sistema de Agendamento de Laboratórios

Sistema de agendamento de aulas em laboratórios utilizando o algoritmo GRASP (Greedy Randomized Adaptive Search Procedure) para otimização de alocação de recursos.

## Descrição

O sistema permite agendar aulas em 4 laboratórios diferentes, considerando:
- **Laboratórios**: Lab1 (54 alunos), Lab2 (54 alunos), Lab3 (24 alunos), Lab4 (24 alunos)
- **Dias**: Segunda a Sexta-feira
- **Horários**: 4 turnos (08:00-10:00, 10:00-12:00, 13:30-15:30, 15:30-17:30)

## Pré-requisitos

- Python 3.6 ou superior
- Biblioteca `reportlab` para geração de PDFs

## Instalação

1. Clone ou baixe os arquivos do projeto
2. Certifique-se de que o Python está instalado:
```bash
python --version
```
3. Instale a biblioteca reportlab:
```bash
pip install reportlab
```

## Como Executar

Execute o programa com o seguinte comando:

```bash
python grasp.py
```

## Arquivos de Exemplo

O sistema inclui arquivos CSV de exemplo para testes:

| Arquivo | Descrição |
|---------|-----------|
| `agenda.csv` | Agenda real com dados de professores |
| `agenda_saturada.csv` | Cenário com mais aulas do que slots disponíveis (120 aulas para 80 slots) |
| `agenda_exata.csv` | Cenário com solução exata (80 aulas para 80 slots) |

## Funcionalidades

O sistema apresenta um menu interativo com as seguintes opções:

### 1. Agendar aula (manual)
Permite agendar manualmente uma aula informando:
- Nome da disciplina
- Professor
- Quantidade de alunos
- Dia da semana
- Horário
- Laboratório

O sistema verifica automaticamente:
- Conflitos de horário
- Capacidade do laboratório

### 2. Ver agenda manual completa
Exibe todas as aulas agendadas manualmente, organizadas por:
- Laboratório
- Dia da semana
- Horário

### 3. Ver disponibilidade (manual)
Mostra os horários livres em cada laboratório para agendamento manual.

### 4. Rodar GRASP (automático) com dados do CSV
Executa o algoritmo GRASP para otimizar automaticamente a alocação das aulas lidas de um arquivo CSV. O sistema:
- Solicita o nome do arquivo CSV
- Carrega as aulas do arquivo
- Aplica o algoritmo GRASP
- Exibe as aulas não alocadas (se houver)
- Gera um PDF com a agenda otimizada

### 5. Gerar PDF da agenda manual
Gera um arquivo PDF formatado com a agenda manual atual.

### 6. Gerar PDF da última agenda GRASP
Gera novamente o PDF da última execução do GRASP.

### 0. Sair
Encerra o sistema.

## Geração de PDFs

O sistema gera PDFs formatados no estilo calendário, contendo:
- Tabelas por laboratório com dias da semana nas colunas
- Informações de disciplina, professor e número de alunos
- **Seção de aulas não alocadas** (quando aplicável): lista as aulas que não puderam ser agendadas devido a conflitos ou capacidade insuficiente

O nome do PDF segue o padrão: `{nome_do_csv}_grasp.pdf`
- Exemplo: `agenda_saturada.csv` → `agenda_saturada_grasp.pdf`

## Formato do Arquivo CSV

O arquivo CSV deve seguir o formato:

```csv
Nome do Professor,Segunda,Terça,Quarta,Quinta,Sexta,,,
8-10h,Disciplina A (30 alunos),,,Disciplina B (25 alunos),,,,
10-12h,,,Disciplina C,,,,,,
...
```

**Observações:**
- O número de alunos pode ser especificado no formato `(XX alunos)`
- Se não especificado, assume-se 30 alunos por padrão
- Linhas de horário: `8-10h`, `10-12h`, `13:30 - 15:30`, `15:30 - 17:30`

## Exemplo de Uso

1. Execute o programa:
```bash
python grasp.py
```

2. Escolha a opção 4 para executar o GRASP:
```
Escolha: 4
Digite o nome do arquivo CSV (ex: agenda.csv): agenda_saturada
```

3. O sistema irá:
   - Carregar as aulas do CSV
   - Executar o algoritmo GRASP
   - Exibir aulas não alocadas (se houver)
   - Mostrar a agenda otimizada
   - Gerar o PDF automaticamente

## Algoritmo GRASP

O sistema implementa o algoritmo GRASP com:
- **Fase Construtiva**: Constrói soluções gulosas randomizadas usando RCL (Restricted Candidate List)
- **Busca Local**: Refinamento através de movimentação e troca de aulas entre salas
- **Parâmetro ALPHA**: 0.3 (controla o nível de aleatoriedade)
- **Iterações**: 30 iterações por execução

### Função Objetivo
O algoritmo maximiza um score baseado em:
- Prioridade dos laboratórios (Lab1 e Lab2 têm maior prioridade)
- Minimização de capacidade ociosa (melhor encaixe)

### Aulas Não Alocadas
Quando uma aula não pode ser alocada (todos os laboratórios ocupados ou sem capacidade suficiente), ela é registrada e exibida:
- No console durante a execução
- Em uma seção especial no PDF gerado

## Estrutura do Código

- `Sala`: Classe que representa um laboratório
- `Aula`: Classe que representa uma aula a ser agendada
- `SlotAgenda`: Representa um slot de tempo em um laboratório
- `carregar_aulas_do_csv()`: Lê aulas de um arquivo CSV
- `construir_solucao_grasp()`: Fase construtiva do GRASP (retorna agenda e aulas não alocadas)
- `buscar_melhora_local()`: Fase de busca local
- `grasp()`: Função principal que executa múltiplas iterações
- `gerar_pdf_agenda()`: Gera PDF formatado da agenda

## Restrições

O sistema respeita as seguintes restrições:
- Uma sala não pode ter duas aulas no mesmo horário
- O número de alunos não pode exceder a capacidade da sala
- Cada aula já possui dia e horário pré-definidos no CSV

## Autor

Sistema desenvolvido para Projeto e Análise de Algoritmos (PAA)
