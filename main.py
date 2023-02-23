import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer

from serial_plot_ui import Ui_MainWindow

from serial.tools.list_ports import comports
import serial
import threading
from datetime import datetime

import pyqtgraph as pg

# personal lib
import serial_config
from uart_analyze import UartAnalyze

data_list = []
uart_data = UartAnalyze()
old_frame_num = 0


class SerialPlot(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(SerialPlot, self).__init__()
        self.curve = []
        self.setupUi(self)
        self.setWindowTitle("HSerialPlot")
        self.setWindowIcon(QIcon('icon.png'))
        self.device_list = []
        self.serial = serial.Serial()
        # self.data = bytearray()
        self.receive_en = False
        self.log_err = None
        self.send_data_num = 0
        self.received_data_num = 0
        self.x_start = 0
        self.x_end = 0
        self.read_thread = threading.Thread(target=self.read_uart, daemon=True)
        self.read_thread_alive = True
        self.init()
        # 绘图初始化
        graph = pg.GraphicsLayoutWidget()
        self.graph_layout.addWidget(graph)
        self.graph_plot = graph.addPlot(title="串口数据绘制", colspan=2)
        self.config_graph()
        # 定时器用于绘图
        self.plot_timer = QTimer()

    def init(self):
        # 可用端口
        self.get_valid_serial()
        # 波特率
        baudrate = [str(baudrate) for baudrate in serial_config.BAUDRATES]
        self.serial_baudrate_select_box.addItems(baudrate)
        self.serial_baudrate_select_box.setCurrentText('115200')
        # 数据位
        bytesize = [str(bytesize) for bytesize in self.serial.BYTESIZES]
        self.serial_databits_select_box.addItems(bytesize)
        self.serial_databits_select_box.setCurrentText('8')
        # 校验位
        parites = [str(parites) for parites in self.serial.PARITIES]
        self.serial_parity_select_box.addItems(parites)
        # 停止位
        stopbits = [str(stopbits) for stopbits in self.serial.STOPBITS]
        self.serial_stopbits_select_box.addItems(stopbits)
        # 设置自动清0行数
        self.receive_text.document().setMaximumBlockCount(1000)
        # 串口检测
        self.serial_detect_bt.clicked.connect(self.get_valid_serial)
        # 打开串口
        self.open_serial_bt.clicked.connect(self.open_serial)
        # 关闭串口
        self.close_serial_bt.clicked.connect(self.close_serial)
        # 清除接收
        self.receive_clear_button.clicked.connect(self.receive_data_clear)
        # 清除发送
        self.send_clear_button.clicked.connect(self.send_data_clear)
        # 发送数据
        self.send_button.clicked.connect(self.send_data)
        # 帧协议解析
        self.uart_analyze_bt.clicked.connect(self.uart_analyze_init)
        # 自动计算一帧长度
        self.u8_num_spinBox.valueChanged.connect(self.clc_frame_length)
        self.s8_num_spinBox.valueChanged.connect(self.clc_frame_length)
        self.u16_num_spinBox.valueChanged.connect(self.clc_frame_length)
        self.s16_num_spinBox.valueChanged.connect(self.clc_frame_length)
        self.u32_num_spinBox.valueChanged.connect(self.clc_frame_length)
        self.s32_num_spinBox.valueChanged.connect(self.clc_frame_length)
        self.f32_num_spinBox.valueChanged.connect(self.clc_frame_length)
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

    # 计算一帧的长度
    def clc_frame_length(self):
        frame_len = 4 + \
                    (self.u8_num_spinBox.value() + self.s8_num_spinBox.value()) + \
                    (self.u16_num_spinBox.value() + self.s16_num_spinBox.value()) * 2 + \
                    (self.u32_num_spinBox.value() + self.s32_num_spinBox.value()) * 4 + \
                    (self.f32_num_spinBox.value()) * 4
        self.frame_len_spinBox.setValue(frame_len)

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
            curve = self.graph_plot.plot(uart_data.analyze_data_list[0], pen=serial_config.colors[i], name=name,
                                         clear=False)
            self.curve.append(curve)

    # 定时器绘图
    def serial_graph_plot(self):
        global old_frame_num
        historyLength = 100
        uart_data.uart_analyze()
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
            self.curve[i].setData(uart_data.analyze_data_list[i])

        self.analyze_data_text.clear()
        self.analyze_data_text.setText(uart_data.frame_string)

    # 初始化串口解析参数
    def uart_analyze_init(self):
        #
        u8_num = self.u8_num_spinBox.value()
        s8_num = self.s8_num_spinBox.value()
        u16_num = self.u16_num_spinBox.value()
        s16_num = self.s16_num_spinBox.value()
        u32_num = self.u32_num_spinBox.value()
        s32_num = self.s32_num_spinBox.value()
        f32_num = self.f32_num_spinBox.value()
        # uart_data.format_style = [u8_num, s8_num, u16_num, s16_num, u32_num, s32_num, f32_num]
        uart_data.format_style = '<' + \
                                 'b' * s8_num + 'B' * u8_num + \
                                 'h' * s16_num + 'H' * u16_num + \
                                 'i' * s32_num + 'I' * u32_num + \
                                 'f' * f32_num
        uart_data.cmd_length = self.frame_len_spinBox.value()
        cmd = int(self.cmd_edit.text(), 16)
        uart_data.cmd_head = cmd >> 8
        uart_data.cmd_tail = cmd & 0xFF
        self.plot_timer.start(10)
        self.plot_timer.timeout.connect(self.serial_graph_plot)

    def get_valid_serial(self):
        # 获取串口列表并添加
        port_list = list(comports())
        self.device_list = [port.device for port in port_list]
        self.serial_select_box.clear()
        self.serial_select_box.addItems(self.device_list)

    def open_serial(self):
        # 设置端口号,波特率,数据位,停止位,校验位
        self.serial.port = self.serial_select_box.currentText()
        self.serial.baudrate = int(self.serial_baudrate_select_box.currentText())
        self.serial.bytesize = int(self.serial_databits_select_box.currentText())
        self.serial.stopbits = int(self.serial_stopbits_select_box.currentText())
        self.serial.parity = self.serial_parity_select_box.currentText()
        # 打开串口，使用QMessageBox输出异常
        try:
            self.serial.open()
        except serial.SerialException as except_msg:
            log_err = except_msg.args[0]
            QMessageBox.critical(self, "串口打开失败", log_err)
            return None

        # 初始化帧协议
        # self.uart_analyze_init()

        if self.serial.is_open:
            # 关闭->按钮(打开串口)
            self.open_serial_bt.setEnabled(False)
            # 打开->按钮(关闭串口)
            self.close_serial_bt.setEnabled(True)
            status = self.serial.port + "已打开"
            self.serial_status_gruop.setTitle(status)
            # 打开绘图定时器
            # self.plot_timer.start(10)
            # self.plot_timer.timeout.connect(self.serial_graph_plot)
            # 使用线程读取串口数据
            self.receive_en = True
            if self.read_thread_alive:
                self.read_thread.start()
            else:
                self.read_thread = threading.Thread(target=self.read_uart, daemon=True)
                self.read_thread.start()

    def close_serial(self):
        # 关闭进程读取
        self.receive_en = False
        # 关闭串口
        self.serial.close()
        # 打开->按钮(打开串口)
        self.open_serial_bt.setEnabled(True)
        # 关闭->按钮(关闭串口)
        self.close_serial_bt.setEnabled(False)
        self.serial_status_gruop.setTitle("串口状态(已关闭)")

    def read_uart(self):
        self.read_thread_start()
        data_ascii = bytearray()
        while self.serial.is_open and self.receive_en:
            try:
                data = self.serial.read(self.serial.in_waiting)
            except serial.SerialException as e:
                self.log_err = e.args[0]
                break
            else:
                if data:
                    uart_data.get_data(data)
                    locale_time = datetime.utcnow().strftime('%H:%M:%S.%f')[:-3]
                    try:
                        # Hex 接收
                        if self.hex_receive.isChecked():
                            show_receive = "[%s]<-%s\n" % (locale_time, data.hex(' '))
                            self.receive_text.insertPlainText(show_receive)

                        # ASCII 接收
                        else:
                            data_ascii.extend(data)
                            if data_ascii.endswith(b'\n'):
                                show_receive = "[%s]<-%s" % (locale_time, data_ascii.decode("utf-8"))
                                data_ascii.clear()
                                self.receive_text.insertPlainText(show_receive)

                        # 移动光标至下一行
                        text_cursor = self.receive_text.textCursor()
                        text_cursor.movePosition(text_cursor.End)
                        self.receive_text.setTextCursor(text_cursor)
                        # 更新接收数据长度
                        self.received_data_num += len(data)
                        self.serial_receive_num_edit.setText(str(self.received_data_num))
                        # 绘图
                        # self.serial_graph_plot()
                    except Exception as e:
                        self.log_err = e.args[0]
                        break
        self.read_thread_finish()

    def read_thread_start(self):
        self.read_thread_alive = True
        self.serial_rt_status_group.setTitle("数据接收中")

    def read_thread_finish(self):
        self.read_thread_alive = False
        self.serial_rt_status_group.setTitle("停止接收")
        if self.log_err is not None:
            print(self.log_err)
            QMessageBox.critical(self, "串口打开失败", self.log_err)

    def send_data_clear(self):
        self.send_data_num = 0
        self.send_text.setText("")
        self.serial_send_num_edit.setText("")

    def receive_data_clear(self):
        self.received_data_num = 0
        self.receive_text.setText("")
        self.serial_receive_num_edit.setText("")
        self.graph_plot.clear()

    def send_data(self):
        if self.serial.is_open:
            input_s = self.send_text.toPlainText()
            if input_s:
                # Hex 发送
                if self.hex_send.isChecked():
                    try:
                        send_list = [int(x, 16) for x in input_s.split()]
                    except ValueError as e:
                        self.log_err = e.args[0]
                        QMessageBox.critical(self, "hex转换失败", self.log_err)
                        return None

                    send_bytes = bytes(send_list)
                # ASCII 发送
                else:
                    try:
                        send_bytes = (input_s + '\r\n').encode('utf-8')
                    except UnicodeEncodeError as e:
                        self.log_err = e.args[0]
                        QMessageBox.critical(self, "字符串转换失败", self.log_err)
                        return None

                try:
                    num = self.serial.write(send_bytes)
                    locale_time = datetime.utcnow().strftime('%H:%M:%S.%f')[:-3]
                    self.serial_send_num_edit.setText(str(self.send_data_num))
                    # Hex 回显
                    if self.hex_receive.isChecked():
                        output_s = send_bytes.hex(' ') + '\n'
                    # ASCII 回显
                    else:
                        output_s = send_bytes.decode('utf-8')

                    show_send = "[%s]->%s" % (locale_time, output_s)
                    self.receive_text.insertPlainText(show_send)
                    self.send_data_num += num
                except Exception as e:
                    self.log_err = e.args[0]
                    QMessageBox.critical(self, "发送失败", self.log_err)
                    return None
        else:
            QMessageBox.critical(self, "发送失败", "串口未打开")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    serial_plot = SerialPlot()
    serial_plot.show()
    sys.exit(app.exec_())
