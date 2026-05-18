import struct

REG_BACKUP_ADDR = 0x3d000
POP_REGS = ["r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12", "lr"]

backed_up_sp = 0

def backup_sp(emu):
    global backed_up_sp

    backed_up_sp = emu.read_register("sp")

    print("Backed up SP:", hex(backed_up_sp))

def handle_syscall(emu):
    global backed_up_sp

    pc = emu.read_register("pc")
    cpsr = emu.read_register("cpsr")
    print(f"Syscall hit at pc=0x{pc:08x} cpsr={cpsr:08x}")

    for i, reg in enumerate(POP_REGS):
        mem_backup_bytes = emu.read_memory(REG_BACKUP_ADDR + (i * 4), 4)
        backup_val = struct.unpack("<L", mem_backup_bytes)[0]
        emu.write_register(reg, backup_val)
        print(f"  Restoring {reg}={hex(backup_val)}")

    emu.write_register("pc", 0xffff00e0)
    emu.write_register("sp", backed_up_sp)
