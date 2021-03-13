
import socket
import threading
import sys
import pickle

from Operation import Operation

class KVStore:
    def __init__(self):
        self._dict = dict()

    def __repr__(self):
        return repr(self._dict)

    def get(self, key):
        return self._dict[key]

    def put(self, key, value):
        self._dict[key] = value


class Block:
    def __init__(self,  operation: Operation,
                 nonce: str,
                 hashPointer: int):
        self.operation = operation
        # [TODO] Calculate nonce in constructor
        self.nonce = nonce
        self.hashPointer = hashPointer
        # [TODO] Add requestID field

    def __repr__(self):
        return f"Block({repr(self.operation)}, {repr(self.nonce)}, {repr(self.hashPointer)})"


class Blockchain:
    def __init__(self):
        self._list = list()

    def __repr__(self):
        return repr(self._list)

    def append(self, block: Block):
        self._list.append(block)

    def generateKVStore(self):
        "Returns the KVStore generated from performing the blockchain's operations in order"
        kvstore = KVStore()
        for block in self._list:
            op = block.operation
            if op.type == "put":
                kvstore.put(op.key, op.value)
            elif op.type == "get":
                pass
            else:
                raise Exception(f"Invalid operation type: {op.type}")
        return kvstore

    @classmethod
    def read(cls, filename):
        try:
            with open(filename, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError as e:
            print(e)
            return cls()

    def write(self, filename: str):
        with open(filename, "wb") as f:
            pickle.dump(self, f)


# putOp = Operation.Put(1, 2)
# getOp = Operation.Get(1)

# print(putOp)
# print(getOp)

# blocks = []

# blocks.append(Block(putOp, 123, 456))
# print(blocks[0])

# blocks.append(Block(getOp, 123, 654))
# print(blocks[1])

# bc1 = Blockchain()
# for block in blocks:
#     bc1.append(block)

# bc1.write("test")

# bc2 = Blockchain.read("test")
# print(bc2)
