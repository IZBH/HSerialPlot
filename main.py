import sys
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
import pyqtgraph as pg

# personal library
from serial_plot_ui import Ui_MainWindow
from uart_analyze import UartAnalyze

# global var
uart_data = UartAnalyze()
old_frame_num = 0

colors = [(255,182,193), (220,20,60), (0,0,255), (30,144,255),
          (135,206,250), (0,255,255), (127,255,170), (245,255,250),
          (60,179,113), (0,128,0), (255,255,240), (255,255,0),
          (128,128,0), (238,232,170), (255,165,0), (255,0,0),
          (255,255,255), (255,0,255), (148,0,211), (72,61,139),
          (72,61,139), (135,206,235), (72,209,204), (60,179,113),
          (0,255,0), (85,107,47), (255,248,220), (218,165,32),
          (255,140,0), (255,99,71), (106,90,205), (238,130,238)]


class UartAnalyzeThread(QThread):
    finished_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        uart_data.thread_uart_analyze()
        self.finished_signal.emit()


class SerialPlot(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(SerialPlot, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("HSerialPlot")
        self.setWindowIcon(QIcon(r'D:\code\HSerialPlot\icon.png'))
        # 绘图列表
        self.curve = []
        # 串口对象
        self.serial = QSerialPort(self)
        self.received_data_num = 0
        self.send_data_num = 0
        self.show_receive = True
        # 串口解析线程
        self.uart_analyze_thread = UartAnalyzeThread()
        self.start_plot = False
        # 绘图界面
        graph = pg.GraphicsLayoutWidget()
        self.graph_layout.addWidget(graph)
        self.graph_plot = graph.addPlot(title="串口数据绘制", colspan=2)
        # 定时器初始化
        self.plot_timer = QTimer()
        # 固定窗口大小
        self.setFixedSize(1200, 700)
        # 初始化
        self.init()

    def init(self):
        self.init_param()
        self.connect_signal()
        self.get_valid_serial()
        self.config_graph()

    def init_param(self):
        # 设置自动清0行数
        self.receive_text.document().setMaximumBlockCount(500)
        # 设置范围
        self.u8_num_spinBox.setRange(0, 32)
        self.s8_num_spinBox.setRange(0, 32)
        self.u16_num_spinBox.setRange(0, 32)
        self.s16_num_spinBox.setRange(0, 32)
        self.u32_num_spinBox.setRange(0, 32)
        self.s32_num_spinBox.setRange(0, 32)
        self.f32_num_spinBox.setRange(0, 32)
        self.frame_len_spinBox.setRange(4, 150)
        # 设置默认值
        self.s8_num_spinBox.setValue(1)
        self.s16_num_spinBox.setValue(1)
        self.s32_num_spinBox.setValue(1)
        self.frame_len_spinBox.setValue(11)
        # 默认十六进制收发
        self.hex_send.setChecked(True)
        self.hex_receive.setChecked(True)
        # 默认小端
        self.little_endian_radiobt.setChecked(True)
        # 波特率选择窗口参数
        baudrate = [str(baudrate) for baudrate in QSerialPortInfo.standardBaudRates()]
        self.serial_baudrate_select_box.addItems(baudrate)
        self.serial_baudrate_select_box.addItem("自定义")
        self.serial_baudrate_select_box.setCurrentText('115200')

    def connect_signal(self):
        # 串口检测
        self.serial_detect_bt.clicked.connect(self.get_valid_serial)
        # 打开串口
        self.open_serial_bt.clicked.connect(self.open_serial)
        # 设置波特率
        self.serial_baudrate_select_box.currentIndexChanged.connect(self.custom_baudrate)
        # 清除接收
        self.receive_clear_button.clicked.connect(self.receive_data_clear)
        # 清除发送
        self.send_clear_button.clicked.connect(self.send_data_clear)
        # 发送数据
        self.send_button.clicked.connect(self.send_data)
        # 接收数据
        self.serial.readyRead.connect(self.read_data)
        # 定时器刷新绘图
        self.plot_timer.timeout.connect(self.serial_graph_plot)
        # 协议解析
        self.uart_analyze_bt.clicked.connect(self.uart_analyze_init)
        # 计算一帧长度
        self.u8_num_spinBox.valueChanged.connect(self.clc_frame_length)
        self.s8_num_spinBox.valueChanged.connect(self.clc_frame_length)
        self.u16_num_spinBox.valueChanged.connect(self.clc_frame_length)
        self.s16_num_spinBox.valueChanged.connect(self.clc_frame_length)
        self.u32_num_spinBox.valueChanged.connect(self.clc_frame_length)
        self.s32_num_spinBox.valueChanged.connect(self.clc_frame_length)
        self.f32_num_spinBox.valueChanged.connect(self.clc_frame_length)


    def get_valid_serial(self):
        serial_list = [device.portName() for device in QSerialPortInfo.availablePorts()]
        self.serial_select_box.clear()
        self.serial_select_box.addItems(serial_list)

    def custom_baudrate(self):
        if self.serial_baudrate_select_box.currentIndex() == 15:
            self.serial_baudrate_select_box.setEditable(True)
            self.serial_baudrate_select_box.setCurrentText(None)
        else:
            self.serial_baudrate_select_box.setEditable(False)

    def receive_data_clear(self):
        self.received_data_num = 0
        self.receive_text.setText("")
        self.serial_receive_num_edit.setText("")
        self.graph_plot.clear()

    def send_data_clear(self):
        self.send_data_num = 0
        self.send_text.setText("")
        self.serial_send_num_edit.setText("")

    def clc_frame_length(self):
        frame_len = 4 + \
                    (self.u8_num_spinBox.value() + self.s8_num_spinBox.value()) + \
                    (self.u16_num_spinBox.value() + self.s16_num_spinBox.value()) * 2 + \
                    (self.u32_num_spinBox.value() + self.s32_num_spinBox.value()) * 4 + \
                    (self.f32_num_spinBox.value()) * 4
        self.frame_len_spinBox.setValue(frame_len)

    def uart_analyze_init(self):
        # 读取格式化参数
        u8_num = self.u8_num_spinBox.value()
        s8_num = self.s8_num_spinBox.value()
        u16_num = self.u16_num_spinBox.value()
        s16_num = self.s16_num_spinBox.value()
        u32_num = self.u32_num_spinBox.value()
        s32_num = self.s32_num_spinBox.value()
        f32_num = self.f32_num_spinBox.value()
        endian = '<'
        if self.little_endian_radiobt.isChecked():
            endian = '<'
        elif self.big_endian_radiobt.isChecked():
            endian = '>'
        # 设置格式化参数
        uart_data.format_style = \
            endian + 'b' * s8_num + 'B' * u8_num + 'h' * s16_num + 'H' * u16_num + 'i' * s32_num + "I" * u32_num + \
            'f' * f32_num
        uart_data.cmd_length = self.frame_len_spinBox.value()
        cmd = int(self.cmd_edit.text(), 16)
        uart_data.cmd_head = cmd >> 8
        uart_data.cmd_tail = cmd & 0xFF
        self.show_receive = False
        if not self.start_plot:
            # 启动绘图定时器
            self.plot_timer.start(10)
            # 启动解析线程
            self.uart_analyze_thread.start()
            self.start_plot = True

    def config_graph(self):
        # 启用抗锯齿
        pg.setConfigOptions(antialias=True)
        self.graph_plot.setLabel('left', text='串口数据')
        self.graph_plot.showGrid(x=True, y=True)
        # self.graph_plot.setLogMode(x=False, y=False)
        self.graph_plot.setLabel('bottom', text='time', units='s')
        # 初始化绘图
        # 添加图例
        self.graph_plot.addLegend(colCount=2)
        for i in range(32):
            name = 'data' + str(i)
            curve = self.graph_plot.plot(uart_data.analyze_data_list[0], pen=colors[i], name=name,
                                         clear=False)
            self.curve.append(curve)


    def open_serial(self):
        if self.serial.isOpen():
            QMessageBox.critical(self, "串口打开失败", "串口被占用")
            return

        # set Port
        port = self.serial_select_box.currentText()
        self.serial.setPortName(port)
        # setBaudrate
        baudrate = int(self.serial_baudrate_select_box.currentText())
        self.serial.setBaudRate(baudrate)
        # set Databits
        databits = int(self.serial_databits_select_box.currentText())
        if databits == 8:
            self.serial.setDataBits(QSerialPort.Data8)
        elif databits == 7:
            self.serial.setDataBits(QSerialPort.Data7)
        elif databits == 6:
            self.serial.setDataBits(QSerialPort.Data6)
        elif databits == 5:
            self.serial.setDataBits(QSerialPort.Data5)
        # set Stopbits
        stopbits = self.serial_stopbits_select_box.currentText()
        if stopbits == '1':
            self.serial.setStopBits(QSerialPort.OneStop)
        elif stopbits == '1.5':
            self.serial.setStopBits(QSerialPort.OneAndHalfStop)
        elif stopbits == '2':
            self.serial.setStopBits(QSerialPort.TwoStop)
        # set Parity
        parity = self.serial_parity_select_box.currentText()
        if parity == "No":
            self.serial.setParity(QSerialPort.NoParity)
        elif parity == "Even":
            self.serial.setParity(QSerialPort.EvenParity)
        elif parity == "Odd":
            self.serial.setParity(QSerialPort.OddParity)
        elif parity == "Space":
            self.serial.setParity(QSerialPort.SpaceParity)
        elif parity == "Mark":
            self.serial.setParity(QSerialPort.MarkParity)
        # open Serial
        self.serial.open(QSerialPort.ReadWrite)
        # 设置UI
        self.open_serial_bt.setEnabled(False)
        self.close_serial_bt.setEnabled(True)
        self.serial_status_gruop.setTitle(port + "已打开")

    def send_data(self):
        # 状态判断
        if not self.serial.isOpen():
            QMessageBox.critical(self, "发送失败", "串口未打开")
            return
        # 数据判断
        send_s = self.send_text.toPlainText()
        if not send_s:
            QMessageBox.critical(self, "发送失败", "发送数据为空")
            return
        # 数据转换
        if self.hex_send.isChecked():
            # 转换为Hex格式
            try:
                send_list = [int(x, 16) for x in send_s.split()]
            except ValueError as e:
                log_err = e.args[0]
                QMessageBox.critical(self, "发送失败", log_err)
                return
            send_bytes = bytes(send_list)
        else:
            # 转换为ASCII格式
            try:
                send_bytes = (send_s + '\r\n').encode('utf-8')
            except UnicodeEncodeError as e:
                log_err = e.args[0]
                QMessageBox.critical(self, "字符串转换失败", log_err)
                return

        # 发送数据
        self.serial.writeData(send_bytes)
        # 发送字节数统计
        self.send_data_num += len(send_bytes)
        self.serial_send_num_edit.setText(str(self.send_data_num))
        locale_time = datetime.utcnow().strftime('%H:%M:%S.%f')[:-3]
        # 回显数据生成
        if self.hex_receive.isChecked():
            send_s = send_bytes.hex(' ') + '\n'
        # ASCII 回显
        else:
            send_s = send_bytes.decode('utf-8')
        show_s = "[%s]->%s" % (locale_time, send_s)
        # 显示
        self.receive_text.insertPlainText(show_s)
        text_cursor = self.receive_text.textCursor()
        text_cursor.movePosition(text_cursor.End)
        self.receive_text.setTextCursor(text_cursor)

    def read_data(self):
        # 读取数据用于显示
        r_data = bytes(self.serial.readAll())
        # 读取到串口解析buffer
        uart_data.get_data(bytearray(r_data))
        # 显示接收到的数据个数
        self.received_data_num += len(r_data)
        self.serial_receive_num_edit.setText(str(self.received_data_num))
        # 不需要显示接收到的数据，直接退出
        if not self.show_receive:
            return
        # 显示读取到的数据
        locale_time = datetime.utcnow().strftime('%H:%M:%S.%f')[:-3]
        # 数据转换
        if self.hex_receive.isChecked():
            show_receive = "[%s]<-%s\n" % (locale_time, r_data.hex(' '))
        else:
            show_receive = "[%s]<-%s" % (locale_time, r_data.decode("utf-8"))
        # 显示接收到的数据
        self.receive_text.insertPlainText(show_receive)
        text_cursor = self.receive_text.textCursor()
        text_cursor.movePosition(text_cursor.End)
        self.receive_text.setTextCursor(text_cursor)

    def serial_graph_plot(self):
        global old_frame_num
        historyLength = 100
        # uart_data.uart_analyze()
        if uart_data.frame_num < historyLength:
            start = 0
            end = historyLength
        else:
            start = uart_data.frame_num - historyLength
            end = uart_data.frame_num
            if old_frame_num != uart_data.frame_num:
                self.graph_plot.setXRange(start, end, update=True)
                old_frame_num = uart_data.frame_num

        for i in range(32):
            try:
                self.curve[i].setData(uart_data.analyze_data_list[i])
            except:
                self.plot_timer.stop()
                QMessageBox.critical(self, "定时器已关闭", "绘图出错")

        self.analyze_data_text.clear()
        self.analyze_data_text.setText(uart_data.frame_string)


if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    serial_plot = SerialPlot()
    serial_plot.show()
    sys.exit(app.exec_())
