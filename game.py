import pyxel
try:
    from cliente import ClienteRede
except ImportError:
    print("Aviso: arquivo cliente.py não encontrado.")
    ClienteRede = None

pyxel.init(128, 128, title="Super Jump Online", fps=30)
pyxel.load("main.pyxres")

# --- REDE ---
print("Conectando ao servidor...")
rede = None
meu_id = 0
outros_jogadores = {}

if ClienteRede:
    try:
        rede = ClienteRede()
        meu_id = rede.player_id
    except:
        print("Falha ao conectar. Jogando em modo Offline.")

# --- ESTADOS DO JOGO ---
# 0: Menu Seleção Personagem
# 1: Tela de Vidas
# 2: Jogo Rodando
# 3: Game Over
game_state = 0
player_lives = 3
selected_skin = 0  # 0: Normal, 1: Vermelho, 2: Verde

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

# Tiles e Mapas (Mantido original)
BLOC_JAUNE = (10,20); PETITE_PLANCHE = (0,26)
LONGUE_PLANCHE_R = (3,26); LONGUE_PLANCHE = (2,26); LONGUE_PLANCHE_L = (1,26)
tiles_sol_dur = [BLOC_JAUNE, PETITE_PLANCHE,LONGUE_PLANCHE,LONGUE_PLANCHE_L,LONGUE_PLANCHE_R]

SOL_HERBE_L = (10, 27); SOL_HERBE = (11, 27); SOL_HERBE_R = (12, 27)
SOL_BOIS_L = (1, 27); SOL_BOIS = (2, 27); SOL_BOIS_R = (3, 27) 
PLANCHE_L = (1, 25); PLANCHE = (2, 25); PLANCHE_R = (3, 25)
tiles_sol = [SOL_HERBE_L, SOL_HERBE, SOL_HERBE_R, SOL_BOIS_L, SOL_BOIS, SOL_BOIS_R, PLANCHE_L, PLANCHE, PLANCHE_R]

TERRE_L = (10,28); TERRE_L_DOWN = (10,29)
TERRE_CENTER = (11,28); TERRE_CENTER_DOWN = (11,29)
TERRE_R = (12,28); TERRE_R_DOWN = (12,29)
tiles_mur = [TERRE_L,TERRE_L_DOWN, TERRE_CENTER,TERRE_CENTER_DOWN, TERRE_R,TERRE_R_DOWN, BLOC_JAUNE, PETITE_PLANCHE, LONGUE_PLANCHE_R,LONGUE_PLANCHE,LONGUE_PLANCHE_L]
tiles_plafond = [TERRE_CENTER_DOWN,TERRE_L_DOWN,TERRE_R_DOWN, BLOC_JAUNE, PETITE_PLANCHE, LONGUE_PLANCHE_L,LONGUE_PLANCHE,LONGUE_PLANCHE_R]

# --- FUNÇÃO AUXILIAR DE SKIN ---
def apply_skin(skin_id):
    """Troca as cores baseadas na escolha"""
    pyxel.pal() # Reset
    if skin_id == 1: # Vermelho (Troca azul/ciano por vermelho/rosa)
        pyxel.pal(1, 8)
        pyxel.pal(5, 2)
        pyxel.pal(6, 9)
        pyxel.pal(12, 8)
    elif skin_id == 2: # Verde (Troca azul por verde)
        pyxel.pal(1, 3)
        pyxel.pal(5, 11)
        pyxel.pal(6, 3)
        pyxel.pal(12, 11)

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
    # Lógica simplificada de animação
    moving = False
    if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
        sl[1] = 16
        sl[0] += 8
        moving = True
    elif pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_Q):
        sl[1] = 24
        sl[0] += 8
        moving = True
    
    if moving and (sl[0] == 40 or sl[0] == 0): sl[0] = 0
    if not moving: sl[0] = 0 # Idle frame
    
    return sl

def reset_player():
    global player_x, player_y, velocity_y
    player_x = 10
    player_y = 56
    velocity_y = 0

# --- UPDATES POR ESTADO ---

def update_menu():
    global selected_skin, game_state, player_lives
    
    # Seleção de Personagem
    if pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_D):
        selected_skin = (selected_skin + 1) % 3
    if pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_Q):
        selected_skin = (selected_skin - 1) % 3
        
    # Confirmar
    if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A):
        player_lives = 3 # Reseta vidas
        game_state = 1   # Vai para tela de vidas

def update_pregame():
    global game_state
    # Apenas espera confirmar para começar
    if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A):
        reset_player()
        game_state = 2

