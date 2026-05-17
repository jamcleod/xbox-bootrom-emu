import smallworld
import struct

# Honestly might not be a memory controller? idk
class UnkMemoryControllerModel(smallworld.state.models.MemoryMappedModel):
    def __init__(self):
        super().__init__(0x01010000, 0x18)

        self.unk0 = 0
        self.unk4 = 2
        #self.unk8 = 0x200000
        self.unk14 = 0

    def on_read(self, emu, addr, size, _) -> bytes:
        assert size == 4

        match addr:
            case 0x01010000:
                val = self.unk0

            case 0x01010004:
                val = self.unk4

            case 0x01010008:
                val = 0x200000

            case 0x01010014:
                val = self.unk14

            case _:
                pc = emu.read_register("pc")
                raise NotImplementedError(f"UnkMemoryController read fail pc={hex(pc)} addr={hex(addr)}")

        return struct.pack("<L", val)

    def on_write(self, emu, addr, size, data):
        assert size == 4

        val = struct.unpack("<L", data)[0]

        match addr:
            case 0x01010000:
                self.unk0 = val

            case 0x01010004:
                self.unk4 = val

            case 0x01010008:
                pass #self.unk8 = val

            case 0x01010014:
                self.unk14 = val

            case _:
                pc = emu.read_register("pc")
                raise NotImplementedError(f"UnkMemoryController write fail pc={hex(pc)} addr={hex(addr)} val={hex(val)}")

        print(f"[mem_ctrl.unk] *{hex(addr)} = {hex(val)}")
