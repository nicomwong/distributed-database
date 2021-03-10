
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
        