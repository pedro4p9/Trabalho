import pyxel
from cliente import ClienteRede

pyxel.init(128, 128, title="Super Jump Online", fps=30)
pyxel.load("main.pyxres")

# --- REDE ---
print("Conectando ao servidor...")
rede = None
meu_id = 0
outros_jogadores = {}
jogo_pronto = False  # Nova flag para indicar se o jogo pode começar
total_jogadores = 0

try:
    rede = ClienteRede()
    meu_id = rede.player_id
except Exception as e:
    print(f"Falha ao conectar: {e}")
    print("O jogo requer conexão com o servidor. Saindo...")
    pyxel.quit()
    exit()

game_state = 0
player_lives = 3
selected_skin = -1  # Alterado para -1 inicialmente (nenhuma skin escolhida)
# --- PERSONAGENS (linhas no pyxres) ---
PERSONAGENS = [
    {"nome": "HERO",   "idle_v": 16},  # (0,2)
    {"nome": "NINJA",  "idle_v": 40},  # (0,5)
    {"nome": "ROBOT",  "idle_v": 56},  # (0,7)
    {"nome": "BEAST",  "idle_v": 72},  # (0,9)
]

camera_x = 0
camera_y = 0

# Jogador
player_speed = 2.5
player_x = 60 
player_y = 60
player_u = 0 
player_v = 16
velocity_y = 0
gravity = 1
jump_force = -8
on_ground = False
bladeliste = []
blade_speed = 1
charge = 0
sprite_liste = [0,8] 

# --- ITENS COLECIONÁVEIS ---
# Definições dos tiles de itens do Pyxel Edit
OURO = (2, 24)      # Tile (2, 24) - Player 1
PRATA = (1, 24)     # Tile (1, 24) - Player 2  
BRONZE = (0, 24)    # Tile (0, 24) - Players 3+
TILE_VAZIO = (0, 0) # Tile vazio para substituir itens coletados

# --- CHECKPOINT E FIM DE FASE ---
CHECKPOINT = (3, 21)    # Tile (3, 21) - Checkpoint
FIM_FASE = (2, 21)      # Tile (2, 21) - Fim da Fase

# Pontuação por tipo de item
PONTOS_POR_ITEM = {
    OURO: 10,    # Player 1: 10 pontos
    PRATA: 10,    # Player 2: 5 pontos
    BRONZE: 10    # Players 3+: 2 pontos
}

# Bonus por completar fase
BONUS_FIM_FASE = 50

# Itens coletados (armazena posições dos tiles coletados)
itens_coletados = set()  # Formato: (tile_x, tile_y)

# Checkpoint ativo (último checkpoint coletado)
checkpoint_ativo = None  # Formato: (x, y) em pixels
checkpoints_coletados = set()  # Formato: (tile_x, tile_y) - todos checkpoints coletados

# Pontuação dos jogadores
pontuacao_jogadores = {}
pontuacao_jogadores[meu_id] = 0

# Tiles e Mapas
BLOC_JAUNE = (10,20); PETITE_PLANCHE = (0,26)
LONGUE_PLANCHE_R = (3,26); LONGUE_PLANCHE = (2,26); LONGUE_PLANCHE_L = (1,26)
tiles_sol_dur = [BLOC_JAUNE, PETITE_PLANCHE,LONGUE_PLANCHE,LONGUE_PLANCHE_L,LONGUE_PLANCHE_R]

SOL_HERBE_L = (10, 27); SOL_HERBE = (11, 27); SOL_HERBE_R = (12, 27)
SOL_BOIS_L = (1, 27); SOL_BOIS = (2, 27); SOL_BOIS_R = (3, 27) 
PLANCHE_L = (0, 25); PLANCHE = (1, 25); PLANCHE_R = (2, 25)
METAL_L = (3,25); METAL = (4,25); METAL_R = (5,25)
tiles_sol = [SOL_HERBE_L, SOL_HERBE, SOL_HERBE_R, SOL_BOIS_L, SOL_BOIS, SOL_BOIS_R, PLANCHE_L, PLANCHE, PLANCHE_R, METAL_L, METAL, METAL_R]

