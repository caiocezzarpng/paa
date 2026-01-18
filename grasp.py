import random
import os
import csv
import re
from datetime import datetime

# Para gerar PDF (instalar com: pip install reportlab)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

# =========================
# Modelagem das entidades
# =========================

class Sala:
    def __init__(self, nome, capacidade, prioridade=0):
        self.nome = nome
        self.capacidade = capacidade
        # prioridade > 0 favorece uso, < 0 desfavorece (mas NÃO é penalização de violação)
        self.prioridade = prioridade  

class Aula:
    def __init__(self, disciplina="", professor="", alunos=0, dia=None, horario=None):
        self.disciplina = disciplina
        self.professor = professor
        self.alunos = alunos
        # Para o GRASP, consideramos aulas com dia/horário já definidos
        self.dia = dia
        self.horario = horario

class SlotAgenda:
    def __init__(self):
        self.ocupado = 0
        self.aula = None

# =========================
# Constantes e dados
# =========================

MAX_SALAS = 4
MAX_HORARIOS = 4
MAX_DIAS = 5
ALPHA = 0.3  

salas = [
    Sala("Lab1", 54, prioridade=2),  # mais desejado
    Sala("Lab2", 54, prioridade=2),  # mais desejado
    Sala("Lab3", 24, prioridade=-1), # menos desejado ]
    Sala("Lab4", 24, prioridade=1),  # intermediário
]

dias_semana = [
    "Segunda-feira",
    "Terça-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira"
]

horarios_texto = [
    "08:00 às 10:00",
    "10:00 às 12:00",
    "13:30 às 15:30",
    "15:30 às 17:30",
]


def criar_agenda_vazia():
    return [[[SlotAgenda() for _ in range(MAX_HORARIOS)]
             for _ in range(MAX_DIAS)]
             for _ in range(MAX_SALAS)]

# agenda global usada no modo manual (mantida por compatibilidade)
agenda_manual = criar_agenda_vazia()


# =========================
# Funções básicas (restrições)
# =========================

def pode_agendar(sala_idx, dia, horario, alunos, agenda):
    # conflito de sala
    if agenda[sala_idx][dia][horario].ocupado:
        return False
    # capacidade
    if salas[sala_idx].capacidade < alunos:
        return False
    return True


# =========================
# Modo manual (igual ao original, só adaptado)
# =========================

def inicializar_agenda(agenda):
    for s in range(MAX_SALAS):
        for d in range(MAX_DIAS):
            for h in range(MAX_HORARIOS):
                agenda[s][d][h].ocupado = 0
                agenda[s][d][h].aula = None

def mostrar_dias():
    print("\nDias da semana:")
    for i, dia in enumerate(dias_semana):
        print(f"{i} - {dia}")

def mostrar_horarios():
    print("\nHorários:")
    for i, texto in enumerate(horarios_texto):
        print(f"{i} - {texto}")

def mostrar_salas():
    print("\nLaboratórios:")
    for i, s in enumerate(salas):
        print(f"{i} - {s.nome} (capacidade {s.capacidade})")

def agendar_aula_manual():
    disciplina = input("\nDisciplina: ")
    professor = input("Professor: ")
    try:
        alunos = int(input("Quantidade de alunos: "))
        mostrar_dias()
        dia = int(input("Escolha o dia: "))
        mostrar_horarios()
        horario = int(input("Escolha o horário: "))
        mostrar_salas()
        sala = int(input("Escolha o laboratório: "))

        if (0 <= sala < MAX_SALAS and
            0 <= dia < MAX_DIAS and
            0 <= horario < MAX_HORARIOS):

            if pode_agendar(sala, dia, horario, alunos, agenda_manual):
                slot = agenda_manual[sala][dia][horario]
                slot.ocupado = 1
                slot.aula = Aula(disciplina, professor, alunos, dia, horario)
                print(" Aula agendada manualmente com sucesso!")
            else:
                print("Erro: conflito ou capacidade insuficiente.")
        else:
            print("Erro: dados inválidos.")
    except ValueError:
        print("Erro: entrada inválida.")


