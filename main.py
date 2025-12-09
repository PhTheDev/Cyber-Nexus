#!/usr/bin/env python3
"""
Cyber Nexus - Jogo Educacional de Algoritmos de Grafos
Autores: Pedro Henrique Faria e Caio Leal Granja
Versão Corrigida para 1920x1080 - Bug de botões corrigido
"""

import pygame
import sys
import random
import math
from collections import deque
from enum import Enum

# Inicialização do Pygame
pygame.init()

# Constantes para 1920x1080
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
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
        self.radius = 35
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
        border_width = 6 if self.selected else 3
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.radius, border_width)
        
        # Desenhar ID
        font = pygame.font.Font(None, 36)
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
            width = 7
        else:
            color = COLOR_EDGE
            width = 3
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
        pygame.draw.rect(screen, color, self.rect, border_radius=12)
        pygame.draw.rect(screen, COLOR_NODE, self.rect, 4, border_radius=12)
        
        # Ajustar tamanho da fonte baseado no comprimento do texto
        font_size = 36
        if len(self.text) > 15:
            font_size = 30
        elif len(self.text) > 12:
            font_size = 32
            
        font = pygame.font.Font(None, font_size)
        text_surface = font.render(self.text, True, COLOR_TEXT)
        
        # Verificar se o texto cabe no botão
        text_width, text_height = text_surface.get_size()
        max_width = self.rect.width - 20  # Margem de 10 pixels em cada lado
        max_height = self.rect.height - 10  # Margem de 5 pixels em cada lado
        
        if text_width > max_width:
            # Reduzir fonte se necessário
            font_size = int(font_size * (max_width / text_width))
            font = pygame.font.Font(None, font_size)
            text_surface = font.render(self.text, True, COLOR_TEXT)
        
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
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

def generate_random_graph(num_nodes=12, min_x=250, max_x=1670, min_y=250, max_y=750):
    """Gera um grafo aleatório conectado com múltiplos caminhos"""
    graph = Graph()
    nodes = []
    
    # Criar nós com posições aleatórias
    for i in range(num_nodes):
        attempts = 0
        while attempts < 50:
            x = random.randint(min_x, max_x)
            y = random.randint(min_y, max_y)
            
            # Verificar distância mínima de outros nós
            valid = True
            for node in nodes:
                dist = math.sqrt((node.x - x) ** 2 + (node.y - y) ** 2)
                if dist < 120:  # Aumentada distância mínima
                    valid = False
                    break
            
            if valid:
                break
            attempts += 1
        
        is_target = (i == num_nodes - 1)
        node = Node(i + 1, x, y, is_target)
        nodes.append(node)
        graph.add_node(node)
    
    # Primeiro nó é o inicial
    graph.start_node = nodes[0]
    
    # FASE 1: Criar árvore geradora mínima
    connected = [nodes[0]]
    unconnected = nodes[1:]
    
    tree_edges = []
    
    while unconnected:
        best_pair = None
        best_distance = float('inf')
        
        for uc in unconnected:
            for c in connected:
                dist = math.sqrt((uc.x - c.x)**2 + (uc.y - c.y)**2)
                if dist < best_distance:
                    best_distance = dist
                    best_pair = (c, uc)
        
        if best_pair:
            node1, node2 = best_pair
            graph.add_edge(node1, node2)
            tree_edges.append((node1, node2))
            connected.append(node2)
            unconnected.remove(node2)
    
    # FASE 2: Adicionar arestas extras
    target_node = nodes[-1]
    potential_target_connections = []
    
    for node in nodes[:-1]:
        if node not in target_node.neighbors:
            dist = math.sqrt((node.x - target_node.x)**2 + (node.y - target_node.y)**2)
            if dist < 500:
                potential_target_connections.append((node, dist))
    
    potential_target_connections.sort(key=lambda x: x[1])
    num_target_edges = min(4, len(potential_target_connections))
    
    for i in range(num_target_edges):
        if i < len(potential_target_connections):
            node = potential_target_connections[i][0]
            if node not in target_node.neighbors:
                graph.add_edge(node, target_node)
    
    # Adicionar mais arestas para conectar o grafo
    num_extra_edges = random.randint(num_nodes * 2, num_nodes * 3)
    
    for _ in range(num_extra_edges):
        node1 = random.choice(nodes)
        node2 = random.choice(nodes)
        
        if (node1 != node2 and 
            node2 not in node1.neighbors and 
            (node1, node2) not in tree_edges and 
            (node2, node1) not in tree_edges):
            
            dist = math.sqrt((node1.x - node2.x)**2 + (node1.y - node2.y)**2)
            max_dist = 600 if num_nodes > 10 else 500
            
            if dist < max_dist:
                prob = 0.7 - (dist / max_dist) * 0.4
                if random.random() < prob:
                    graph.add_edge(node1, node2)
    
    # Garantir conectividade mínima
    for node in nodes:
        if node != graph.start_node and node != target_node:
            if len(node.neighbors) < 2:
                candidates = [n for n in nodes 
                            if n != node and 
                            n not in node.neighbors]
                
                if candidates:
                    # Escolher o mais próximo
                    candidates.sort(key=lambda n: math.sqrt((n.x - node.x)**2 + (n.y - node.y)**2))
                    for candidate in candidates:
                        if candidate not in node.neighbors:
                            graph.add_edge(node, candidate)
                            break
    
    return graph

