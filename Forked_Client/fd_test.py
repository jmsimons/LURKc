import threading, select, pickle, os, struct

class Q:

    def __init__(self): ### Q object that uses a threading Lock and bytes pipe file for put() and get() ###
        self.lock = threading.Lock()
        self.rq, self.wq = os.pipe() # Pipe returns two file descriptors, this class's fileno and read mothods reference self.fq, where the put method references self.wq #

    def put(self, item): ## writes 2-byte length for subsefquent pickle object written ##
        with self.lock:
            item = pickle.dumps(item)
            bytes_to_write = struct.pack('<h', len(item))
            print(bytes_to_write)
            os.write(self.wq, bytes_to_write)
            os.write(self.wq, item)

    def get(self): ## Reads 2-bytes for subsequent pickle object to read ##
        with self.lock:
            bytes_to_read = struct.unpack('<h', os.read(self.rq, 2))[0]
            print(bytes_to_read)
            data = os.read(self.rq, bytes_to_read)
            print(data)
            item = pickle.loads(data)
            return item

    def fileno(self):
        fno = self.rq
        return fno

q = Q()

def select_loop(pollable_file): ### Watches for activity on pollable_file ###
    while True:
        print('Loop start...')
        readers, _, _ = select.select([pollable_file], [], [])
        for r in readers:
            print('Reading...')
            item = r.get()['text']
            print(item)
        if item == None: break # Breaks out of while loop when {'item': None}

# Loads three dictionaries to q #
q.put({'text': 'Hell'})
q.put({'text': 'O'})
q.put({'text': 'World'})

# Starts thread #
thread = threading.Thread(target = select_loop, args = (q, )) # Passes in q to select_loop as pollable_file #
thread.start()

# Loads 100 more sets of the same three dictionaries to q #
for i in range(100):
    q.put({'text': 'Hell'})
    q.put({'text': 'O'})
    q.put({'text': 'World'})

# Loads dictionary which signals thread to terminate #
q.put({'text': None})

thread.join()