def mostrar_agenda(agenda):
    print("\n===== AGENDA COMPLETA =====")
    for s_idx in range(MAX_SALAS):
        print(f"\n{salas[s_idx].nome}")
        for d in range(MAX_DIAS):
            print(f" {dias_semana[d]}:")
            for h in range(MAX_HORARIOS):
                slot = agenda[s_idx][d][h]
                if slot.ocupado and slot.aula is not None:
                    a = slot.aula
                    print(f"  {horarios_texto[h]} -> {a.disciplina} ({a.professor}, {a.alunos} alunos)")
                else:
                    print(f"  {horarios_texto[h]} -> Livre")


def ver_disponibilidade(agenda):
    print("\n******* DISPONIBILIDADE *******")
    for s_idx in range(MAX_SALAS):
        print(f"\n{salas[s_idx].nome}")
        for d in range(MAX_DIAS):
            livres_no_dia = []
            for h in range(MAX_HORARIOS):
                if agenda[s_idx][d][h].ocupado == 0:
                    livres_no_dia.append(horarios_texto[h])
            if livres_no_dia:
                print(f" {dias_semana[d]}:")
                for texto in livres_no_dia:
                    print(f"  {texto}")


# =========================
# Geração de PDF (Agenda/Calendário)
# =========================

def gerar_pdf_agenda(agenda, nome_arquivo=None, aulas_nao_alocadas=None):
    """
    Gera um PDF com a agenda de horários no formato de calendário.
    Cada sala terá sua própria tabela com dias da semana nas colunas e horários nas linhas.
    Se houver aulas não alocadas, inclui uma seção adicional listando-as.
    """
    if nome_arquivo is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"agenda_labs_{timestamp}.pdf"
    
    # Configurar documento em modo paisagem para melhor visualização
    doc = SimpleDocTemplate(
        nome_arquivo,
        pagesize=landscape(A4),
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1*cm,
        bottomMargin=1*cm
    )
    
    elementos = []
    styles = getSampleStyleSheet()
    
    # Estilo para título
    titulo_style = ParagraphStyle(
        'TituloAgenda',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,  # centralizado
        spaceAfter=20
    )
    
    # Estilo para nome da sala
    sala_style = ParagraphStyle(
        'NomeSala',
        parent=styles['Heading2'],
        fontSize=12,
        alignment=0,
        spaceAfter=10,
        textColor=colors.darkblue
    )
    
    # Estilo para células
    celula_style = ParagraphStyle(
        'Celula',
        parent=styles['Normal'],
        fontSize=8,
        alignment=1,
        leading=10
    )
    
    # Título principal
    data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M")
    titulo = Paragraph(f"Agenda de Laboratórios - Gerado em {data_geracao}", titulo_style)
    elementos.append(titulo)
    elementos.append(Spacer(1, 0.5*cm))
    
    # Para cada sala, criar uma tabela no estilo calendário
    for s_idx in range(MAX_SALAS):
        sala = salas[s_idx]
        
        # Nome da sala
        nome_sala = Paragraph(f"{sala.nome} (Capacidade: {sala.capacidade} alunos)", sala_style)
        elementos.append(nome_sala)
        
        # Cabeçalho da tabela: Horário + dias da semana
        cabecalho = ["Horário"] + [dia[:3] for dia in dias_semana]  # Abreviar dias
        
        # Dados da tabela
        dados_tabela = [cabecalho]
        
        for h in range(MAX_HORARIOS):
            linha = [horarios_texto[h]]
            
            for d in range(MAX_DIAS):
                slot = agenda[s_idx][d][h]
                if slot.ocupado and slot.aula is not None:
                    aula = slot.aula
                    # Formatar conteúdo da célula
                    conteudo = f"<b>{aula.disciplina}</b><br/>{aula.professor}<br/>({aula.alunos} alunos)"
                    celula = Paragraph(conteudo, celula_style)
                    linha.append(celula)
                else:
                    linha.append(Paragraph("<font color='gray'>Livre</font>", celula_style))
            
            dados_tabela.append(linha)
        
        # Criar tabela
        larguras_colunas = [3.5*cm] + [4.5*cm] * MAX_DIAS
        tabela = Table(dados_tabela, colWidths=larguras_colunas)
        
        # Estilizar tabela
        estilo_tabela = TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            
            # Coluna de horários
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#D6DCE4')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (0, -1), 8),
            
            # Corpo da tabela
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            
            # Altura das linhas
            ('ROWHEIGHT', (0, 1), (-1, -1), 1.5*cm),
            
            # Alternar cores das linhas
            ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
        ])
        
        tabela.setStyle(estilo_tabela)
        elementos.append(tabela)
        elementos.append(Spacer(1, 1*cm))
    
    # Seção de aulas não alocadas (se houver)
    if aulas_nao_alocadas:
        elementos.append(Spacer(1, 0.5*cm))
        
        # Estilo para título da seção de não alocadas
        titulo_nao_alocadas_style = ParagraphStyle(
            'TituloNaoAlocadas',
            parent=styles['Heading2'],
            fontSize=14,
            alignment=0,
            spaceAfter=10,
            textColor=colors.HexColor('#C00000')
        )
        
        titulo_nao_alocadas = Paragraph("⚠ Aulas Não Alocadas", titulo_nao_alocadas_style)
        elementos.append(titulo_nao_alocadas)
        
        # Texto explicativo
        texto_explicativo = Paragraph(
            "As seguintes aulas não puderam ser alocadas devido a conflitos "
            "de horário ou capacidade insuficiente dos laboratórios:",
            styles['Normal']
        )
        elementos.append(texto_explicativo)
        elementos.append(Spacer(1, 0.3*cm))
        
        # Cabeçalho da tabela de não alocadas
        cabecalho_nao_alocadas = ["Disciplina", "Professor", "Dia", "Horário", "Alunos"]
        dados_nao_alocadas = [cabecalho_nao_alocadas]
        
        for aula in aulas_nao_alocadas:
            dia_nome = dias_semana[aula.dia] if aula.dia is not None else "N/A"
            horario_nome = horarios_texto[aula.horario] if aula.horario is not None else "N/A"
            linha = [
                Paragraph(aula.disciplina[:40] + "..." if len(aula.disciplina) > 40 else aula.disciplina, celula_style),
                aula.professor,
                dia_nome[:3],
                horario_nome,
                str(aula.alunos)
            ]
            dados_nao_alocadas.append(linha)
        
        # Linha de total
        dados_nao_alocadas.append([
            Paragraph(f"<b>Total: {len(aulas_nao_alocadas)} aula(s) não alocada(s)</b>", celula_style),
            "", "", "", ""
        ])
        
        tabela_nao_alocadas = Table(
            dados_nao_alocadas,
            colWidths=[7*cm, 4*cm, 2.5*cm, 4*cm, 2*cm]
        )
        
        estilo_nao_alocadas = TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C00000')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # Bordas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#C00000')),
            # Última linha (total)
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFE0E0')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('SPAN', (0, -1), (-1, -1)),
        ])
        
        tabela_nao_alocadas.setStyle(estilo_nao_alocadas)
        elementos.append(tabela_nao_alocadas)
    
    # Gerar PDF
    try:
        doc.build(elementos)
        caminho_completo = os.path.abspath(nome_arquivo)
        print(f"\n✓ PDF gerado com sucesso!")
        print(f"  Arquivo: {caminho_completo}")
        return caminho_completo
    except Exception as e:
        print(f"\n✗ Erro ao gerar PDF: {e}")
        return None


