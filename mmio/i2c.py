import smallworld
import struct

class I2cControllerModel(smallworld.state.models.MemoryMappedModel):
    def __init__(self):
        super().__init__(0x07860400, 8)

    def cmd_read(self):
        return 1

    def status_read(self):
        return 1

    def cmd_write(self, val: int):
        print(f"I2C CMD Write {hex(val)}")

    def on_read(self, emu, addr, size, _) -> bytes:
        assert size == 4

        match addr:
            case 0x07860400:
                val = self.cmd_read()

            case 0x07860404:
                val = self.status_read()

            case _:
                raise NotImplementedError(f"Invalid I2C MMIO access address {hex(addr)}")

        return struct.pack("<L", val)

    def on_write(self, emu, addr, size, data) -> bytes:
        assert size == 4

        val = struct.unpack('<L', data)[0]

        match addr:
            case 0x07860400:
                self.cmd_write(val)
            case _:
                raise NotImplementedError(f"Invalid I2C MMIO access address {hex(addr)}")
