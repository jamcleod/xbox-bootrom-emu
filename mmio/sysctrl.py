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

        self.storage = {
            # Pretend our PCIe clock is already snychronized with the south bridge
            0x07800020: 1,
        }

    def on_read(self, emu, addr, size, _) -> bytes:
        assert size == 4

        val = self.storage.get(addr, 0)

        print(f"sysctrl: Read {name(addr)} = {val}")

        return struct.pack("<L", val)

    def on_write(self, emu, addr, size, data):
        assert size == 4
        val = struct.unpack("<L", data)[0]
        self.storage[addr] = val
        print(f"sysctrl: Write {name(addr)} = {val}")

class SystemStatusModel(smallworld.state.models.MemoryMappedModel):
    def __init__(self):
        super().__init__(0x07800400, 0x1c)

        self.status = 0
        self.config = 0
        self.flags = 0
        self.flags2 = 0

    def read_status(self):
        return self.status

    def write_status(self, val: int):
        print(f"sysstat: write status {hex(val)}")
        self.status = val

    def read_status2(self, emu):
        pc = emu.read_register("pc")
        print(f"sysstat: read status2 at pc={hex(pc)}")

        # Break out of warmboot loop
        if pc == 0xffff3934:
            return 0b1100

        return 0b100

    def read_config(self):
        return self.config

    def write_config(self, val: int):
        print(f"sysstat: write config {hex(val)}")
        self.config = val

    def write_flags(self, val: int):
        print(f"sysstat: write flags {hex(val)}")
        self.flags = val

    def read_flags(self):
        return self.flags

    def write_flags2(self, val: int):
        print(f"sysstat: write flags2 {hex(val)}")
        self.flags2 = val

    def read_flags2(self):
        return self.flags2

    def on_read(self, emu, addr, size, _) -> bytes:
        assert size == 4

        match addr:
            case 0x07800400:
                val = self.read_status()

            case 0x07800408:
                val = self.read_flags()

            case 0x0780040C:
                val = self.read_flags2()

            case 0x07800414:
                val = self.read_status2(emu)

            case 0x07800418:
                val = self.read_config()

            case _:
                pc = emu.read_register("pc")
                raise NotImplementedError(f"Read unsupported SystemStatus register addr=0x{addr:08X} pc=0x{pc:08X}")

        return struct.pack("<L", val)

    def debug_out(self, val: int):
        print(f"sysstat: debug out 0x{val:08X}")

    def on_write(self, emu, addr, size, data):
        assert size == 4
        val = struct.unpack('<L', data)[0]

        match addr:
            case 0x07800400:
                self.write_status(val)

            case 0x07800404:
                self.debug_out(val)

            case 0x07800408:
                self.write_flags(val)

            case 0x0780040C:
                self.write_flags2(val)

            case 0x07800418:
                self.write_config(val)

            case _:
                pc = emu.read_register("pc")
                raise NotImplementedError(f"Write unsupported SystemStatus register addr=0x{addr:08X} pc=0x{pc:08X} val={hex(val)}")
