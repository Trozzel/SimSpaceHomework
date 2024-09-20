import sys
from tkinter import Tk
from ServerGUI import ServerGui
from simple_server import SimpleServer
from simple_client import SimpleClient

if __name__ == "__main__":
    server_type = "gui"
    if len(sys.argv) == 2:
        server_type = sys.argv[1]

    if server_type == "gui":
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
    elif server_type == "cli":
        server = SimpleServer()
        server.start()

        client = SimpleClient()
        client.start()

        server.join()
        client.join()
    else:
        print("USAGE:")
        print("python ss_server.py     ~ starts the GUI server")
        print("python ss_server.py gui ~ starts the GUI server")
        print("python ss_server.py cli ~ starts the CLI server")
