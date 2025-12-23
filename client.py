import socket
import protocol
import sys
import struct


class BlackjackClient:
    def __init__(self, team_name="Yossi's stars"):
        self.team_name = team_name
        self.tcp_socket = None
        self.server_address = None
        self.server_name = None
        self.wins = 0
        self.rounds_played = 0

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
        # Calculate expected message size (Magic+Type+Result+Rank+Suit = 4+1+1+2+1 = 9 bytes)
        MSG_SIZE = 9

        try:
            while game_active:
                # 1. Read from network and append to buffer
                try:
                    chunk = self.tcp_socket.recv(protocol.BUFFER_SIZE)
                    if not chunk:
                        print("Server disconnected.")
                        break
                    data_buffer += chunk
                except Exception as e:
                    print(f"Receive error: {e}")
                    break

                # 2. Process ALL complete messages in the buffer
                while len(data_buffer) >= MSG_SIZE:
                    # Extract one packet
                    packet = data_buffer[:MSG_SIZE]
                    data_buffer = data_buffer[MSG_SIZE:]  # Remove it from buffer

                    valid, result, rank, suit = protocol.unpack_payload_server(packet)

                    if not valid:
                        print("Error: Invalid message format (Magic Cookie mismatch?).")
                        continue  # Skip bad packet

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

                        # Reset for next round
                        cards_received_counter = 0
                        my_turn = True

        except Exception as e:
            print(f"Game error: {e}")
        finally:
            if self.tcp_socket:
                self.tcp_socket.close()

            # Print Stats
            win_rate = (self.wins / self.rounds_played * 100) if self.rounds_played > 0 else 0
            print(f"Finished playing {self.rounds_played} rounds, win rate: {win_rate:.1f}%")

    def prompt_user(self):
        action = input("Type 'Hit' to draw another card, or 'Stand' to hold: ").strip()
        while action not in ["Hit", "Stand"]:
            print("Invalid choice.")
            action = input("Type 'Hit' to draw another card, or 'Stand' to hold: ").strip()

        payload = protocol.pack_payload_client(action)
        self.tcp_socket.sendall(payload)
        return action

    def format_card(self, rank, suit):
        ranks = {1: 'Ace', 11: 'Jack', 12: 'Queen', 13: 'King'}
        rank_str = ranks.get(rank, str(rank))
        suit_str = protocol.SUITS.get(suit, 'Unknown')
        return f"{rank_str} of {suit_str}"


if __name__ == "__main__":
    client = BlackjackClient(team_name="Yossi's stars")
    client.find_server()
    if client.connect_to_server():
        client.play_game()