import smallworld
import struct

class TimerModel(smallworld.state.models.MemoryMappedModel):
    def __init__(self):
        super().__init__(0x07802000, 0x14)
        self.timer_value = 0
        self.enabled = 0

    def read_ctrl(self):
        return 0

    def write_ctrl(self, val: int):
        print(f"Timer ctrl: {hex(val)}")

    def read_enable(self):
        return self.enabled

    def write_enable(self, val: int):
        self.enabled = val

        if val == 0:
            print("Timer disabled")
        else:
            print("Timer enabled")

    def read_value(self):
        return self.timer_value

    def write_value(self, val: int):
        self.timer_value = val
        print(f"Set timer to {val}")

    def on_read(self, emu, addr, size, _) -> bytes:
        assert size == 4

        match addr:
            case 0x07802000:
                val = self.read_ctrl()
            case 0x0780200C:
                val = self.read_enable()
            case 0x07802010:
                val = self.read_value()
            case _:
                raise NotImplementedError(f"Invalid I2C MMIO access address {hex(addr)}")

        return struct.pack("<L", val)

    def on_write(self, emu, addr, size, data) -> bytes:
        assert size == 4

        val = struct.unpack('<L', data)[0]

        match addr:
            case 0x07802000:
                self.write_ctrl(val)
            case 0x0780200C:
                self.write_enable(val)
            case 0x07802010:
                self.write_value(val)
            case _:
                raise NotImplementedError(f"Invalid I2C MMIO access address {hex(addr)}")
