import socket
import protocol


class BlackjackClient:
    def __init__(self, team_name="Team Lazy name choosers"):
        self.team_name = team_name
        self.tcp_socket = None
        self.server_address = None  # Tuple (ip, port)
        self.server_name = None

    def find_server(self):
        """
        Step 4: Network Discovery
        Listens on UDP port 13122 for an 'Offer' message.
        """
        print("Client started, listening for offer requests...")

        # Open UDP socket
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Allow multiple clients to listen on the same port (SO_REUSEPORT)
        # This is critical for testing multiple clients on one machine [cite: 118-124]
        try:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            # SO_REUSEPORT might not be available on Windows,
            # but is standard on Linux/Mac (Hackathon env).
            # On Windows, SO_REUSEADDR is sometimes used, but strictly
            # the assignment mentions SO_REUSEPORT.
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        udp_socket.bind(('', protocol.UDP_PORT))

        while True:
            try:
                # Receive packet
                data, addr = udp_socket.recvfrom(protocol.BUFFER_SIZE)

                # Unpack
                valid, server_port, server_name = protocol.unpack_offer(data)

                if valid:
                    print(f"Received offer from {server_name} at {addr[0]}")

                    # Store server details
                    # addr[0] is the Server's IP address
                    # server_port is the TCP port sent in the payload [cite: 89]
                    self.server_address = (addr[0], server_port)
                    self.server_name = server_name

                    udp_socket.close()
                    return  # Found a server, proceed to connect

            except Exception as e:
                print(f"Error receiving offer: {e}")

    def connect_to_server(self):
        """
        Establishes the TCP connection.
        """
        try:
            print(f"Connecting to {self.server_address}...")
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.connect(self.server_address)
            print("Connected successfully.")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False


if __name__ == "__main__":
    client = BlackjackClient(team_name="Team Yossi's stars")
    client.find_server()
    client.connect_to_server()

    # TODO Game logic will go here