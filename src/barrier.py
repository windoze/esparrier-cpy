"""
Barrier client protocol implementation.
@see https://qemu.readthedocs.io/en/latest/interop/barrier.html
"""

import utils

# Field types
INT8 = 0
INT16 = 1
INT32 = 2
STRING = 3
BYTES = 4
SINT16 = 5
SINT32 = 6

class BarrierMessage:
    """
    Base class for Barrier messages.
    """
    CMD = "Barrier"
    FIELD_DEF = [
        # ("COMMAND", STRING, 0),
    ]

    def __init__(self, **fields):
        if not hasattr(self, "buffer"):
            return
        # self.buffer needs to have correct length before calling this
        cmd_bytes = self.CMD.encode("utf-8")
        l = len(cmd_bytes)
        self.buffer[0:l] = cmd_bytes
        if fields:
            for k in fields:
                self.__setattr__(k, fields[k])

    def unmarshal(self, buffer):
        self.buffer = buffer
    
    def __len__(self):
        return len(self.buffer)

    def __getattr__(self, name):
        for (n, type, offset) in self.FIELD_DEF:
            offset = offset + len(self.CMD)
            if n == name:
                if type == INT8:
                    return self.buffer[offset]
                elif type == INT16:
                    return int.from_bytes(self.buffer[offset:offset+2], "big")
                elif type == INT32:
                    return int.from_bytes(self.buffer[offset:offset+4], "big")
                elif type == STRING:
                    size = int.from_bytes(self.buffer[offset:offset+4], "big")
                    return self.buffer[offset+4:offset+4+size].decode("utf-8")
                elif type == BYTES:
                    size = int.from_bytes(self.buffer[offset:offset+4], "big")
                    return self.buffer[offset+4:offset+4+size]
                elif type == SINT16:
                    value = int.from_bytes(self.buffer[offset:offset+2], "big")
                    if value >= 0x8000:
                        value -= 0x10000
                    return value
                elif type == SINT32:
                    value = int.from_bytes(self.buffer[offset:offset+4], "big")
                    if value >= 0x80000000:
                        value -= 0x100000000
                    return value
        raise AttributeError("No such attribute: %s" % name)

    def __setattr__(self, name, value):
        for (n, type, offset) in self.FIELD_DEF:
            offset = offset + len(self.CMD)
            if n == name:
                if type == INT8:
                    self.buffer[offset] = value
                elif type == INT16:
                    self.buffer[offset:offset+2] = value.to_bytes(2, "big")
                elif type == INT32:
                    self.buffer[offset:offset+4] = value.to_bytes(4, "big")
                elif type == STRING:
                    self.buffer[offset:offset+4] = len(value).to_bytes(4, "big")
                    self.buffer[offset+4:] = value.encode("utf-8")
                elif type == BYTES:
                    self.buffer[offset:offset+4] = len(value).to_bytes(4, "big")
                    self.buffer[offset+4:] = value
                elif type == SINT16:
                    if value < 0:
                        value += 0x10000
                    self.buffer[offset:offset+2] = value.to_bytes(2, "big")
                elif type == SINT32:
                    if value < 0:
                        value += 0x100000000
                    self.buffer[offset:offset+4] = value.to_bytes(4, "big")
                return

    def dump(self):
        print(self.__class__.__name__, end="(")
        for (name, type, offset) in self.FIELD_DEF:
            if name.startswith("__"):
                continue
            elif type == BYTES:
                print(name, ": ...", end=", ")
            else:
                print(name, ":", self.__getattr__(name), end=", ")
        print(")")


class Hello(BarrierMessage):
    """
    Hello, server -> client
    """
    CMD = "Barrier"
    FIELD_DEF = [
        ("minor", INT16, 0),
        ("major", INT16, 2),
    ]

    def __init__(self, **fields):
        if fields:
            self.buffer = bytearray(7 + 4)
        super().__init__(**fields)


class HelloBack(BarrierMessage):
    """
    HelloBack, client -> server
    """
    CMD = "Barrier"
    FIELD_DEF = [
        ("minor", INT16, 0),
        ("major", INT16, 2),
        ("name", STRING, 4),
    ]

    def __init__(self, **fields):
        if fields:
            self.buffer = bytearray(7 + 4 + len(fields["name"].encode("utf-8")))
        super().__init__(**fields)


