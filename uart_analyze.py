import struct


class UartAnalyze:
    def __init__(self):
        # 串口解析
        self.buffer_size = 1024 * 1024 * 100
        self.uart_data = bytearray(self.buffer_size)
        self.analyze_data_list = [[] for i in range(32)]
        self.data_head = 0
        self.data_tail = 0
        self.frame_num = 0
        self.thread_start = False
        # 帧协议
        self.frame = bytearray(255)
        self.cmd_head = 0xAA
        self.cmd_tail = 0x55
        self.cmd_length = 11
        self.format_style = None
        self.frame_string = None

    def get_data(self, receive_data: bytearray):
        for data in receive_data:
            self.uart_data[self.data_tail] = data
            self.data_tail += 1
            if self.data_tail >= self.buffer_size:
                self.data_tail = 0

    def get_buffer_length(self):
        if self.data_tail >= self.data_head:
            return self.data_tail - self.data_head
        else:
            return self.data_tail + self.buffer_size - self.data_head

    def thread_uart_analyze(self):
        while True:
            self.uart_analyze()

    def uart_analyze(self):
        length = self.get_buffer_length()
        # 存在未解析的数据
        if length > 0:
            cmd_head = self.uart_data[self.data_head]
            # 命令头正确开始解析
            if cmd_head == self.cmd_head:
                # 解析一帧数据
                while True:
                    cmd_length = self.get_buffer_length()
                    # 缓存长度大于一帧数据的长度，开始进行判断
                    if cmd_length >= self.cmd_length:
                        # 判断帧结尾
                        tail_index = (self.data_head + self.cmd_length - 1) % self.buffer_size
                        cmd_tail = self.uart_data[tail_index]
                        if cmd_tail == self.cmd_tail:
                            self.analyze_data()
                            self.frame_num += 1
                            # 将帧头向后移动一帧
                            self.data_head = (self.data_head + self.cmd_length) % self.buffer_size
                        else:
                            # 帧尾不符合,头向后移动
                            self.data_head += 1
                        # 一帧解析完毕，跳出循环
                        break
            # 命令头错误,头向后移动
            else:
                self.data_head += 1
                if self.data_head >= self.buffer_size:
                    self.data_head = 0

    # 解析数据
    def analyze_data(self):
        # 读取一帧数据
        self.frame.clear()
        for i in range(self.cmd_length):
            index = (i + self.data_head) % self.buffer_size
            data = self.uart_data[index]
            self.frame.append(data)
        # 根据初始化的格式进行转换
        data_tuple = struct.unpack(self.format_style, self.frame[3:-1])
        # 将该帧数据放入对应的list
        for i in range(len(data_tuple)):
            data = data_tuple[i]
            self.analyze_data_list[i].append(data)
        # 回显解析的数据
        self.frame_string = str(data_tuple)


# just for test
if __name__ == '__main__':
    uart_test = UartAnalyze()
    uart_test.format_style = '>' + 'b' + 'h' + 'i'
    tmp_data1 = bytearray([0xAA, 0xFF, 0xFF, 0x01, 0x00, 0x02, 0x00, 0x00, 0x00, 0x03, 0x55])
    uart_test.get_data(tmp_data1)
    uart_test.uart_analyze()

    tmp_data2 = bytearray([0xAA, 0xFF, 0xFF, 0x02, 0x00, 0x03, 0x00, 0x00, 0x00, 0x04, 0x55])
    uart_test.get_data(tmp_data2)
    uart_test.uart_analyze()

    tmp_data2 = bytearray([0xAA, 0xFF, 0xFF, 0xFF, 0x00, 0x04, 0x00, 0x00, 0x00, 0x05, 0x55])
    uart_test.get_data(tmp_data2)
    uart_test.uart_analyze()
    print(uart_test.analyze_data_list)
