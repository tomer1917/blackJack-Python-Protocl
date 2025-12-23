import socket
import protocol
import sys


class BlackjackClient:
    def __init__(self, team_name="Yossi's stars"):
        self.team_name = team_name
        self.tcp_socket = None
        self.server_address = None
        self.server_name = None

    def find_server(self):
        print("Client started, listening for offer requests...")
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        udp_socket.bind(('', protocol.UDP_PORT))

        while True:
            try:
                data, addr = udp_socket.recvfrom(protocol.BUFFER_SIZE)
                valid, server_port, server_name = protocol.unpack_offer(data)

                if valid:
                    print(f"Received offer from {server_name} at {addr[0]}")
                    self.server_address = (addr[0], server_port)
                    self.server_name = server_name
                    udp_socket.close()
                    return
            except Exception as e:
                print(f"Error receiving offer: {e}")

    def connect_to_server(self):
        try:
            print(f"Connecting to {self.server_address}...")
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.connect(self.server_address)
            print("Connected successfully.")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    def play_game(self):
        # Ask user for number of rounds
        try:
            rounds = int(input("How many rounds do you want to play? "))
        except ValueError:
            print("Invalid input, defaulting to 1 round.")
            rounds = 1

        # 1. Send Request Message
        req_msg = protocol.pack_request(rounds, self.team_name)
        self.tcp_socket.sendall(req_msg)

        # 2. Game Loop
        game_active = True
        cards_in_hand = 0  # Track how many cards we have in the current round

        try:
            while game_active:
                # Wait for server message
                data = self.tcp_socket.recv(protocol.BUFFER_SIZE)
                if not data:
                    print("Server disconnected.")
                    break

                valid, result, rank, suit = protocol.unpack_payload_server(data)

                if not valid:
                    print("Error: Invalid message received from server.")
                    break

                # Format the card string
                card_str = self.format_card(rank, suit)

                if result == protocol.RESULT_ACTIVE:
                    # We received a player card
                    cards_in_hand += 1
                    print(f"Your card: {card_str}")

                    # LOGIC FIX: Only ask for input if we have at least 2 cards
                    if cards_in_hand < 2:
                        continue

                        # Decide: Hit or Stand
                    action = input("Type 'Hit' to draw another card, or 'Stand' to hold: ").strip()
                    while action not in ["Hit", "Stand"]:
                        print("Invalid choice. Please type 'Hit' or 'Stand'.")
                        action = input("Type 'Hit' to draw another card, or 'Stand' to hold: ").strip()

                    payload = protocol.pack_payload_client(action)
                    self.tcp_socket.sendall(payload)

                else:
                    # Round Ended (Win/Loss/Tie)
                    print(f"Dealer's card: {card_str}")

                    if result == protocol.RESULT_WIN:
                        print("You won this round! :)")
                    elif result == protocol.RESULT_LOSS:
                        print("You lost this round. :(")
                    elif result == protocol.RESULT_TIE:
                        print("It's a tie.")

                    print("-" * 20)
                    cards_in_hand = 0  # Reset counter for the next round

        except Exception as e:
            print(f"Game error: {e}")
        finally:
            self.tcp_socket.close()
            print("Disconnected from server.")

    def format_card(self, rank, suit):
        # Helper to make output nice
        ranks = {1: 'Ace', 11: 'Jack', 12: 'Queen', 13: 'King'}
        rank_str = ranks.get(rank, str(rank))
        suit_str = protocol.SUITS.get(suit, 'Unknown')
        return f"{rank_str} of {suit_str}"


if __name__ == "__main__":
    client = BlackjackClient(team_name="Yossi's stars")

    # Discovery
    client.find_server()

    # Connection & Gameplay
    if client.connect_to_server():
        client.play_game()