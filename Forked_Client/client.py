import threading, multiprocessing, select, pickle, os, struct, time
from game import Game
from LURKp import LURKprot
from game_components import Character


class Q:

    def __init__(self): ### Queue object that uses a threading Lock and bytes pipe file for put() and get() ###
        self.lock = multiprocessing.Lock()
        self.rq, self.wq = os.pipe() # Pipe returns two file descriptors, this class's fileno and read mothods reference self.fq, where the put method references self.wq #

    def put(self, item): ## writes 2-byte length for subsefquent pickle object written ##
        with self.lock:
            item = pickle.dumps(item)
            bytes_to_write = struct.pack('<H', len(item))
            os.write(self.wq, bytes_to_write)
            os.write(self.wq, item)

    def get(self): ## Reads 2-byte length for subsequent pickle object read ##
        with self.lock:
            bytes_to_read = struct.unpack('<H', os.read(self.rq, 2))[0]
            data = os.read(self.rq, bytes_to_read)
            item = pickle.loads(data)
            return item

    def fileno(self): ## Returns the read file descriptor ## 
        fno = self.rq
        return fno


class Client: ### This class holds Player data and processes incoming and outgoing socket communication in its own thread ###

    def __init__(self, conn, router_queue, send_queue, character):
        self.name = character['name']
        self.game = Game()
        self.send_queue = send_queue
        self.client_router = router_queue
        self.new_thread(conn)

    def new_thread(self, conn):
        self.conn = conn
        self.lurk = LURKprot(conn = conn)
        self.thread = threading.Thread(target = self.conn_loop, name = f'{self.name}_thread')
        self.active = True
        self.thread.start()

    def conn_loop(self): ### Routes incoming message to other player or game queue, outgoing message to conn, or flags self.conn as broken ###
        print('Conn Loop Started:', threading.current_thread().name)
        while self.active:
            readers, _, errors = select.select([self.conn, self.send_queue], [], [self.conn]) # Writers should be a file which can be polled or watched
            for reader in readers:
                if reader == self.conn:
                    message_dict = self.lurk.decode()
                    # print(message_dict)
                    if message_dict and message_dict['type'] in (1, 2, 3, 4, 5, 6, 12):
                        # print('Incoming from', self.character.name, message_dict)
                        self.game.route_action((self.name, message_dict))
                    else:
                        self.active = False
                        print(f'Problem data from {self.name}: {message_dict}')
                else:
                    message_dict = reader.get()
                    # print('Outgoing to', self.character.name, message_dict)
                    if 
                    self.lurk.encode(message_dict)
            for error in errors:
                print('Error in', self.name, error)
                self.active = False
                # self.game.remove.put((self.name, time.time()))
        print(self.name, 'conn_loop ended!')
