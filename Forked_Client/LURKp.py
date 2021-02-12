import struct, threading, sys
from time import sleep

class LURKprot:

    def __init__(self, conn = None):
        
        from LURKprot_keys import error_key, message_types, message_key

        self.version = '2.2'
        self.conn = conn
        self.error_key = error_key
        self.message_types = {v:k for k,v in message_types.items()}
        self.message_key = message_key

    def set_conn(self, conn):
        self.conn = conn

    def decode(self, conn = None): ## Uses self.message_key to decode server messages, returns a message dictionary ##
        if not conn: conn = self.conn
        try: data = conn.recv(1)
        except: return None
        if data not in (b'', None, 0):
            mes_type = struct.unpack('<B', data)[0]
            if mes_type not in self.message_key:
                print('Message Type Error:', mes_type)
                return None
            message_dict = {'type': mes_type}
            reference = self.message_key[mes_type]
            for key in reference['order']:
                length = reference[key][0]
                if not length:
                    length = message_dict['length']
                    format = reference[key][1].format(length)
                else: format = reference[key][1]
                data = conn.recv(length)
                if not data: return None
                # print(format, data)
                value = struct.unpack(format, data)
                if len(value) == 1: value = value[0]
                elif len(value) > 1: value = ''.join([chr(i) for i in value if i])
                else: value = ''
                message_dict[key] = value
            # print('Incoming: ', message_dict, 'from', threading.current_thread().name)
            return message_dict
        else:
            # print('Problem Data:', data)
            return data

    def encode(self, message_dict, conn = None): ## Uses self.message_key to encode message for server from a message dictionary ##
        if not conn:
            conn = self.conn
            if not conn: return
        # print('Outgoing: ', message_dict)
        mes_type = message_dict['type']
        reference = self.message_key[mes_type]
        message = bytes([mes_type])
        for key in reference['order']:
            format_key = reference[key]
            if key != 'length': value = message_dict[key]
            else: value = len(message_dict['text'])
            value_type = type(value)
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
        try:
            conn.send(message)
        except:
            # raise
            e = sys.exc_info()[0]
            print('Error:', e)


    def search_type(self, message_dict):
        for k, v in self.message_key:
            if sorted(v['order']) == tuple(sorted(message_dict.keys())):
                message_dict['type'] = k
                self.encode(message_dict)

    def get_char_message(self, char_dict):
        char_dict['type'] = self.message_types['Character']
        return char_dict

    def get_chat_message(self, sender, target, text):
        message_dict = {'type': self.message_types['Chat'],
                        'sender': sender,
                        'text': text,
                        'recipient': target}
        return message_dict
    
    def get_err_message(self, code, text = None):
        message_dict = {'type': self.message_types['Error'],
                        'code': code}
        message_dict['text'] = text if text else self.error_key[code]
        return message_dict
    
    def get_accept_message(self, code):
        return {'type': self.message_types['Action Accepted'],
                'code': code}

    def get_cur_room_message(self, room_dict):
        room_dict['type'] = self.message_types['Current Room']
        return room_dict
    
    def get_con_room_message(self, room_dict):
        room_dict['type'] = self.message_types['Connecting Room']
        return room_dict

    def get_game_message(self, initial_points, stat_limit, description):
        return {
            'type': self.message_types['Game'],
            'points': initial_points,
            'limit': stat_limit,
            'text': description
        }
    
    def get_version_message(self):
        version = self.version.split('.')
        return {
            'type': self.message_types['LURK Version'],
            'major': int(version[0]),
            'minor': int(version[1]),
            'text': "This server doesn't support any protocol extensions."
        }
    