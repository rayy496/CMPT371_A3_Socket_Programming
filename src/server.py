"""
CMPT 371 A3: TCP File Transfer Server
Architecture: threaded TCP server with a simple text-header protocol.
"""

from __future__ import annotations

import os
import socket
import threading
from pathlib import Path


HOST = "127.0.0.1"
PORT = 5050
BUFFER_SIZE = 4096
STORAGE_DIR = Path(__file__).resolve().parent.parent / "server_storage"

# class based off socket to handle data transfer via bytearray
class BufferedSocket:
    """Read newline-delimited headers and exact byte payloads from one socket."""

    # initialize the object
    def __init__(self, conn: socket.socket) -> None:
        self.conn = conn
        self.buffer = bytearray()

    # handle receiving byte str from client, up to a newline
    # returns a str of the first tuple from partition(b"\n"), essentially the main server message
    # sets self.buffer with whatever comes after the newline (in practice, empty)
    def recv_line(self) -> str:
        while b"\n" not in self.buffer:
            chunk = self.conn.recv(BUFFER_SIZE)
            if not chunk:
                raise ConnectionError("Connection closed while waiting for a header.")
            self.buffer.extend(chunk)

        line, _, remainder = self.buffer.partition(b"\n")
        self.buffer = bytearray(remainder)
        return line.decode("utf-8").strip()

    # takes working dir file name and total file size
    # first writes whatever is in buffer to <working_dir>/<output_file>, 
    # then writes wtv is being received from server
    def recv_to_file(self, output_file, size: int) -> None:
        remaining = size

        if self.buffer:
            consumed = min(len(self.buffer), remaining)
            output_file.write(self.buffer[:consumed])
            del self.buffer[:consumed]
            remaining -= consumed

        while remaining > 0:
            chunk = self.conn.recv(min(BUFFER_SIZE, remaining))
            if not chunk:
                raise ConnectionError("Connection closed during file transfer.")
            output_file.write(chunk)
            remaining -= len(chunk)

    # send a message to client (e.g. for status/response)
    def send_line(self, message: str) -> None:
        self.conn.sendall(f"{message}\n".encode("utf-8"))

# helper fcn to determine valid filename
# "valid" meaning no ".", "..", or slashes to ensure user doesn't access files from elsewhere
def is_valid_filename(filename: str) -> bool:
    if not filename or filename in {".", ".."}:
        return False
    if "/" in filename or "\\" in filename:
        return False
    return os.path.basename(filename) == filename

# helper fcn to get server_storage filepath
# builds a path object as a possible destination for a new file
def safe_storage_path(filename: str) -> Path:
    return STORAGE_DIR / filename

# list command
# first, retrieves all files in server_storage, appends to array
# then, sends line with total # of files
# then, sends a line for each file with its name and size
def handle_list(buffered: BufferedSocket) -> None:
    files = []
    for path in sorted(STORAGE_DIR.iterdir()):
        if path.is_file():
            files.append((path.name, path.stat().st_size))

    buffered.send_line(f"OK {len(files)}")
    for name, size in files:
        buffered.send_line(f"FILE {name} {size}")
    buffered.send_line("END")

# upload command
# gets filename and file size from client
# sets up intended + temp destinations
# writes data received from to temp destination first, then replaces file with intended dest
# if error is encountered during writing, delete the file at temp dest
# finally, send status msg to client
def handle_upload(buffered: BufferedSocket, parts: list[str]) -> None:
    if len(parts) != 3:
        buffered.send_line("ERROR Usage: UPLOAD <filename> <size>")
        return

    _, filename, size_text = parts
    if not is_valid_filename(filename):
        buffered.send_line("ERROR Invalid filename.")
        return

    try:
        size = int(size_text)
    except ValueError:
        buffered.send_line("ERROR File size must be an integer.")
        return

    if size < 0:
        buffered.send_line("ERROR File size must be non-negative.")
        return

    destination = safe_storage_path(filename)
    temp_destination = destination.with_name(f".{filename}.part-{threading.get_ident()}")
    buffered.send_line("READY")
    try:
        with temp_destination.open("wb") as output_file:
            buffered.recv_to_file(output_file, size)
        temp_destination.replace(destination)
    except Exception:
        if temp_destination.exists():
            temp_destination.unlink()
        raise

    buffered.send_line(f"OK Uploaded {filename} ({size} bytes)")

