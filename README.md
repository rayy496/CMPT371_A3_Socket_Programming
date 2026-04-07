# CMPT 371 A3 Socket Programming: TCP File Transfer System

**Course:** CMPT 371 - Data Communications & Networking  
**Instructor:** Mirza Zaeem Baig  
**Semester:** Spring 2026

## Group Members

| Name | Student ID | Email |
| :--- | :--- | :--- |
| Ray Yamada | 301605651 |  |
| Eva Nguyen | 301425444 | dva11@sfu.ca |

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

Note that `<local_path>` uses the *working* directory, `<working_directory>` (where client is launched from), so if client is launched from `CMPT371_A3_Socket_Programming/`, the server checks for `CMPT371_A3_Socket_Programming/<local_path>` when handling file upload/download.  

`<remote_filename>` is thought of as `<working_directory>/server_storage/<remote_filename>` folder.  

Example: 
- client started from `CMPT371_A3_Socket_Programming/`
- client enters: `upload file.txt` 
  - `<local_path>` is `CMPT371_A3_Socket_Programming/file.txt` 
- `file.txt` is uploaded to `CMPT371_A3_Socket_Programming/server_storage/file.txt`

---

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

## 8. Demo Flow

1. Start the server.
2. Connect Client A and run `list`.
3. Upload a text file from Client A.
4. Connect Client B and run `list` to show shared server state.
5. Download the uploaded file from Client B.
6. Delete the file from one client.
7. Attempt to download the deleted file to demonstrate server-side error handling.

## 9. Video Demo

[File transfer demo](https://youtu.be/GmR7TZXajFs)

## 10. Limitations

Since the scope of this project is limited due to time, there are a few limitations with its functionality. Namely:

- The program uses TCP sockets, so it follows TCP guarantees (e.g. data integrity). However, there is no encryption or authentication being done, so there are no guarantees for security.
- There are only so many commands, and all of them are performed via CLI, which can be confusing to inexperienced users. 
- Only text and binary files are supported. This is because the program handles data transfer using byte arrays and uses a simple read/write system with a BufferedStream.
- There is no file compression. The program reads and writes all incoming data as-is and creates a new file where it is needed, meaning they will all be the same size. 
- No guarantees for latency or long transfers. In the event that the client experiences high latency and/or needs to wait a long time for the file to be uploaded/downloaded, there are no guarantees in terms of minimum time for an operation to be completed.
- Server must start before client. If client tries to start first, it will not wait for a connection: the connection will be refused and the program will exit. 
- No file sanitization. In the event a client tries to upload the same file or upload a file with the same name as one in `server_storage`, the old file will be overwritten. This means users could perform unintentionally destructive operations, with no support to alert or revert the change. 
- No support to close server. Currently there is no implementation for the server to close itself (e.g. via admin intervention) so the process must be killed manually. 

### Possible future improvements

- Enforce authentication + implement encryption
- Create user-friendly GUI
- More file type support
- (De)compression for files to save space and improve speed of upload/download
- Ensure minimum operation complete time
- Filename sanitization + option to name uploaded files
- Manual server commands for admin intervention

## 11. Academic Integrity and References

Update this section with your actual sources before submission.

- Code Origin:
  - Core socket programming, protocol handling, and file-transfer logic were implemented in this repository for the course project.
- GenAI Usage:
  - Document any AI tools used for planning, debugging, or documentation writing.
- References:
  - [Python Socket Programming HOWTO](https://docs.python.org/3/howto/sockets.html)
  - [Python threading documentation](https://docs.python.org/3/library/threading.html)
