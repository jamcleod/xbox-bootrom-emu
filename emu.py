#!/usr/bin/env -S nix develop github:smallworld-re/smallworld -c python

import smallworld
import logging
import struct

from mpu import AddMpuRegionModel, SetMpuEnableModel, ConfigureMpuSubregion, RUN_IN_USER_JAIL_ADDR, run_in_user_jail_start
from mmio.fuses import ProdFuseModel, EntitlementFuseModel, SecFlagsFuseModel, UnkFusesModel, FuseCalibrationControllerModel
from mmio.gpio import GpioModel, DebugStatusModel
from mmio.sysctrl import SystemControlModel, SystemStatusModel
from mmio.mem_ctrl import UnkMemoryControllerModel
from mmio.emmc import EmmcControllerModel
from mmio.pcie import PcieControllerModel
from mmio.crypto import CryptoEngineModel
from mmio.soc_cfg import SocConfigModel
from mmio.i2c import I2cControllerModel
from mmio.timer import TimerModel
from mmio.otp import OtpModel

class IgnoreAccess(smallworld.state.models.MemoryMappedModel):
    def on_read(self, e, a, s, _):
        pass

    def on_write(self, e, a, s, _):
        pass

# Set up logging
smallworld.logging.setup_logging(level=logging.INFO)
#smallworld.logging.setup_logging(level=logging.DEBUG)

# Define the platform
platform = smallworld.platforms.Platform(
    smallworld.platforms.Architecture.ARM_V7R, smallworld.platforms.Byteorder.LITTLE
)

# Create a machine to hold all of our state
machine = smallworld.state.Machine()

# Create a CPU for our platform and add it to the machine
cpu = smallworld.state.cpus.CPU.for_platform(platform)
machine.add(cpu)

with open('xbox_bootrom.bin', 'rb') as f:
    bootrom_bytes = f.read()

# Add code
code = smallworld.state.memory.code.Executable.from_bytes(bootrom_bytes, address=0xffff_0000)
machine.add(code)

# Add RAM
ram = smallworld.state.memory.Memory(0x00f0_0000, 0x2000)
machine.add(ram)

# Add more RAM
RAM_START = 0x00038000
RAM_SIZE = 0x00008000
ram38000 = smallworld.state.memory.Memory(RAM_START, RAM_SIZE)
machine.add(ram38000)

# Add SRAM
SRAM_START = 0x0003B000
SRAM_SIZE = 0x2000
sram = smallworld.state.memory.Memory(SRAM_START, SRAM_SIZE)
machine.add(sram)

# Set the instruction pointer to the code entrypoint
cpu.pc.set(code.address)

# We need to establish when we want to stop
machine.add_exit_point(0xffff_276e)

# Add MPU configuration function models
machine.add(AddMpuRegionModel())
machine.add(SetMpuEnableModel())
machine.add(ConfigureMpuSubregion())

# Add GPIO MMIO device
machine.add(GpioModel())
machine.add(DebugStatusModel())

# Add eFUSE MMIO devices
machine.add(ProdFuseModel())
machine.add(EntitlementFuseModel())
machine.add(SecFlagsFuseModel())
machine.add(UnkFusesModel())
machine.add(FuseCalibrationControllerModel())

# Add system control MMIO device
machine.add(SystemControlModel())
machine.add(SystemStatusModel())
machine.add(IgnoreAccess(0x7002800, 4))

# Memory timing stuff
machine.add(IgnoreAccess(0x07830000, 0x1000))

# Add I2C Controller
machine.add(I2cControllerModel())

# Timer
machine.add(TimerModel())

# OTP
machine.add(OtpModel())

# Memory controller of some form maybe?
machine.add(UnkMemoryControllerModel())

# eMMC (Southbridge PCIe?)
machine.add(EmmcControllerModel())
machine.add(PcieControllerModel())

# No clue, 0x1030314
machine.add(IgnoreAccess(0x1030314, 4))

# SoC Configuration Registers
machine.add(SocConfigModel())

# idk
machine.add(IgnoreAccess(0x01040198, 4))
machine.add(IgnoreAccess(0x01093034, 4))
machine.add(IgnoreAccess(0x01029000, 0x198))

class Idfk(smallworld.state.models.MemoryMappedModel):
    def __init__(self):
        super().__init__(0x010400a4, 4)

    def on_read(self, e, a, s, _):
        return struct.pack('<L', 0x20000000 | 8 | 4)

    def on_write(self, e, a, s, _):
        #raise Exception("Idfk write")
        pass

machine.add(Idfk())
machine.add(IgnoreAccess(0x01022250, 4))
machine.add(IgnoreAccess(0x01045000, 0x1000))
machine.add(IgnoreAccess(0x0107fb00, 8))

# SRAM Init Model
class SramInitModel(smallworld.state.models.Model):
    name = "sram_init"
    platform = platform
    abi = smallworld.platforms.ABI.NONE

    def model(self, emu):
        pass

machine.add(SramInitModel(0xffff5160))

# Assorted configurations
machine.add(IgnoreAccess(0x010464b4, 4))
machine.add(IgnoreAccess(0x0107c00c, 4))
machine.add(IgnoreAccess(0x0104e3fc, 4))
machine.add(IgnoreAccess(0x01048900, 4))
machine.add(IgnoreAccess(0x01061fec, 4))
machine.add(IgnoreAccess(0x0104ac0c, 4))
machine.add(IgnoreAccess(0x01070800, 4))
machine.add(IgnoreAccess(0x010498f4, 4))

# Crypto Engine Controller
machine.add(CryptoEngineModel())

# Create a unicorn emulator.
unicorn = smallworld.emulators.UnicornEmulator(platform)

# Add hook to start of `run_in_usr_jail` function to print out the jail entrypoint
unicorn.hook_instruction(RUN_IN_USER_JAIL_ADDR, run_in_user_jail_start)

# Emulate our machine
machine = machine.emulate(unicorn)
