import smallworld
import struct

reg_names = {
    0x0780000C: "MMIO_SYS_CTRL",
    0x07800020: "MMIO_PLL_LOCK",
    0x07800040: "MMIO_CLOCK_CTRL_40",
    0x07800044: "MMIO_CLOCK_CTRL_44",
    0x078000A0: "MMIO_KEY_SRC_A",
    0x078000A4: "MMIO_KEY_SRC_B",
    0x078000E0: "MMIO_SEC_MODE",
    0x078000E4: "MMIO_STACK_CANARY",
    0x078000F0: "MMIO_BOOT_STATUS",
}

def name(addr):
    return reg_names.get(addr, f"UNKNOWN {hex(addr)}")

class SystemControlModel(smallworld.state.models.MemoryMappedModel):
    def __init__(self):
        super().__init__(0x07800000, 0x100)

        self.storage = {}

    def on_read(self, emu, addr, size, _) -> bytes:
        assert size == 4

        val = self.storage.get(addr, 0)

        print(f"sysctrl: Read {name(addr)} = {val}")

        return struct.pack("<L", val)

    def on_write(self, emu, addr, size, data) -> bytes:
        assert size == 4
        val = struct.unpack("<L", data)[0]
        self.storage[addr] = val
        print(f"sysctrl: Write {name(addr)} = {val}")
