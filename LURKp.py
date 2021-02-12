import socket, struct
from time import sleep


class Conn:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
    
    def connect(self):
        # try:
        self.soc.connect((self.host, self.port))
        self.connected = True
        # except:
        #     print("Can't connect to", self.host, self.port)
        #     return False
        # return True
    
    def detach(self):
        self.connected = False
        return self.soc.detach()

    def send(self, bytes):
        if self.connected:
            self.soc.send(bytes)
    
    def recv(self, len):
        if self.connected:
            data = self.soc.recv(len)
        else:
            data = None
        return data


class LURKp:

    def __init__(self, host, port):

        self.error_key = {0: 'Other',
                          1: 'Bad Room Number',
                          2: 'Name Already Taken',
                          3: 'No Monster',
                          4: 'Bad Stats',
                          5: 'Player Not Ready',
                          6: 'No Target',
                          7: 'No Fight',
                          8: 'No PVP Fight'}
                        
        self.message_key = {1: {'order': ('length', 'recipient', 'sender', 'text'), # Message <->
                                'length': (2, '<H'),
                                'recipient': (32, '<32B'),
                                'sender': (32, '<32B'),
                                'text': (0, '<{}B')},
                            2: {'order': ('room', ), # Changeroom ->
                                'room': (2, '<H'),},
                            3: {'order': ()}, # Fight ->
                            4: {'order': ('name', ), # PVPFight ->
                                'name': (32, '<32B')},
                            5: {'order': ('name', ), # Loot ->
                                'name': (32, '<32B')},
                            6: {'order': ()}, # Start ->
                            7: {'order': ('code', 'length', 'text'), # Error <-
                                'code': (1, '<B'),
                                'length': (2, '<H'),
                                'text': (0, '<{}B')},
                            8: {'order': ('code', ), # Action Accepted <-
                                'code': (1, '<B')},
                            9: {'order': ('room', 'name', 'length', 'text'), # Current Room Message <-
                                'room': (2, '<H'),
                                'name': (32, '<32B'),
                                'length': (2, '<H'),
                                'text': (0, '<{}B')},
                            10: {'order': ('name', 'flags', 'attack', 'defense', 'regen', 'health', 'gold', 'room', 'length', 'text'), # Character <->
                                'name': (32, '<32B'),
                                'flags': (1, '<B'),
                                'attack': (2, '<H'),
                                'defense': (2, '<H'),
                                'regen': (2, '<H'),
                                'health': (2, '<h'),
                                'gold': (2, '<H'),
                                'room': (2, '<H'),
                                'length': (2, '<H'),
                                'text': (0, '<{}B')},
                            11: {'order': ('points', 'limit', 'length', 'text'), # Game Message <-
                                'points': (2, '<H'),
                                'limit': (2, '<H'),
                                'length': (2, '<H'),
                                'text': (0, '<{}B')},
                            12: {'order': ()}, # Leave Game ->
                            13: {'order': ('room', 'name', 'length', 'text'), # Connecting Room <-
                                'room': (2, '<H'),
                                'name': (32, '<32B'),
                                'length': (2, '<H'),
                                'text': (0, '<{}B')},
                            14: {'order': ('major', 'minor', 'length', 'text'), # Server Version <-
                                'major': (1, '<B'),
                                'minor': (1, '<B'),
                                'length': (2, '<H'),
                                'text': (0, '<{}B')}}

        self.conn = Conn(host, port)

    def decode(self): ## Uses self.message_key to decode server messages, returns a message dictionary ##
        if self.conn.connected:
            data = self.conn.recv(1)
            # print(data)
            if data not in (b'', None, 0):
                mes_type = struct.unpack('<B', data)[0]
                # print('Message Type:', mes_type)
                message_dict = {'type': mes_type}
                if mes_type == 4: return message_dict
                reference = self.message_key[mes_type]
                for key in reference['order']:
                    length = reference[key][0]
                    if not length:
                        length = message_dict['length']
                        format = reference[key][1].format(length)
                    else: format = reference[key][1]
                    data = self.conn.recv(length)
                    print(format, data)
                    if not data: return None
                    value = struct.unpack(format, data)
                    # print('Value:', value, '\n', 'has length:', len(value))
                    if len(value) == 1: value = value[0]
                    elif len(value) > 1: value = ''.join([chr(i) for i in value if i])
                    else: value = ''
                    message_dict[key] = value
                print('Incoming: ', message_dict)
                return message_dict
            else:
                print('Problem Data:', data)
            return None

    def encode(self, message_dict): ## Uses self.message_key to encode message for server from a message dictionary ##
        if self.conn.connected:
            print('Outgoing: ', message_dict)
            mes_type = message_dict['type']
            reference = self.message_key[mes_type]
            message = bytes([mes_type])
            for key in reference['order']:
                format_key = reference[key]
                if key != 'length': value = message_dict[key]
                else: value = len(message_dict['text'])
                value_type = type(value)
                # print(value)
                if value_type == int:
                    if format_key[0]:
                        if format_key[0] == 1: message += bytes([value])
                        elif format_key[0] == 2: message += struct.pack(format_key[1], value)                            
                    else:
                        format = format_key[1].format(message_dict['length'])
                        message += struct.pack(format, value)
                elif value_type == str:
                    if key == 'text': message += bytes(value, 'UTF-8')
                    else:
                        message += bytes(value, 'UTF-8')[:31]
                        message += bytes(32 - len(value))
            # print(message)
            self.conn.send(message)

    def join_server(self, name):
        self.name = name
        return self.conn.connect()
    
    def leave_server(self):
        message_dict = {'type': 12}
        self.encode(message_dict)
        self.conn.detach()

    def start(self):
        message_dict = {'type': 6}
        self.encode(message_dict)

    def send_character(self, char_dict):
        char_dict['type'] = 10
        self.encode(char_dict)

    def send_chat(self, text, target = ''):
        message_dict = {'type': 1,
                        'sender': self.name,
                        'text': text,
                        'recipient': target}
        self.encode(message_dict)
    
    def change_room(self, room):
        message_dict = {'type': 2,
                        'room': room}
        self.encode(message_dict)
    
    def fight(self, target = None):
        if target:
            message_dict = {'type': 4,
                            'name': target}
        else:
            message_dict = {'type': 3}
        self.encode(message_dict)

    def loot(self, target):
        message_dict = {'type': 5,
                        'name': target}
        self.encode(message_dict)