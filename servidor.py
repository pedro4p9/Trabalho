import socket, threading, pickle, time

def get_local_ip():
    """Tenta descobrir o IP da máquina na rede local"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Não precisa estar conectado de verdade para pegar o IP da interface
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

class ServidorPlatformer:
    def __init__(self):
        self.jogadores = {} 
        self.jogadores_prontos = {}  # Dicionário para rastrear jogadores prontos
        self.ip_local = get_local_ip()
        self.porta = 5555
        
        # Criar socket UDP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Usar SO_REUSEADDR para evitar problemas de porta em uso
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Vincular a todas as interfaces
        self.sock.bind(("0.0.0.0", self.porta))
        
        print("-" * 50)
        print(f"[SERVIDOR] Online!")
        print(f"[IP LOCAL] {self.ip_local}")
        print(f"[PORTA] {self.porta}")
        print("-" * 50)
        print(f"[INSTRUÇÕES]")
        print(f"1. Anote o IP acima: {self.ip_local}")
        print(f"2. Em outros computadores, use este IP para conectar")
        print("-" * 50)

    def handle_clients(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(2048)
                conteudo = pickle.loads(data)

                # Novo Jogador (Handshake)
                if isinstance(conteudo, list):
                    pid = len(self.jogadores)
                    self.jogadores[pid] = {
                        "x": 60, "y": 60, "u": 0, "v": 0, 
                        "skin": -1, "addr": addr, "pronto": False,
                        "pontos": 0
                    }
                    self.jogadores_prontos[pid] = False
                    print(f"[CONEXÃO] Player {pid+1} conectado de {addr}")
                    self.sock.sendto(pickle.dumps({"player_id": pid}), addr)
                    continue
                
                # Atualização de Dados
                if isinstance(conteudo, dict) and "id" in conteudo:
                    pid = conteudo["id"]
                    if pid in self.jogadores:
                        # Atualiza endereço (pode ter mudado com NAT)
                        self.jogadores[pid]["addr"] = addr
                        
                        # Atualiza dados do jogador
                        self.jogadores[pid].update({
                            "x": conteudo["x"], "y": conteudo["y"],
                            "u": conteudo["u"], "v": conteudo["v"],
                            "skin": conteudo.get("skin", -1),
                            "pontos": conteudo.get("pontos", 0)
                        })
                        
                        # Marca como pronto se tiver skin escolhida
                        if conteudo.get("skin", -1) >= 0:
                            self.jogadores[pid]["pronto"] = True
                            self.jogadores_prontos[pid] = True
                        else:
                            self.jogadores[pid]["pronto"] = False
                            self.jogadores_prontos[pid] = False

                    # Prepara resposta com estado de todos os jogadores
                    estado_compacto = {}
                    for k, v in self.jogadores.items():
                        estado_compacto[k] = {
                            "x": v["x"], "y": v["y"],
                            "u": v["u"], "v": v["v"],
                            "skin": v["skin"],
                            "pronto": v["pronto"],
                            "pontos": v["pontos"]
                        }
                    
                    # Adiciona flag global de jogo pronto
                    todos_prontos = all(self.jogadores_prontos.values()) and len(self.jogadores) >= 2
                    resposta = {
                        "estado_jogadores": estado_compacto,
                        "jogo_pronto": todos_prontos,
                        "total_jogadores": len(self.jogadores)
                    }
                    
                    self.sock.sendto(pickle.dumps(resposta), addr)

            except Exception as e:
                print(f"Erro no processamento: {e}")

    def iniciar(self):
        print(f"[SERVIDOR] Aguardando conexões na porta {self.porta}...")
        print(f"[SERVIDOR] Pressione Ctrl+C para encerrar")
        
        t = threading.Thread(target=self.handle_clients, daemon=True)
        t.start()
        
        # Mantém o programa vivo
        try:
            while True: 
                # Mostra status periodicamente
                print(f"\r[Jogadores conectados: {len(self.jogadores)} | Prontos: {sum(self.jogadores_prontos.values())}]", end="")
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n\n[SERVIDOR] Encerrando...")
            print(f"[SERVIDOR] {len(self.jogadores)} jogadores desconectados")

if __name__ == "__main__":
    ServidorPlatformer().iniciar()