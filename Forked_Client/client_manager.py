from LURKconfig import game_settings
from client import Client, Q
from LURKp import LURKprot
from models import Session, Player, Character, Room, Connection
from math import ceil
import threading, time
import multiprocessing.dummy as mp

class ClientManager: ### Uses a threaded loop to relay messages between Clients ###

    def __init__(self):
        self.game_settings = game_settings
        self.lurk = LURKprot()
        self.players = {}
        self.router_queue = mp.Queue()
        self.thread = threading.Thread(target = self.message_loop)
        self.thread.start()

    def route_message(self, message):
        name, message_dict = message
        if name in self.players:
            self.players[name].send_queue.put(message_dict)
        else:
            print(f'Player Route Error: {name} not found')

    def message_loop(self):
        while True:
            message = self.router_queue.get()
            self.route_message(message)

    def greet_conn(self, conn):
        lurk_version = self.lurk.get_version_message()
        self.lurk.encode(lurk_version, conn = conn)
        greeting = self.lurk.get_game_message(self.game_settings['initial_points'], self.game_settings['stat_limit'], self.game_settings['greeting'])
        self.lurk.encode(greeting, conn = conn)

    def spawn_client(self, conn, router_queue, character):
        send_queue = Q()
        p = mp.Process(target = Client, args = (conn, router_queue, send_queue, character))
        p.start()
        return send_queue

    def approve_conn(self, conn): ### Checks availability of name or innactive Player object, creates/updates Player or responds with error message ###
        message_dict = self.lurk.decode(conn = conn)
        if message_dict and 'type' in message_dict and message_dict['type'] == 10:
            name = message_dict['name']
            # print(f'Approval pending for: {name}')
            stats_total = message_dict['attack'] + message_dict['defense'] + message_dict['regen']
            if stats_total == self.game_settings['initial_points']:
                if name in self.players:
                    print("Attempting to resurrect")
                    if self.resurrect_player(conn, message_dict):
                        self.players[name] = self.spawn_client(conn, self.router_queue, message_dict)
                        return True
                else:
                    print(f'Adding new player: {name}')
                    self.players[name] = self.spawn_client(conn, self.router_queue, message_dict)
                    # self.game_queue.put((name, message_dict))
                    return True
            else:
                print(f"Rejecting character stats for {name}")
                text = f"Attack, defense, and regen must total {self.game_settings['initial_points']}"
                error_message = self.lurk.get_err_message(4, text = text)
                self.lurk.encode(error_message, conn = conn)
        return False
    
    def resurrect_player(self, conn, character_dict):
        name = character_dict['name']
        try: self.players[name].conn.send(bytes(1)) # attempt writing to the socket to see if it's alive
        except:
            print('Found existing player with broken conn, replacing conn...')
            self.players[name].new_thread(conn)
            return True
        print("Rejecting new conn")
        error_message = self.lurk.get_err_message(2)
        self.lurk.encode(error_message, conn = conn)
        return False
    
    def add_player(self, action): ### Checks availability of name or innactive Player object, creates/updates Player or responds with error message ###
        name, character_dict = action
        print(f'Adding character: {name}')
        with Session() as s:
            player = s.query(Character).filter_by(name = name).first()
            if player:
                self.players[name].alive = True
                self.players[name].set_flags(character_dict['flags'])
                self.players[name].health = 100
            else:
                self.players[name] = Character(character_dict = character_dict) #Player(self, conn, character_dict = character_dict)
            accept_message = self.lurk.get_accept_message(10)
            self.client_queue.put((name, accept_message))
            approved_character = self.lurk.get_char_message(self.players[name].get_dict())
            self.client_queue.put((name, approved_character))
