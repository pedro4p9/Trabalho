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
        self.ip_local = get_local_ip()
        self.porta = 5555
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", self.porta))
        
        print("-" * 30)
        print(f"[SERVIDOR] Online!")
        print(f"[IP PARA CONECTAR] {self.ip_local}")
        print(f"[PORTA] {self.porta}")
        print("-" * 30)

    def handle_clients(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(2048)
                conteudo = pickle.loads(data)

                # Novo Jogador (Handshake)
                if isinstance(conteudo, list):
                    pid = len(self.jogadores)
                    self.jogadores[pid] = {"x": 60, "y": 60, "u": 0, "v": 0, "skin": 0, "addr": addr}
                    print(f"[CONEXÃO] Player {pid+1} vindo de {addr}")
                    self.sock.sendto(pickle.dumps({"player_id": pid}), addr)
                    continue
                
                # Atualização de Dados
                if isinstance(conteudo, dict) and "id" in conteudo:
                    pid = conteudo["id"]
                    if pid in self.jogadores:
                        self.jogadores[pid].update({
                            "x": conteudo["x"], "y": conteudo["y"],
                            "u": conteudo["u"], "v": conteudo["v"],
                            "skin": conteudo.get("skin", 0)
                        })

                    # Envia o estado de todos os outros para o cliente
                    # Filtramos o 'addr' para não enviar dados sensíveis/desnecessários
                    estado_compacto = {k: {i: v[i] for i in v if i != 'addr'} for k, v in self.jogadores.items()}
                    self.sock.sendto(pickle.dumps(estado_compacto), addr)

            except Exception as e:
                print(f"Erro no processamento: {e}")

    def iniciar(self):
        t = threading.Thread(target=self.handle_clients, daemon=True)
        t.start()
        # Mantém o programa vivo
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            print("\nEncerrando servidor...")

if __name__ == "__main__":
    ServidorPlatformer().iniciar()