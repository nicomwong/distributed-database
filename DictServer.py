
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

    @classmethod
    def _successfulNonceHash(cls, _hash):
        "Returns True iff _hash is an integer that ends in 0, 1, or 2"
        if _hash == None:
            return False
        else:
            return _hash % 10 <= 2

    @classmethod
    def _calculateNonce(cls, operation_n):
        "Returns Nonce_n such that SHA256(Operation_n|Nonce_n) satisfies cls._successfulNonceHash()"
        _hash = None
        while not(cls._successfulNonceHash(_hash)):
            # Generating random string of size 10 for nonce
            nonce = ''.join(random.choice(string.ascii_letters)
                            for i in range(10))
            hashFunc = hashlib.sha256()
            hashFunc.update(repr(operation_n).encode() + nonce.encode())
            # Convert from hex to decimal
            _hash = int(hashFunc.hexdigest(), 16)

        # Found a nonce such that the hash that satisfies the critera
        print(f"Calculated nonce {nonce} such that h = {_hash}")
        return nonce

    @classmethod
    def _calculateHashPointer(cls, prevBlock):
        "Returns HashPointer_n+1 = SHA256(Operation_n|Nonce_n|HashPointer_n) as a hexadecimal string"
        if prevBlock is None:
            return None
        else:
            hashFunc = hashlib.sha256()
            hashFunc.update(repr(prevBlock.operation).encode() +
                            prevBlock.nonce.encode())
            if prevBlock.hashPointer:
                hashFunc.update( prevBlock.hashPointer.to_bytes(32, byteorder='big') )
            # print(f"Calculated hash pointer {hashFunc.hexdigest()}")
            return hashFunc.hexdigest()

    def __init__(self, operation, nonce, hashPointer, requestID):
        self.operation = operation
        self.hashPointer = hashPointer
        self.nonce = nonce
        self.requestID = requestID

    @classmethod
    def Create(cls, operation, requestID, prevBlock):
        nonce = cls._calculateNonce(operation)
        hashPointer = cls._calculateHashPointer(prevBlock)
        return cls(operation, nonce, hashPointer, requestID)

    def __repr__(self):
        return f"Block({repr(self.operation)}, {repr(self.nonce)}, {repr(self.hashPointer)}, {repr(self.requestID)})"


class Blockchain:
    def __init__(self):
        self._list = list()
        self.depth = 0  # Next index that is either empty or has a tentative block

    def __repr__(self):
        return repr(self._list)

    def append(self, block: Block):
        self._list.append(block)

    def accept(self, block: Block):
        pass

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

# b1 = Block.Create(putOp, (0, 0), None)
# print(b1)

# b2 = Block.Create(getOp, (0, 0), b1)
# print(b2)

# b3 = Block(putOp, b2)
# print(b3)

# blocks.append(Block(getOp, 123, 654))
# print(blocks[1])

# bc1 = Blockchain()
# for block in blocks:
#     bc1.append(block)

# bc1.write("test")

# bc2 = Blockchain.read("test")
# print(bc2)