class DInfo(BarrierMessage):
    """
    DInfo, client -> server
    """
    CMD = "DINF"
    FIELD_DEF = [
        ("x_origin", INT16, 0),
        ("y_origin", INT16, 2),
        ("width", INT16, 4),
        ("height", INT16, 6),
        ("__unknown__", INT16, 8),
        ("x", INT16, 10),
        ("y", INT16, 12),
    ]

    def __init__(self, **fields):
        if fields:
            self.buffer = bytearray(4 + 14)
        super().__init__(**fields)


class CNoop(BarrierMessage):
    """
    CNoop, client -> server
    """
    CMD = "CNOP"

    def __init__(self):
        self.buffer = bytearray(4)
        super().__init__()


class CClose(BarrierMessage):
    """
    CClose, server -> client
    """
    CMD = "CBYE"

    def __init__(self):
        self.buffer = bytearray(4)
        super().__init__()


class CEnter(BarrierMessage):
    """
    CEnter, server -> client
    """
    CMD = "CINN"
    FIELD_DEF = [
        ("x", INT16, 0),
        ("y", INT16, 2),
        ("seq", INT32, 4),
        ("modifier", INT16, 8),
    ]

    def __init__(self, **fields):
        self.buffer = bytearray(4 + 10)
        super().__init__(**fields)

class CLeave(BarrierMessage):
    """
    CLeave, server -> client
    """
    CMD = "COUT"

    def __init__(self):
        self.buffer = bytearray(4)
        super().__init__()

class CClipboard(BarrierMessage):
    """
    CClipboard, server -> client
    """
    CMD = "CCLP"
    FIELD_DEF = [
        ("id", INT8, 0),
        ("seq", INT32, 1),
    ]

    def __init__(self, **fields):
        if fields:
            self.buffer = bytearray(4 + 5)
        super().__init__(**fields)

class CScreenSaver(BarrierMessage):
    """
    CScreenSaver, server -> client
    """
    CMD = "CSEC"
    FIELD_DEF = [
        ("started", INT8, 0),
    ]

    def __init__(self, **fields):
        if fields:
            self.buffer = bytearray(4 + 1)
        super().__init__(**fields)

class CResetOptions(BarrierMessage):
    """
    CResetOptions, server -> client
    """
    CMD = "CROP"

    def __init__(self):
        self.buffer = bytearray(4)
        super().__init__()

class CInfoAck(BarrierMessage):
    """
    CInfoAck, server -> client
    """
    CMD = "CIAK"

    def __init__(self):
        self.buffer = bytearray(4)
        super().__init__()


class CKeepAlive(BarrierMessage):
    """
    CKeepAlive, server -> client
    """
    CMD = "CALV"

    def __init__(self):
        self.buffer = bytearray(4)
        super().__init__()

class DKeyDown(BarrierMessage):
    """
    DKeyDown, server -> client
    """
    CMD = "DKDN"
    FIELD_DEF = [
        ("keyid", INT16, 0),
        ("modifier", INT16, 2),
        ("button", INT16, 4),
    ]

    def __init__(self, **fields):
        if fields:
            self.buffer = bytearray(4 + 6)
        super().__init__(**fields)

class DKeyRepeat(BarrierMessage):
    """
    DKeyRepeat, server -> client
    """
    CMD = "DKRP"
    FIELD_DEF = [
        ("keyid", INT16, 0),
        ("modifier", INT16, 2),
        ("repeat", INT16, 4),
        ("button", INT16, 6),
    ]

    def __init__(self, **fields):
        if fields:
            self.buffer = bytearray(4 + 8)
        super().__init__(**fields)

class DKeyUp(BarrierMessage):
    """
    DKeyUp, server -> client
    """
    CMD = "DKUP"
    FIELD_DEF = [
        ("keyid", INT16, 0),
        ("modifier", INT16, 2),
        ("button", INT16, 4),
    ]

    def __init__(self, **fields):
        if fields:
            self.buffer = bytearray(4 + 6)
        super().__init__(**fields)


