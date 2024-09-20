################################################################################
#
#
###############################################################################
import os, sys
import pickle
from time import sleep
from socket import AF_INET, SOCK_STREAM
import socket
from threading import Thread, Lock
from queue import Queue

################################## GLOBALS #################################
HOST = ''
PORT = 50007
BLOCK_SZ = 2048
LOCK = Lock()
DELAY = 0.2
PORTS = [50001, 50002, 50003]


# PASS LOCK TO CLIENT
################################################################################
def get_lock():
    return LOCK


# MUTEX PRINT
################################################################################
def print_mtx(*args):
    LOCK.acquire()
    for arg in args:
        print(arg, end=' ')
    LOCK.release()


def input_mtx(*args):
    LOCK.acquire()
    response = input("Enter command > ")
    LOCK.release()
    return response



# CLASS - my_queue
# ******************************************************************************#
class QCustom:
    """
        Description
        ----
        Provides ability to get last item
    """

    def __init__(self):
        self.q = []

    def size(self):
        return len(self.q)

    def put(self, elem):
        self.q += [elem]

    def front(self):
        return self.q[0]

    def back(self):
        return self.q[-1]

    def pop(self, idx=0):
        return self.q.pop(idx)

    def empty(self):
        return self.size() == 0

    def clear(self):
        self.q = []


# CLASS - SimpleServer
# ******************************************************************************#
class SimpleServer(Thread):
    """
        Description
        ----
        Run server in a separate thread
    """

    def __init__(self, host=HOST, port=PORT, num_conn=1,
                 cmd_out_fcn=print_mtx, res_out_fcn=print_mtx, input_fcn=input):
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.num_conn = num_conn

        self.cmd_out_fcn = cmd_out_fcn  # displays results to command window
        self.res_out_fcn = res_out_fcn  # displays results to results window
        self.input_fcn   = input_fcn    # provides means for user input

        self.command_q = QCustom()
        self.srvr_sock = None
        self.conn = None
        self.address = None

        self.exit = False  # Triggers closing of object

    # DISPLAY HELP
    ############################################################################
    @staticmethod
    def disp_help(cmd_out_fcn):
        cmd_out_fcn("""Enter a shell command...
            Enter 'send' to send commands, 'get' to get results."
            Enter 'help' for general usage.
            or 'exit' to exit.\n""")

    # EXIT
    ############################################################################
    def quit_server(self):
        self.exit = True
        self.conn.close()

    # CREATE SERVER
    ############################################################################
    def create_server(self):
        self.srvr_sock = socket.socket(AF_INET, SOCK_STREAM)
        self.srvr_sock.bind((self.host, self.port))
        self.srvr_sock.listen(self.num_conn)
        self.conn, self.address = self.srvr_sock.accept()

    # SEND COMMANDS
    ############################################################################
    def send_commands(self, event=None):
        self.cmd_out_fcn(">>> Server sending commands >>>\n> ")
        while not self.command_q.empty():
            self.conn.send(self.command_q.pop().encode())
            sleep(DELAY)
        self.conn.send(b"server done")
        sleep(DELAY)

    # GET RESULTS FROM CLIENT
    ############################################################################
    def get_results(self):
        """
            Description
            -----
            Request results from the client
        """
        self.conn.send(b"send results")
        sleep(DELAY)
        data = ''
        self.conn.settimeout(1.0)
        self.res_out_fcn("RESULTS FROM CLIENT:\n")
        while True:
            try:
                pickled_data = self.conn.recv(BLOCK_SZ)
            except socket.timeout:
                break
            data = pickle.loads(pickled_data)
            # HANDLE DATA FROM CLIENT
            if data == "no data from client":
                self.res_out_fcn("No data from client" + '\n')
            else:
                idx = 0
                if data[1]:
                    idx = 1
                self.res_out_fcn(data[0] + ':' + '\n')

                # import ipdb; ipdb.set_trace()
                if isinstance(data[1], bytes):
                    self.res_out_fcn('\t')      # Can't concat bytes
                    self.res_out_fcn(data[1])
                    self.res_out_fcn('\n')
                else:
                    [self.res_out_fcn('\t' + line + '\n') for line in data[idx]]

            self.res_out_fcn('\t' + '-' * 50 + '\n')
        self.conn.settimeout(None)

    # RECEIVE FROM CLIENT
    ############################################################################
    def recv_from_client(self):
        while True:
            data = self.conn.recv(BLOCK_SZ)
            if not data:
                break
            self.res_out_fcn("SERVER: received, ", data)

    # RUN SERVER
    #############################################################################
    def run_server_machine(self):
        # GET INPUT FROM USER
        general_cmds = ["exit", "send", "get", "help"]
        command = ''
        while command not in general_cmds:
            sleep(0.1)  # Resolve stdin / stdout conflicts
            command = self.input_fcn("Enter command > ")
            self.command_q.put(command)

        # HANDLE COMMANDS
        if command == "exit":
            self.quit_server()
        elif command == "send":
            self.command_q.pop(-1)
            self.send_commands()  # send commands on commands_q
        elif command == "get":
            self.command_q.clear()
            self.get_results()
        elif command == "help":
            self.disp_help(self.cmd_out_fcn)

    # RUN - Thread.run override
    ############################################################################
    def run(self):
        self.disp_help(self.cmd_out_fcn)
        # self.cmd_out_fcn("> ")
        # CREATE SERVER OBJECT AND WAIT FOR LISTENER
        self.create_server()

        # RUN MACHINE UNTIL self.exit == True
        while not self.exit:
            self.run_server_machine()


# ==============================================================================#
if __name__ == "__main__":
    print_mtx("hello", 5)
