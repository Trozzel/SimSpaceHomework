################################################################################
#
#
################################################################################
import pickle
import queue
import _thread as thread
from queue import Queue
from time import sleep
from tkinter import *
import socket
from tkinter.messagebox import showerror, showinfo, showwarning

import ipdb

from simple_server import SimpleServer
from simple_client import SimpleClient

################################## GLOBALS #####################################
HOST = ''
PORT = 50007
DELAY = 0.2
BLOCK_SZ = 2048
CMD_WIN_Q = Queue()
RES_WIN_Q = Queue()
USR_INP_Q = Queue()
DEMO = True
INSTRUCT_TEXT = "                           INSTRUCTIONS\n" + \
                "Press 'Start Server' to initiate the server.\n" + \
                "Enter commands in the Command window.\n" + \
                "Press 'Send' to send your commands to the client\n" + \
                "Press 'Retrieve' to retrieve client response from the client"


# CLASS - ScrolledText
# ******************************************************************************#
class ScrolledText(Frame):
    def __init__(self, parent=None, text='', file=None):
        Frame.__init__(self, parent)
        self.pack(expand=YES, fill=BOTH)
        self.create_widgets()
        self.settext(text, file)

    # CREATE WIDGETS
    ############################################################################
    def create_widgets(self):
        sbar = Scrollbar(self)
        text = Text(self, relief=SUNKEN)
        sbar.config(command=text.yview)
        text.config(yscrollcommand=sbar.set)
        sbar.pack(side=RIGHT, fill=Y)
        text.pack(side=LEFT, expand=YES, fill=BOTH)
        text.bind("<Return>", self.upon_enter)
        self.text = text

    # SET TEXT
    ############################################################################
    def settext(self, text='> ', pos="1.0", file=None):
        if file:
            text = open(file, 'r').read()
        # self.text.delete('1.0', END)
        self.text.insert("1.0", text)
        self.text.mark_set(INSERT, END)
        self.text.focus()

    # GET TEXT
    ############################################################################
    def gettext(self):
        return self.text.get('1.0', END + '-1c')

    # GET UPON ENTRY
    ############################################################################
    def upon_enter(self, event):
        last_line = self.text.index(END) + "-1line"
        pos = self.text.search("> ", last_line, END)

        # INSERT COMMAND INTO QUEUE
        if pos:
            cmd = self.text.get(pos, END)[2:]
            if "Server sending commands" in cmd:
                return "break"
            if cmd.endswith('\n'):
                cmd = cmd[:-1]
            USR_INP_Q.put(cmd)

            self.text.mark_set(INSERT, END)
            last_line = self.text.index(END) + "-1line"
            self.text.insert(END, "\n> ")
            self.text.mark_set(INSERT, END)
        return "break"


# SIMPLE SERVER WRAPPER - re-implement run_server_machine
# ******************************************************************************#
class SimpleServerWrapper(SimpleServer):
    def __init__(self, host=HOST, port=PORT, num_conn=1,
                 cmd_out_fcn=None, res_out_fcn=None, input_fcn=None):
        SimpleServer.__init__(self, host, port, num_conn,
                              cmd_out_fcn, res_out_fcn, input_fcn)

    # DISPLAY HELP - override
    ############################################################################
    @staticmethod
    def disp_help(cmd_out_fcn):
        cmd_out_fcn("Welcome to the SimSpace Homework Server!\n")
        cmd_out_fcn("Press 'Start Server' to initiate the server.\n")
        cmd_out_fcn("Enter commands in the Command window.\n")
        cmd_out_fcn("Press 'Send' to send your commands to the client\n")
        cmd_out_fcn("Press 'Retrieve' to retrieve client response from the client\n")

    # RUN - override
    ############################################################################
    def run(self):
        # CREATE SERVER OBJECT AND WAIT FOR LISTENER
        # self.disp_help(self.cmd_out_fcn)
        self.create_server()

        while not self.exit:
            sleep(0.2)


# DUMMY INPUT COMMAND
#################################################################################
def dummy_input(txt):
    return


