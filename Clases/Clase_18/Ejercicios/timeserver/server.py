import socketserver
import time

class TimeUDPHandler(socketserver.BaseRequestHandler):
    """
    Handler UDP que responde con la hora actual cuando recibe 'time'.
    En UDP, self.request es una tupla (data, socket).
    """
    
    def handle(self):
        """
        Maneja cada datagrama UDP recibido.
        """
        # Extraer datos y socket de la tupla
        data, socket = self.request
        
        # Decodificar el mensaje del cliente
        message = data.decode('utf-8').strip()
        print(f"UDP from {self.client_address}: {message}")
        
        # Verificar si el mensaje es 'time'
        if message.lower() == 'time':
            # Preparar respuesta con la hora actual
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            response = current_time
            print(f"Sending time to {self.client_address}: {response}")
        else:
            # Mensaje de error si no es 'time'
            response = f"Error: Invalid command '{message}'. Use 'time' to get current time."
            print(f"Invalid command from {self.client_address}: {message}")
        
        # Enviar respuesta al cliente específico
        socket.sendto(response.encode('utf-8'), self.client_address)


class CustomUDPServer(socketserver.UDPServer):
    """
    Servidor UDP personalizado con configuraciones específicas.
    """
    
    def __init__(self, server_address, RequestHandlerClass):
        # Permitir reutilización de direcciones
        self.allow_reuse_address = True
        super().__init__(server_address, RequestHandlerClass)
        
    def server_bind(self):
        """Override para mostrar información de binding"""
        super().server_bind()
        print(f"UDP Server bound to {self.server_address}")


if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 9876  # Escuchar en todas las interfaces
    
    # Crear servidor UDP personalizado
    with CustomUDPServer((HOST, PORT), TimeUDPHandler) as server:
        print(f"UDP Time Server started on port {PORT}")
        print("Waiting for 'time' requests...")
        print("Send 'time' to get current server time")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nUDP Server stopped")