
class UartAnalyze:
    def __init__(self):
        # 串口解析
        self.buffer_size = 1024 * 1024
        self.uart_data = bytearray(self.buffer_size)
        self.analyze_data_list = [[] for i in range(32)]
        self.data_head = 0
        self.data_tail = 0
        self.frame_num = 0
        self.thread_start = False
        # 帧协议
        self.frame = []
        self.cmd_head = 0xAA
        self.cmd_length = 132
        self.byte_num = 0
        self.half_word_num = 0
        self.word_num = 32
        self.cmd_tail = 0x55

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

        # 命令头，时间戳
        index = 0
        cmd_head = self.frame[0]
        time_scale = (self.frame[1] << 8) + self.frame[2]
        index += 3

        # 8bit数据
        for i in range(0, self.byte_num, 1):
            byte_data = self.frame[index]
            self.analyze_data_list[i].append(byte_data)
            # print(byte_data)
            index += 1

        # 16bit数据
        for i in range(0, self.half_word_num * 2, 2):
            half_word_data = self.frame[index] + (self.frame[index + 1] << 8)
            self.analyze_data_list[self.byte_num + i // 2].append(half_word_data)
            # print(half_word_data)
            index += 2

        # 32bit数据
        for i in range(0, self.word_num * 4, 4):
            word_data = (self.frame[index] << 0) + (self.frame[index + 1] << 8) + (self.frame[index + 2] << 16) + \
                        (self.frame[index + 3] << 24)
            self.analyze_data_list[self.byte_num + self.half_word_num + i // 4].append(word_data)
            # print(word_data)
            index += 4
        # print(self.analyze_data_list)
        # just for test
        # print(self.frame)


# just for test
if __name__ == '__main__':
    uart_test = UartAnalyze()
    uart_test.cmd_length = 11
    uart_test.byte_num = 1
    uart_test.half_word_num = 1
    uart_test.word_num = 1
    tmp_data1 = bytearray([0xAA, 0xFF, 0xFF, 0x01, 0x00, 0x02, 0x00, 0x00, 0x00, 0x03, 0x55])
    uart_test.get_data(tmp_data1)
    uart_test.uart_analyze()
    #
    tmp_data2 = bytearray([0xAA, 0xFF, 0xFF, 0x02, 0x00, 0x03, 0x00, 0x00, 0x00, 0x04, 0x55])
    uart_test.get_data(tmp_data2)
    uart_test.uart_analyze()
    #
    tmp_data2 = bytearray([0xAA, 0xFF, 0xFF, 0xFF, 0x00, 0x04, 0x00, 0x00, 0x00, 0x05, 0x55])
    uart_test.get_data(tmp_data2)
    uart_test.uart_analyze()

    uart_test.cmd_length = 132
    uart_test.byte_num = 0
    uart_test.half_word_num = 0
    uart_test.word_num = 32
    tmp_data2 = bytearray([0xAA, 0XFF, 0xFF,
                           0x00, 0x00, 0x00, 0x00,
                           0x01, 0x00, 0x00, 0x00,
                           0x02, 0x00, 0x00, 0x00,
                           0x03, 0x00, 0x00, 0x00,
                           0x04, 0x00, 0x00, 0x00,
                           0x05, 0x00, 0x00, 0x00,
                           0x06, 0x00, 0x00, 0x00,
                           0x07, 0x00, 0x00, 0x00,
                           0x08, 0x00, 0x00, 0x00,
                           0x09, 0x00, 0x00, 0x00,
                           0x0a, 0x00, 0x00, 0x00,
                           0x0b, 0x00, 0x00, 0x00,
                           0x0c, 0x00, 0x00, 0x00,
                           0x0d, 0x00, 0x00, 0x00,
                           0x0e, 0x00, 0x00, 0x00,
                           0x0f, 0x00, 0x00, 0x00,
                           0x10, 0x00, 0x00, 0x00,
                           0x11, 0x00, 0x00, 0x00,
                           0x12, 0x00, 0x00, 0x00,
                           0x13, 0x00, 0x00, 0x00,
                           0x14, 0x00, 0x00, 0x00,
                           0x15, 0x00, 0x00, 0x00,
                           0x16, 0x00, 0x00, 0x00,
                           0x17, 0x00, 0x00, 0x00,
                           0x18, 0x00, 0x00, 0x00,
                           0x19, 0x00, 0x00, 0x00,
                           0x1a, 0x00, 0x00, 0x00,
                           0x1b, 0x00, 0x00, 0x00,
                           0x1c, 0x00, 0x00, 0x00,
                           0x1d, 0x00, 0x00, 0x00,
                           0x1e, 0x00, 0x00, 0x00,
                           0x1f, 0x00, 0x00, 0x00,
                           0x55
                           ])
    uart_test.get_data(tmp_data2)
    uart_test.uart_analyze()
    # print(uart_test.analyze_data_list)

    # value1_uint8 = np.array(uart_test.analyze_data_list[0], dtype=np.uint8)
    # value1_int8 = np.array(uart_test.analyze_data_list[0], dtype=np.int8)
    #
    # # 浮点转换
    # hex_value = 0xcd + (0xcc << 8) + (0xf6 << 16) + (0x42 << 24)
    # print(hex_value)
    # tmp = np.array([hex_value], dtype=np.uint32)
    # print(tmp)
    # tmp.dtype = np.float32
    # print(tmp)
