################################################################################
#
#
################################################################################
import os, sys, pickle
import subprocess as sp
from threading import Thread
from socket import AF_INET, SOCK_STREAM
from time import sleep
import socket
from threading import Thread, Lock
from queue import Queue
from simple_server import SimpleServer, print_mtx

################################## GLOBALS #################################
HOST = "localhost"
PORT = 50007
LOCK = Lock()
BLOCK_SZ = 1024
DELAY = 0.2
PORTS = [50001, 50002, 50003]


# CLASS - SimpleClient
# ******************************************************************************#
class SimpleClient(Thread):
    """
        Description
        ----
        Simple client to receive shell commands from server to execute on
        client machine

        NOTE: Inherits Thread for demo purposes (i.e. run in same interpreter
        on same machine)
    """

    def __init__(self, host=HOST, port=PORT):
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.client_q = Queue()
        self.client_sock = socket.socket(AF_INET, SOCK_STREAM)
        for _ in range(5):
            try:
                self.client_sock.connect((self.host, self.port))
                break
            except ConnectionRefusedError:
                sleep(1)

        self.exit = False

    # SAFE QUIT
    ############################################################################
    def quit_client(self):
        print_mtx("Shutting down client...")
        self.client_sock.close()

    # EXECUTE SHELL COMMAND
    ############################################################################
    def shell_cmd(self, command):
        """
            Description
            ----
            Executes a shell command on local (client) machine via os.popen.
            Stores response onto the
        """
        pipe = sp.Popen(command, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
        result  = pipe.communicate()

        res_list = [];  line = ''
        if result[0]:
            for char in result[0].decode():
                if char == '\n':
                    if line.startswith('\n'):
                        line = line[1:]
                    res_list.append(line)
                    line = ''
                line = line + char
        else:
            res_list = result[1]

        self.client_q.put((command, res_list))
        return False

    # SEND RESULTS
    ############################################################################
    def send_results(self):
        """
            Description
            ----
            Send items on client_q to the server
        """
        if self.client_q.empty():
            self.client_sock.send(pickle.dumps("no data from client"))
            sleep(DELAY)
        else:
            while not self.client_q.empty():
                msg = pickle.dumps(self.client_q.get())
                self.client_sock.send(msg)
                sleep(DELAY)

    # HANDLE DATA FROM SERVER
    ############################################################################
    def handle_data_from_server(self, data):
        """

        """
        if data == b"server done":
            return
        if data == b"send results":
            self.send_results()
        elif data == b"exit":
            self.exit = True
        else:
            self.shell_cmd(data.decode())

    # RUN CLIENT MACHINE
    ############################################################################
    def run(self):
        while not self.exit:
            data = self.client_sock.recv(BLOCK_SZ)
            if not data:
                break
            else:
                self.handle_data_from_server(data)


# ==============================================================================#
if __name__ == "__main__":
    server = SimpleServer()
    server.start()

    client = SimpleClient()
    client.start()

    server.join()
    client.join()