# download command
# get filename from client command
# retrieve path object using filename (i.e. <working_dir>/server_storage/<filename>)
# get file size using path object
# read file using path object (i.e. from <working_dir>/server_storage/<filename>)
# send all data from file to client
def handle_download(buffered: BufferedSocket, parts: list[str]) -> None:
    if len(parts) != 2:
        buffered.send_line("ERROR Usage: DOWNLOAD <filename>")
        return

    _, filename = parts
    if not is_valid_filename(filename):
        buffered.send_line("ERROR Invalid filename.")
        return

    source = safe_storage_path(filename)
    if not source.is_file():
        buffered.send_line("ERROR File not found.")
        return

    size = source.stat().st_size
    buffered.send_line(f"FILE {filename} {size}")
    with source.open("rb") as input_file:
        while True:
            chunk = input_file.read(BUFFER_SIZE)
            if not chunk:
                break
            buffered.conn.sendall(chunk)

# delete command
# gets filename from user command
# makes target path object (i.e. <working_dir>/server_storage/<filename>)
# removes target using unlink()
# sends response to client
def handle_delete(buffered: BufferedSocket, parts: list[str]) -> None:
    if len(parts) != 2:
        buffered.send_line("ERROR Usage: DELETE <filename>")
        return

    _, filename = parts
    if not is_valid_filename(filename):
        buffered.send_line("ERROR Invalid filename.")
        return

    target = safe_storage_path(filename)
    if not target.is_file():
        buffered.send_line("ERROR File not found.")
        return

    target.unlink()
    buffered.send_line(f"OK Deleted {filename}")

# handle the client and their commands
# first, opens socket using BufferedSocket class, prints status msg on connection
# then, handles input received from socket
def handle_client(conn: socket.socket, addr: tuple[str, int]) -> None:
    buffered = BufferedSocket(conn)
    print(f"[CONNECT] Client connected from {addr[0]}:{addr[1]}")

    try:
        while True:
            header = buffered.recv_line()
            if not header:
                buffered.send_line("ERROR Empty command.")
                continue

            parts = header.split()
            command = parts[0].upper()

            # handle user commands
            # inform user if command is unsupported
            # if "QUIT", close connection to client and print status msg
            if command == "LIST":
                handle_list(buffered)
            elif command == "UPLOAD":
                handle_upload(buffered, parts)
            elif command == "DOWNLOAD":
                handle_download(buffered, parts)
            elif command == "DELETE":
                handle_delete(buffered, parts)
            elif command == "QUIT":
                buffered.send_line("OK Goodbye.")
                break
            else:
                buffered.send_line("ERROR Unsupported command.")
    except ConnectionError as exc:
        print(f"[DISCONNECT] {addr[0]}:{addr[1]} disconnected: {exc}")
    except OSError as exc:
        print(f"[ERROR] Client {addr[0]}:{addr[1]}: {exc}")
    finally:
        conn.close()
        print(f"[CLOSED] Connection closed for {addr[0]}:{addr[1]}")

# start the server
# creates server_storage directory if not already existing
# <working_dir>/server_storage
# starts a worker thread for each client connection
def start_server() -> None:
    STORAGE_DIR.mkdir(exist_ok=True)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[STARTING] File server listening on {HOST}:{PORT}")
    print(f"[STORAGE] Serving files from {STORAGE_DIR}")

    try:
        while True:
            conn, addr = server.accept()
            worker = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            worker.start()
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Server closing...")
    finally:
        server.close()


if __name__ == "__main__":
    start_server()
