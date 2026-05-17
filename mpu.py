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

    def __init__(self):
        super().__init__(ADD_MPU_REGION_ADDR)

    def model(self, emu):
        global mpu_regions

        region_num = emu.read_register("r0")
        base_addr = emu.read_register("r1")
        size_enable = emu.read_register("r2")
        perms = emu.read_register("r3")

        mpu_regions.append([region_num, base_addr, size_enable, perms])

def perms_to_strs(perms: int) -> (str, str):
    xn = (perms >> 12) & 1
    ap = (perms >> 8) & 0b111
    
    x = 'x' if xn == 0 else '-'
    return [
        ('---', '---'),
        ('rw'+x, '---'),
        ('rw'+x, 'r-'+x),
        ('rw'+x, 'rw'+x),
        ('???', '???'),
        ('r-'+x, '---'),
        ('r-'+x, 'r-'+x),
        ('???', '???'),
    ][ap]

class SetMpuEnableModel(smallworld.state.models.Model):
    name = "set_mpu_enable"
    platform = platform
    abi = smallworld.platforms.ABI.NONE

    def __init__(self):
        super().__init__(SET_MPU_ENABLE_ADDR)

    def model(self, emu):
        global mpu_regions

        # TODO: enforce?
        print("Configured MPU Regions:")
        for region_num, base_addr, size_enable, perms in mpu_regions:
            size_exponent = (size_enable >> 1) & 0b11111
            size = 0 if size_exponent == 0 else 2 ** (size_exponent + 1)
            enabled = (size_enable & 1) != 0
            subregion_bits = (size_enable >> 8) & 0b11111111

            pl1, pl0 = perms_to_strs(perms)

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
            enabled = " (Enabled)" if enabled else "(Disabled)"

            print(f"  [{region_num:3}] {enabled} addr=0x{base_addr:08X} size=0x{size:08X} PL1={pl1} PL0={pl0} disabled_subregions={subregion_bits:08b}")
            print(f"                   {share_text} {mem_type} ({desc})\n")

def region_num_to_index(num: int) -> int:
    global mpu_regions

    for i, region in enumerate(mpu_regions):
        if region[0] == num:
            return i

    return None

RUN_IN_USER_JAIL_ADDR = 0xffff175c

def run_in_user_jail_start(emu):
    mpu_subregion_config = emu.read_register("r0")
    jail_entrypoint = emu.read_register("r1")
    r2 = emu.read_register("r2")
    r3 = emu.read_register("r3")

    print(f"[hook] Run user jail: mpu_config=0x{mpu_subregion_config:08x} entrypoint=0x{jail_entrypoint:08x}")

class ConfigureMpuSubregion(smallworld.state.models.Model):
    name = "configure_mpu_subregion"
    platform = platform
    abi = smallworld.platforms.ABI.NONE

    def __init__(self):
        super().__init__(0xffff5212)

    # ; RGNR = r0
    # mcr    p15, 0, r0, cr6, cr2, 0
    # ; r0 = DRSR
    # mrc    p15, 0, r0, cr6, cr1, 2
    # ; r0 &= 0xffff00ff
    # bic    r0, r0, #0xff00
    # ; r1 &= 0xff
    # and    r1, r1, #0xff
    # ; r0 |= r1 << 8
    # orr.w  r0, r0, r1, lsl #8
    # ; DRSR = r0
    # mcr    p15, 0, r0, cr6, cr1, 2
    # ; r0 = 0
    # movs   r0, 0
    # ; RGNR = r0
    # mcr    p15, 0, r0, cr6, cr2, 0
    #
    # ; if (r0 != 0) goto UndefinedHandler;
    # tst    r0, r0
    # it     ne
    # udf.ne #0xff
    #
    # return;
    # bx     lr
    def model(self, emu):
        global mpu_regions

        region_num = emu.read_register("r0")
        disable_subregion_mask = emu.read_register("r1")

        i = region_num_to_index(region_num)

        # Update `mpu_region` array
        _, base_addr, size_enable, perms = mpu_regions[i]
        mpu_regions[i][2] = (size_enable & 0xffff00ff) | ((disable_subregion_mask & 0xff) << 8)

        pl1, pl0 = perms_to_strs(perms)
        size_exponent = (size_enable >> 1) & 0b11111
        size = 0 if size_exponent == 0 else 2 ** (size_exponent + 1)

        # Log update
        old_subregion_mask = (size_enable >> 8) & 0xff
        print(f"[mpu] Updated region {region_num} {old_subregion_mask:08b} -> {disable_subregion_mask:08b}")
        print(f"[mpu]   addr=0x{base_addr:08X} size=0x{size:08X} PL1={pl1} PL0={pl0}")
