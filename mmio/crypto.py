import smallworld
import struct

REG_NAMES = {
    0x07820044:"MMIO_CRYPTO_PLL",
    0x07820048:"MMIO_CRYPTO_CONFIG",
    0x07820060:"MMIO_CRYPTO_WARMUP",
    0x07820180:"MMIO_CRYPTO_KICK_LO",
    0x078201C0:"MMIO_CRYPTO_KICK_HI",
    0x07820184:"MMIO_CRYPTO_DMA_CTRL",
    0x07820188:"MMIO_CRYPTO_DMA_LEN",
    0x0782018C:"MMIO_CRYPTO_SRC_MASK",
    0x07820190:"MMIO_CRYPTO_SRC_OFF",
    0x07820194:"MMIO_CRYPTO_DST_MASK",
    0x07820198:"MMIO_CRYPTO_DST_OFF",
    0x0782019C:"MMIO_CRYPTO_IV_0",
    0x078201A8:"MMIO_CRYPTO_IV_3",
    0x078201C4:"MMIO_CRYPTO_KSEL_0",
    0x078201C8:"MMIO_CRYPTO_KSEL_1",
    0x078201CC:"MMIO_CRYPTO_KSEL_2",
    0x07820210:"MMIO_CRYPTO_STAT_0",
}

def reg_name(addr: int) -> str:
    return REG_NAMES.get(addr, f"MMIO_CRYPTO_{hex(addr)}")

class CryptoEngineModel(smallworld.state.models.MemoryMappedModel):
    def __init__(self):
        super().__init__(0x07820000, 0x1000)

        self.storage = {
            0x7820290: 0
        }

    def read_status(self, emu):
        pc = emu.read_register("pc")
        if pc == 0xffff056c:
            val = 0
        else:
            val = 1
        #print(f"[crypto] Read MMIO_CRYPTO_STATUS = {val}")
        return val

    def on_read(self, emu, addr, size, _) -> bytes:
        assert size == 4

        match addr:
            case 0x7820048 | 0x7820060 | 0x7820290:
                val = self.storage.get(addr, 0)
                #pc = emu.read_register("pc")
                #print(f"[crypto] Read {reg_name(addr)} = {hex(val)} (pc=0x{pc:08x})")

            case 0x7820208:
                val = 0x400000

            case 0x782020c:
                val = self.read_status(emu)

            case _:
                pc = emu.read_register("pc")
                raise NotImplementedError(f"Crypto Engine Read pc={hex(pc)} addr={hex(addr)}")

        return struct.pack("<L", val)

    def on_write(self, emu, addr, size, data):
        assert size == 4
        val = struct.unpack("<L", data)[0]

        def print_log():
            pass
            #pc = emu.read_register("pc")
            #print(f"[crypto] Write {reg_name(addr)} = {hex(val)} (pc=0x{pc:08x})")

        match addr:
            case _ if addr in range(0x7820100, 0x7820300, 4):
                print_log()

            case 0x7820048 | 0x7820060:
                print_log()

            case _:
                pc = emu.read_register("pc")
                raise NotImplementedError(f"Crypto Engine Controller Write pc={hex(pc)} addr={hex(addr)} val={hex(val)}")