TERRE_L = (10,28); TERRE_L_DOWN = (10,29)
TERRE_CENTER = (11,28); TERRE_CENTER_DOWN = (11,29)
TERRE_R = (12,28); TERRE_R_DOWN = (12,29)
tiles_mur = [TERRE_L,TERRE_L_DOWN, TERRE_CENTER,TERRE_CENTER_DOWN, TERRE_R,TERRE_R_DOWN, BLOC_JAUNE, PETITE_PLANCHE, LONGUE_PLANCHE_R,LONGUE_PLANCHE,LONGUE_PLANCHE_L]
tiles_plafond = [TERRE_CENTER_DOWN,TERRE_L_DOWN,TERRE_R_DOWN, BLOC_JAUNE, PETITE_PLANCHE, LONGUE_PLANCHE_L,LONGUE_PLANCHE,LONGUE_PLANCHE_R]


def apply_skin(skin_id):
    pyxel.pal()  # mantém compatibilidade, mas não muda cores


# --- FUNÇÕES LÓGICAS ---
def blade_reloaded(recharge):
    if pyxel.frame_count % 60 == 0 and recharge == 0: return recharge + 1
    return recharge

def blade_creation(x,y,bladeliste,recharge):
    if pyxel.btnr(pyxel.KEY_ALT) and recharge == 1:
        bladeliste.append([x,y])
        return bladeliste, 0
    return bladeliste, recharge

def blade_deplacement(bladeliste):
    for blade in bladeliste:
        blade[0] += blade_speed 
        if blade[0] > 256: bladeliste.remove(blade) 
    return bladeliste 

