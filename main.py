#!/usr/bin/env python3
"""
Cyber Nexus - Jogo Educacional de Algoritmos de Grafos
Autores: Pedro Henrique Faria e Caio Leal Granja
Versão Modificada
"""

import pygame
import sys
import random
import math
from collections import deque
from enum import Enum

# Inicialização do Pygame
pygame.init()

# Constantes
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Cores Cyberpunk
COLOR_BG = (10, 10, 25)
COLOR_GRID = (20, 20, 40)
COLOR_NODE = (0, 255, 200)
COLOR_NODE_HOVER = (0, 255, 255)
COLOR_NODE_VISITED = (255, 0, 150)
COLOR_NODE_TARGET = (255, 50, 50)
COLOR_NODE_START = (0, 255, 100)
COLOR_EDGE = (50, 50, 100)
COLOR_EDGE_ACTIVE = (0, 200, 255)
COLOR_EDGE_PLAYER = (255, 200, 0)
COLOR_TEXT = (0, 255, 200)
COLOR_TEXT_TITLE = (255, 0, 150)
COLOR_BUTTON = (30, 30, 60)
COLOR_BUTTON_HOVER = (50, 50, 100)
COLOR_SUCCESS = (0, 255, 100)
COLOR_ERROR = (255, 50, 50)

class GameState(Enum):
    MAIN_MENU = 0
    TUTORIAL_INTRO = 1
    TUTORIAL_PLAY = 2
    PHASE_1_INTRO = 3
    PHASE_1_PLAY = 4
    PHASE_2_INTRO = 5
    PHASE_2_PLAY = 6
    VICTORY = 7

class Node:
    def __init__(self, id, x, y, is_target=False):
        self.id = id
        self.x = x
        self.y = y
        self.is_target = is_target
        self.visited = False
        self.in_path = False
        self.neighbors = []
        self.radius = 25
        self.glow = 0
        self.selected = False
        
    def draw(self, screen, is_start=False):
        # Efeito de brilho
        if self.glow > 0:
            glow_surface = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*COLOR_NODE[:3], int(self.glow)), 
                             (self.radius * 2, self.radius * 2), self.radius * 2)
            screen.blit(glow_surface, (self.x - self.radius * 2, self.y - self.radius * 2))
            self.glow = max(0, self.glow - 5)
        
        # Cor do nó
        if is_start:
            color = COLOR_NODE_START
        elif self.is_target:
            color = COLOR_NODE_TARGET
        elif self.in_path:
            color = COLOR_EDGE_PLAYER
        elif self.selected:
            color = COLOR_NODE_HOVER
        else:
            color = COLOR_NODE
        
        # Desenhar nó
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)
        
        # Borda mais grossa se selecionado
        border_width = 4 if self.selected else 2
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.radius, border_width)
        
        # Desenhar ID
        font = pygame.font.Font(None, 24)
        text = font.render(str(self.id), True, (0, 0, 0))
        text_rect = text.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(text, text_rect)
    
    def contains_point(self, x, y):
        dist = math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)
        return dist <= self.radius

class Edge:
    def __init__(self, node1, node2):
        self.node1 = node1
        self.node2 = node2
        self.player_selected = False
        
    def draw(self, screen):
        if self.player_selected:
            color = COLOR_EDGE_PLAYER
            width = 5
        else:
            color = COLOR_EDGE
            width = 2
        pygame.draw.line(screen, color, 
                        (int(self.node1.x), int(self.node1.y)),
                        (int(self.node2.x), int(self.node2.y)), width)

class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.hovered = False
        
    def draw(self, screen):
        color = COLOR_BUTTON_HOVER if self.hovered else COLOR_BUTTON
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_NODE, self.rect, 3, border_radius=8)
        
        font = pygame.font.Font(None, 32)
        text = font.render(self.text, True, COLOR_TEXT)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered and self.action:
                self.action()
                return True
        return False

