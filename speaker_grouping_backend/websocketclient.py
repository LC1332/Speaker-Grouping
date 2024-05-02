import websocket
import configparser



def create_connection():
    # Replace 'your_ip' and 'your_port' with your server's IP and port
    config = configparser.ConfigParser()
    config.read('config.ini')
    server_ip = config['DEFAULT']['ServerIP']
    server_port = config['DEFAULT']['ServerPort']
    ws = 0
    ws_url = f"ws://{server_ip}:{server_port}/ws"
    print(ws_url)
    try:
        ws = websocket.create_connection(ws_url)
        print("Connected to the server")
        # You can now send and receive messages using ws.send() and ws.recv()
    except Exception as e:
        print("Failed to connect to the server:", e)
    return ws

