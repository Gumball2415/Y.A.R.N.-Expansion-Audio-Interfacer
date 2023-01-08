# S.C.A.R.F. Expansion Audio Interfacer Address Decoder
# Firmware v.0.0.7
# Copyright (C) 2022 Persune

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


def AddressDecode(ROMAddr: int) -> int:
    # Inputs:

    # xxW REDC BA98 7654 3210
    # ||| |||| |||| |||| ||||
    # ||| |+++ ++++ ++++ ++++- CPU_A0...CPU_A14:    CPU address bus
    # ||| +--- ---- ---- ----- RomSel:              Active low, only way to determine CPU_A15
    # ||+ ---- ---- ---- ----- CPU_RW:              Low indicates write, high indicates read
    # ++- ---- ---- ---- ----- x:                   reserved for future use

    RomSel      = not ((ROMAddr >> 15) == 0x01)
    CPU_RW      = (ROMAddr >> 16) == 0x01
    CPU_addr    = (ROMAddr | ((not RomSel) << 15)) & 0xFFFF  # approximate address

    # Outputs:

    # xx543210
    # ||||||||
    # |||||||+- VRC6_Enable     Active low
    # ||||||+-- VRC7_Enable     Active low
    # |||||+--- S5B_Enable:     Active low
    # ||||+---- N163_Enable     Active high,    CPU_A14
    # |||+----- MMC5_Enable     Active high
    # ||+------ FDS_Enable      Active low
    # ++------- x:              reserved

    VRC6_Enable = False
    VRC7_Enable = False
    S5B_Enable  = False
    N163_Enable = False
    MMC5_Enable = False
    FDS_Enable  = False

    # Addresses based on https://www.nesdev.org/wiki/NSF
    # Important: mirrored registers are not supported!

    # VRC6:	 10xx 0000 0000 00xx
        # Audio registers:
            # $9003	    	 W
            # $9000-$9002	 W
            # $A000-$A002	 W
            # $B000-$B002	 W
    if not (((CPU_addr >= 0x9000 and CPU_addr <= 0x9003)
        or (CPU_addr >= 0xA000 and CPU_addr <= 0xA002)
        or (CPU_addr >= 0xB000 and CPU_addr <= 0xB002)) and (not CPU_RW)):
        VRC6_Enable = True

    # VRC7:	 1xxx 0000 00x1 0000
        # Audio registers:
            # $9010		     W
            # $9030		     W
            # $E000		     W
    if not ((CPU_addr == 0x9010 or CPU_addr == 0x9030 or CPU_addr == 0xE000) and (not CPU_RW)):
        VRC7_Enable = True

    # S5B: 11xx xxxx xxxx xxxx
        # Audio registers:
            # $C000-$DFFF	 W
            # $E000-$FFFF	 W
    if not ((CPU_addr == 0xC000 or CPU_addr == 0xE000) and (not CPU_RW)):
        S5B_Enable  = True

    # N163:	 x1xx xxxx xxxx xxxx
        # Audio registers:
            # $4800-$4FFF	RW
            # $E000-$E7FF	 W
            # $F800-$FFFF	RW
    if ((CPU_addr == 0xE000 or CPU_addr == 0xF800) and (not CPU_RW)
        or (CPU_addr == 0x4800)):
        N163_Enable = True

    # MMC5:	 0101 xxxx xxxx xxxx
        # Audio registers:
            # $5000-$5007	 W
            # $5010         RW
            # $5011          W
            # $5015         RW
            # $5205-$5206   RW      MMC5 multiplier
            # $5C00-$5FF5   RW      MMC5 internal extended RAM
    if ((((CPU_addr >= 0x5000 and CPU_addr <= 0x5007) or CPU_addr == 0x5011) and (not CPU_RW))
        or ((((CPU_addr >= 0x5C00 and CPU_addr <= 0x5FF5)))
        or (CPU_addr == 0x5015 or CPU_addr == 0x5205 or CPU_addr == 0x5206))):
        MMC5_Enable = True

    # FDS:	 0100 0000 xxxx xxxx
        # Audio registers:
            # $4023         ?
            # $4040-$4080   RW
            # $4082-$408A    W
            # $4090-$4097   R
    if not ((CPU_addr == 0x4023 or (CPU_addr >= 0x4040 and CPU_addr <= 0x4080))
        or ((CPU_addr >= 0x4082 and CPU_addr <= 0x408A) and (not CPU_RW))
        or ((CPU_addr >= 0x4090 and CPU_addr <= 0x4097) and CPU_RW)):
        FDS_Enable  = True

    return 0xFF & ((VRC6_Enable << 0) | (VRC7_Enable << 1) | (S5B_Enable << 2) | (N163_Enable << 3) | (MMC5_Enable << 4) | (FDS_Enable << 5))

print("Generating ROM...")
FileBytes = []

# for 512k PROM
for x in range(pow(2, 19)):
    byte = AddressDecode(x)
    FileBytes.append(byte)
    print("{:05x}".format(x),"{:08b}".format(byte))

print("Opening file...")
SCARFAddrFile = open("SCARFADDR.bin", "wb")

print("Writing file...")
byteformat = bytearray(FileBytes)
SCARFAddrFile.write(byteformat)


print("Closing file...")
SCARFAddrFile.close()