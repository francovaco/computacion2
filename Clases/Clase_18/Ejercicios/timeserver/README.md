# UDP Time Server

Servidor y cliente UDP en Docker que devuelve la hora actual del servidor.

## Descripción

- **Servidor UDP**: Escucha en el puerto 9876 y responde con la hora actual cuando recibe el mensaje "time"
- **Cliente UDP**: Se conecta al servidor y solicita la hora automáticamente

## Estructura

```
.
├── server.py
├── client.py
├── Dockerfile.server
├── Dockerfile.client
└── docker-compose.yml
```

## Uso

### Iniciar servicios

```bash
docker-compose up --build
```

### Probar desde el host

```bash
echo "time" | nc -u localhost 9876
```

### Ver logs

```bash
# Servidor
docker logs udp-time-server

# Cliente
docker logs udp-time-client
```

### Detener servicios

```bash
docker-compose down
```

## Respuestas

- **Comando válido**: `time` → Devuelve: `2024-09-30 14:30:45`
- **Comando inválido**: `otro` → Devuelve: `Error: Invalid command 'otro'. Use 'time' to get current time.`