class DMouseDown(BarrierMessage):
    """
    DMouseDown, server -> client
    """
    CMD = "DMDN"
    FIELD_DEF = [
        ("button", INT8, 0),
    ]

    def __init__(self, **fields):
        if fields:
            self.buffer = bytearray(4 + 1)
        super().__init__(**fields)

class DMouseUp(BarrierMessage):
    """
    DMouseUp, server -> client
    """
    CMD = "DMUP"
    FIELD_DEF = [
        ("button", INT8, 0),
    ]

    def __init__(self, **fields):
        if fields:
            self.buffer = bytearray(4 + 1)
        super().__init__(**fields)

class DMouseMove(BarrierMessage):
    """
    DMouseMove, server -> client
    """
    CMD = "DMMV"
    FIELD_DEF = [
        ("x", INT16, 0),
        ("y", INT16, 2),
    ]

    def __init__(self, **fields):
        if fields:
            self.buffer = bytearray(4 + 4)
        super().__init__(**fields)

class DMouseRelMove(BarrierMessage):
    """
    DMouseRelMove, server -> client
    """
    CMD = "DMRM"
    FIELD_DEF = [
        ("x", INT16, 0),
        ("y", INT16, 2),
    ]

    def __init__(self, **fields):
        if fields:
            self.buffer = bytearray(4 + 4)
        super().__init__(**fields)

class DMouseWheel(BarrierMessage):
    """
    DMouseWheel, server -> client
    """
    CMD = "DMWM"
    FIELD_DEF = [
        ("x", SINT16, 0),
        ("y", SINT16, 2),
    ]
    
    def __init__(self, **fields):
        if fields:
            self.buffer = bytearray(4 + 4)
        super().__init__(**fields)

class DClipboard(BarrierMessage):
    """
    DClipboard, server -> client
    """
    CMD = "DCLP"
    FIELD_DEF = [
        ("id", INT8, 0),
        ("seq", INT32, 1),
        ("mark", INT8, 5),
        ("data", BYTES, 6),
    ]

    def __init__(self, **fields):
        if fields:
            self.buffer = bytearray(4 + 6 + len(fields["data"].encode("utf-8")))
        super().__init__(**fields)


# TODO:
class DSetOptions(BarrierMessage):
    """
    DSetOptions, server -> client
    """
    CMD = "DSOP"
    FIELD_DEF = [
        ("x", INT16, 0),
        ("y", INT16, 2),
    ]

    def __init__(self, **fields):
        if fields:
            self.buffer = bytearray(4 + 2)
        super().__init__(**fields)

class DFileTransfer(BarrierMessage):
    """
    DFileTransfer, server -> client
    """
    CMD = "DFTR"
    FIELD_DEF = [
        ("mark", INT8, 0),
        ("content", BYTES, 1),
    ]

    def __init__(self, **fields):
        if fields:
            self.buffer = bytearray(4 + 1 + len(fields["content"].encode("utf-8")))
        super().__init__(**fields)


class DDragInfo(BarrierMessage):
    """
    DDragInfo, server -> client
    """
    CMD = "DDRG"
    FIELD_DEF = [
        ("nb", INT16, 0),
        ("content", BYTES, 2),
    ]

    def __init__(self, **fields):
        if fields:
            self.buffer = bytearray(4 + 2 + len(fields["content"].encode("utf-8")))
        super().__init__(**fields)


class QInfo(BarrierMessage):
    """
    QInfo, server -> client
    """
    CMD = "QINF"

    def __init__(self):
        self.buffer = bytearray(4)
        super().__init__()

class EIncompatible(BarrierMessage):
    """
    EIncompatible, server -> client
    """
    CMD = "EICV"
    FIELD_DEF = [
        ("minor", INT16, 0),
        ("major", INT16, 2),
    ]

    def __init__(self, **fields):
        if fields:
            self.buffer = bytearray(4)
        super().__init__(**fields)

class EBusy(BarrierMessage):
    """
    EBusy, server -> client
    """
    CMD = "EBSY"

    def __init__(self):
        self.buffer = bytearray(4)
        super().__init__()

