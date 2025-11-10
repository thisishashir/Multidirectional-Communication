import socket
import threading
import os
from tkinter import Tk, filedialog

# ===================== File Sending Function =====================
def send_file(conn):
    Tk().withdraw()
    file_path = filedialog.askopenfilename(title="Select file to send")
    if not file_path:
        print("No file selected.")
        return

    filename = os.path.basename(file_path)
    name_bytes = filename.encode()

    # Send filename length + filename
    conn.send(len(name_bytes).to_bytes(2, "big"))
    conn.send(name_bytes)

    # Send file data
    with open(file_path, "rb") as f:
        conn.sendall(f.read())

    print(f"\n✅ File '{filename}' sent successfully!")

# ===================== File Receiving Function =====================
def receive_file(conn, stop_event):
    try:
        while not stop_event.is_set():
            name_len_bytes = conn.recv(2)
            if not name_len_bytes:
                break
            name_len = int.from_bytes(name_len_bytes, "big")
            filename = conn.recv(name_len).decode()

            with open("received_" + filename, "wb") as f:
                while True:
                    data = conn.recv(4096)
                    if not data:
                        break
                    f.write(data)
                    if len(data) < 4096:
                        break
            print(f"\n📥 File '{filename}' received successfully!")

    # Handle connection closed from remote side
    except ConnectionResetError:
        print("\n🔴 Connection closed by the other side.")
    # Handle connection closed locally (WinError 10053)
    except OSError as e:
        if e.errno == 10053:
            print("\n🟡 Connection closed locally.")
        elif e.errno == 10054:
            print("\n🔴 Connection closed by the other side.")
        else:
            print("⚠️ Connection interrupted.")
    except Exception:
        print("⚠️ Connection ended unexpectedly.")

# ===================== Server Function =====================
def start_server():
    host = input("Enter your IP address (for example 127.0.0.1): ")
    port = int(input("Enter port (e.g. 5000): "))
    s = socket.socket()
    s.bind((host, port))
    s.listen(1)
    print("🟢 Waiting for connection...")

    conn, addr = s.accept()
    print(f"🔗 Connected to {addr}")

    stop_event = threading.Event()
    receiver_thread = threading.Thread(target=receive_file, args=(conn, stop_event))
    receiver_thread.start()

    while True:
        cmd = input("Type 'send' to send a file or 'exit' to quit: ").lower()
        if cmd == "send":
            send_file(conn)
        elif cmd == "exit":
            stop_event.set()
            conn.close()
            receiver_thread.join()
            print("\n🔵 Connection closed. Server stopped.")
            break

# ===================== Client Function =====================
def connect_to_peer():
    host = input("Enter peer IP address: ")
    port = int(input("Enter port: "))
    s = socket.socket()
    s.connect((host, port))
    print("🔗 Connected to peer!")

    stop_event = threading.Event()
    receiver_thread = threading.Thread(target=receive_file, args=(s, stop_event))
    receiver_thread.start()

    while True:
        cmd = input("Type 'send' to send a file or 'exit' to quit: ").lower()
        if cmd == "send":
            send_file(s)
        elif cmd == "exit":
            stop_event.set()
            s.close()
            receiver_thread.join()
            print("\n🟢 Connection closed. Client disconnected.")
            break

# ===================== Main Menu =====================
print("=== 🌐 Multidirectional File Transfer System ===")
choice = input("1. Start as Server\n2. Connect to Peer\nChoose option (1/2): ")

if choice == "1":
    start_server()
else:
    connect_to_peer()
