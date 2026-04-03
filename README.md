# CMPT 371 A3 Socket Programming: TCP File Transfer System

**Course:** CMPT 371 - Data Communications & Networking  
**Instructor:** Mirza Zaeem Baig  
**Semester:** Spring 2026

## Group Members

| Name | Student ID | Email |
| :--- | :--- | :--- |
| Jane Doe | 301111111 | jane.doe@university.edu |
| John Smith | 301222222 | john.smith@university.edu |

Replace the placeholder member information above before submission.

## 1. Project Overview

This project is a command-line TCP file transfer system built with Python's standard library socket API. A central server accepts multiple client connections concurrently and provides a shared file repository. Clients can list files, upload files, download files, delete files, and disconnect using a small text-based application protocol over TCP.

The project is intentionally scoped to be reliable and easy to demo within a short course-project timeline:

- No GUI
- No external dependencies
- No authentication
- No resume support
- No encryption or compression

## 2. Features

- Multi-client server using `threading`
- Shared server-side storage folder
- Upload and download support for text and binary files
- Delete and list operations
- Explicit server responses for success and failure
- Filename validation to block path traversal such as `../secret.txt`
- Header framing with newline-delimited commands and exact-size file payload transfer

## 3. Project Structure

```text
CMPT371_A3_Socket_Programming/
├── README.md
├── src/
│   ├── client.py
│   └── server.py
└── server_storage/
```

The `server_storage/` directory is created automatically the first time the server starts.

## 4. Prerequisites

- Python 3.10 or newer
- No `pip install` step required

## 5. How to Run

Run all commands from the project root.

### Step 1: Start the server

```bash
python3 src/server.py
```

Expected console output:

```text
[STARTING] File server listening on 127.0.0.1:5050
```

### Step 2: Start a client

Open a new terminal and run:

```bash
python3 src/client.py
```

Expected console output:

```text
Connected to file server at 127.0.0.1:5050
Commands:
  list
  upload <local_path>
  download <remote_filename> <local_path>
  delete <remote_filename>
  quit
```

### Step 3: Run client commands

Available commands:

- `list`
- `upload <local_path>`
- `download <remote_filename> <local_path>`
- `delete <remote_filename>`
- `help`
- `quit`

Example session:

```text
file-transfer> list
No files available on the server.

file-transfer> upload ./demo.txt
OK Uploaded demo.txt (42 bytes)

file-transfer> list
Files on server:
  demo.txt (42 bytes)

file-transfer> download demo.txt ./downloads/demo_copy.txt
Downloaded demo.txt to downloads/demo_copy.txt (42 bytes)

file-transfer> delete demo.txt
OK Deleted demo.txt

file-transfer> quit
OK Goodbye.
```

## 6. Protocol Design

The application-layer protocol uses ASCII text headers terminated by `\n`. File bytes are transferred immediately after headers that include a declared size.

### Client commands

- `LIST`
- `UPLOAD <filename> <size>`
- `DOWNLOAD <filename>`
- `DELETE <filename>`
- `QUIT`

### Server responses

- `OK <message>`
- `ERROR <message>`
- `READY`
- `FILE <filename> <size>`
- `END`

### Protocol flow

**List files**

```text
Client: LIST
Server: OK 2
Server: FILE report.txt 128
Server: FILE photo.png 20480
Server: END
```

**Upload a file**

```text
Client: UPLOAD report.txt 128
Server: READY
Client: <128 raw bytes>
Server: OK Uploaded report.txt (128 bytes)
```

**Download a file**

```text
Client: DOWNLOAD report.txt
Server: FILE report.txt 128
Server: <128 raw bytes>
```

**Delete a file**

```text
Client: DELETE report.txt
Server: OK Deleted report.txt
```

## 7. Validation and Edge Cases

- Invalid filenames are rejected if they contain path separators such as `/` or `\`, or if they try to use special names like `.` or `..`.
- Download and delete requests for missing files return an explicit error response.
- Upload requests reject non-integer or negative sizes.
- The server handles each client in its own thread so one client does not block new connections.
- TCP buffering is handled with an application-layer reader that separates newline headers from raw payload bytes.
- Interrupted uploads are discarded so partial files are not published in shared storage.
- If a client disconnects during transfer, the server logs the disconnect and continues serving later clients.

## 8. Suggested Demo Flow

For a short video demo, show the following in order:

1. Start the server.
2. Connect Client A and run `list`.
3. Upload a text file from Client A.
4. Connect Client B and run `list` to show shared server state.
5. Download the uploaded file from Client B.
6. Delete the file from one client.
7. Attempt to download the deleted file to demonstrate server-side error handling.

## 9. Video Demo

Add your final video link here before submission:

- `[Project Demo Video](PASTE-YOUR-VIDEO-LINK-HERE)`

## 10. Academic Integrity and References

Update this section with your actual sources before submission.

- Code Origin:
  - Core socket programming, protocol handling, and file-transfer logic were implemented in this repository for the course project.
- GenAI Usage:
  - Document any AI tools used for planning, debugging, or documentation writing.
- References:
  - [Python Socket Programming HOWTO](https://docs.python.org/3/howto/sockets.html)
  - [Python threading documentation](https://docs.python.org/3/library/threading.html)
