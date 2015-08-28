# ***************************************
# *     Author  Sadat Anwar 2015		*
# ***************************************

from __future__ import print_function
from os.path import isfile, join
import pypruss
import struct
import mmap
import subprocess

# Base folder fariables
binary_folder = "../bin/"
assembler_folder = "../assembler/"
header_folder = "../header/"
output_folder = "../msp_out/"

# Reset PRU binary location
reset_pru_bin = binary_folder + "reset.bin"

# Power up the Device by making VCC high (P8_13)
GPIO0_offset = 0x44E07000
GPIO0_size = 0x44E07fff - GPIO0_offset
GPIO_OE = 0x134
GPIO_SETDATAOUT = 0x194
GPIO_CLEARDATAOUT = 0x190
VCC = 1 << 23

# Compile binary file
def compile_assembler(file_name):
    p = subprocess.Popen(["pasm", "-b", file_name], cwd=binary_folder)
    p.wait()


def resetPRU(start_stop):
    for PRU in range(0, 2):
        if isfile(reset_pru_bin):
            pypruss.init()  # Init the PRU
            pypruss.open(1)  # Open PRU event 0 which is PRU0_ARM_INTERRUPT
            pypruss.pruintc_init()  # Init the interrupt controller
            pypruss.exec_program(PRU, reset_pru_bin)  # Load firmware "mem_write.bin" on PRU 0
            pypruss.wait_for_event(1)  # Wait for event 0 which is connected to PRU0_ARM_INTERRUPT
            print("PRU " + str(PRU) + " " + start_stop)
            pypruss.clear_event(1)  # Clear the event
            pypruss.exit()
        else:
            compile_assembler(header_folder + "reset.p")

# Reset the GPIO on both PRU
resetPRU("shut down")

with open("/dev/mem", "r+b") as f:
    mem = mmap.mmap(f.fileno(), GPIO0_size, offset=GPIO0_offset)

mem[GPIO_CLEARDATAOUT:GPIO_CLEARDATAOUT + 4] = struct.pack("<L", VCC)
