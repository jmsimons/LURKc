
# # # Module that initializes server conn, 

from client_manager import ClientManager
import socket, select, logging, os
from multiprocessing import Pipe, Process, Queue

host = '0.0.0.0'
port = 5050

def setup_logging():
    FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
    logging.basicConfig(filename = 'LURK.log', level = logging.DEBUG)

def spawn_game_process(game_queue, client_queue):
    p = Process(target = Game, args = (game_queue, client_queue), daemon = True)
    p.start()
    print('Conn Process PID:', os.getpid())
    print('Game Process PID:', p.pid)

def main(server_conn):
    conns = []
    attempts = []
    client_manager = ClientManager()
    conns.append(server_conn)
    while True: ### The main process should only handle initial connections, passing subsequent messages into game ###
        # print(f'Listening for conns: {conns}')
        readers, _, _ = select.select(conns, [], []) #.extend(new_conns)
        for reader in readers:
            if reader == server_conn:
                conn, addr = server_conn.accept()
                print("New Client; Address:", addr, "Conn:", conn)
                logging.log(logging.INFO, f"New Client Address: {addr}")
                conns.insert(0, conn)
                attempts.insert(0, 0)
                client_manager.greet_conn(conn)
            else:
                index = conns.index(reader)
                attempts[index] += 1
                if client_manager.approve_conn(reader):
                    conns.pop(index)
                    attempts.pop(index)
                elif attempts[index] == 5:
                    print('Closing conn after 5 attemps:', reader)
                    conns.pop(index)
                    attempts.pop(index)

if __name__ == '__main__':
    setup_logging()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while port <= 5054:
        try:
            s.bind((host, port))
            break
        except socket.error as e:
            print('Error binding port:', str(e))
            port += 1
    
    s.listen(10)
    print(f'Listening on: {host}:{port}')
    # TODO: add logic that kills the child process(es)
    main(s)
    