# =========================
# GRASP: construção + busca local
# =========================

def avaliar_agenda(agenda):
    """
    Mede a qualidade da agenda com critérios simples:
      - prefere salas de maior prioridade
      - prefere menor sobra de capacidade (encaixe melhor)
    Não há penalização de violação: violações simplesmente não são aceitas.
    """
    score = 0
    for s_idx in range(MAX_SALAS):
        sala = salas[s_idx]
        for d in range(MAX_DIAS):
            for h in range(MAX_HORARIOS):
                slot = agenda[s_idx][d][h]
                if slot.ocupado and slot.aula is not None:
                    alunos = slot.aula.alunos
                    sobra = sala.capacidade - alunos
                    score += sala.prioridade
                    score -= sobra * 0.1
    return score


def construir_solucao_grasp(aulas):
    """
    Fase construtiva:
      - percorre a lista de aulas
      - gera todos os slots viáveis (respeitando restrições duras)
      - monta RCL com base em custo (sobra, prioridade de sala)
      - escolhe aleatório da RCL
    Retorna: tupla (agenda, aulas_nao_alocadas)
    """
    agenda = criar_agenda_vazia()
    aulas_nao_alocadas = []  # Lista para rastrear aulas não alocadas

    for aula in aulas:
        candidatos = []
        dia = aula.dia
        horario = aula.horario

        for s_idx in range(MAX_SALAS):
            if pode_agendar(s_idx, dia, horario, aula.alunos, agenda):
                sobra = salas[s_idx].capacidade - aula.alunos
                # custo menor = melhor (sobra pequena e sala prioritária)
                custo = (sobra, -salas[s_idx].prioridade)
                candidatos.append((custo, s_idx, dia, horario))

        if not candidatos:
            # Não conseguiu alocar essa aula - adicionar à lista de não alocadas
            aulas_nao_alocadas.append(aula)
            continue

        candidatos.sort(key=lambda x: x[0])
        limite = max(1, int(len(candidatos) * ALPHA))
        rcl = candidatos[:limite]
        _, sala_escolhida, d, h = random.choice(rcl)

        slot = agenda[sala_escolhida][d][h]
        slot.ocupado = 1
        slot.aula = aula

    return agenda, aulas_nao_alocadas