class EUnknown(BarrierMessage):
    """
    EUnknown, server -> client
    """
    CMD = "EUNK"

    def __init__(self):
        self.buffer = bytearray(4)
        super().__init__()

class EBad(BarrierMessage):
    """
    EBad, server -> client
    """
    CMD = "EBAD"

    def __init__(self):
        self.buffer = bytearray(4)
        super().__init__()


MESSAGES = {
    "Barr": Hello,
    "DINF": DInfo,
    "CNOP": CNoop,
    "CBYE": CClose,
    "CINN": CEnter,
    "COUT": CLeave,
    "CCLP": CClipboard,
    "CSEC": CScreenSaver,
    "CROP": CResetOptions,
    "CIAK": CInfoAck,
    "CALV": CKeepAlive,
    "DKDN": DKeyDown,
    "DKRP": DKeyRepeat,
    "DKUP": DKeyUp,
    "DMDN": DMouseDown,
    "DMUP": DMouseUp,
    "DMMV": DMouseMove,
    "DMRM": DMouseRelMove,
    "DMWM": DMouseWheel,
    "DCLP": DClipboard,
    "DSOP": DSetOptions,
    "DFTR": DFileTransfer,
    "DDRG": DDragInfo,
    "QINF": QInfo,
    "EICV": EIncompatible,
    "EBSY": EBusy,
    "EUKN": EUnknown,
    "EBAD": EBad,
}

def decode_message(buffer):
    t = buffer[0:4].decode("utf-8")
    msg = MESSAGES[t]()
    msg.buffer = buffer
    return msg

class BarrierClient:
    def __init__(self, server, port, width, height, name):
        self.seq = 0
        self.width = width
        self.height = height
        self.x = width // 2
        self.y = height // 2
        self.name = name
        self.size_buf = bytearray(4)
        self.socket = utils.connect(host=server, port=port)
    
    def run(self):
        while True:
            message = self.read_message()
            if message is None:
                continue
            # print("Received message", end=": ")
            # message.dump()
            self.on_message(message)
    
    def on_message(self, message):
        if isinstance(message, Hello):
            self.send_message(HelloBack(major = message.major, minor = message.minor, name=self.name))
        elif isinstance(message, CKeepAlive):
            self.send_message(CNoop())
        elif isinstance(message, QInfo):
            self.send_message(self.get_info())
        elif isinstance(message, CEnter):
            utils.set_led(0, 128, 0) # Light green
            self.seq = message.seq
            self.move_mouse(message.x, message.y)
        elif isinstance(message, CLeave):
            utils.set_led(0, 32, 0) # Dim green
        elif isinstance(message, DMouseMove):
            self.move_mouse(message.x, message.y)
        elif isinstance(message, DMouseRelMove):
            self.move_mouse(self.x + message.x, self.y + message.y)
        elif isinstance(message, DMouseWheel):
            pass
        elif isinstance(message, DKeyDown):
            self.send_key(message.keyid, message.modifier, message.button,)
        elif isinstance(message, DKeyRepeat):
            for n in range(message.repeat):
                self.send_key(message.keyid, message.modifier, message.button)
        elif isinstance(message, DKeyUp):
            self.send_key(message.keyid, message.modifier, message.button, False)
    
    def get_info(self):
        return DInfo(x_origin=0, y_origin=0, width=self.width, height=self.height, x=self.x, y=self.y)
    
    def send_message(self, message):
        print("Sending message", end=": ")
        message.dump()
        utils.write_int(self.socket, len(message))
        utils.write_buf(self.socket, message.buffer)

    def read_message(self):
        size = utils.read_int(self.socket)
        buffer = utils.read_buf(self.socket, size)
        if buffer is None:
            return None
        return decode_message(buffer)
    
    def move_mouse(self, x, y):
        utils.move_mouse_rel(x-self.x, y-self.y)
        self.x = x
        self.y = y
    
    def send_key(self, id, modifier, button, down=True):
        print("Key", id, "button", button, "pressed" if down else "released")
        if down:
            utils.key_down(id, modifier, button)
        else:
            utils.key_up(id, modifier, button)
