from openocd import OpenOcd
import time

with OpenOcd() as oocd:
    oocd.halt()
    registers = oocd.read_registers(['pc', 'sp'])

    print('Program counter: 0x%x' % registers['pc'])
    print('Stack pointer: 0x%x' % registers['sp'])

    cmd = 'read_memory 0x29000000 32 1'
    res = oocd.execute(cmd)
    print(res)

    oocd.resume()