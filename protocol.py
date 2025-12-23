import struct

# --- Constants ---
MAGIC_COOKIE = 0xabcddcba
MSG_TYPE_OFFER = 0x2
MSG_TYPE_REQUEST = 0x3
MSG_TYPE_PAYLOAD = 0x4

# Fixed ports and buffer sizes
UDP_PORT = 13122  # [cite: 114]
BUFFER_SIZE = 1024

# Result codes [cite: 101]
RESULT_ACTIVE = 0x0
RESULT_TIE = 0x1
RESULT_LOSS = 0x2
RESULT_WIN = 0x3

# Card Suits Mapping (0-3) [cite: 103]
SUITS = {0: 'Hearts', 1: 'Diamonds', 2: 'Clubs', 3: 'Spades'}

# --- Offer Message (UDP) ---
# Format: Magic(4) + Type(1) + ServerPort(2) + ServerName(32) = 39 bytes
# Struct format: !IBH32s (I=4 bytes, B=1 byte, H=2 bytes, 32s=32 char string)
OFFER_FMT = '!IBH32s'


def pack_offer(server_port, server_name):
    """
    Packs the UDP Offer message.
    server_name must be padded/truncated to 32 bytes[cite: 90].
    """
    # Encode name to bytes and ensure length is 32
    name_bytes = server_name.encode('utf-8')[:32].ljust(32, b'\x00')
    return struct.pack(OFFER_FMT, MAGIC_COOKIE, MSG_TYPE_OFFER, server_port, name_bytes)


def unpack_offer(data):
    """
    Unpacks the UDP Offer message.
    Returns: (valid, server_port, server_name)
    """
    try:
        if len(data) != struct.calcsize(OFFER_FMT):
            return False, None, None

        cookie, msg_type, server_port, name_bytes = struct.unpack(OFFER_FMT, data)

        if cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_OFFER:
            return False, None, None

        # Decode name and strip null padding
        server_name = name_bytes.decode('utf-8').rstrip('\x00')
        return True, server_port, server_name
    except Exception as e:
        print(f"Error unpacking offer: {e}")
        return False, None, None


# --- Request Message (TCP) ---
# Format: Magic(4) + Type(1) + NumRounds(1) + TeamName(32) = 38 bytes
# Struct format: !IBB32s
REQUEST_FMT = '!IBB32s'


def pack_request(num_rounds, team_name):
    """
    Packs the TCP Request message sent by Client.
    team_name must be padded/truncated to 32 bytes[cite: 95].
    """
    name_bytes = team_name.encode('utf-8')[:32].ljust(32, b'\x00')
    return struct.pack(REQUEST_FMT, MAGIC_COOKIE, MSG_TYPE_REQUEST, num_rounds, name_bytes)


def unpack_request(data):
    """
    Unpacks the TCP Request message received by Server.
    Returns: (valid, num_rounds, team_name)
    """
    try:
        if len(data) != struct.calcsize(REQUEST_FMT):
            return False, None, None

        cookie, msg_type, num_rounds, name_bytes = struct.unpack(REQUEST_FMT, data)

        if cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_REQUEST:
            return False, None, None

        team_name = name_bytes.decode('utf-8').rstrip('\x00')
        return True, num_rounds, team_name
    except:
        return False, None, None


# --- Payload Message (TCP) ---
# Note: Client and Server payload structures are different [cite: 96]

# Client Payload (Player Decision)
# Format: Magic(4) + Type(1) + Decision(5)
# Struct format: !IB5s
PAYLOAD_CLIENT_FMT = '!IB5s'


def pack_payload_client(decision):
    """
    Packs client decision ("Hit" or "Stand").
    Must be 5 bytes.
    """
    # Ensure strict 5 byte length as per
    if decision == "Hit":
        dec_bytes = b"Hittt"
    else:
        dec_bytes = b"Stand"

    return struct.pack(PAYLOAD_CLIENT_FMT, MAGIC_COOKIE, MSG_TYPE_PAYLOAD, dec_bytes)


def unpack_payload_client(data):
    """
    Unpacks client payload.
    Returns: (valid, decision_string)
    """
    try:
        if len(data) != struct.calcsize(PAYLOAD_CLIENT_FMT):
            return False, None

        cookie, msg_type, dec_bytes = struct.unpack(PAYLOAD_CLIENT_FMT, data)

        if cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_PAYLOAD:
            return False, None

        decision = dec_bytes.decode('utf-8')
        return True, decision
    except:
        return False, None


# Server Payload (Game State)
# Format: Magic(4) + Type(1) + Result(1) + Rank(2) + Suit(1)
# Struct format: !IBBHB
PAYLOAD_SERVER_FMT = '!IBBHB'


def pack_payload_server(result, rank, suit):
    """
    Packs server response.
    Result: 0-3
    Rank: 1-13 (2 bytes) [cite: 103]
    Suit: 0-3 (1 byte) [cite: 103]
    """
    return struct.pack(PAYLOAD_SERVER_FMT, MAGIC_COOKIE, MSG_TYPE_PAYLOAD, result, rank, suit)


def unpack_payload_server(data):
    """
    Unpacks server response.
    Returns: (valid, result, rank, suit)
    """
    try:
        expected_size = struct.calcsize(PAYLOAD_SERVER_FMT)
        # We allow reading partial if buffer is large, but strictly we need at least expected_size
        if len(data) < expected_size:
            return False, None, None, None

        cookie, msg_type, result, rank, suit = struct.unpack(PAYLOAD_SERVER_FMT, data[:expected_size])

        if cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_PAYLOAD:
            return False, None, None, None

        return True, result, rank, suit
    except:
        return False, None, None, None