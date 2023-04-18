from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection

import json


# 读取elf文件获得其中的全局变量，返回其名称:[地址]
def get_global_var(elf_file):
    global_var = {}
    for section in elf_file.iter_sections():
        if not isinstance(section, SymbolTableSection):
            continue
        if section['sh_entsize'] == 0:
            continue
        for symbol in section.iter_symbols():
            if symbol['st_info']['type'] == 'STT_OBJECT' and symbol['st_info']['bind'] == 'STB_GLOBAL':
                global_var[symbol.name] = [hex(symbol['st_value'])]
    return global_var


# 返回基本类型对应的 DIE
def get_type_die(dwarf_info, addr):
    type_die = dwarf_info.get_DIE_from_refaddr(addr)
    while type_die.tag != 'DW_TAG_base_type':
        addr = type_die.attributes['DW_AT_type'].value + type_die.cu.cu_offset
        type_die = dwarf_info.get_DIE_from_refaddr(addr)
    return type_die


# 读取所有变量的基本类型
def get_data_type(dwarf_info, elf_data: dict):
    for CU in dwarf_info.iter_CUs():
        for DIE in CU.iter_DIEs():
            if DIE.tag == 'DW_TAG_variable':
                try:
                    name = DIE.attributes['DW_AT_name'].value.decode('utf-8')
                    if name in elf_data:
                        # 获取地址时，使用 DW_AT_type 的偏移地址 + CU(编译单元的地址)
                        addr = DIE.attributes['DW_AT_type'].value + CU.cu_offset
                        type_die = get_type_die(dwarf_info, addr)
                        data_type = type_die.attributes['DW_AT_name'].value.decode('utf-8')
                        # 避免重复添加类型
                        if len(elf_data[name]) == 1:
                            elf_data[name].append(data_type)
                # 忽略 DIE 不具有属性 DW_AT_name 导致的异常
                except KeyError as e:
                    None
    return elf_data


with open('trace_read_symbol/test_mcu0.exe', 'rb') as f:
    elf = ELFFile(f)
    dwarfinfo = elf.get_dwarf_info()
    # 读取全局变量和地址,存入字典
    data_set = get_global_var(elf)
    # 读取变量类型,存入字典
    data_set = get_data_type(dwarfinfo, data_set)
    # JSON格式化打印输出
    print(json.dumps(data_set, sort_keys=True, indent=4))
