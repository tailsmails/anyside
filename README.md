# Anyside
Transport-Agnostic Covert Tunneling Sandbox & Protocol Gateway

Anyside is a specialized network tunneling tool written in V. It completely detaches standard SOCKS5/TCP networking from the underlying transport medium. 

It accepts standard incoming SOCKS5 connections, multiplexes them, wraps the payloads in sequence-ordered, CRC-verified Base64 frames, and delegates the physical transmission to a user-defined external adapter.

If you can move a string of text from point A to point B (via DNS TXT records, Telegram bots, audio FSK, email, or directory polling), Anyside can tunnel a full TCP stream over it. This makes it a highly flexible sandbox for rapid prototyping of novel network transport protocols.

---

## Key Features

*   **Persistent Subprocess Communication:** Launches the transport adapter process once at startup and communicates in real-time via standard streams (`stdin` and `stdout`). This bypasses the heavy CPU overhead of spawning processes on every packet.
*   **Modulo 8-Bit Sequence Reordering:** Built-in sliding-window reordering buffer using modular arithmetic (`diff := u8(seq - expected)`). It handles sequence wrapping (from 255 to 0), discards late/duplicate packets, and buffers out-of-order packets to restore the exact sequential stream required by TCP.
*   **Multiplexing:** Supports multiple concurrent connections over a single transport adapter channel using a 1-byte connection ID (`conn_id`).
*   **Integrity Verification:** Uses a 4-byte CRC32 checksum alongside error recovery routines (`try_recover`) to attempt single-byte correction over corrupted ASCII mediums (vital for unstable transport layers like RF or Audio).
*   **Zero External Dependencies:** Built entirely on top of the V standard library. No package installation is required.

---

## Quick Start

### 1. Build the Binary
Compile the project with optimizations:
```bash
v -prod -cc gcc anyside.v -o anyside
```

### 2. Run the Target Server
```bash
./anyside -m server -e "python3 -u adapter.py" -c 1024 -d 50 -v
```

### 3. Run the Local Client
```bash
./anyside -m client -l 127.0.0.1:1080 -e "python3 -u adapter.py" -c 1024 -d 50 -v
```

### 4. Verify the Tunnel
Test SOCKS5 proxy routing over your custom transport medium:
```bash
curl -x socks5://127.0.0.1:1080 https://duckduckgo.com
```

---

## The Adapter Contract (Standard I/O API)

Anyside does not handle the transport layer itself. Instead, it interacts with your adapter script (written in Python, Go, Bash, etc.) using persistent standard stream commands. 

Your adapter process is spawned once and must run an infinite loop reading commands from `stdin` and printing output to `stdout` (make sure to **flush** the output immediately).

### 1. Transmission (`TX <base64_string>`)
When Anyside has data to send, it writes a single line to your adapter's `stdin`:
```text
TX dXNlcg==...
```
Your script must read this command, extract the Base64 string, and physically transmit it to the destination.

### 2. Reception (`RX`)
Triggered continuously based on the polling delay (`-d`). Anyside writes a single line to your adapter's `stdin`:
```text
RX
```
Your script must query the physical medium for pending data, print any received Base64 strings line-by-line to `stdout`, and conclude the batch by printing `__END_BATCH__` on a new line and flushing.

**Example Adapter Response for `RX`:**
```text
dXNlcg==...
YmFzZTY0...
__END_BATCH__
```

---

## Frame Structure

Anyside packages all data into binary frames before converting them into transport-safe Base64 strings.

```text
+-------------------+-------------+--------------+-------------+-------------+------------------+-------------------+
| Magic (2B) 0xDEAD | Command(1B) | Conn ID (1B) | Seq No (1B) | Length (2B) |   Payload (NB)   |   CRC-32 (4B)     |
+-------------------+-------------+--------------+-------------+-------------+------------------+-------------------+
```

*   **Magic Bytes:** `0xDE 0xAD` for frame synchronization.
*   **Command:** 
    *   `0x01` : Connection Request
    *   `0x02` : Data Payload
    *   `0x03` : Connection Successful
    *   `0x04` : Connection Failed
*   **Connection ID:** 1-byte identifier allowing up to 255 concurrent streams over one transport link.
*   **Sequence Number:** 1-byte counter used by the receiver's sliding window to reorder out-of-order packets.
*   **Length:** 2-byte big-endian payload length.
*   **Payload:** Raw SOCKS5/TCP payload.
*   **CRC-32:** 4-byte checksum over the entire preceding frame structure.
