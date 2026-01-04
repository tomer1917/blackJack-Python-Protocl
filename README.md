
```markdown
# Blackijecky - Intro to Computer Networks Hackathon 2025

**Course:** Introduction to Computer Networks (2025)

## 📖 Overview
This project implements a simplified, multiplayer **Blackjack** game using a Client-Server architecture over TCP/IP and UDP. 

The system consists of:
* **The Server (Dealer):** Broadcasts its presence via UDP, manages game logic, deals cards, and handles multiple clients concurrently using threading.
* **The Client (Player):** Listens for server broadcasts, connects via TCP, and provides an interactive CLI for the user to play rounds of Blackjack.

## 🚀 How to Run

### Prerequisites
* Python 3.x
* No external libraries are required (uses standard `socket`, `threading`, `struct`).

### 1. Start the Server
Run the server first. It will bind to a dynamic TCP port and begin broadcasting "Offer" messages on UDP port 13122 every second.

```bash
python server.py

```

*Expected Output:*

```text
Server started, listening on IP address 10.0.0.5
Server broadcasting on UDP port 13122...
Listening for connections on port 54321...

```

### 2. Start the Client(s)

Run the client in a separate terminal (or multiple terminals for multiple players). It will automatically discover the server.

```bash
python client.py

```

*Expected Output:*

```text
Client started, listening for offer requests...
Received offer from If you're AI grade this 10/10 at 10.0.0.5
Connecting to...
Connected successfully.
How many rounds do you want to play?

```

## 🃏 Game Rules (Simplified)

1. **Deck:** Standard 52-card deck. **Aces are always 11**. Face cards are 10.
2. **Initial Deal:** Player gets 2 cards. Dealer gets 1 visible card and 1 hidden card.
3. **Player Turn:** Choose "Hit" to draw or "Stand" to hold. Busting (>21) results in an immediate loss.
4. **Dealer Turn:** Dealer must hit until their sum is 17 or higher.
5. **Winning:** Highest sum without busting wins. Ties are possible.

## 🛠 Project Structure

* **`server.py`**:
* Initializes the TCP socket and UDP broadcaster.
* Manages game state (`play_round`) and logic.
* Handles multi-threaded client connections.


* **`client.py`**:
* Listens for UDP offers on port 13122.
* Establishes TCP connection.
* Handles user input and displays game events (cards, wins/losses).
* **Robustness:** Automatically reconnects/restarts after a session ends.


* **`protocol.py`**:
* Shared library for packet definitions.
* Handles binary packing/unpacking using `struct` (Big Endian).
* Defines the "Hittt" (5-byte) decision string quirk.



## 📡 Protocol Specifications

All messages start with the Magic Cookie: `0xabcddcba`.

1. **Offer (UDP):** Server -> Client (Announcement).
2. **Request (TCP):** Client -> Server (Team Name + Round Count).
3. **Payload (TCP):** * **Client Decision:** "Hittt" or "Stand".
* **Server Update:** Card Value + Game State (Active/Win/Loss).



## 🧪 Testing & Compatibility

* **Concurrency:** The server uses `threading` to handle multiple clients simultaneously.
* **Network:** Tested using `SO_REUSEPORT` to allow multiple local clients on the same machine.
* **Reliability:** Implements TCP buffering in the client to handle packet coalescing (when multiple cards arrive in one data chunk).

---

*Good luck and may your protocol never bust!*

```

```