def est_solide(x, y):
    return pyxel.tilemaps[0].pget(int(x//8), int(y//8)) in tiles_sol

def est_mur(x, y):
    return pyxel.tilemaps[0].pget(int(x//8), int(y//8)) in tiles_mur

def est_plafond(x, y):
    return pyxel.tilemaps[0].pget(int(x//8), int(y//8)) in tiles_plafond

def on_floor(x, y):
    tile = pyxel.tilemaps[0].pget((x + 3) // 8, (y + 8) // 8)
    return tile in tiles_sol or tile in tiles_sol_dur

def player_deplacement(x, y):
    new_x = x
    if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
        if x < 10000 and not est_mur(x + 8, y) and not est_mur(x + 8, y + 7):
            new_x += player_speed
    if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_Q):
        if x > 0 and not est_mur(x - 1, y) and not est_mur(x - 1, y + 7):
            new_x -= player_speed
    return new_x, y

def collision_sol_precise(x, y, vy):
    foot_x, foot_y = int((x + 3) // 8), int((y + 8) // 8)
    if pyxel.tilemaps[0].pget(foot_x, foot_y) in tiles_sol and vy >= 0:
        return foot_y * 8 - 8, 0
    return y, vy

def collision_sol_dur(x, y, vy):
    foot_x, foot_y = int((x + 3) // 8), int((y + 8) // 8)
    head_y = int((y - 1) // 8)
    if pyxel.tilemaps[0].pget(foot_x, foot_y) in tiles_sol_dur and vy >= 0:
        return foot_y * 8 - 8, 0
    elif pyxel.tilemaps[0].pget(foot_x, head_y) in tiles_sol_dur and vy < 0:
        return (head_y + 1) * 8, 0
    return y, vy

def sprite_balance(sl):
    if selected_skin < 0:
        return sl
        
    base_v = PERSONAGENS[selected_skin]["idle_v"]
    moving = False
    
    # Controle de velocidade da animação (opcional, para não ficar muito rápido)
    animate = pyxel.frame_count % 2 == 0

    if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
        sl[1] = base_v      # Define a linha da Direita
        if animate:
            sl[0] += 8
        moving = True

    elif pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_Q):
        sl[1] = base_v + 8  # Define a linha da Esquerda
        if animate:
            sl[0] += 8
        moving = True

    # Reseta o ciclo se passar do último frame (56 = 7 * 8)
    if sl[0] > 56:
        sl[0] = 0

    # SE ESTIVER PARADO:
    if not moving:
        sl[0] = 0
        
    return sl

def reset_player():
    global player_x, player_y, velocity_y
    # Se tem checkpoint, respawna lá, senão no início
    if checkpoint_ativo:
        player_x, player_y = checkpoint_ativo
    else:
        player_x = 10
        player_y = 56
    velocity_y = 0

def jogador_pode_coletar_tipo(jogador_id, tipo_tile):
    """Define qual jogador pode coletar qual tipo de item baseado no tile"""
    if jogador_id == 0:  # Player 1
        return tipo_tile == OURO
    elif jogador_id == 1:  # Player 2
        return tipo_tile == PRATA
    else:  # Players 3+
        return tipo_tile == BRONZE

def verificar_coleta_itens(jogador_id, jogador_x, jogador_y):
    """Verifica se o jogador está sobre um item coletável"""
    global itens_coletados, pontuacao_jogadores
    
    # Verifica uma área de 2x2 tiles ao redor do centro do jogador
    center_tile_x = int(jogador_x // 8)
    center_tile_y = int(jogador_y // 8)
    
    for offset_x in range(-1, 2):  # -1, 0, 1
        for offset_y in range(-1, 2):  # -1, 0, 1
            tile_x = center_tile_x + offset_x
            tile_y = center_tile_y + offset_y
            
            # Verifica se está dentro dos limites do mapa
            if (0 <= tile_x < pyxel.tilemaps[0].width and 
                0 <= tile_y < pyxel.tilemaps[0].height):
                
                tile = pyxel.tilemaps[0].pget(tile_x, tile_y)
                
                # Se for um item coletável e ainda não foi coletado
                if tile in [OURO, PRATA, BRONZE]:
                    pos_key = (tile_x, tile_y)
                    if pos_key in itens_coletados:
                        continue
                    
                    # Verifica colisão pixel-perfect
                    tile_px = tile_x * 8
                    tile_py = tile_y * 8
                    
                    # O jogador tem 8x8 pixels, verifica se há sobreposição
                    if (jogador_x < tile_px + 8 and 
                        jogador_x + 8 > tile_px and
                        jogador_y < tile_py + 8 and 
                        jogador_y + 8 > tile_py):
                        
                        # Verifica se o jogador pode coletar este tipo de item
                        if jogador_pode_coletar_tipo(jogador_id, tile):
                            # Marca como coletado
                            itens_coletados.add(pos_key)
                            
                            # Remove o item do mapa (substitui por tile vazio)
                            pyxel.tilemaps[0].pset(tile_x, tile_y, TILE_VAZIO)
                            
                            # Calcula pontos
                            pontos = PONTOS_POR_ITEM[tile]
                            
                            # Atualiza pontuação
                            if jogador_id in pontuacao_jogadores:
                                pontuacao_jogadores[jogador_id] += pontos
                            else:
                                pontuacao_jogadores[jogador_id] = pontos
                            
                            return True, tile, (tile_x, tile_y), pontos
    
    return False, None, None, 0

def verificar_checkpoint_fim(jogador_x, jogador_y):
    """Verifica se o jogador atingiu checkpoint ou fim de fase"""
    global checkpoint_ativo, checkpoints_coletados, game_state, pontuacao_jogadores
    
    # Verifica uma área de 2x2 tiles ao redor do centro do jogador
    center_tile_x = int(jogador_x // 8)
    center_tile_y = int(jogador_y // 8)
    
    for offset_x in range(-1, 2):  # -1, 0, 1
        for offset_y in range(-1, 2):  # -1, 0, 1
            tile_x = center_tile_x + offset_x
            tile_y = center_tile_y + offset_y
            
            # Verifica se está dentro dos limites do mapa
            if (0 <= tile_x < pyxel.tilemaps[0].width and 
                0 <= tile_y < pyxel.tilemaps[0].height):
                
                tile = pyxel.tilemaps[0].pget(tile_x, tile_y)
                
                # Verifica colisão pixel-perfect
                tile_px = tile_x * 8
                tile_py = tile_y * 8
                
                if (jogador_x < tile_px + 8 and 
                    jogador_x + 8 > tile_px and
                    jogador_y < tile_py + 8 and 
                    jogador_y + 8 > tile_py):
                    
                    # CHECKPOINT
                    if tile == CHECKPOINT:
                        pos_key = (tile_x, tile_y)
                        
                        # Se ainda não coletou este checkpoint específico
                        if pos_key not in checkpoints_coletados:
                            # Atualiza checkpoint ativo (último coletado)
                            checkpoint_ativo = (tile_px, tile_py - 8)  # Posição acima do checkpoint
                            checkpoints_coletados.add(pos_key)
                            
                            # Adiciona pontos por checkpoint (apenas na primeira vez)
                            if meu_id in pontuacao_jogadores:
                                pontuacao_jogadores[meu_id] += 20  # Bonus por checkpoint
                            
                            # Toca som (se houver)
                            return "checkpoint", pos_key
                        else:
                            # Já coletou antes, mas ainda pode atualizar como checkpoint ativo
                            checkpoint_ativo = (tile_px, tile_py - 8)
                            return "checkpoint_atualizado", pos_key
                    
                    # FIM DE FASE
                    elif tile == FIM_FASE:
                        # Adiciona bonus por completar fase
                        if meu_id in pontuacao_jogadores:
                            pontuacao_jogadores[meu_id] += BONUS_FIM_FASE
                        
                        # Vai para tela de fase completa
                        game_state = 5
                        return "fim_fase", None
    
    return None, None

def resetar_itens_coletados():
    """Reseta todos os itens coletados - reconstrói o mapa original"""
    global itens_coletados, checkpoint_ativo, checkpoints_coletados
    
    # Limpa as listas
    itens_coletados.clear()
    checkpoints_coletados.clear()
    checkpoint_ativo = None
    
    # Recarrega o tilemap original para restaurar os itens
    pyxel.load("main.pyxres")

def desenhar_efeito_item(tile_x, tile_y, tile_type):
    """Desenha um efeito visual nos itens não coletados"""
    if pyxel.frame_count % 30 < 15:
        px = tile_x * 8 - camera_x
        py = tile_y * 8 - camera_y
        
        if tile_type == OURO:
            cor = 10  # Amarelo/ouro
        elif tile_type == PRATA:
            cor = 7   # Cinza/prata
        elif tile_type == BRONZE:
            cor = 8   # Marrom/bronze
        elif tile_type == CHECKPOINT:
            # Checkpoints coletados têm cor diferente
            if (tile_x, tile_y) in checkpoints_coletados:
                cor = 12  # Azul mais claro para checkpoint ativo
            else:
                cor = 11  # Azul normal para checkpoint não coletado
        elif tile_type == FIM_FASE:
            cor = 9   # Verde para fim de fase
        
        # Desenha um quadrado brilhante ao redor
        pyxel.rectb(px, py, 8, 8, cor)
        
        # Se for checkpoint ativo (último coletado), destaca mais
        if tile_type == CHECKPOINT and checkpoint_ativo:
            checkpoint_tile_x = int(checkpoint_ativo[0] // 8)
            checkpoint_tile_y = int((checkpoint_ativo[1] + 8) // 8)  # Ajuste pois checkpoint_ativo está acima do tile
            if tile_x == checkpoint_tile_x and tile_y == checkpoint_tile_y:
                # Desenha um segundo brilho para checkpoint ativo
                pyxel.rectb(px-1, py-1, 10, 10, 13)  # Branco/amarelo

def update_menu():
    global selected_skin, game_state
    
    # Seleção de Personagem
    if pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_D):
        selected_skin = (selected_skin + 1) % len(PERSONAGENS)
    if pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_Q):
        selected_skin = (selected_skin - 1) % len(PERSONAGENS)
        if selected_skin < 0:
            selected_skin = len(PERSONAGENS) - 1
        
    # Confirmar personagem
    if pyxel.btnp(pyxel.KEY_SPACE):
        if selected_skin >= 0:  # Só confirma se uma skin foi escolhida
            # Envia dados para o servidor informando a escolha
            dados = {
                "id": meu_id,
                "x": player_x, "y": player_y,
                "u": sprite_liste[0], "v": sprite_liste[1],
                "skin": selected_skin
            }
            rede.enviar(dados)
            game_state = 1  # Vai para tela de aguardo

def update_aguardo():
    global game_state, jogo_pronto, total_jogadores, outros_jogadores, player_lives
    
    # Atualiza dados com o servidor para verificar status
    dados = {
        "id": meu_id,
        "x": player_x, "y": player_y,
        "u": sprite_liste[0], "v": sprite_liste[1],
        "skin": selected_skin
    }
    
    resposta = rede.enviar(dados)
    
    if resposta:
        # Atualiza lista de outros jogadores
        if "estado_jogadores" in resposta:
            outros_jogadores = resposta["estado_jogadores"]
        
        # Verifica se o jogo está pronto para começar
        if "jogo_pronto" in resposta:
            jogo_pronto = resposta["jogo_pronto"]
        
        if "total_jogadores" in resposta:
            total_jogadores = resposta["total_jogadores"]
        
        # Se o jogo estiver pronto, vai para tela de vidas
        if jogo_pronto:
            # Prepara para começar o jogo
            player_lives = 99
            resetar_itens_coletados()
            pontuacao_jogadores[meu_id] = 0
            # Inicializa pontuação dos outros jogadores
            for pid in outros_jogadores:
                if pid != meu_id:
                    pontuacao_jogadores[pid] = 0
            game_state = 2

def update_pregame():
    global game_state
    # Apenas espera confirmar para começar
    if pyxel.btnp(pyxel.KEY_SPACE):
        reset_player()
        game_state = 3  # Jogo rodando

def update_game():
    global player_x, player_y, velocity_y, on_ground, camera_x, camera_y
    global bladeliste, charge, sprite_liste, outros_jogadores, player_lives, game_state
    global pontuacao_jogadores, jogo_pronto

    # 1. Física
    sprite_liste = sprite_balance(sprite_liste)
    player_x, player_y = player_deplacement(player_x, player_y)
    player_y, velocity_y = collision_sol_precise(player_x, player_y, velocity_y)
    player_y, velocity_y = collision_sol_dur(player_x, player_y, velocity_y)
    
    on_ground = on_floor(player_x, player_y) and velocity_y == 0

    bladeliste, charge = blade_creation(player_x, player_y, bladeliste, charge) 
    bladeliste = blade_deplacement(bladeliste)
    charge = blade_reloaded(charge)

    # Pulo
    if on_ground:
        velocity_y = 0
        if pyxel.btnp(pyxel.KEY_SPACE):
            velocity_y = jump_force
            on_ground = False
    elif est_plafond(player_x, player_y - 1) and est_plafond(player_x +7, player_y -1):
        velocity_y = 2.5
    else:
        velocity_y = min(velocity_y + gravity, 8)
    
    player_y += velocity_y

    # 2. Verificar coleta de itens
    coletou, tipo_item, pos_item, pontos = verificar_coleta_itens(meu_id, player_x, player_y)
    
    # 3. Verificar checkpoint ou fim de fase
    evento, pos_checkpoint = verificar_checkpoint_fim(player_x, player_y)
    
    # 4. Rede (Envia Skin, pontuação e itens coletados)
    meus_dados = {
        "id": meu_id,
        "x": player_x, "y": player_y,
        "u": sprite_liste[0], "v": sprite_liste[1],
        "skin": selected_skin,
        "pontos": pontuacao_jogadores.get(meu_id, 0),
        "coletou": coletou,
        "tipo_item": tipo_item if coletou else None,
        "pos_item": pos_item if coletou else None,
        "evento": evento,
        "pos_checkpoint": pos_checkpoint if evento and "checkpoint" in evento else None,
        "fim_fase": True if evento == "fim_fase" else False
    }
    recebido = rede.enviar(meus_dados)
    if recebido and "estado_jogadores" in recebido: 
        outros_jogadores = recebido["estado_jogadores"]
        # Atualiza pontuações dos outros jogadores
        for pid, dados in outros_jogadores.items():
            if pid != meu_id and "pontos" in dados:
                pontuacao_jogadores[pid] = dados["pontos"]
            
            # Se outro jogador coletou um item, remove do mapa local também
            if (pid != meu_id and "coletou" in dados and 
                dados["coletou"] and "pos_item" in dados and 
                dados["pos_item"]):
                
                tile_x, tile_y = dados["pos_item"]
                pos_key = (tile_x, tile_y)
                
                # Marca como coletado localmente
                itens_coletados.add(pos_key)
                
                # Remove do mapa local
                pyxel.tilemaps[0].pset(tile_x, tile_y, TILE_VAZIO)
            
            # Se outro jogador ativou checkpoint
            if (pid != meu_id and "evento" in dados and 
                dados["evento"] and "checkpoint" in dados["evento"] and
                "pos_checkpoint" in dados and dados["pos_checkpoint"]):
                
                tile_x, tile_y = dados["pos_checkpoint"]
                pos_key = (tile_x, tile_y)
                
                # Marca checkpoint como coletado
                if pos_key not in checkpoints_coletados:
                    checkpoints_coletados.add(pos_key)
    # 5. Câmera
    screen_width, screen_height = 128, 128
    map_width = pyxel.tilemaps[0].width * 8
    
    target_cam_x = max(0, min(player_x - 64, map_width - 128))
    camera_x += (target_cam_x - camera_x) * 0.1
    
    margin = 32
    if player_y < camera_y + margin: camera_y -= (camera_y + margin - player_y) * 0.2
    elif player_y > camera_y + 128 - margin: camera_y += (player_y - (camera_y + 128 - margin)) * 0.2
    camera_y = max(0, min(camera_y, pyxel.tilemaps[0].height * 8 - 128))

    # 6. Morte / Respawn
    if player_y > 200 or pyxel.btn(pyxel.KEY_R):
        player_lives -= 1
        if player_lives <= 0:
            game_state = 4 # Game Over
        else:
            reset_player()

    if pyxel.btnp(pyxel.KEY_ESCAPE): pyxel.quit()

def update_fase_completa():
    global game_state
    # Espera confirmar para voltar ao menu
    if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_R):
        game_state = 0

# --- DRAWS POR ESTADO ---

def draw_menu():
    pyxel.cls(0)
    pyxel.text(30, 20, "SELECT CHARACTER", 7)
    
    # Desenha setas
    if pyxel.frame_count % 30 < 15:
        pyxel.text(45, 60, "<", 7)
        pyxel.text(75, 60, ">", 7)
    
    # Desenha Personagem com a Skin
    if selected_skin >= 0:
        char = PERSONAGENS[selected_skin]
        pyxel.blt(58, 56, 0, 0, char["idle_v"], 8, 8, 5)
        pyxel.text(
            64 - len(char["nome"]) * 2,
            75,
            char["nome"],
            7
        )
    else:
        pyxel.text(55, 60, "?", 7)
    
    # Informação sobre os itens
    pyxel.text(20, 90, "COLLECTIBLES:", 7)
    pyxel.text(20, 100, "P1: GOLD ONLY", 10)
    pyxel.text(20, 108, "P2: SILVER ONLY", 7)
    pyxel.text(20, 116, "P3+: BRONZE ONLY", 8)
    
    pyxel.text(35, 125, "PRESS SPACE", 10)

def draw_aguardo():
    pyxel.cls(0)
    pyxel.text(45, 20, "WAITING FOR PLAYERS", 7)
    
    # Mostra status do jogador atual
    if selected_skin >= 0:
        char = PERSONAGENS[selected_skin]
        pyxel.text(45, 35, f"YOU: {char['nome']}", 10)
        pyxel.blt(80, 30, 0, 0, char["idle_v"], 8, 8, 5)
    else:
        pyxel.text(45, 35, "YOU: NO CHARACTER", 8)
    
    # Mostra outros jogadores conectados
    pyxel.text(45, 50, "OTHER PLAYERS:", 7)
    
    y_offset = 60
    outros_count = 0
    if outros_jogadores:
        for pid, dados in outros_jogadores.items():
            if pid != meu_id:
                skin_outro = dados.get("skin", -1)
                if skin_outro >= 0 and skin_outro < len(PERSONAGENS):
                    char_nome = PERSONAGENS[skin_outro]["nome"]
                    status = "READY" if dados.get("pronto", False) else "CHOOSING..."
                else:
                    char_nome = "CHOOSING..."
                    status = "CHOOSING..."
                
                pyxel.text(45, y_offset, f"P{pid+1}: {char_nome} ({status})", 
                          10 if dados.get("pronto", False) else 8)
                y_offset += 10
                outros_count += 1
    
    if outros_count == 0:
        pyxel.text(45, 60, "No other players yet...", 8)
    
    # Mostra status de prontidão
    pyxel.text(30, 90, f"TOTAL PLAYERS: {total_jogadores}", 7)
    
    if jogo_pronto:
        pyxel.text(30, 100, "GAME READY! Starting soon...", 10)
    else:
        if total_jogadores >= 2:
            ready_count = sum(1 for pid, dados in outros_jogadores.items() 
                            if dados.get("pronto", False) and pid != meu_id)
            pyxel.text(30, 100, f"WAITING FOR {2 - (ready_count + 1)} MORE", 8)
        else:
            pyxel.text(30, 100, f"NEED {2 - total_jogadores} MORE PLAYER(S)", 8)
    
    pyxel.text(35, 115, "PRESS SPACE WHEN READY", 10 if jogo_pronto else 8)

def draw_pregame():
    pyxel.cls(0)
    # Desenha Vidas
    pyxel.text(50, 50, "READY?", 7)
    
    cor_vida = 8 # Vermelho
    pyxel.text(45, 70, f"LIVES: {player_lives}", cor_vida)
    
    # Desenha corações simples
    for i in range(min(player_lives, 10)):  # Limita a mostrar no máximo 10 vidas
        pyxel.text(45 + (i*10), 80, "v", cor_vida)
        
    if player_lives > 10:
        pyxel.text(45, 90, f"+{player_lives-10} MORE", 7)
        
    pyxel.text(35, 100, "PRESS SPACE", 10)

def draw_game_screen():
    pyxel.cls(6)
    
    # Desenha o tilemap (os itens já removidos não aparecerão)
    pyxel.bltm(0, 0, 0, camera_x , camera_y , 128, 128, 5)
    
    start_x = max(0, int(camera_x // 8) - 1)
    start_y = max(0, int(camera_y // 8) - 1)
    end_x = min(pyxel.tilemaps[0].width, int((camera_x + 128) // 8) + 1)
    end_y = min(pyxel.tilemaps[0].height, int((camera_y + 128) // 8) + 1)
    
    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            tile = pyxel.tilemaps[0].pget(x, y)
            if tile in [OURO, PRATA, BRONZE, CHECKPOINT, FIM_FASE]:
                # Para itens coletáveis, verifica se não foi coletado
                if tile in [OURO, PRATA, BRONZE] and (x, y) in itens_coletados:
                    continue
                desenhar_efeito_item(x, y, tile)
    
    # HUD de Vidas e Pontuação
    pyxel.text(2, 2, f"LIFE:{player_lives}", 8)
    if meu_id in pontuacao_jogadores:
        pyxel.text(2, 10, f"SCORE:{pontuacao_jogadores[meu_id]}", 10)
    
    # Mostra checkpoint ativo
    if checkpoint_ativo:
        pyxel.text(2, 18, "CHECKPOINT!", 11)
        # Mostra quantos checkpoints coletados
        pyxel.text(2, 26, f"CP: {len(checkpoints_coletados)}", 12)
    
    pyxel.text(100, 2, f"P{meu_id+1}", 11)
    # Mostra pontuação de outros jogadores
    y_offset = 10
    for pid, pontos in pontuacao_jogadores.items():
        if pid != meu_id:
            pyxel.text(100, y_offset, f"P{pid+1}:{pontos}", 7)
            y_offset += 8

    # Desenha Player Local
    if selected_skin >= 0:
        apply_skin(selected_skin)
        pyxel.blt(player_x - camera_x, player_y - camera_y, 0, sprite_liste[0], sprite_liste[1], 8, 8, 5)
        pyxel.pal() # Reset palette

    # Desenha Outros Jogadores
    if outros_jogadores:
        for pid, dados in outros_jogadores.items():
            if pid != meu_id:
                px, py = dados["x"], dados["y"]
                skin_remota = dados.get("skin", -1)
                
                if skin_remota >= 0:
                    apply_skin(skin_remota)
                    pyxel.blt(px - camera_x, py - camera_y, 0, dados["u"], dados["v"], 8, 8, 5)
                    pyxel.pal()
                    
                    pyxel.text(px - camera_x, py - camera_y - 6, f"P{pid+1}", 7)

    for blade in bladeliste:
        pyxel.blt(blade[0], blade[1], 0, 48, 88, 8, 8, 5)

def draw_gameover():
    pyxel.cls(0)
    pyxel.text(45, 50, "GAME OVER", 8)
    
    # Mostra pontuação final
    if meu_id in pontuacao_jogadores:
        pyxel.text(45, 60, f"SCORE: {pontuacao_jogadores[meu_id]}", 7)
    
    # Mostra checkpoints coletados
    pyxel.text(45, 70, f"CHECKPOINTS: {len(checkpoints_coletados)}", 12)
    
    pyxel.text(25, 80, "PRESS R TO RESTART", 7)
    if pyxel.btn(pyxel.KEY_R):
        global game_state
        game_state = 0 # Volta pro menu

def draw_fase_completa():
    pyxel.cls(0)
    pyxel.text(40, 40, "LEVEL COMPLETE!", 11)
    
    # Mostra pontuação final
    if meu_id in pontuacao_jogadores:
        pyxel.text(40, 50, f"SCORE: {pontuacao_jogadores[meu_id]}", 7)
        pyxel.text(40, 58, f"BONUS: +{BONUS_FIM_FASE}", 10)
        pyxel.text(40, 66, f"TOTAL: {pontuacao_jogadores[meu_id]}", 10)
    
    # Mostra estatísticas
    total_itens = len([1 for x in range(pyxel.tilemaps[0].width) 
                      for y in range(pyxel.tilemaps[0].height)
                      if pyxel.tilemaps[0].pget(x, y) in [OURO, PRATA, BRONZE]])
    itens_coletados_count = len(itens_coletados)
    pyxel.text(30, 76, f"ITEMS: {itens_coletados_count}/{total_itens}", 7)
    
    # Mostra checkpoints coletados
    total_checkpoints = len([1 for x in range(pyxel.tilemaps[0].width) 
                           for y in range(pyxel.tilemaps[0].height)
                           if pyxel.tilemaps[0].pget(x, y) == CHECKPOINT])
    
    pyxel.text(30, 84, f"CHECKPOINTS: {len(checkpoints_coletados)}/{total_checkpoints}", 12)
    
    # Calcula porcentagem de conclusão
    if total_itens > 0:
        porcentagem = (itens_coletados_count / total_itens) * 100
        pyxel.text(30, 92, f"COMPLETION: {porcentagem:.0f}%", 10 if porcentagem > 50 else 8)
    
    # Mostra mensagem baseada no desempenho
    if len(checkpoints_coletados) == total_checkpoints and itens_coletados_count == total_itens:
        pyxel.text(20, 102, "PERFECT RUN!", 10)
    elif len(checkpoints_coletados) > total_checkpoints // 2:
        pyxel.text(20, 102, "GREAT JOB!", 11)
    else:
        pyxel.text(20, 102, "GOOD EFFORT!", 7)
    
    pyxel.text(30, 115, "PRESS SPACE TO CONTINUE", 10)

def update():
    global game_state
    
    if game_state == 0:
        update_menu()
    elif game_state == 1:
        update_aguardo()
    elif game_state == 2:
        update_pregame()
    elif game_state == 3:
        update_game()
    elif game_state == 4: 
        if pyxel.btn(pyxel.KEY_R): 
            game_state = 0
    elif game_state == 5:
        update_fase_completa()

def draw():
    if game_state == 0:
        draw_menu()
    elif game_state == 1:
        draw_aguardo()
    elif game_state == 2:
        draw_pregame()
    elif game_state == 3:
        draw_game_screen()
    elif game_state == 4:
        draw_gameover()
    elif game_state == 5:
        draw_fase_completa()

pyxel.run(update, draw)