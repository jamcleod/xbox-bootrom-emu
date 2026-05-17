import smallworld
import struct

class PcieControllerModel(smallworld.state.models.MemoryMappedModel):
    def __init__(self):
        super().__init__(0x010a0000, 0x1000)

    def on_read(self, emu, addr, size, _) -> bytes:
        pass

    def on_write(self, emu, addr, size, data):
        assert size == 4
        val = struct.unpack('<L', data)[0]

        match addr:
            case 0x10a0008 | 0x10a0014 | 0x10a0018 | 0x10a0174:
                print(f"PCIe config+{hex(addr - 0x10a0000)} val={hex(val)}")

            case _:
                pc = emu.read_register("pc")
                raise NotImplementedError(f"PCIe Controller Write pc={hex(pc)} addr={hex(addr)} val={hex(val)}")