def clonar_agenda(agenda):
    nova = criar_agenda_vazia()
    for s in range(MAX_SALAS):
        for d in range(MAX_DIAS):
            for h in range(MAX_HORARIOS):
                if agenda[s][d][h].ocupado:
                    nova[s][d][h].ocupado = 1
                    nova[s][d][h].aula = agenda[s][d][h].aula
    return nova


def buscar_melhora_local(agenda, max_tentativas=100):
    """
    Busca local simples:
      - escolhe aleatoriamente um dia/horário
      - tenta trocar aulas entre salas ou mover para sala livre
      - aceita apenas movimentos que melhoram o score e respeitam as restrições
    """
    melhor_agenda = clonar_agenda(agenda)
    melhor_score = avaliar_agenda(melhor_agenda)

    for _ in range(max_tentativas):
        d = random.randrange(MAX_DIAS)
        h = random.randrange(MAX_HORARIOS)

        ocupadas = [s for s in range(MAX_SALAS) if melhor_agenda[s][d][h].ocupado]
        livres = [s for s in range(MAX_SALAS) if not melhor_agenda[s][d][h].ocupado]

        # movimento 1: troca entre duas salas ocupadas
        if len(ocupadas) >= 2:
            s1, s2 = random.sample(ocupadas, 2)
            nova = clonar_agenda(melhor_agenda)

            aula1 = nova[s1][d][h].aula
            aula2 = nova[s2][d][h].aula

            if (salas[s1].capacidade >= aula2.alunos and
                salas[s2].capacidade >= aula1.alunos):

                nova[s1][d][h].aula, nova[s2][d][h].aula = aula2, aula1

                score = avaliar_agenda(nova)
                if score > melhor_score:
                    melhor_agenda = nova
                    melhor_score = score
                    continue

        # movimento 2: mover aula de sala ocupada para sala livre
        if ocupadas and livres:
            s_ocup = random.choice(ocupadas)
            s_livre = random.choice(livres)
            nova = clonar_agenda(melhor_agenda)

            aula = nova[s_ocup][d][h].aula
            if salas[s_livre].capacidade >= aula.alunos:
                nova[s_livre][d][h].ocupado = 1
                nova[s_livre][d][h].aula = aula

                nova[s_ocup][d][h].ocupado = 0
                nova[s_ocup][d][h].aula = None

                score = avaliar_agenda(nova)
                if score > melhor_score:
                    melhor_agenda = nova
                    melhor_score = score
                    continue

    return melhor_agenda, melhor_score


def grasp(aulas, iteracoes=20):
    melhor_global = None
    melhor_score_global = float("-inf")
    melhor_aulas_nao_alocadas = []  # Rastrear aulas não alocadas da melhor solução

    for _ in range(iteracoes):
        agenda_inicial, aulas_nao_alocadas = construir_solucao_grasp(aulas)
        agenda_refinada, score = buscar_melhora_local(agenda_inicial)

        if score > melhor_score_global:
            melhor_score_global = score
            melhor_global = agenda_refinada
            melhor_aulas_nao_alocadas = aulas_nao_alocadas

    return melhor_global, melhor_score_global, melhor_aulas_nao_alocadas