# CLASS SERVER GUI
# ******************************************************************************#
class ServerGui(Frame):
    """
        Description
        ----
        Provides graphical interface to SimPace server
    """

    def __init__(self, parent=None, **options):
        Frame.__init__(self, parent, **options)
        self.server = SimpleServerWrapper()  # SimpleServer object
        self.pack()
        self.host_var = StringVar()  # connected to host Entry
        self.port_var = StringVar()  # connected to port Entry
        self.keep_polling = True  # stop queue polling thread when False

        self.create_widgets()

    # START SERVER
    ############################################################################
    def start_server(self):
        # DISABLE / ENABLE BUTTONS
        self.start_btn.config(state=DISABLED)
        self.send_btn.config(state=NORMAL)
        self.recv_btn.config(state=NORMAL)

        host = self.host_var.get()
        port = int(self.port_var.get())
        self.server.host = host
        self.server.port = port
        self.server.cmd_out_fcn = CMD_WIN_Q.put
        self.server.res_out_fcn = RES_WIN_Q.put
        self.server.input_fcn = dummy_input  # The tk.Text places on USR_INP_Q

        # START SERVER IN SEPARATE THREAD
        self.server.start()
        sleep(0.5)
        # self.cmdwin.text.insert(END, "> ")

        # IF DEMO, START THE CLIENT IN SEPARATE THREAD
        if DEMO:
            try:
                client = SimpleClient()
                client.start()
            except socket.error:
                self.safe_quit()
            self.cmdwin.text.insert(END, "Server is connected to client <")
            self.cmdwin.text.insert(END, self.server.address[0] + ':')
            self.cmdwin.text.insert(END, str(self.server.address[1]) + ">\n")
            self.cmdwin.text.insert(END, "> ")

        # POLL FOR DATA IN SEPARATE THREAD
        self.poll_queues()

    # CREATE WIDGETS
    ############################################################################
    def create_widgets(self):
        """
            Description
            ----
            Make widgets
        """
        global CMD_WIN_Q

        Label(self, text="Welcome to the SimSpace Homework Server",
              font=(None, 20)).pack(side=TOP)
        Label(self, text=INSTRUCT_TEXT, justify=LEFT, borderwidth=1,
              relief=SUNKEN).pack(side=TOP)

        # COMMAND WINDOW
        left_frame = Frame(self)
        left_frame.pack(side=LEFT, expand=YES)
        Label(left_frame, text="Command Window").pack(side=TOP)
        self.cmdwin = ScrolledText(left_frame)
        self.cmdwin.pack(side=TOP)
        send_btn = Button(left_frame, text="Send")
        send_btn.pack(side=BOTTOM)
        send_btn.config(command=self.server.send_commands, state=DISABLED)

        # MIDDLE WIDGETS
        middle_frame = Frame(self)
        Label(middle_frame, text="Server Host").pack(side=TOP)
        middle_frame.pack(side=LEFT)
        host_edit = Entry(middle_frame, width=10)
        host_edit.pack(side=TOP)
        host_edit.config(textvariable=self.host_var,
                         background="white", foreground="black",
                         insertbackground="black")
        host_edit.insert(0, "localhost")

        port_edit = Entry(middle_frame, width=10)
        Label(middle_frame, text="Server Port").pack(side=TOP)
        port_edit.pack(side=TOP)
        port_edit.config(textvariable=self.port_var,
                         background="white", foreground="black",
                         insertbackground="black")
        port_edit.insert(0, "50007")

        start_btn = Button(middle_frame, text="Start Server", width=10)
        start_btn.pack(side=TOP)
        start_btn.config(command=self.start_server)

        # RESULTS WINDOW
        right_frame = Frame(self)
        right_frame.pack(side=RIGHT, expand=YES)
        Label(right_frame, text="Results Window").pack(side=TOP)
        self.reswin = ScrolledText(right_frame)
        self.reswin.pack(side=TOP)
        recv_btn = Button(right_frame, text="Retrieve Results")
        recv_btn.pack(side=BOTTOM)
        recv_btn.config(command=self.server.get_results, state=DISABLED)

        # ATTACH TO SELF
        self.start_btn = start_btn
        self.send_btn = send_btn
        self.recv_btn = recv_btn
        self.start_btn.focus()

    # POLL FOR TEXT FROM QUEUES
    ############################################################################
    def poll_queues(self):
        """
            Description
            -----
            Run in separate thread to poll the queues in order to display text
            in correct window
        """
        global CMD_WIN_Q, RES_WIN_Q, USR_INP_Q

        # @@@@@@@@@@@@@@@@@@@@ GET DATA FROM QUEUES @@@@@@@@@@@@@@@@@@@@@@@@@@@#
        def __get_data_from_queues():
            cmd_win_str = res_win_str = usr_inp_str = ''
            while self.keep_polling:
                try:
                    cmd_win_str = CMD_WIN_Q.get_nowait()
                    self.cmdwin.text.insert(END, cmd_win_str)
                except queue.Empty:
                    pass
                try:
                    res_win_str = RES_WIN_Q.get_nowait()
                    self.reswin.text.insert(END, res_win_str)
                    self.reswin.text.see(END)
                except queue.Empty:
                    pass
                try:
                    self.server.command_q.put(USR_INP_Q.get_nowait())
                except queue.Empty:
                    pass
                sleep(0.2)

        thread.start_new_thread(__get_data_from_queues, ())

    # SAFE QUIT
    ############################################################################
    def safe_quit(self):
        self.keep_polling = False  # queue polling
        try:
            self.server.send_commands(b"exit")
            self.server.quit_server()
        except socket.error:
            pass
        self.quit()


# ==============================================================================#
if __name__ == "__main__":
    root = Tk()
    server = ServerGui()


    # HANDLE WINDOW EVENTS
    # ---------------------------------------------------------------------------#
    def control_q_quit(event):
        server.safe_quit()


    def win_close_btn():
        server.keep_polling = False
        try:
            server.server.send_commands(b"exit")
            server.server.quit_server()
        except Exception as e:
            print(e)
        root.destroy()


    # ---------------------------------------------------------------------------#

    root.protocol("WM_DELETE_WINDOW", win_close_btn)
    root.bind('<Control-KeyPress-q>', control_q_quit)
    root.title("SimSpace Homework")

    root.mainloop()
