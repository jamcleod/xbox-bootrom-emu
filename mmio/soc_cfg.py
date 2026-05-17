import smallworld
import struct

class SocConfigModel(smallworld.state.models.MemoryMappedModel):
    def __init__(self):
        super().__init__(0x01080000, 0x1c)

        self.storage = {}

    def on_read(self, emu, addr, size, _) -> bytes:
        assert size == 4

        match addr:
            case 0x01080000 | 0x01080004 | 0x01080008 | 0x0108000c | 0x01080010 | 0x01080018:
                val = self.storage.get(addr, 0)
                print(f"soc_cfg: Read {hex(addr)} = {hex(val)}")

                return struct.pack("<L", val)

            case _:
                pc = emu.read_register("pc")
                raise NotImplementedError(f"Read unsupported SocConfig register addr=0x{addr:08X} pc=0x{pc:08X}")

    def on_write(self, emu, addr, size, data):
        assert size == 4
        val = struct.unpack("<L", data)[0]

        match addr:
            case 0x01080000 | 0x01080004 | 0x01080008 | 0x0108000c | 0x01080010 | 0x01080018:
                self.storage[addr] = val

            case _:
                pc = emu.read_register("pc")
                raise NotImplementedError(f"Write unsupported SocConfig addr={hex(addr)} pc={hex(pc)} val={hex(val)}")