class CyberNexus:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
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
        
        # Armazenar grafo atual para reutilização
        self.current_graph_state = None
        self.current_phase = None
        
        self.buttons = []
        self.setup_main_menu()
        
    def setup_main_menu(self):
        """Tela principal do jogo"""
        self.buttons = [
            Button(SCREEN_WIDTH//2 - 200, 400, 400, 80, "TUTORIAL", 
                   lambda: self.change_state(GameState.TUTORIAL_INTRO)),
            Button(SCREEN_WIDTH//2 - 200, 520, 400, 80, "COMEÇAR A JOGAR", 
                   lambda: self.change_state(GameState.PHASE_1_INTRO)),
            Button(SCREEN_WIDTH//2 - 200, 640, 400, 80, "SAIR", 
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
            Button(SCREEN_WIDTH//2 + 50, 850, 350, 80, "COMEÇAR TUTORIAL", 
                   lambda: self.change_state(GameState.TUTORIAL_PLAY)),
            Button(SCREEN_WIDTH//2 - 400, 850, 350, 80, "VOLTAR", 
                   lambda: self.change_state(GameState.MAIN_MENU)),
        ]
        
    def setup_tutorial_play(self):
        """Tutorial interativo"""
        self.graph = Graph()
        
        # Criar grafo simples
        node1 = Node(1, 600, 540)
        node2 = Node(2, 900, 540)
        node3 = Node(3, 1200, 540)
        node4 = Node(4, 1500, 540, is_target=True)
        
        self.graph.add_node(node1)
        self.graph.add_node(node2)
        self.graph.add_node(node3)
        self.graph.add_node(node4)
        
        self.graph.add_edge(node1, node2)
        self.graph.add_edge(node2, node3)
        self.graph.add_edge(node3, node4)
        
        self.graph.start_node = node1
        
        self.buttons = [
            Button(100, 950, 300, 80, "RESETAR CAMINHO",
                   lambda: self.reset_current_path()),
            Button(SCREEN_WIDTH//2 - 150, 950, 300, 80, "COMEÇAR A JOGAR", 
                   lambda: self.change_state(GameState.PHASE_1_INTRO)),
            Button(SCREEN_WIDTH - 400, 950, 300, 80, "VOLTAR", 
                   lambda: self.change_state(GameState.MAIN_MENU)),
        ]
        
        self.message = "Clique nos nós em sequência para criar um caminho!"
        self.current_graph_state = None
        self.current_phase = "tutorial"
        
    def setup_phase_1_intro(self):
        """Introdução da Fase 1 - BFS"""
        self.buttons = [
            Button(SCREEN_WIDTH//2 + 50, 850, 350, 80, "JOGAR FASE 1", 
                   lambda: self.change_state(GameState.PHASE_1_PLAY)),
            Button(SCREEN_WIDTH//2 - 400, 850, 350, 80, "VOLTAR", 
                   lambda: self.change_state(GameState.MAIN_MENU)),
        ]
        
    def setup_phase_1_play(self):
        """Fase 1 - BFS com grafo aleatório"""
        if self.current_phase == "phase1" and self.current_graph_state:
            self.graph = self.current_graph_state
            self.graph.reset()
        else:
            self.graph = generate_random_graph(12)
            self.current_graph_state = self.graph
            self.current_phase = "phase1"
        
        self.player_path = []
        self.selected_node = None
        
        self.show_available_paths()
        
        self.buttons = [
            Button(100, 950, 250, 70, "VERIFICAR", 
                   lambda: self.verify_bfs()),
            Button(380, 950, 280, 70, "RESETAR CAMINHO", 
                   lambda: self.reset_current_path()),
            Button(690, 950, 250, 70, "NOVO GRAFO", 
                   lambda: self.new_graph()),
            Button(SCREEN_WIDTH - 350, 950, 250, 70, "MENU", 
                   lambda: self.change_state(GameState.MAIN_MENU)),
        ]
        
        if not self.message:
            self.message = "Clique nos nós para criar um caminho BFS do nó verde ao vermelho!"
        
    def setup_phase_2_intro(self):
        """Introdução da Fase 2 - DFS"""
        self.buttons = [
            Button(SCREEN_WIDTH//2 + 50, 850, 350, 80, "JOGAR FASE 2", 
                   lambda: self.change_state(GameState.PHASE_2_PLAY)),
            Button(SCREEN_WIDTH//2 - 400, 850, 350, 80, "VOLTAR", 
                   lambda: self.change_state(GameState.MAIN_MENU)),
        ]
        
    def setup_phase_2_play(self):
        """Fase 2 - DFS com grafo aleatório"""
        if self.current_phase == "phase2" and self.current_graph_state:
            self.graph = self.current_graph_state
            self.graph.reset()
        else:
            self.graph = generate_random_graph(12)
            self.current_graph_state = self.graph
            self.current_phase = "phase2"
        
        self.player_path = []
        self.selected_node = None
        
        self.show_available_paths()
        
        self.buttons = [
            Button(100, 950, 250, 70, "VERIFICAR", 
                   lambda: self.verify_dfs()),
            Button(380, 950, 280, 70, "RESETAR CAMINHO", 
                   lambda: self.reset_current_path()),
            Button(690, 950, 250, 70, "NOVO GRAFO", 
                   lambda: self.new_graph()),
            Button(SCREEN_WIDTH - 350, 950, 250, 70, "MENU", 
                   lambda: self.change_state(GameState.MAIN_MENU)),
        ]
        
        if not self.message:
            self.message = "Clique nos nós para criar um caminho DFS do nó verde ao vermelho!"
        
    def setup_victory(self):
        """Tela de vitória"""
        self.buttons = [
            Button(SCREEN_WIDTH//2 - 200, 850, 400, 80, "VOLTAR AO MENU", 
                   lambda: self.change_state(GameState.MAIN_MENU)),
        ]
        
    def reset_current_path(self):
        """Reseta apenas o caminho do jogador, mantendo o mesmo grafo"""
        self.graph.reset()
        self.player_path = []
        self.selected_node = None
        self.message = "Caminho resetado! Tente novamente no mesmo grafo."
        self.message_color = COLOR_TEXT
        
        # Recriar botões originais da fase atual
        if self.state == GameState.PHASE_1_PLAY:
            self.buttons = [
                Button(100, 950, 250, 70, "VERIFICAR", 
                       lambda: self.verify_bfs()),
                Button(380, 950, 280, 70, "RESETAR CAMINHO", 
                       lambda: self.reset_current_path()),
                Button(690, 950, 250, 70, "NOVO GRAFO", 
                       lambda: self.new_graph()),
                Button(SCREEN_WIDTH - 350, 950, 250, 70, "MENU", 
                       lambda: self.change_state(GameState.MAIN_MENU)),
            ]
        elif self.state == GameState.PHASE_2_PLAY:
            self.buttons = [
                Button(100, 950, 250, 70, "VERIFICAR", 
                       lambda: self.verify_dfs()),
                Button(380, 950, 280, 70, "RESETAR CAMINHO", 
                       lambda: self.reset_current_path()),
                Button(690, 950, 250, 70, "NOVO GRAFO", 
                       lambda: self.new_graph()),
                Button(SCREEN_WIDTH - 350, 950, 250, 70, "MENU", 
                       lambda: self.change_state(GameState.MAIN_MENU)),
            ]
        elif self.state == GameState.TUTORIAL_PLAY:
            self.buttons = [
                Button(100, 950, 300, 80, "RESETAR CAMINHO",
                       lambda: self.reset_current_path()),
                Button(SCREEN_WIDTH//2 - 150, 950, 300, 80, "COMEÇAR A JOGAR", 
                       lambda: self.change_state(GameState.PHASE_1_INTRO)),
                Button(SCREEN_WIDTH - 400, 950, 300, 80, "VOLTAR", 
                       lambda: self.change_state(GameState.MAIN_MENU)),
            ]
        
        if self.state in [GameState.PHASE_1_PLAY, GameState.PHASE_2_PLAY]:
            self.show_available_paths()
    
    def new_graph(self):
        """Gera um novo grafo aleatório"""
        if self.state == GameState.PHASE_1_PLAY:
            self.current_graph_state = None
            self.setup_phase_1_play()
            self.message = "Novo grafo gerado! Tente encontrar o caminho BFS."
        elif self.state == GameState.PHASE_2_PLAY:
            self.current_graph_state = None
            self.setup_phase_2_play()
            self.message = "Novo grafo gerado! Tente encontrar o caminho DFS."
        self.message_color = COLOR_TEXT
        
    def handle_node_click(self, pos):
        """Lidar com clique em nós"""
        for node in self.graph.nodes:
            if node.contains_point(pos[0], pos[1]):
                if not self.player_path:
                    if node == self.graph.start_node:
                        self.player_path.append(node)
                        node.in_path = True
                        self.message = f"Nó {node.id} selecionado! Continue o caminho..."
                        self.message_color = COLOR_TEXT
                    else:
                        self.message = "Você deve começar pelo nó VERDE (inicial)!"
                        self.message_color = COLOR_ERROR
                else:
                    last_node = self.player_path[-1]
                    
                    if node in last_node.neighbors and node not in self.player_path:
                        self.player_path.append(node)
                        node.in_path = True
                        
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
                return
                
    def show_available_paths(self):
        """Mostra quantos caminhos diferentes existem até o alvo"""
        if self.state not in [GameState.PHASE_1_PLAY, GameState.PHASE_2_PLAY]:
            return
        
        def count_paths_dfs(current, target, visited, path_count):
            if current == target:
                return path_count + 1
            
            visited.add(current)
            
            for neighbor in current.neighbors:
                if neighbor not in visited:
                    path_count = count_paths_dfs(neighbor, target, visited, path_count)
            
            visited.remove(current)
            return path_count
        
        visited = set()
        num_paths = count_paths_dfs(self.graph.start_node, self.graph.target_node, visited, 0)
        
        path_info = f"Há {num_paths} caminho(s) possível(is) até o alvo."
        
        if self.message_color != COLOR_ERROR:
            self.message = path_info
            self.message_color = COLOR_TEXT
    
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
        if self.player_path == bfs_path:
            self.message = "🎉 SUCESSO! Sistema hackeado! Você executou um BFS perfeito!"
            self.message_color = COLOR_SUCCESS
            self.phase1_completed = True
            
            self.buttons = [
                Button(100, 950, 280, 70, "CONTINUAR PRATICANDO",
                       lambda: self.reset_current_path()),
                Button(410, 950, 250, 70, "NOVO GRAFO",
                       lambda: self.new_graph()),
                Button(SCREEN_WIDTH//2 + 50, 950, 300, 70, "PRÓXIMA FASE", 
                       lambda: self.change_state(GameState.PHASE_2_INTRO)),
            ]
        else:
            is_valid_path = True
            for i in range(len(self.player_path) - 1):
                if self.player_path[i+1] not in self.player_path[i].neighbors:
                    is_valid_path = False
                    break
            
            if is_valid_path:
                bfs_path_ids = [str(node.id) for node in bfs_path]
                player_path_ids = [str(node.id) for node in self.player_path]
                
                self.message = f"Caminho válido, mas não é BFS ótimo. Caminho BFS correto: {' → '.join(bfs_path_ids)}"
                self.message_color = COLOR_ERROR
                
                self.buttons = [
                    Button(100, 950, 250, 70, "TENTAR NOVAMENTE",
                           lambda: self.reset_current_path()),
                    Button(380, 950, 300, 70, "VER CAMINHO CORRETO",
                           lambda: self.show_correct_path(bfs_path)),
                    Button(710, 950, 250, 70, "NOVO GRAFO",
                           lambda: self.new_graph()),
                    Button(SCREEN_WIDTH - 350, 950, 250, 70, "MENU",
                           lambda: self.change_state(GameState.MAIN_MENU)),
                ]
            else:
                self.message = "Caminho inválido! Verifique as conexões."
                self.message_color = COLOR_ERROR
    
    def show_correct_path(self, correct_path):
        """Mostra o caminho correto ao jogador"""
        self.graph.reset()
        
        for i in range(len(correct_path) - 1):
            node1 = correct_path[i]
            node2 = correct_path[i + 1]
            node1.in_path = True
            node2.in_path = True
            
            for edge in self.graph.edges:
                if (edge.node1 == node1 and edge.node2 == node2) or \
                   (edge.node1 == node2 and edge.node2 == node1):
                    edge.player_selected = True
        
        correct_path[-1].in_path = True
        
        self.message = "Caminho BFS correto mostrado em amarelo. Tente replicá-lo!"
        self.message_color = COLOR_SUCCESS
        self.player_path = []
        
        # CORREÇÃO: Manter o botão VERIFICAR quando tentar novamente
        if self.state == GameState.PHASE_1_PLAY:
            self.buttons = [
                Button(100, 950, 250, 70, "TENTAR EU MESMO",
                       lambda: self.reset_to_phase1()),
                Button(380, 950, 250, 70, "NOVO GRAFO",
                       lambda: self.new_graph()),
                Button(SCREEN_WIDTH - 350, 950, 250, 70, "MENU",
                       lambda: self.change_state(GameState.MAIN_MENU)),
            ]
        elif self.state == GameState.PHASE_2_PLAY:
            self.buttons = [
                Button(100, 950, 250, 70, "TENTAR EU MESMO",
                       lambda: self.reset_to_phase2()),
                Button(380, 950, 250, 70, "NOVO GRAFO",
                       lambda: self.new_graph()),
                Button(SCREEN_WIDTH - 350, 950, 250, 70, "MENU",
                       lambda: self.change_state(GameState.MAIN_MENU)),
            ]
    
    def reset_to_phase1(self):
        """Reseta para a fase 1 com botões originais"""
        self.graph.reset()
        self.player_path = []
        self.selected_node = None
        self.message = "Tente encontrar o caminho BFS correto!"
        self.message_color = COLOR_TEXT
        
        # Restaurar botões originais da fase 1
        self.buttons = [
            Button(100, 950, 250, 70, "VERIFICAR", 
                   lambda: self.verify_bfs()),
            Button(380, 950, 280, 70, "RESETAR CAMINHO", 
                   lambda: self.reset_current_path()),
            Button(690, 950, 250, 70, "NOVO GRAFO", 
                   lambda: self.new_graph()),
            Button(SCREEN_WIDTH - 350, 950, 250, 70, "MENU", 
                   lambda: self.change_state(GameState.MAIN_MENU)),
        ]
        
        self.show_available_paths()
    
    def reset_to_phase2(self):
        """Reseta para a fase 2 com botões originais"""
        self.graph.reset()
        self.player_path = []
        self.selected_node = None
        self.message = "Tente encontrar o caminho DFS correto!"
        self.message_color = COLOR_TEXT
        
        # Restaurar botões originais da fase 2
        self.buttons = [
            Button(100, 950, 250, 70, "VERIFICAR", 
                   lambda: self.verify_dfs()),
            Button(380, 950, 280, 70, "RESETAR CAMINHO", 
                   lambda: self.reset_current_path()),
            Button(690, 950, 250, 70, "NOVO GRAFO", 
                   lambda: self.new_graph()),
            Button(SCREEN_WIDTH - 350, 950, 250, 70, "MENU", 
                   lambda: self.change_state(GameState.MAIN_MENU)),
        ]
        
        self.show_available_paths()
                
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
        
        is_valid = True
        for i in range(len(self.player_path) - 1):
            if self.player_path[i+1] not in self.player_path[i].neighbors:
                is_valid = False
                break
        
        if not is_valid:
            self.message = "Caminho inválido! Verifique as conexões."
            self.message_color = COLOR_ERROR
            return
        
        player_path_ids = [str(node.id) for node in self.player_path]
        self.message = f"🎉 SUCESSO! Firewall penetrado! Caminho DFS: {' → '.join(player_path_ids)}"
        self.message_color = COLOR_SUCCESS
        self.phase2_completed = True
        
        if self.phase1_completed:
            self.buttons = [
                Button(100, 950, 280, 70, "CONTINUAR PRATICANDO",
                       lambda: self.reset_current_path()),
                Button(410, 950, 250, 70, "NOVO GRAFO",
                       lambda: self.new_graph()),
                Button(SCREEN_WIDTH//2 + 50, 950, 350, 70, "MISSÃO COMPLETA", 
                       lambda: self.change_state(GameState.VICTORY)),
            ]
        else:
            self.buttons = [
                Button(100, 950, 280, 70, "CONTINUAR PRATICANDO",
                       lambda: self.reset_current_path()),
                Button(410, 950, 250, 70, "NOVO GRAFO",
                       lambda: self.new_graph()),
                Button(SCREEN_WIDTH - 350, 950, 250, 70, "MENU",
                       lambda: self.change_state(GameState.MAIN_MENU)),
            ]
            
    def draw_grid(self):
        """Desenhar grade cyberpunk de fundo"""
        for x in range(0, SCREEN_WIDTH, 60):
            pygame.draw.line(self.screen, COLOR_GRID, (x, 0), (x, SCREEN_HEIGHT), 2)
        for y in range(0, SCREEN_HEIGHT, 60):
            pygame.draw.line(self.screen, COLOR_GRID, (0, y), (SCREEN_WIDTH, y), 2)
            
    def draw_title(self, text, y=120, size=96):
        """Desenhar título"""
        font = pygame.font.Font(None, size)
        title = font.render(text, True, COLOR_TEXT_TITLE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, y))
        
        shadow = font.render(text, True, (50, 0, 25))
        shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH // 2 + 5, y + 5))
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(title, title_rect)
        
    def draw_text_box(self, lines, y_start=250, width=1200):
        """Desenhar caixa de texto com múltiplas linhas"""
        x = SCREEN_WIDTH // 2 - width // 2
        line_height = 45
        padding = 30
        
        total_height = len(lines) * line_height + padding * 2
        
        bg_rect = pygame.Rect(x, y_start, width, total_height)
        bg_surface = pygame.Surface((width, total_height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surface, (20, 20, 50, 220), bg_surface.get_rect(), border_radius=15)
        pygame.draw.rect(bg_surface, COLOR_NODE, bg_surface.get_rect(), 4, border_radius=15)
        self.screen.blit(bg_surface, (x, y_start))
        
        font = pygame.font.Font(None, 32)
        y = y_start + padding
        for line in lines:
            text = font.render(line, True, COLOR_TEXT)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += line_height
            
    def draw_message(self):
        """Desenhar mensagem de status"""
        if self.message:
            font = pygame.font.Font(None, 36)
            text = font.render(self.message, True, self.message_color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 150))
            
            bg_rect = text_rect.inflate(40, 20)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(bg_surface, (0, 0, 0, 200), bg_surface.get_rect(), border_radius=10)
            self.screen.blit(bg_surface, bg_rect)
            
            self.screen.blit(text, text_rect)
            
    def draw_legend(self):
        """Desenhar legenda de cores e informações do grafo"""
        panel_x = 1550
        panel_y = 50
        panel_width = 320
        panel_height = 250
        
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (10, 10, 30, 220), panel_surface.get_rect(), border_radius=15)
        pygame.draw.rect(panel_surface, COLOR_NODE, panel_surface.get_rect(), 3, border_radius=15)
        self.screen.blit(panel_surface, (panel_x, panel_y))
        
        font_title = pygame.font.Font(None, 36)
        title = font_title.render("LEGENDA", True, COLOR_TEXT_TITLE)
        self.screen.blit(title, (panel_x + 30, panel_y + 20))
        
        font_text = pygame.font.Font(None, 28)
        legend_items = [
            ("Nó Inicial", COLOR_NODE_START),
            ("Nó Normal", COLOR_NODE),
            ("Nó no Caminho", COLOR_EDGE_PLAYER),
            ("Nó Alvo", COLOR_NODE_TARGET),
        ]
        
        y_offset = panel_y + 70
        for label, color in legend_items:
            pygame.draw.circle(self.screen, color, (panel_x + 35, y_offset + 10), 16)
            pygame.draw.circle(self.screen, (255, 255, 255), (panel_x + 35, y_offset + 10), 16, 3)
            text = font_text.render(label, True, COLOR_TEXT)
            self.screen.blit(text, (panel_x + 60, y_offset))
            y_offset += 40
    
        if self.state in [GameState.PHASE_1_PLAY, GameState.PHASE_2_PLAY] and self.graph.nodes:
            y_offset += 10
            
            total_degree = sum(len(node.neighbors) for node in self.graph.nodes)
            avg_degree = total_degree / len(self.graph.nodes)
            
            if avg_degree > 3.5:
                pygame.draw.circle(self.screen, COLOR_SUCCESS, (panel_x + 240, y_offset + 10), 10)
            elif avg_degree > 2.5:
                pygame.draw.circle(self.screen, (255, 255, 0), (panel_x + 240, y_offset + 10), 10)
            else:
                pygame.draw.circle(self.screen, COLOR_ERROR, (panel_x + 240, y_offset + 10), 10)
                
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
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state in [GameState.TUTORIAL_PLAY, GameState.PHASE_1_PLAY, GameState.PHASE_2_PLAY]:
                    self.handle_node_click(event.pos)
            
            for button in self.buttons:
                button.handle_event(event)
                
    def draw(self):
        self.screen.fill(COLOR_BG)
        self.draw_grid()
        
        if self.state == GameState.MAIN_MENU:
            self.draw_title("CYBER NEXUS", y=180, size=120)
            
            font = pygame.font.Font(None, 48)
            subtitle = font.render("Jogo Educacional de Algoritmos de Grafos", True, COLOR_TEXT)
            subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 280))
            self.screen.blit(subtitle, subtitle_rect)
            
            font_small = pygame.font.Font(None, 32)
            credits = font_small.render("Por Pedro Henrique Faria e Caio Leal Granja", True, COLOR_TEXT)
            credits_rect = credits.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
            self.screen.blit(credits, credits_rect)
            
        elif self.state == GameState.TUTORIAL_INTRO:
            self.draw_title("TUTORIAL", y=120)
            
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
            self.draw_text_box(lines, y_start=250)
            
        elif self.state == GameState.TUTORIAL_PLAY:
            self.draw_message()
            self.graph.draw(self.screen)
            self.draw_legend()
            
        elif self.state == GameState.PHASE_1_INTRO:
            self.draw_title("FASE 1: BUSCA EM LARGURA (BFS)", y=100, size=72)
            
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
            self.draw_text_box(lines, y_start=200, width=1300)
            
        elif self.state == GameState.PHASE_1_PLAY:
            self.draw_message()
            self.graph.draw(self.screen)
            self.draw_legend()
            
        elif self.state == GameState.PHASE_2_INTRO:
            self.draw_title("FASE 2: BUSCA EM PROFUNDIDADE (DFS)", y=100, size=72)
            
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
            self.draw_text_box(lines, y_start=200, width=1300)
            
        elif self.state == GameState.PHASE_2_PLAY:
            self.draw_message()
            self.graph.draw(self.screen)
            self.draw_legend()
            
        elif self.state == GameState.VICTORY:
            self.draw_title("MISSÃO CUMPRIDA!", y=180, size=96)
            
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
            self.draw_text_box(lines, y_start=350, width=1200)
            
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