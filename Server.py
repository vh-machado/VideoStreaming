import sys
import socket
from ServerWorker import ServerWorker

class Server:
    
    def main(self):
        try:
            SERVER_PORT = int(sys.argv[1])
        except:
            print("[Usage: Server.py Server_port]\n")
            sys.exit(1)  # Exit if no port is provided
        
        rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        rtspSocket.bind(('', SERVER_PORT))
        rtspSocket.listen(5)        

        print(f"Servidor RTSP iniciado e ouvindo na porta {SERVER_PORT}...")

        # Receive client info (address, port) through RTSP/TCP session
        while True:
            connSocket, clientAddr = rtspSocket.accept()  # Desempacota a tupla (connSocket, clientAddr)
            print(f"Conexão recebida de {clientAddr}")
            
            # Passa a tupla para o ServerWorker
            clientInfo = {}
            clientInfo['rtspSocket'] = (connSocket, clientAddr)  # Tupla (connSocket, clientAddr)
            
            # Cria e executa o ServerWorker
            ServerWorker(clientInfo).run()

if __name__ == "__main__":
    (Server()).main()