# =========================
# Leitura do CSV e extração de aulas
# =========================

def mapear_horario(horario_texto):
    """
    Mapeia o texto do horário do CSV para o índice correspondente.
    """
    horario_texto = horario_texto.strip().lower()
    
    if '8' in horario_texto and '10' in horario_texto:
        return 0  # 08:00 às 10:00
    elif '10' in horario_texto and '12' in horario_texto:
        return 1  # 10:00 às 12:00
    elif '13' in horario_texto and '15' in horario_texto:
        return 2  # 13:30 às 15:30
    elif '15' in horario_texto and '17' in horario_texto:
        return 3  # 15:30 às 17:30
    
    return None


def mapear_dia(coluna_idx):
    """
    Mapeia o índice da coluna para o dia da semana.
    Coluna 1 = Segunda (0), Coluna 2 = Terça (1), etc.
    """
    if 1 <= coluna_idx <= 5:
        return coluna_idx - 1
    return None


def carregar_aulas_do_csv(caminho_csv="agenda.csv"):
    """
    Lê o arquivo CSV e extrai as aulas (disciplina, professor, dia, horário).
    Retorna uma lista de objetos Aula.
    """
    aulas = []
    professor_atual = None
    
    try:
        with open(caminho_csv, 'r', encoding='utf-8') as arquivo:
            leitor = csv.reader(arquivo)
            linhas = list(leitor)
    except FileNotFoundError:
        print(f"Erro: Arquivo '{caminho_csv}' não encontrado.")
        return []
    except Exception as e:
        print(f"Erro ao ler arquivo CSV: {e}")
        return []
    
    for linha in linhas:
        if len(linha) < 6:
            continue
        
        primeira_celula = linha[0].strip() if linha[0] else ""
        
        # Ignora linhas vazias, de cabeçalho de seção ou almoço
        if not primeira_celula:
            continue
        if 'PROFESSORES' in primeira_celula.upper():
            continue
        if 'Almoço' in primeira_celula:
            continue
        
        # Detecta se é uma linha de professor (nome seguido de dias da semana)
        # Verifica se a segunda célula contém "Segunda"
        if len(linha) > 1 and linha[1] and 'Segunda' in linha[1]:
            professor_atual = primeira_celula.strip()
            # Remove asteriscos e observações do nome
            professor_atual = re.sub(r'\*+.*', '', professor_atual).strip()
            continue
        
        # Detecta se é uma linha de horário
        horario_idx = mapear_horario(primeira_celula)
        
        if horario_idx is not None and professor_atual:
            # Percorre as colunas dos dias (1 a 5)
            for col_idx in range(1, min(6, len(linha))):
                disciplina = linha[col_idx].strip() if linha[col_idx] else ""
                
                # Ignora células vazias, almoço ou apenas espaços
                if not disciplina or disciplina.lower() == 'almoço':
                    continue
                
                dia_idx = mapear_dia(col_idx)
                if dia_idx is None:
                    continue
                
                # Limpa o nome da disciplina (remove quebras de linha, etc.)
                disciplina = ' '.join(disciplina.split())
                
                # Tenta extrair número de alunos se estiver no formato "(XX alunos)"
                # Por padrão, usa 30 alunos se não especificado
                alunos = 30
                match_alunos = re.search(r'\((\d+)\s*alunos?\)', disciplina, re.IGNORECASE)
                if match_alunos:
                    alunos = int(match_alunos.group(1))
                
                # Cria a aula
                aula = Aula(
                    disciplina=disciplina,
                    professor=professor_atual,
                    alunos=alunos,
                    dia=dia_idx,
                    horario=horario_idx
                )
                aulas.append(aula)
    
    print(f"\n✓ Carregadas {len(aulas)} aulas do arquivo CSV.")
    return aulas


def exemplo_aulas():
    # Função mantida para compatibilidade
    return [
        Aula("PAA", "Prof. A", 40, dia=0, horario=0),
        Aula("Cálculo", "Prof. B", 50, dia=0, horario=0),
        Aula("Desenho de Máquinas", "Prof. Pedro", 30, dia=1, horario=2),
    ]


