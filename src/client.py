"""
CMPT 371 A3: TCP File Transfer Client
Architecture: CLI client for a threaded TCP file transfer server.
"""

from __future__ import annotations

import shlex
import socket
from pathlib import Path


HOST = "127.0.0.1"
PORT = 5050
BUFFER_SIZE = 4096


class BufferedSocket:
    """Read newline-delimited headers and exact byte payloads from one socket."""

    def __init__(self, conn: socket.socket) -> None:
        self.conn = conn
        self.buffer = bytearray()

    def recv_line(self) -> str:
        while b"\n" not in self.buffer:
            chunk = self.conn.recv(BUFFER_SIZE)
            if not chunk:
                raise ConnectionError("Connection closed while waiting for a header.")
            self.buffer.extend(chunk)

        line, _, remainder = self.buffer.partition(b"\n")
        self.buffer = bytearray(remainder)
        return line.decode("utf-8").strip()

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

    def send_line(self, message: str) -> None:
        self.conn.sendall(f"{message}\n".encode("utf-8"))


def print_help() -> None:
    print("Commands:")
    print("  list")
    print("  upload <local_path>")
    print("  download <remote_filename> <local_path>")
    print("  delete <remote_filename>")
    print("  quit")


def handle_list(buffered: BufferedSocket) -> None:
    buffered.send_line("LIST")
    status = buffered.recv_line()
    if not status.startswith("OK "):
        print(status)
        return

    try:
        count = int(status.split()[1])
    except (IndexError, ValueError):
        print("ERROR Invalid server response.")
        return

    if count == 0:
        print("No files available on the server.")
    else:
        print("Files on server:")

    while True:
        line = buffered.recv_line()
        if line == "END":
            break
        if line.startswith("FILE "):
            _, filename, size_text = line.split(maxsplit=2)
            print(f"  {filename} ({size_text} bytes)")
        else:
            print(f"Unexpected response: {line}")
            break


def handle_upload(buffered: BufferedSocket, local_path_text: str) -> None:
    local_path = Path(local_path_text).expanduser()
    if not local_path.is_file():
        print("Local file not found.")
        return

    filename = local_path.name
    if "/" in filename or "\\" in filename or filename in {".", ".."}:
        print("Local filename is not valid for upload.")
        return

    size = local_path.stat().st_size
    buffered.send_line(f"UPLOAD {filename} {size}")
    response = buffered.recv_line()
    if response != "READY":
        print(response)
        return

    with local_path.open("rb") as input_file:
        while True:
            chunk = input_file.read(BUFFER_SIZE)
            if not chunk:
                break
            buffered.conn.sendall(chunk)

    print(buffered.recv_line())


def handle_download(buffered: BufferedSocket, remote_filename: str, local_path_text: str) -> None:
    local_path = Path(local_path_text).expanduser()
    if local_path.exists() and local_path.is_dir():
        local_path = local_path / remote_filename

    if local_path.parent != Path("") and not local_path.parent.exists():
        local_path.parent.mkdir(parents=True, exist_ok=True)

    buffered.send_line(f"DOWNLOAD {remote_filename}")
    response = buffered.recv_line()
    if response.startswith("ERROR"):
        print(response)
        return

    parts = response.split()
    if len(parts) != 3 or parts[0] != "FILE":
        print("ERROR Invalid server response.")
        return

    _, server_filename, size_text = parts
    try:
        size = int(size_text)
    except ValueError:
        print("ERROR Invalid file size from server.")
        return

    with local_path.open("wb") as output_file:
        buffered.recv_to_file(output_file, size)

    print(f"Downloaded {server_filename} to {local_path} ({size} bytes)")


def handle_delete(buffered: BufferedSocket, remote_filename: str) -> None:
    buffered.send_line(f"DELETE {remote_filename}")
    print(buffered.recv_line())


def start_client() -> None:
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((HOST, PORT))
    buffered = BufferedSocket(conn)

    print(f"Connected to file server at {HOST}:{PORT}")
    print_help()

    try:
        while True:
            raw_command = input("\nfile-transfer> ").strip()
            if not raw_command:
                continue

            try:
                parts = shlex.split(raw_command)
            except ValueError as exc:
                print(f"Input error: {exc}")
                continue

            command = parts[0].lower()

            if command == "list":
                handle_list(buffered)
            elif command == "upload":
                if len(parts) != 2:
                    print("Usage: upload <local_path>")
                else:
                    handle_upload(buffered, parts[1])
            elif command == "download":
                if len(parts) != 3:
                    print("Usage: download <remote_filename> <local_path>")
                else:
                    handle_download(buffered, parts[1], parts[2])
            elif command == "delete":
                if len(parts) != 2:
                    print("Usage: delete <remote_filename>")
                else:
                    handle_delete(buffered, parts[1])
            elif command == "quit":
                buffered.send_line("QUIT")
                print(buffered.recv_line())
                break
            elif command == "help":
                print_help()
            else:
                print("Unknown command. Type 'help' to see available commands.")
    except (ConnectionError, OSError) as exc:
        print(f"Connection error: {exc}")
    finally:
        conn.close()


if __name__ == "__main__":
    start_client()
