from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection

symbol_dict = {}

# Open the ELF file
with open('trace_read_symbol/test_mcu0.exe', 'rb') as f:
    elf = ELFFile(f)

    #读取全局符号
    symtab = elf.get_section_by_name('.symtab')
    if symtab is not None and isinstance(symtab, SymbolTableSection):

        # Iterate over all the symbols in the symbol table
        for symbol in symtab.iter_symbols():

            # Check if the symbol is a global variable
            if symbol['st_info']['type'] == 'STT_OBJECT' and symbol['st_info']['bind'] == 'STB_GLOBAL':

                # Get the symbol name, address, and size
                symbol_name = symbol.name
                symbol_address = symbol['st_value']
                symbol_size = symbol['st_size']
                symbol_dict[symbol_name] = [hex(symbol_address), symbol_size]

                # Get the symbol type
                # symbol_type = symbol['st_info']['type']

                # Print the symbol information
                # print(f"Symbol: {symbol_name} Type: {symbol_type} Address: 0x{symbol_address:x} Size: {symbol_size}")


    dwarf_info = elf.get_dwarf_info()
    for cu in dwarf_info.iter_CUs():
        for DIE in cu.iter_DIEs():
            try:
                if DIE.tag == 'DW_TAG_variable' and DIE.attributes['DW_AT_name'].value == b'data_a':

                    # 获取DIE的DW_AT_type对应的偏移地址
                    decl_type = DIE.attributes['DW_AT_type'].value
                    # 获取DIE对应的基地址
                    cu_offset = cu.cu_offset
                    # DIE的DW_AT_type对应的地址
                    addr = cu_offset + decl_type

                    tmp_die = dwarf_info.get_DIE_from_refaddr(addr)
                    tmp_die_type = tmp_die.attributes['DW_AT_type'].value
                    cu_offset = tmp_die.cu.cu_offset
                    addr = cu_offset + tmp_die_type

                    tmp1_die = dwarf_info.get_DIE_from_refaddr(addr)
                    tmp1_die_type = tmp1_die.attributes['DW_AT_type'].value
                    cu_offset = tmp1_die.cu.cu_offset
                    addr = cu_offset + tmp1_die_type

                    tmp2_die = dwarf_info.get_DIE_from_refaddr(addr)
                    tag = tmp2_die.tag
                    size = tmp2_die.attributes['DW_AT_byte_size'].value
                    encoding = tmp2_die.attributes['DW_AT_encoding'].value
                    name = tmp2_die.attributes['DW_AT_name'].value

                    print(tmp_die)
            except Exception as e:
                    print(e.args)