# =========================
# Menu principal
# =========================

# Variável global para armazenar última agenda GRASP gerada
ultima_agenda_grasp = None

def main():
    global ultima_agenda_grasp
    random.seed(42)
    inicializar_agenda(agenda_manual)

    while True:
        print("\n=== SISTEMA DE AGENDAMENTO DE LABS ===")
        print("1 - Agendar aula (manual)")
        print("2 - Ver agenda manual completa")
        print("3 - Ver disponibilidade (manual)")
        print("4 - Rodar GRASP (automático) com dados do CSV")
        print("5 - Gerar PDF da agenda manual")
        print("6 - Gerar PDF da última agenda GRASP")
        print("0 - Sair")

        opcao = input("Escolha: ")

        if opcao == '1':
            agendar_aula_manual()
        elif opcao == '2':
            mostrar_agenda(agenda_manual)
        elif opcao == '3':
            ver_disponibilidade(agenda_manual)
        elif opcao == '4':
            # Solicita o nome do arquivo ao usuário
            nome_arquivo = input("\nDigite o nome do arquivo CSV (ex: agenda.csv): ").strip()
            
            if not nome_arquivo:
                print("\n⚠ Nome do arquivo não pode ser vazio.")
                continue
            
            # Adiciona extensão .csv se não foi informada
            if not nome_arquivo.lower().endswith('.csv'):
                nome_arquivo += '.csv'
            
            # Tenta encontrar o arquivo no diretório do script ou no diretório atual
            caminho_csv = os.path.join(os.path.dirname(__file__), nome_arquivo)
            if not os.path.exists(caminho_csv):
                caminho_csv = nome_arquivo
            
            if not os.path.exists(caminho_csv):
                print(f"\n⚠ Arquivo '{nome_arquivo}' não encontrado.")
                continue
            
            aulas = carregar_aulas_do_csv(caminho_csv)
            
            if not aulas:
                print("\n⚠ Nenhuma aula encontrada no CSV. Verifique o arquivo.")
            else:
                print(f"\nExecutando GRASP com {len(aulas)} aulas...")
                melhor_agenda, score, aulas_nao_alocadas = grasp(aulas, iteracoes=30)
                ultima_agenda_grasp = melhor_agenda
                
                # Mostrar aviso de aulas não alocadas no console
                if aulas_nao_alocadas:
                    print(f"\n⚠ Atenção: {len(aulas_nao_alocadas)} aula(s) não puderam ser alocadas!")
                    for aula in aulas_nao_alocadas:
                        dia_nome = dias_semana[aula.dia] if aula.dia is not None else "N/A"
                        horario_nome = horarios_texto[aula.horario] if aula.horario is not None else "N/A"
                        print(f"   - {aula.disciplina} ({aula.professor}) - {dia_nome}, {horario_nome}")
                
                print(f"\nScore da melhor agenda (GRASP): {score}")
                mostrar_agenda(melhor_agenda)
                
                # Gera PDF automaticamente (incluindo aulas não alocadas)
                # Nome do PDF baseado no nome do arquivo CSV de entrada
                nome_base = os.path.splitext(os.path.basename(nome_arquivo))[0]
                nome_pdf = f"{nome_base}_grasp.pdf"
                print(f"\nGerando PDF da agenda GRASP: {nome_pdf}...")
                gerar_pdf_agenda(melhor_agenda, nome_pdf, aulas_nao_alocadas)
        elif opcao == '5':
            print("\nGerando PDF da agenda manual...")
            gerar_pdf_agenda(agenda_manual, "agenda_manual.pdf")
        elif opcao == '6':
            if ultima_agenda_grasp is None:
                print("\n⚠ Nenhuma agenda GRASP foi gerada ainda. Execute a opção 4 primeiro.")
            else:
                print("\nGerando PDF da agenda GRASP...")
                gerar_pdf_agenda(ultima_agenda_grasp, "agenda_grasp.pdf")
        elif opcao == '0':
            print(" Encerrando o sistema.")
            break
        else:
            print(" Opção inválida.")

if __name__ == "__main__":
    main()
 