import smallworld
import struct

class ProdFuseModel(smallworld.state.models.MemoryMappedModel):
    def __init__(self):
        super().__init__(0x07860000, 4)

    def on_read(self, emu, addr, size, _) -> bytes:
        assert size == 4

        return struct.pack("<L", 0x10)

    def on_write(self, emu, addr, size, data) -> bytes:
        raise Exception("Not supported")

class EntitlementFuseModel(smallworld.state.models.MemoryMappedModel):
    def __init__(self):
        super().__init__(0x07860028, 4)

    def on_read(self, emu, addr, size, _) -> bytes:
        assert size == 4

        return struct.pack("<L", 0xfc0)

    def on_write(self, emu, addr, size, data) -> bytes:
        raise Exception("Not supported")

class SecFlagsFuseModel(smallworld.state.models.MemoryMappedModel):
    def __init__(self):
        super().__init__(0x0786104C, 4)

    def on_read(self, emu, addr, size, _) -> bytes:
        assert size == 4

        return struct.pack("<L", 0x80) # enable debug

    def on_write(self, emu, addr, size, data) -> bytes:
        raise Exception("Not supported")