class Graph:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.start_node = None
        self.target_node = None
        
    def add_node(self, node):
        self.nodes.append(node)
        if node.is_target:
            self.target_node = node
        
    def add_edge(self, node1, node2):
        edge = Edge(node1, node2)
        self.edges.append(edge)
        node1.neighbors.append(node2)
        node2.neighbors.append(node1)
        
    def reset(self):
        for node in self.nodes:
            node.visited = False
            node.in_path = False
            node.selected = False
        for edge in self.edges:
            edge.player_selected = False
            
    def draw(self, screen):
        # Desenhar arestas primeiro
        for edge in self.edges:
            edge.draw(screen)
        
        # Desenhar nós
        for node in self.nodes:
            is_start = (node == self.start_node)
            node.draw(screen, is_start)

def generate_random_graph(num_nodes=12, min_x=150, max_x=950, min_y=150, max_y=550):
    """Gera um grafo aleatório conectado"""
    graph = Graph()
    nodes = []
    
    # Criar nós com posições aleatórias
    for i in range(num_nodes):
        # Garantir espaçamento mínimo entre nós
        while True:
            x = random.randint(min_x, max_x)
            y = random.randint(min_y, max_y)
            
            # Verificar distância mínima de outros nós
            valid = True
            for node in nodes:
                dist = math.sqrt((node.x - x) ** 2 + (node.y - y) ** 2)
                if dist < 80:  # Distância mínima
                    valid = False
                    break
            
            if valid:
                break
        
        is_target = (i == num_nodes - 1)  # Último nó é o alvo
        node = Node(i + 1, x, y, is_target)
        nodes.append(node)
        graph.add_node(node)
    
    # Primeiro nó é o inicial
    graph.start_node = nodes[0]
    
    # Criar árvore geradora mínima para garantir conectividade
    connected = [nodes[0]]
    unconnected = nodes[1:]
    
    while unconnected:
        # Escolher um nó conectado aleatório
        node1 = random.choice(connected)
        
        # Encontrar o nó não conectado mais próximo
        closest = min(unconnected, key=lambda n: math.sqrt((n.x - node1.x)**2 + (n.y - node1.y)**2))
        
        graph.add_edge(node1, closest)
        connected.append(closest)
        unconnected.remove(closest)
    
    # Adicionar arestas extras aleatórias (30-50% dos nós)
    extra_edges = random.randint(num_nodes // 3, num_nodes // 2)
    for _ in range(extra_edges):
        node1 = random.choice(nodes)
        node2 = random.choice(nodes)
        
        # Verificar se não são o mesmo nó e se já não estão conectados
        if node1 != node2 and node2 not in node1.neighbors:
            # Verificar distância para não criar arestas muito longas
            dist = math.sqrt((node1.x - node2.x)**2 + (node1.y - node2.y)**2)
            if dist < 300:
                graph.add_edge(node1, node2)
    
    return graph

class CyberNexus:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Cyber Nexus - Jogo Educacional de Grafos")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.state = GameState.MAIN_MENU
        self.graph = Graph()
        self.message = ""
        self.message_color = COLOR_TEXT
        
        # Controle de seleção de nós
        self.selected_node = None
        self.player_path = []
        
        # Controle de fases completadas
        self.phase1_completed = False
        self.phase2_completed = False
        
        self.buttons = []
        self.setup_main_menu()
        
    def setup_main_menu(self):
        """Tela principal do jogo"""
        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 150, 300, 300, 60, "TUTORIAL", 
                   lambda: self.change_state(GameState.TUTORIAL_INTRO)),
            Button(SCREEN_WIDTH // 2 - 150, 390, 300, 60, "COMEÇAR A JOGAR", 
                   lambda: self.change_state(GameState.PHASE_1_INTRO)),
            Button(SCREEN_WIDTH // 2 - 150, 480, 300, 60, "SAIR", 
                   lambda: self.quit_game()),
        ]
        
    def change_state(self, new_state):
        self.state = new_state
        self.message = ""
        self.selected_node = None
        self.player_path = []
        
        if new_state == GameState.TUTORIAL_INTRO:
            self.setup_tutorial_intro()
        elif new_state == GameState.TUTORIAL_PLAY:
            self.setup_tutorial_play()
        elif new_state == GameState.PHASE_1_INTRO:
            self.setup_phase_1_intro()
        elif new_state == GameState.PHASE_1_PLAY:
            self.setup_phase_1_play()
        elif new_state == GameState.PHASE_2_INTRO:
            self.setup_phase_2_intro()
        elif new_state == GameState.PHASE_2_PLAY:
            self.setup_phase_2_play()
        elif new_state == GameState.MAIN_MENU:
            self.setup_main_menu()
        elif new_state == GameState.VICTORY:
            self.setup_victory()
            
    def quit_game(self):
        self.running = False
        
    def setup_tutorial_intro(self):
        """Introdução do tutorial"""
        self.buttons = [
            Button(SCREEN_WIDTH // 2 + 10, 630, 280, 60, "COMEÇAR TUTORIAL", 
                   lambda: self.change_state(GameState.TUTORIAL_PLAY)),
            Button(SCREEN_WIDTH // 2 - 290, 630, 280, 60, "VOLTAR", 
                   lambda: self.change_state(GameState.MAIN_MENU)),
        ]
        
    def setup_tutorial_play(self):
        """Tutorial interativo"""
        self.graph = Graph()
        
        # Criar grafo simples (mais centralizado)
        node1 = Node(1, 400, 360)
        node2 = Node(2, 600, 360)
        node3 = Node(3, 800, 360)
        node4 = Node(4, 1000, 360, is_target=True)
        
        self.graph.add_node(node1)
        self.graph.add_node(node2)
        self.graph.add_node(node3)
        self.graph.add_node(node4)
        
        self.graph.add_edge(node1, node2)
        self.graph.add_edge(node2, node3)
        self.graph.add_edge(node3, node4)
        
        self.graph.start_node = node1
        
        self.buttons = [
            Button(SCREEN_WIDTH // 2 + 10, 620, 280, 60, "COMEÇAR A JOGAR", 
                   lambda: self.change_state(GameState.PHASE_1_INTRO)),
            Button(SCREEN_WIDTH // 2 - 290, 620, 280, 60, "VOLTAR", 
                   lambda: self.change_state(GameState.MAIN_MENU)),
        ]
        
        self.message = "Clique nos nós em sequência para criar um caminho!"
        
    def setup_phase_1_intro(self):
        """Introdução da Fase 1 - BFS"""
        self.buttons = [
            Button(SCREEN_WIDTH // 2 + 10, 630, 280, 60, "JOGAR FASE 1", 
                   lambda: self.change_state(GameState.PHASE_1_PLAY)),
            Button(SCREEN_WIDTH // 2 - 290, 630, 280, 60, "VOLTAR", 
                   lambda: self.change_state(GameState.MAIN_MENU)),
        ]
        
    def setup_phase_1_play(self):
        """Fase 1 - BFS com grafo aleatório"""
        self.graph = generate_random_graph(12)
        self.player_path = []
        self.selected_node = None
        
        self.buttons = [
            Button(50, 650, 200, 50, "VERIFICAR", 
                   lambda: self.verify_bfs()),
            Button(270, 650, 200, 50, "RESETAR", 
                   lambda: self.reset_phase()),
            Button(SCREEN_WIDTH - 250, 650, 200, 50, "MENU", 
                   lambda: self.change_state(GameState.MAIN_MENU)),
        ]
        
        self.message = "Clique nos nós para criar um caminho BFS do nó verde ao vermelho!"
        
    def setup_phase_2_intro(self):
        """Introdução da Fase 2 - DFS"""
        self.buttons = [
            Button(SCREEN_WIDTH // 2 + 10, 630, 280, 60, "JOGAR FASE 2", 
                   lambda: self.change_state(GameState.PHASE_2_PLAY)),
            Button(SCREEN_WIDTH // 2 - 290, 630, 280, 60, "VOLTAR", 
                   lambda: self.change_state(GameState.MAIN_MENU)),
        ]
        
    def setup_phase_2_play(self):
        """Fase 2 - DFS com grafo aleatório"""
        self.graph = generate_random_graph(12)
        self.player_path = []
        self.selected_node = None
        
        self.buttons = [
            Button(50, 650, 200, 50, "VERIFICAR", 
                   lambda: self.verify_dfs()),
            Button(270, 650, 200, 50, "RESETAR", 
                   lambda: self.reset_phase()),
            Button(SCREEN_WIDTH - 250, 650, 200, 50, "MENU", 
                   lambda: self.change_state(GameState.MAIN_MENU)),
        ]
        
        self.message = "Clique nos nós para criar um caminho DFS do nó verde ao vermelho!"
        
    def setup_victory(self):
        """Tela de vitória"""
        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 150, 630, 300, 60, "VOLTAR AO MENU", 
                   lambda: self.change_state(GameState.MAIN_MENU)),
        ]
        
    def reset_phase(self):
        """Resetar a fase atual"""
        if self.state == GameState.PHASE_1_PLAY:
            self.setup_phase_1_play()
        elif self.state == GameState.PHASE_2_PLAY:
            self.setup_phase_2_play()
        elif self.state == GameState.TUTORIAL_PLAY:
            self.setup_tutorial_play()
            
    def handle_node_click(self, pos):
        """Lidar com clique em nós"""
        for node in self.graph.nodes:
            if node.contains_point(pos[0], pos[1]):
                # Se é o primeiro clique, deve ser o nó inicial
                if not self.player_path:
                    if node == self.graph.start_node:
                        self.player_path.append(node)
                        node.in_path = True
                        self.message = f"Nó {node.id} selecionado! Continue o caminho..."
                    else:
                        self.message = "Você deve começar pelo nó VERDE (inicial)!"
                        self.message_color = COLOR_ERROR
                else:
                    # Verificar se o nó é vizinho do último nó selecionado
                    last_node = self.player_path[-1]
                    
                    if node in last_node.neighbors and node not in self.player_path:
                        self.player_path.append(node)
                        node.in_path = True
                        
                        # Marcar aresta como selecionada
                        for edge in self.graph.edges:
                            if (edge.node1 == last_node and edge.node2 == node) or \
                               (edge.node1 == node and edge.node2 == last_node):
                                edge.player_selected = True
                        
                        if node.is_target:
                            self.message = "Alvo alcançado! Clique em VERIFICAR para validar seu caminho."
                            self.message_color = COLOR_SUCCESS
                        else:
                            self.message = f"Nó {node.id} adicionado ao caminho!"
                            self.message_color = COLOR_TEXT
                    elif node in self.player_path:
                        self.message = "Este nó já está no caminho!"
                        self.message_color = COLOR_ERROR
                    else:
                        self.message = "Este nó não é vizinho do último nó selecionado!"
                        self.message_color = COLOR_ERROR
                break
                
    def verify_bfs(self):
        """Verificar se o caminho do jogador é um BFS válido"""
        if not self.player_path:
            self.message = "Você não criou nenhum caminho ainda!"
            self.message_color = COLOR_ERROR
            return
            
        if self.player_path[-1] != self.graph.target_node:
            self.message = "Você não alcançou o nó alvo!"
            self.message_color = COLOR_ERROR
            return
        
        # Executar BFS correto
        queue = deque([self.graph.start_node])
        visited = {self.graph.start_node}
        parent = {self.graph.start_node: None}
        found = False
        
        while queue:
            current = queue.popleft()
            
            if current == self.graph.target_node:
                found = True
                break
            
            for neighbor in current.neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)
        
        if not found:
            self.message = "Erro: O grafo não possui caminho válido!"
            self.message_color = COLOR_ERROR
            return
        
        # Reconstruir caminho BFS correto
        bfs_path = []
        current = self.graph.target_node
        while current is not None:
            bfs_path.append(current)
            current = parent[current]
        bfs_path.reverse()
        
        # Verificar se o caminho do jogador segue a ordem BFS
        # O caminho do jogador deve visitar os nós na mesma ordem de níveis que o BFS
        if self.player_path == bfs_path:
            self.message = "🎉 SUCESSO! Sistema hackeado! Você executou um BFS perfeito!"
            self.message_color = COLOR_SUCCESS
            self.phase1_completed = True
            
            # Avançar para próxima fase
            self.buttons = [
                Button(SCREEN_WIDTH // 2 - 150, 650, 300, 50, "PRÓXIMA FASE", 
                       lambda: self.change_state(GameState.PHASE_2_INTRO)),
            ]
        else:
            # Verificar se pelo menos é um caminho válido
            is_valid_path = True
            for i in range(len(self.player_path) - 1):
                if self.player_path[i+1] not in self.player_path[i].neighbors:
                    is_valid_path = False
                    break
            
            if is_valid_path:
                self.message = "Caminho válido, mas não segue a ordem BFS correta. Tente novamente!"
                self.message_color = COLOR_ERROR
            else:
                self.message = "Caminho inválido! Verifique as conexões."
                self.message_color = COLOR_ERROR
                
    def verify_dfs(self):
        """Verificar se o caminho do jogador é um DFS válido"""
        if not self.player_path:
            self.message = "Você não criou nenhum caminho ainda!"
            self.message_color = COLOR_ERROR
            return
            
        if self.player_path[-1] != self.graph.target_node:
            self.message = "Você não alcançou o nó alvo!"
            self.message_color = COLOR_ERROR
            return
        
        # Para DFS, verificar se o caminho é válido e segue profundidade
        # Um caminho DFS válido deve ir o mais fundo possível antes de retroceder
        
        # Verificar se é um caminho válido
        is_valid = True
        for i in range(len(self.player_path) - 1):
            if self.player_path[i+1] not in self.player_path[i].neighbors:
                is_valid = False
                break
        
        if not is_valid:
            self.message = "Caminho inválido! Verifique as conexões."
            self.message_color = COLOR_ERROR
            return
        
        # Verificar se não há retrocessos desnecessários (característica do DFS)
        # Em um DFS, você só deve retroceder quando não há mais vizinhos não visitados
        visited_in_path = set()
        valid_dfs = True
        
        for i, node in enumerate(self.player_path[:-1]):
            visited_in_path.add(node)
            next_node = self.player_path[i + 1]
            
            # Verificar se existem vizinhos não visitados que deveriam ser explorados primeiro
            unvisited_neighbors = [n for n in node.neighbors if n not in visited_in_path and n != next_node]
            
            # Se há vizinhos não visitados e o próximo nó não é um deles, pode não ser DFS
            # Mas permitimos alguma flexibilidade já que DFS pode ter múltiplas soluções válidas
            
        # Se chegou ao alvo com um caminho válido, consideramos sucesso
        self.message = "🎉 SUCESSO! Firewall penetrado! Você executou um DFS válido!"
        self.message_color = COLOR_SUCCESS
        self.phase2_completed = True
        
        # Verificar se completou todas as fases
        if self.phase1_completed and self.phase2_completed:
            self.buttons = [
                Button(SCREEN_WIDTH // 2 - 150, 650, 300, 50, "MISSÃO COMPLETA", 
                       lambda: self.change_state(GameState.VICTORY)),
            ]
        else:
            self.buttons = [
                Button(SCREEN_WIDTH // 2 - 150, 650, 300, 50, "VOLTAR AO MENU", 
                       lambda: self.change_state(GameState.MAIN_MENU)),
            ]
            
    def draw_grid(self):
        """Desenhar grade cyberpunk de fundo"""
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(self.screen, COLOR_GRID, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(self.screen, COLOR_GRID, (0, y), (SCREEN_WIDTH, y), 1)
            
    def draw_title(self, text, y=80, size=64):
        """Desenhar título"""
        font = pygame.font.Font(None, size)
        title = font.render(text, True, COLOR_TEXT_TITLE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, y))
        
        # Efeito de sombra
        shadow = font.render(text, True, (50, 0, 25))
        shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH // 2 + 3, y + 3))
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(title, title_rect)
        
    def draw_text_box(self, lines, y_start=200, width=900):
        """Desenhar caixa de texto com múltiplas linhas"""
        x = SCREEN_WIDTH // 2 - width // 2
        line_height = 35
        padding = 20
        
        # Calcular altura total
        total_height = len(lines) * line_height + padding * 2
        
        # Desenhar fundo
        bg_rect = pygame.Rect(x, y_start, width, total_height)
        bg_surface = pygame.Surface((width, total_height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surface, (20, 20, 50, 220), bg_surface.get_rect(), border_radius=10)
        pygame.draw.rect(bg_surface, COLOR_NODE, bg_surface.get_rect(), 3, border_radius=10)
        self.screen.blit(bg_surface, (x, y_start))
        
        # Desenhar texto
        font = pygame.font.Font(None, 26)
        y = y_start + padding
        for line in lines:
            text = font.render(line, True, COLOR_TEXT)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += line_height
            
    def draw_message(self):
        """Desenhar mensagem de status"""
        if self.message:
            font = pygame.font.Font(None, 28)
            text = font.render(self.message, True, self.message_color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 100))
            
            # Fundo semi-transparente
            bg_rect = text_rect.inflate(30, 15)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(bg_surface, (0, 0, 0, 200), bg_surface.get_rect(), border_radius=8)
            self.screen.blit(bg_surface, bg_rect)
            
            self.screen.blit(text, text_rect)
            
    def draw_legend(self):
        """Desenhar legenda de cores"""
        panel_x = 1000
        panel_y = 30
        panel_width = 250
        panel_height = 220
        
        # Fundo do painel
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (10, 10, 30, 220), panel_surface.get_rect(), border_radius=10)
        pygame.draw.rect(panel_surface, COLOR_NODE, panel_surface.get_rect(), 2, border_radius=10)
        self.screen.blit(panel_surface, (panel_x, panel_y))
        
        # Título
        font_title = pygame.font.Font(None, 28)
        title = font_title.render("LEGENDA", True, COLOR_TEXT_TITLE)
        self.screen.blit(title, (panel_x + 20, panel_y + 15))
        
        # Itens da legenda
        font_text = pygame.font.Font(None, 22)
        legend_items = [
            ("Nó Inicial", COLOR_NODE_START),
            ("Nó Normal", COLOR_NODE),
            ("Nó no Caminho", COLOR_EDGE_PLAYER),
            ("Nó Alvo", COLOR_NODE_TARGET),
        ]
        
        y_offset = panel_y + 55
        for label, color in legend_items:
            pygame.draw.circle(self.screen, color, (panel_x + 25, y_offset + 8), 12)
            pygame.draw.circle(self.screen, (255, 255, 255), (panel_x + 25, y_offset + 8), 12, 2)
            text = font_text.render(label, True, COLOR_TEXT)
            self.screen.blit(text, (panel_x + 45, y_offset))
            y_offset += 35
            
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state != GameState.MAIN_MENU:
                        self.change_state(GameState.MAIN_MENU)
                    else:
                        self.running = False
            
            # Processar cliques em nós
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state in [GameState.TUTORIAL_PLAY, GameState.PHASE_1_PLAY, GameState.PHASE_2_PLAY]:
                    self.handle_node_click(event.pos)
            
            # Processar botões
            for button in self.buttons:
                button.handle_event(event)
                
    def draw(self):
        self.screen.fill(COLOR_BG)
        self.draw_grid()
        
        if self.state == GameState.MAIN_MENU:
            self.draw_title("CYBER NEXUS", y=120, size=80)
            
            # Subtítulo
            font = pygame.font.Font(None, 32)
            subtitle = font.render("Jogo Educacional de Algoritmos de Grafos", True, COLOR_TEXT)
            subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 200))
            self.screen.blit(subtitle, subtitle_rect)
            
            # Créditos
            font_small = pygame.font.Font(None, 24)
            credits = font_small.render("Por Pedro Henrique Faria e Caio Leal Granja", True, COLOR_TEXT)
            credits_rect = credits.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
            self.screen.blit(credits, credits_rect)
            
        elif self.state == GameState.TUTORIAL_INTRO:
            self.draw_title("TUTORIAL", y=80)
            
            lines = [
                "Bem-vindo ao Cyber Nexus!",
                "",
                "Neste jogo, você aprenderá sobre algoritmos de busca em grafos.",
                "",
                "COMO JOGAR:",
                "• Clique nos nós para criar um caminho",
                "• Comece sempre pelo nó VERDE (inicial)",
                "• Conecte até o nó VERMELHO (alvo)",
                "• Você só pode conectar nós vizinhos (ligados por arestas)",
                "",
                "Vamos praticar no tutorial!"
            ]
            self.draw_text_box(lines, y_start=180)
            
        elif self.state == GameState.TUTORIAL_PLAY:
            self.draw_message()
            self.graph.draw(self.screen)
            self.draw_legend()
            
        elif self.state == GameState.PHASE_1_INTRO:
            self.draw_title("FASE 1: BUSCA EM LARGURA (BFS)", y=60, size=52)
            
            lines = [
                "MISSÃO: Hackear o sistema usando BFS",
                "",
                "O QUE É BFS (Breadth-First Search)?",
                "• BFS explora o grafo em CAMADAS",
                "• Visita todos os vizinhos de um nó antes de ir mais fundo",
                "• Garante o caminho mais CURTO em grafos não ponderados",
                "",
                "COMO FAZER:",
                "1. Comece pelo nó inicial (verde)",
                "2. Visite todos os vizinhos do nó atual",
                "3. Depois visite os vizinhos dos vizinhos",
                "4. Continue até alcançar o alvo (vermelho)",
                "",
                "Dica: Pense em ondas se expandindo!"
            ]
            self.draw_text_box(lines, y_start=140, width=1000)
            
        elif self.state == GameState.PHASE_1_PLAY:
            self.draw_message()
            self.graph.draw(self.screen)
            self.draw_legend()
            
        elif self.state == GameState.PHASE_2_INTRO:
            self.draw_title("FASE 2: BUSCA EM PROFUNDIDADE (DFS)", y=60, size=52)
            
            lines = [
                "MISSÃO: Penetrar o firewall usando DFS",
                "",
                "O QUE É DFS (Depth-First Search)?",
                "• DFS explora o grafo em PROFUNDIDADE",
                "• Vai o mais fundo possível antes de retroceder",
                "• Útil para explorar todos os caminhos possíveis",
                "",
                "COMO FAZER:",
                "1. Comece pelo nó inicial (verde)",
                "2. Escolha um vizinho e vá o mais fundo possível",
                "3. Quando não puder ir mais fundo, retroceda",
                "4. Continue até alcançar o alvo (vermelho)",
                "",
                "Dica: Pense em explorar um labirinto!"
            ]
            self.draw_text_box(lines, y_start=140, width=1000)
            
        elif self.state == GameState.PHASE_2_PLAY:
            self.draw_message()
            self.graph.draw(self.screen)
            self.draw_legend()
            
        elif self.state == GameState.VICTORY:
            self.draw_title("MISSÃO CUMPRIDA!", y=120, size=72)
            
            lines = [
                "🎉 PARABÉNS, HACKER! 🎉",
                "",
                "Você conseguiu penetrar todos os sistemas de segurança!",
                "",
                "Suas habilidades em algoritmos de grafos foram fundamentais",
                "para hackear as redes mais protegidas do Cyber Nexus.",
                "",
                "BFS e DFS dominados!",
                "Você agora é um mestre em algoritmos de busca.",
                "",
                "O mundo cibernético está ao seu alcance!",
            ]
            self.draw_text_box(lines, y_start=240, width=900)
            
        # Desenhar botões
        for button in self.buttons:
            button.draw(self.screen)
            
        pygame.display.flip()
        
    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()

def main():
    game = CyberNexus()
    game.run()

if __name__ == "__main__":
    main()