def update_game():
    global player_x, player_y, velocity_y, on_ground, camera_x, camera_y
    global bladeliste, charge, sprite_liste, outros_jogadores, player_lives, game_state

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
        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_A):
            velocity_y = jump_force
            on_ground = False
    elif est_plafond(player_x, player_y - 1) and est_plafond(player_x +7, player_y -1):
        velocity_y = 2.5
    else:
        velocity_y = min(velocity_y + gravity, 8)
    
    player_y += velocity_y

    # 2. Rede (Envia Skin junto)
    if rede:
        meus_dados = {
            "id": meu_id,
            "x": player_x, "y": player_y,
            "u": sprite_liste[0], "v": sprite_liste[1],
            "skin": selected_skin # <--- ENVIA A COR ESCOLHIDA
        }
        recebido = rede.enviar(meus_dados)
        if recebido: outros_jogadores = recebido

    # 3. Câmera
    screen_width, screen_height = 128, 128
    map_width = pyxel.tilemaps[0].width * 8
    
    target_cam_x = max(0, min(player_x - 64, map_width - 128))
    camera_x += (target_cam_x - camera_x) * 0.1
    
    margin = 32
    if player_y < camera_y + margin: camera_y -= (camera_y + margin - player_y) * 0.2
    elif player_y > camera_y + 128 - margin: camera_y += (player_y - (camera_y + 128 - margin)) * 0.2
    camera_y = max(0, min(camera_y, pyxel.tilemaps[0].height * 8 - 128))

    # 4. Morte / Respawn
    if player_y > 200 or pyxel.btn(pyxel.KEY_R):
        player_lives -= 1
        if player_lives <= 0:
            game_state = 3 # Game Over
        else:
            reset_player()

    if pyxel.btnp(pyxel.KEY_ESCAPE): pyxel.quit()

# --- DRAWS POR ESTADO ---

def draw_menu():
    pyxel.cls(0)
    pyxel.text(30, 20, "SELECT CHARACTER", 7)
    
    # Desenha setas
    if pyxel.frame_count % 30 < 15:
        pyxel.text(45, 60, "<", 7)
        pyxel.text(75, 60, ">", 7)
    
    # Desenha Personagem com a Skin
    apply_skin(selected_skin)
    pyxel.blt(58, 56, 0, 0, 16, 8, 8, 5) # Desenha parado
    pyxel.pal() # Reset
    
    # Nome da Skin
    nomes = ["CLASSIC", "RED HOT", "FOREST"]
    pyxel.text(64 - len(nomes[selected_skin])*2, 75, nomes[selected_skin], 7)
    
    pyxel.text(35, 100, "PRESS SPACE", 10)

def draw_pregame():
    pyxel.cls(0)
    # Desenha Vidas
    pyxel.text(50, 50, "READY?", 7)
    
    cor_vida = 8 # Vermelho
    pyxel.text(45, 70, f"LIVES: {player_lives}", cor_vida)
    
    # Desenha corações simples
    for i in range(player_lives):
        pyxel.text(45 + (i*10), 80, "v", cor_vida)
        
    pyxel.text(35, 100, "PRESS SPACE", 10)

def draw_game_screen():
    pyxel.cls(6)
    pyxel.bltm(0, 0, 0, camera_x , camera_y , 128, 128, 5)
    
    # HUD de Vidas no canto da tela
    pyxel.text(2, 2, f"LIFE:{player_lives}", 8)
    if rede: pyxel.text(100, 2, f"P{meu_id+1}", 11)

    # Desenha Player Local
    apply_skin(selected_skin)
    pyxel.blt(player_x - camera_x, player_y - camera_y, 0, sprite_liste[0], sprite_liste[1], 8, 8, 5)
    pyxel.pal() # Reset palette

    # Desenha Outros Jogadores
    if rede and outros_jogadores:
        for pid, dados in outros_jogadores.items():
            if pid != meu_id:
                px, py = dados["x"], dados["y"]
                skin_remota = dados.get("skin", 0)
                
                apply_skin(skin_remota) # Aplica a cor do amigo
                pyxel.blt(px - camera_x, py - camera_y, 0, dados["u"], dados["v"], 8, 8, 5)
                pyxel.pal() # Reset
                
                pyxel.text(px - camera_x, py - camera_y - 6, f"P{pid+1}", 7)

    for blade in bladeliste:
        pyxel.blt(blade[0],blade[1],0,48,88,8,8,5) 

def draw_gameover():
    pyxel.cls(0)
    pyxel.text(45, 50, "GAME OVER", 8)
    pyxel.text(25, 70, "PRESS R TO RESTART", 7)
    if pyxel.btn(pyxel.KEY_R):
        global game_state
        game_state = 0 # Volta pro menu

# --- MAIN LOOPS ---

def update():
    # Declaramos o global logo no início da função para evitar o SyntaxError
    global game_state
    
    if game_state == 0:
        update_menu()
    elif game_state == 1:
        update_pregame()
    elif game_state == 2:
        update_game()
    elif game_state == 3: 
        # Se estiver em Game Over, espera o R para voltar ao menu
        if pyxel.btn(pyxel.KEY_R): 
            game_state = 0

def draw():
    # O draw apenas lê o game_state, então não precisa obrigatoriamente de global,
    # mas é boa prática manter a consistência.
    if game_state == 0:
        draw_menu()
    elif game_state == 1:
        draw_pregame()
    elif game_state == 2:
        draw_game_screen()
    elif game_state == 3:
        draw_gameover()

pyxel.run(update, draw)