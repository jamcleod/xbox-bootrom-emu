#!/usr/bin/env -S nix develop github:smallworld-re/smallworld -c python

import smallworld
import logging

from mpu import AddMpuRegionModel, SetMpuEnableModel, ADD_MPU_REGION_ADDR, SET_MPU_ENABLE_ADDR
from mmio.fuses import ProdFuseModel, EntitlementFuseModel, SecFlagsFuseModel
from mmio.gpio import GpioModel, DebugStatusModel
from mmio.sysctrl import SystemControlModel
from mmio.i2c import I2cControllerModel
from mmio.timer import TimerModel

class IgnoreAccess(smallworld.state.models.MemoryMappedModel):
    def on_read(self, e, a, s, _):
        pass

    def on_write(self, e, a, s, _):
        pass

# Set up logging
smallworld.logging.setup_logging(level=logging.INFO)

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

# Set the instruction pointer to the code entrypoint
cpu.pc.set(code.address)

# We need to establish when we want to stop
machine.add_exit_point(0xffff_276e)

# Add MPU configuration function models
machine.add(AddMpuRegionModel(ADD_MPU_REGION_ADDR))
machine.add(SetMpuEnableModel(SET_MPU_ENABLE_ADDR))

# Add GPIO MMIO device
machine.add(GpioModel())
machine.add(DebugStatusModel())

# Add eFUSE MMIO devices
machine.add(ProdFuseModel())
machine.add(EntitlementFuseModel())
machine.add(SecFlagsFuseModel())

# Add system control MMIO device
machine.add(SystemControlModel())
machine.add(IgnoreAccess(0x7002800, 4))

# Memory timing stuff
machine.add(IgnoreAccess(0x07830000, 0x1000))

# Add I2C Controller
machine.add(I2cControllerModel())

# Timer
machine.add(TimerModel())

# Create a unicorn emulator.
unicorn = smallworld.emulators.UnicornEmulator(platform)

# Emulate our machine
panda_machine = machine.emulate(unicorn)
