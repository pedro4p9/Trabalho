import socket, threading, pickle, time

class ServidorPlatformer:
    def __init__(self):
        # Agora guardamos também a 'skin' (cor) do jogador
        self.jogadores = {} 
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", 5555))
        print("[SERVIDOR] Online - Super Jump Multiplayer")

    def handle_clients(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(2048)
                
                try:
                    conteudo = pickle.loads(data)
                except:
                    continue

                # Conexão inicial
                if isinstance(conteudo, list) and len(conteudo) == 2:
                    pid = len(self.jogadores)
                    # Padrão: skin 0
                    self.jogadores[pid] = {"x": 60, "y": 60, "u": 0, "v": 0, "skin": 0, "addr": addr}
                    print(f"[NOVO JOGADOR] ID: {pid} - {addr}")
                    self.sock.sendto(pickle.dumps({"player_id": pid}), addr)
                    continue
                
                # Atualização de posição e estado
                if isinstance(conteudo, dict) and "id" in conteudo:
                    pid = conteudo["id"]
                    
                    if pid in self.jogadores:
                        self.jogadores[pid]["x"] = conteudo["x"]
                        self.jogadores[pid]["y"] = conteudo["y"]
                        self.jogadores[pid]["u"] = conteudo["u"]
                        self.jogadores[pid]["v"] = conteudo["v"]
                        # Recebe a skin escolhida pelo cliente
                        self.jogadores[pid]["skin"] = conteudo.get("skin", 0)
                        self.jogadores[pid]["addr"] = addr

                    # Envia estado de todos (sem o IP para economizar bytes)
                    estado_limpo = {k: {key: v[key] for key in v if key != "addr"} for k, v in self.jogadores.items()}
                    self.sock.sendto(pickle.dumps(estado_limpo), addr)

            except Exception as e:
                print(f"Erro: {e}")
                continue

    def iniciar(self):
        threading.Thread(target=self.handle_clients, daemon=True).start()
        while True:
            time.sleep(1)

if __name__ == "__main__":
    ServidorPlatformer().iniciar()