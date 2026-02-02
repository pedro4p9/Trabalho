import socket
import pickle

class ClienteRede:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ip = input("IP do servidor: ")
        self.addr = (ip, 5555)
        self.sock.settimeout(2)

        # Registro inicial
        self.sock.sendto(pickle.dumps([0, False]), self.addr)
        try:
            data, _ = self.sock.recvfrom(2048)
            resposta = pickle.loads(data)
            self.player_id = resposta["player_id"]
            print(f"[CONECTADO] Jogador {self.player_id + 1}")
        except:
            print("Não foi possível conectar ao servidor.")
            exit()

    def enviar(self, dados):
        try:
            self.sock.sendto(pickle.dumps(dados), self.addr)
            data, _ = self.sock.recvfrom(2048)
            return pickle.loads(data)
        except:
            return None