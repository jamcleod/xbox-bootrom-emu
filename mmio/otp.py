import smallworld
import struct

class OtpModel(smallworld.state.models.MemoryMappedModel):
    def __init__(self):
        super().__init__(0x01021000, 8)

    def on_read(self, emu, addr, size, _) -> bytes:
        assert size == 4

        match addr:
            case 0x01021000:
                val = 0

            case 0x01021004:
                val = 0

            case _:
                raise NotImplementedError(f" addr={hex(addr)}")

        return struct.pack("<L", val)

    def on_write(self, emu, addr, size, data):
        raise Exception("Writes not supported in OTP model")
