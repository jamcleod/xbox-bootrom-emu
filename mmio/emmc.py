import smallworld
import struct

READ_BUFFER_ADDR = 0x01000134
READ_BUFFER_SIZE = 0x40

INITIAL_CONFIG_REGS = [0x01000000, 0x01000004, 0x0100000c, 0x01000010, 0x0100001c, 0x01000020, 0x01000024, 0x01000028, 0x0100002C, 0x01000030, 0x01000034, 0x01000038, 0x0100003C, 0x01000040, 0x0100008C, 0x01000094, 0x0100009C, 0x010000A4, 0x010000AC, 0x010000E4, 0x010000DC, 0x01000110]

class EmmcControllerModel(smallworld.state.models.MemoryMappedModel):
    def __init__(self):
        super().__init__(0x01000000, 0x198)

        self.unk_config = 0x10

        self.configured_pos = 0
        self.internal_buffer = bytes(0 for _ in range(0x40))

    def fill_internal_buffer(self):
        with open("flash.bin", "rb") as f:
            f.seek(self.configured_pos)
            self.internal_buffer = f.read(0x40)

    def read_is_data_ready(self):
        return 0x10

    def write_is_data_ready(self, val):
        if val & 1 != 0:
            print(f"[emmc] Data read requested for pos={hex(self.internal_buffer)}")
            self.fill_internal_buffer()

    def write_configured_pos(self, val):
        pos = val & 0xffffffc0
        flags = val & 0x3f

        print(f"[emmc] seek pos={hex(pos)} flags={bin(flags)}")
        self.configured_pos = pos

    def on_read(self, emu, addr, size, _) -> bytes:
        match addr:
            case 0x01000008:
                val = self.read_is_data_ready()

            case 0x01000020:
                val = 0

            case 0x01000080:
                val = self.unk_config

            case 0x01000194:
                val = 0

            case read_addr if read_addr in range(READ_BUFFER_ADDR, READ_BUFFER_ADDR + READ_BUFFER_SIZE):
                read_pos_in_buffer = read_addr - READ_BUFFER_ADDR

                return self.internal_buffer[read_pos_in_buffer:read_pos_in_buffer + size]

            case _:
                pc = emu.read_register("pc")
                raise NotImplementedError(f"Read unsupported emmc controller register addr=0x{addr:08X} pc=0x{pc:08X}")

        assert size == 4
        return struct.pack("<L", val)

    def on_write(self, emu, addr, size, data):
        assert size == 4
        val = struct.unpack("<L", data)[0]

        match addr:
            case 0x01000008:
                self.write_is_data_ready(val)

            case _ if addr in INITIAL_CONFIG_REGS:
                print(f"[emmc] Write unk initial config+{hex(addr - 0x01000000)}={hex(val)}")

            case 0x01000014:
                self.write_configured_pos(val)

            case 0x01000018:
                print(f"[emmc] Write unk flags {hex(val)}")

            case 0x01000080:
                self.unk_config = val

            case _:
                pc = emu.read_register("pc")
                raise NotImplementedError(f"Write unsupported emmc controller register addr=0x{addr:08X} pc=0x{pc:08X} val={hex(val)}")
