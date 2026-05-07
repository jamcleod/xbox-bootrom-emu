import smallworld

ADD_MPU_REGION_ADDR = 0xffff_5250
SET_MPU_ENABLE_ADDR = 0xffff_e5d4

platform = smallworld.platforms.Platform(
    smallworld.platforms.Architecture.ARM_V7R, smallworld.platforms.Byteorder.LITTLE
)

global mpu_regions
mpu_regions = []

# Add model for mpu region handling
class AddMpuRegionModel(smallworld.state.models.Model):
    name = "add_mpu_region"
    platform = platform
    abi = smallworld.platforms.ABI.NONE

    def model(self, emu):
        global mpu_regions

        region_num = emu.read_register("r0")
        base_addr = emu.read_register("r1")
        size_enable = emu.read_register("r2")
        perms = emu.read_register("r3")

        mpu_regions.append((region_num, base_addr, size_enable, perms))

class SetMpuEnableModel(smallworld.state.models.Model):
    name = "set_mpu_enable"
    platform = platform
    abi = smallworld.platforms.ABI.NONE

    def model(self, emu):
        global mpu_regions

        # TODO: enforce?
        print("Configured MPU Regions:")
        for region_num, base_addr, size_enable, perms in mpu_regions:
            size_exponent = (size_enable >> 1) & 0b11111
            size = 0 if size_exponent == 0 else 2 ** (size_exponent + 1)

            xn = (perms >> 12) & 1
            ap = (perms >> 8) & 0b111

            x = 'x' if xn == 0 else '-'
            pl1, pl0 = [
                ('---', '---'),
                ('rw'+x, '---'),
                ('rw'+x, 'r-'+x),
                ('rw'+x, 'rw'+x),
                ('???', '???'),
                ('r-'+x, '---'),
                ('r-'+x, 'r-'+x),
                ('???', '???'),
            ][ap]

            tex = (perms >> 3) & 0b111
            shareable = ((perms >> 2) & 1) != 0
            c = ((perms >> 1) & 1) != 0
            b = (perms & 1) != 0

            if tex & 0b100 != 0:
                desc = "Cacheable memory (not handled)"
                mem_type = "Normal"
                share = shareable
            else:
                desc, mem_type, share = {
                    (0b00, 0, 0): (                                "Strongly-ordered", "Strongly-ordered",      True),
                    (0b00, 0, 1): (                                "Shareable Device",           "Device",      True),
                    (0b00, 1, 0): ("Outer and Inner Write-Through, no Write-Allocate",           "Normal", shareable),
                    (0b00, 1, 1): (   "Outer and Inner Write-Back, no Write-Allocate",           "Normal", shareable),
                    (0b01, 0, 0): (                   "Outer and Inner Non-cacheable",           "Normal", shareable),
                    (0b01, 0, 1): (                                        "Reserved",              "???",      None),
                    (0b01, 1, 0): (                          "Implementation Defined",              "???",      None),
                    (0b01, 1, 1): (      "Outer and Inner Write-Back, Write-Allocate",           "Normal", shareable),
                    (0b10, 0, 0): (                            "Non-shareable Device",           "Device",     False),
                    (0b10, 0, 1): (                                        "Reserved",              "???",      None),
                    (0b10, 1, 0): (                                        "Reserved",              "???",      None),
                    (0b10, 1, 1): (                                        "Reserved",              "???",      None),
                    (0b11, 0, 0): (                                        "Reserved",              "???",      None),
                    (0b11, 0, 1): (                                        "Reserved",              "???",      None),
                    (0b11, 1, 0): (                                        "Reserved",              "???",      None),
                    (0b11, 1, 1): (                                        "Reserved",              "???",      None),
                }[(tex & 0b11, c, b)]

            share_text = "Shareable" if share else "Non-shareable"

            print(f"  [{region_num:3}] addr=0x{base_addr:08X} size=0x{size:08X} PL1={pl1} PL0={pl0} {share_text} {mem_type} ({desc})")
