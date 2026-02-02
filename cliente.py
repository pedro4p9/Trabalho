import socket
import pickle

class ClienteRede:
    def __init__(self, server_ip=None):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(5)  # Timeout de 5 segundos
        
        if server_ip is None:
            # Tenta descobrir automaticamente o servidor na rede local
            server_ip = self.descobrir_servidor()
            if server_ip is None:
                # Se não encontrar, pede manualmente
                server_ip = input("IP do servidor (ex: 192.168.1.100): ")
        
        self.addr = (server_ip, 5555)
        
        # Registro inicial
        print(f"[CLIENTE] Conectando ao servidor {server_ip}:5555...")
        self.sock.sendto(pickle.dumps([0, False]), self.addr)
        
        try:
            data, _ = self.sock.recvfrom(2048)
            resposta = pickle.loads(data)
            self.player_id = resposta["player_id"]
            print(f"[CLIENTE] Conectado como Jogador {self.player_id + 1}")
        except socket.timeout:
            print("[ERRO] Timeout: Servidor não respondeu.")
            print("Verifique:")
            print("1. O servidor está rodando?")
            print("2. O IP está correto?")
            print("3. Firewall permite conexões na porta 5555?")
            exit()
        except Exception as e:
            print(f"[ERRO] Não foi possível conectar ao servidor: {e}")
            exit()

    def descobrir_servidor(self):
        """Tenta descobrir automaticamente o servidor na rede local"""
        # Esta é uma implementação simples - você pode expandir isso
        # Para um sistema real, você pode usar broadcast ou zeroconf
        print("[CLIENTE] Tentando descobrir servidor na rede...")
        
        # Lista de IPs comuns em redes locais
        ips_comuns = []
        base_ip = self.get_my_ip_base()
        
        if base_ip:
            for i in range(1, 255):
                ips_comuns.append(f"{base_ip}.{i}")
        
        # Adiciona localhost caso esteja testando localmente
        ips_comuns.append("127.0.0.1")
        
        for ip in ips_comuns[:20]:  # Testa apenas os primeiros 20
            try:
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                test_sock.settimeout(0.5)
                test_sock.sendto(pickle.dumps([0, False]), (ip, 5555))
                data, _ = test_sock.recvfrom(2048)
                test_sock.close()
                print(f"[CLIENTE] Servidor encontrado em: {ip}")
                return ip
            except:
                pass
        
        print("[CLIENTE] Nenhum servidor encontrado automaticamente")
        return None
    
    def get_my_ip_base(self):
        """Obtém a base do IP da rede local"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 1))
            ip = s.getsockname()[0]
            s.close()
            # Retorna os primeiros 3 octetos (ex: 192.168.1)
            return ".".join(ip.split(".")[:3])
        except:
            return None

    def enviar(self, dados):
        try:
            self.sock.sendto(pickle.dumps(dados), self.addr)
            data, _ = self.sock.recvfrom(2048)
            return pickle.loads(data)
        except socket.timeout:
            print("[ERRO] Timeout na comunicação com servidor")
            return None
        except Exception as e:
            print(f"[ERRO] Erro na comunicação: {e}")
            return None