import LURKconfig
from game_components import Character, Room, Loot
from LURKp import LURKprot
from random import randint
from math import floor, ceil
import queue, threading, time, models
import multiprocessing.dummy as mp

class Game:

    def __init__(self, game_queue, client_queue):
        self.settings = LURKconfig.game_settings
        self.lurk = LURKprot()
        self.rooms = {}
        self.players = {} # Now holds player Character objects instead of Player objects
        # self.game_queue = game_queue
        self.client_queue = client_queue
        # self.load_map()
        # self.game_loop()

    def load_map(self): ### Loads Rooms, Connections, Monsters, and Lootables from database ###
        session = models.Session()
        rooms = session.query(models.Room).all()
        connections = session.query(models.Connection).all()
        monsters = session.query(models.Monster).all()
        lootables = session.query(models.Loot).all()
        for room in rooms:
            number, name, desc = room.id, room.name, room.description
            self.rooms[number] = Room(number, name, desc)
        for connection in connections:
            room1, room2 = connection.room1, connection.room2
            self.rooms[room1].connections.append(room2)
        for monster in monsters:
            self.rooms[monster.room].monsters[monster.name] = Character(table_object = monster, monster = True)
        for lootable in lootables:
            room, name, value, rewards, message = lootable.room, lootable.name, lootable.value, lootable.rewards, lootable.message
            self.rooms[room].lootables.append(Loot(room, name, value, rewards, message))
    
    def route_action(self, action):
        game_actions = { # uses message type to route game actions to class methods #
            1: self.relay_chat,
            2: self.change_room,
            3: self.stage_fight,
            4: self.stage_pvp_fight,
            5: self.loot,
            6: self.start_player,
            12: self.stash_player
        }
        action_type = action[1]['type']
        # print('Processing action:', action_type)
        game_actions[action_type](action)

    # def game_loop(self):
    #     while True:
    #         action = self.game_queue.get()
    #         self.route_action(action)
            # game_queue_size = self.game_queue.qsize()
            # if game_queue_size:
            #     actions = [self.game_queue.get() for _ in range(game_queue_size)]
            #     pool_size = ceil(game_queue_size / 2)
            #     print('Processing', game_queue_size, 'events with', pool_size, 'threads')
            #     with mp.Pool(pool_size) as pool:
            #         pool.map(self.route_action, actions)
            # remove_queue_size = self.remove.qsize()
            # # if remove_queue_size: print('Processing', remove_queue_size, 'removals...')
            # for _ in range(remove_queue_size):
            #     name, time_added = self.remove.get()
            #     if time.time() - time_added < self.settings['stash_player_after']:
            #         item = (name, time_added)
            #         self.remove.put(item)
            #     else:
            #         print(f'Moving {name} to permanent storage.')
            #         self.players.pop(name, 'Player Not Found')
        # time.sleep(.1)

    # def game_loop(self):
    #     while True:
    #         game_queue_size = self.game_queue.qsize()
    #         if game_queue_size:
    #             actions = [self.game_queue.get() for _ in range(game_queue_size)]
    #             adds = [self.add_player(action) for action in actions if action[1]['type'] == 10]
    #             leaves = [self.stash_player(action) for action in actions if action[1]['type'] == 12]
    #             ch_rooms = [self.change_room(action) for action in actions if action[1]['type'] == 2]
    #             starts = [self.start_player(action) for action in actions if action[1]['type'] == 6]
    #             actions = [action for action in actions if action[1]['type'] not in (2, 6, 10, 12)]
    #             if actions:
    #                 pool_size = ceil(game_queue_size / 4)
    #                 with mp.Pool(pool_size) as pool:
    #                     pool.map(self.route_action, actions)
    #         # time.sleep(.2)

    def start_player(self, action): ### Updates character to indicate 'started' and adds player to the appropriate room ###
        name, message = action
        print('Starting Player:', name)
        accept_message = self.lurk.get_accept_message(message['type'])
        self.client_queue.put((name, accept_message))
        self.players[name].started = True
        self.players[name].room = self.settings['start_room']
        self.rooms[self.settings['start_room']].players.append(name)
        self.update_room(self.settings['start_room'])

    def stash_player(self, action): ### Removes Player object from players and current room, adds or updates player record in long-term storage ###
        name = action[0]
        room = self.players[name].room
        print('Stashing Player:', self.players[name].get_dict())
        fairwell = self.lurk.get_chat_message(self.settings['landlord'], name, 'Sad to see you going so sooooon. Fair well!')
        self.client_queue.put((name, fairwell))
        self.rooms[room].players.remove(name)
        self.update_room(room)
        self.players[name].started = False
        self.players[name].ready = False
        self.players[name].active = False
        self.players.pop(name)
    
    def relay_chat(self, action):
        message_dict = action[1]
        target = message_dict['recipient']
        self.client_queue.put((target, message_dict))

    def change_room(self, action): ### Checks that new room is a connection of current room, removes player from current room and adds to new room, calls update_room on both ###
        name, message = action
        new_room = message['room']
        old_room = self.players[name].room
        # print('Player', name, 'room changing from', old_room, 'to', new_room)
        if new_room in self.rooms[old_room].connections:
            accept_message = self.lurk.get_accept_message(message['type'])
            self.client_queue.put((name, accept_message))
            self.players[name].room = new_room
            self.rooms[new_room].players.append(name)
            self.update_room(new_room)
            self.rooms[old_room].players.remove(name)
            self.update_room(old_room)
        else:
            print(f'Room Change Error: {name}, {old_room} -> {new_room}')
            message_dict = self.lurk.get_err_message(1, 'No Connection')
            self.client_queue.put((name, message_dict))

    def update_room(self, room): ### Sends updated characters, connections, and other info to all players in room ###
        # print('Updating room', room)
        current_room = self.lurk.get_cur_room_message(self.rooms[room].get_dict())
        # print(self.rooms[room].players)
        player_characters = [self.players[i].get_dict() for i in self.rooms[room].players]
        player_characters = [self.lurk.get_char_message(i) for i in player_characters]
        monster_characters = [i.get_dict() for i in self.rooms[room].monsters.values()]
        monster_characters = [self.lurk.get_char_message(i) for i in monster_characters]
        connecting_rooms = [self.rooms[i].get_dict() for i in self.rooms[room].connections]
        connecting_rooms = [self.lurk.get_con_room_message(i) for i in connecting_rooms]
        # print(f'Room(Players: {len(player_characters)}, Monsters: {len(monster_characters)}, Connections: {len(connecting_rooms)})')
        for name in self.rooms[room].players:
            if name in self.players:
                self.client_queue.put((name, current_room))
                for update_list in (player_characters, monster_characters, connecting_rooms):
                    for item in update_list:
                        self.client_queue.put((name, item))

    def process_fight(self, room, players_list, monsters_list = None): ### Calculates attack and damage taken for each character's turn, finally calls self.update_room ###
        print(f'Fight in Room: {room}, with Players: {players_list}, and Monsters: {monsters_list}')
        if monsters_list: # whole room fight
            for character in players_list: # Each player attacks first
                player_name = character['name']
                attack = character['attack']
                for character in monsters_list:
                    if character['health'] > 0:
                        calc_attack = randint(int(attack * 0.75), int(attack * 1.25)) # consider moving this above the for loop if functionality is slow #
                        damage_taken = calc_attack - character['defense']
                        print(f"{player_name} dealt {damage_taken} damage to {character['name']}")
                        self.rooms[room].monsters[character['name']].health -= damage_taken
                        if self.rooms[room].monsters[character['name']].health <= 0:
                            self.rooms[room].monsters[character['name']].alive = False
                            payout = ceil(self.rooms[room].monsters[character['name']].gold / float(len(players_list)))
                            self.rooms[room].monsters[character['name']].gold = 0
                            for character in players_list:
                                self.players[character['name']].gold += payout
            for character in monsters_list: # Then monsters attack
                monster_name = character['name']
                attack = character['attack']
                for character in players_list:
                    calc_attack = randint(int(attack * 0.5), int(attack * 1.25)) # consider moving this above the for loop if functionality is slow #
                    damage_taken = calc_attack - character['defense']
                    if damage_taken < 0: damage_taken = 0
                    print(f"{monster_name} dealt {damage_taken} damage to {character['name']}")
                    self.players[character['name']].health -= damage_taken
                    if self.players[character['name']].health <= 0:
                        self.players[character['name']].alive = False
        else: # pvp fight # gold distribution is left up to the loot command for now
            player1, player2 = players_list
            calc_attack = randint(int(player1['attack'] * 0.75), int(player1['attack'] * 1.25))
            damage_taken = calc_attack - player2['defense']
            self.players[player2['name']].health -= damage_taken
            if self.players[player2['name']].health <= 0:
                self.players[player2['name']].alive = False
            else:
                calc_attack = randint(int(player2['attack'] * 0.75), int(player2['attack'] * 1.25))
                damage_taken = calc_attack - player1['defense']
                self.players[player1['name']].health -= damage_taken
                if self.players[player1['name']].health <= 0:
                    self.players[player1['name']].alive = False
        self.update_room(room)

    def stage_fight(self, action): ### Prepares character list for room, passes characters to calculate_attack ###
        name, message = action
        room = self.players[name].room
        if self.rooms[room].monsters:
            accept_message = self.lurk.get_accept_message(message['type'])
            self.client_queue.put((name, accept_message))
            players_list = self.rooms[room].players.copy()
            players_list.remove(name)
            players_list.insert(0, name) # Moves acting player to the front of the list
            print(f'Players list for fight: {players_list}')
            players_list = [self.players[i].get_fight_stats() for i in players_list]
            players_list = [i for i in players_list if i and i['health'] > 0]
            monsters_list = [i.get_fight_stats() for i in self.rooms[room].monsters.values()]
            self.process_fight(room, players_list, monsters_list)
        else:
            message_dict = self.lurk.get_err_message(3)
            self.client_queue.put((name, message_dict))
    
    def stage_pvp_fight(self, action): ### Commences attack sequence, calculating attack and damage taken for each character's turn, and finally calls self.update_room ###
        name, message = action
        target = message['name']
        room = message['room']
        if target in self.rooms[room].players:
            accept_message = self.lurk.get_accept_message(message['type'])
            self.client_queue.put((name, accept_message))
            players_list = [name, target]
            players_list = [self.players[i].get_fight_stats() for i in players_list]
            self.process_fight(room, players_list)
        else:
            message_dict = self.lurk.get_err_message(6)
            self.client_queue.put((name, message_dict))

    def loot(self, action): ### Checks to see if target is lootable, transfers gold ###
        name, message = action
        room = self.players[name].room
        target = message['name']
        if target in self.rooms[room].monsters and self.rooms[room].monsters[target].health <= 0:
            accept_message = self.lurk.get_accept_message(message['type'])
            self.client_queue.put((name, accept_message))
            self.players[name].gold += self.rooms[room].monsters[target].gold
            self.rooms[room].monsters[target].gold = 0
        elif target in self.players and self.players[name].room == self.players[target].room and self.players[target].health <= 0: # should this third condition check whether the target player is listed in the room rather than checking their character.room
            accept_message = self.lurk.get_accept_message(message['type'])
            self.client_queue.put((name, accept_message))
            self.players[name].gold += self.players[target].gold
            self.players[target].gold = 0
        else:
            message_dict = self.lurk.get_err_message(6)
            self.client_queue.put((name, message_dict))
        self.update_room(room)