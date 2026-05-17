import smallworld
import struct

class GpioModel(smallworld.state.models.MemoryMappedModel):
    def __init__(self):
        super().__init__(0x07008114, 8)

        # all disabled by default
        self.enabled_bits = 0b000000
        self.gpio_state = 0b000000

    def gpio_read(self) -> bytes:
        return struct.pack('<L', self.gpio_state)

    def gpio_write(self, val: int):
        print(f"POST: {hex(val)}")
        self.gpio_state = val

    def gpio_enable_read(self) -> bytes:
        return struct.pack('<L', self.enabled_bits)

    def gpio_enable_write(self, val: int):
        self.enabled_bits = val

        states = [f"{i}=" + ("enabled" if ((val >> i) & 1) != 0 else "disabled") for i in range(6)]

        print("GPIOs Reconfigured: ", " ".join(states))

    def on_read(self, emu, addr, size, _) -> bytes:
        assert size == 4

        match addr:
            case 0x07008114:
                return self.gpio_read()

            case 0x07008118:
                return self.gpio_enable_read()

            case _:
                raise NotImplementedError(f"Invalid GPIO MMIO access address {hex(addr)}")

    def on_write(self, emu, addr, size, data) -> bytes:
        assert size == 4

        val = struct.unpack('<L', data)[0]

        match addr:
            case 0x07008114:
                return self.gpio_write(val)

            case 0x07008118:
                return self.gpio_enable_write(val)

            case _:
                raise NotImplementedError(f"Invalid GPIO MMIO access address {hex(addr)}")

# 0x07801000:"MMIO_CLOCK_STATUS", 0x07801004:"MMIO_STAGE_DEBUG",
class DebugStatusModel(smallworld.state.models.MemoryMappedModel):
    def __init__(self):
        super().__init__(0x07801000, 8)

    def on_read(self, emu, addr, size, _) -> bytes:
        assert size == 4

        match addr:
            case 0x07801000:
                return struct.pack('<L', 0)

            case _:
                raise NotImplementedError(f"Invalid DebugStatus MMIO access address {hex(addr)}")

    def on_write(self, emu, addr, size, data) -> bytes:
        assert size == 4

        val = struct.unpack('<L', data)[0]

        match addr:
            case 0x07801000:
                if val & 0x100_0000 != 0:
                    print("DebugStatusModel: marked as ready to send")
            case 0x07801004:
                print(f"POST code / Debug boot progress: {hex(val)}")

            case _:
                raise NotImplementedError(f"Invalid DebugStatus MMIO access address {hex(addr)}")
