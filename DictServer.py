
import socket
import threading
import sys

class KVStore:
    def __init__(self):
        self._dict = dict()

    def get(self, key):
        return self._dict[key]

    def put(self, key, value):
        self._dict[key] = value
        
class Operation:
    def __init__(self, operation, **kwargs):
        self.op = operation

        if 'key' in kwargs:
            self.key = kwargs['key']

        if 'value' in kwargs:
            self.value = kwargs['value']

    @classmethod
    def Put(cls, key, value):
        return cls("put", key=key, value=value)
    
    @classmethod
    def Get(cls, key):
        return cls("get", key=key)

    def __repr__(self):
        rep = f"Operation({repr(self.op)}"

        for k, v in vars(self).items():
            if k != "op":
                rep += f", {k}={repr(v)}"

        rep += ")"

        return rep

class Block:
    def __init__(self,  operation : Operation,
                        nonce : str,
                        hashPointer : int):
        self.operation = operation
        self.nonce = nonce
        self.hashPointer = hashPointer

    def __repr__(self):
        return f"Block({repr(self.operation)}, {repr(self.nonce)}, {repr(self.hashPointer)})"

class BlockChain:
    def __init__(self):
        self._list = list()

    def append(self, block : Block):
        self._list.append(block)

class DictServer:
    pass

putOp = Operation.Put(1, 2)
getOp = Operation.Get(1)

print(putOp)
print(getOp)

block = Block(putOp, 123, 456)
print(block)
