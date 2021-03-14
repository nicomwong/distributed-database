
class Operation:
    def __init__(self, operationType, **kwargs):
        self.type = operationType
        self.key = None
        self.value = None

        if 'key' in kwargs:
            self.key = kwargs['key']

        if 'value' in kwargs:
            self.value = kwargs['value']

    def __hash__(self):
        return hash( (self.type, self.key, self.value) )    # Note: If self.value is None for type=="get", it should always be hashed to the same number

    def __eq__(self, other):
        if self.type == other.type:
            if self.type == "get":
                return self.key == other.key
            elif self.type == "put":
                return self.key == other.key and self.value == other.value
        return False

    @classmethod
    def Put(cls, key, value):
        return cls("put", key=key, value=value)

    @classmethod
    def Get(cls, key):
        return cls("get", key=key)

    def __repr__(self):
        rep = f"Operation({repr(self.type)}"

        for k, v in vars(self).items():
            if k != "type":
                rep += f", {k}={repr(v)}"

        rep += ")"

        return rep
        