
import socket
import threading
import sys
import pickle
import hashlib
import string
import random

from Operation import Operation
# from Blockchain import Blockchain


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
                 prevBlock):
        # Local variables used to calculate nonce
        blockHash = 3
        hashFunc = None
        characters = string.ascii_letters

        # Local variables used to calculate hashPointer
        firstBlock = random.randbytes(64)

        # Class variables
        self.operation = operation
        self.operationStr = repr(operation).encode()
        self.nonce = None
        self.hashPointer = None

        # Calculate nonce
        while ((blockHash % 10) > 2):
            # Generating random string of size 10 for nonce
            self.nonce = ''.join(random.choice(characters)
                                 for i in range(10))
            hashFunc = hashlib.sha256()
            hashFunc.update(self.operationStr)
            hashFunc.update(self.nonce.encode())
            blockHash = int(hashFunc.hexdigest(), 16)

        # Calculate hashPointer
        if prevBlock == None:
            hashFunc = hashlib.sha256()
            hashFunc.update(firstBlock)
            self.hashPointer = hashFunc.hexdigest()

        else:
            hashFunc = hashlib.sha256()
            hashFunc.update(prevBlock.operationStr)
            hashFunc.update(prevBlock.nonce.encode())
            hashFunc.update(prevBlock.hashPointer.encode())
            self.hashPointer = hashFunc.hexdigest()

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

    @ classmethod
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

# b1 = Block(putOp, None)
# print(b1)

# b2 = Block(getOp, b1)
# print(b2)

# blocks.append(Block(getOp, 123, 654))
# print(blocks[1])

# bc1 = Blockchain()
# for block in blocks:
#     bc1.append(block)

# bc1.write("test")

# bc2 = Blockchain.read("test")
# print(bc2)
