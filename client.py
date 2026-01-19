import socket
import protocol
import sys
import os

try:
    import pygame
    MUSIC_AVAILABLE = True
except ImportError:
    MUSIC_AVAILABLE = False
    print("Warning: 'pygame' not found. Music will not play. (pip install pygame)")

class BlackjackClient:
    def __init__(self, team_name="Yossi's stars"):
        self.team_name = team_name
        self.tcp_socket = None
        self.server_address = None
        self.server_name = None
        self.wins = 0
        self.rounds_played = 0
        self.play_music("akeboshi wind.mp3")

    def play_music(self, filename):
        """
        Bonus: Plays background music in a loop.
        """
        if not MUSIC_AVAILABLE:
            return

        try:
            if os.path.exists(filename):
                pygame.mixer.init()
                pygame.mixer.music.load(filename)
                # loops=-1 means loop forever
                pygame.mixer.music.play(loops=-1)
                # Optional: Lower volume so it's not too loud (0.0 to 1.0)
                pygame.mixer.music.set_volume(0.5)
                print(f"🎵 Playing background music: {filename}")
            else:
                print(f"Warning: Music file '{filename}' not found.")
        except Exception as e:
            print(f"Error playing music: {e}")

    def find_server(self):
        """
        Listens for UDP offers. Returns True if a server is found, False otherwise.
        """
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
                    return True
            except Exception as e:
                print(f"Error receiving offer: {e}")
                # We don't return False here, we keep listening

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
        try:
            # We use input() which blocks. This is fine for a simple client.
            # In a GUI or advanced client, this might need to be non-blocking.
            try:
                rounds_request = int(input("How many rounds do you want to play? "))
            except ValueError:
                print("Invalid input, defaulting to 1 round.")
                rounds_request = 1

            req_msg = protocol.pack_request(rounds_request, self.team_name)
            self.tcp_socket.sendall(req_msg)

            game_active = True

            # State tracking
            cards_received_counter = 0
            my_turn = True

            # TCP Buffer
            data_buffer = b""
            MSG_SIZE = 9

            while game_active:
                try:
                    chunk = self.tcp_socket.recv(protocol.BUFFER_SIZE)
                    if not chunk:
                        print("Server disconnected.")
                        break
                    data_buffer += chunk
                except Exception as e:
                    print(f"Receive error: {e}")
                    break

                while len(data_buffer) >= MSG_SIZE:
                    packet = data_buffer[:MSG_SIZE]
                    data_buffer = data_buffer[MSG_SIZE:]

                    valid, result, rank, suit = protocol.unpack_payload_server(packet)

                    if not valid:
                        print("Error: Invalid message format.")
                        continue

                    card_str = self.format_card(rank, suit)

                    if result == protocol.RESULT_ACTIVE:
                        if my_turn:
                            cards_received_counter += 1
                            if cards_received_counter <= 2:
                                print(f"Your card: {card_str}")
                            elif cards_received_counter == 3:
                                print(f"Dealer's visible card: {card_str}")
                                if self.prompt_user() == "Stand":
                                    my_turn = False
                            else:
                                print(f"Your card: {card_str}")
                                if self.prompt_user() == "Stand":
                                    my_turn = False
                        else:
                            print(f"Dealer draws: {card_str}")
                    else:
                        # Round Ended
                        self.rounds_played += 1

                        if my_turn:
                            print(f"Your card: {card_str}")
                        else:
                            print(f"Dealer's final card: {card_str}")

                        if result == protocol.RESULT_WIN:
                            print("You won this round! :)")
                            self.wins += 1
                        elif result == protocol.RESULT_LOSS:
                            print("You lost this round. :(")
                        elif result == protocol.RESULT_TIE:
                            print("It's a tie.")

                        print("-" * 20)

                        cards_received_counter = 0
                        my_turn = True

        except Exception as e:
            print(f"Game error: {e}")
        finally:
            if self.tcp_socket:
                self.tcp_socket.close()

            win_rate = (self.wins / self.rounds_played * 100) if self.rounds_played > 0 else 0
            print(f"Finished playing {self.rounds_played} rounds, win rate: {win_rate:.1f}%")
            print("--- resetting client ---")

            # Reset stats for the new session?
            # The assignment implies "updates its statistics... and moves on", usually per session.
            # We will reset stats for a fresh connection.
            self.wins = 0
            self.rounds_played = 0

    def prompt_user(self):
        print("Type 'Hit' to draw another card, or 'Stand' to hold: ", end='')
        sys.stdout.flush()  # Ensure prompt appears before input
        action = input().strip()
        while action not in ["Hit", "Stand"]:
            print("Invalid choice. Please type 'Hit' or 'Stand'.")
            action = input().strip()

        payload = protocol.pack_payload_client(action)
        self.tcp_socket.sendall(payload)
        return action

    def format_card(self, rank, suit):
        ranks = {1: 'Ace', 11: 'Jack', 12: 'Queen', 13: 'King'}
        rank_str = ranks.get(rank, str(rank))
        suit_str = protocol.SUITS.get(suit, 'Unknown')
        return f"{rank_str} of {suit_str}"


if __name__ == "__main__":
    # "Both server and client applications are supposed to run forever"
    while True:
        client = BlackjackClient(team_name="Yossi's stars")
        client.find_server()
        if client.connect_to_server():
            client.play_game()
        else:
            print("Connection failed, retrying...")