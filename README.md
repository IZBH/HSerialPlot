# HserialPlot

## 软件需求

- 串口数据解析
- 数据格式转换
- 绘图显示

### 串口帧格式

命令头+时间戳+数据补码+命令尾

| 命令头  | 时间戳  |   数据补码   | 命令尾  |
| :-----: | :-----: | :----------: | :-----: |
| 1(byte) | 2(byte) | 0-32*4(byte) | 1(byte) |

### 数据格式转换

对解析出的一帧进行数据的格式转换，由于发送的数据均为其补码，需要对该格式进行转换。

**例子**

```
AA 00 00 FF FE FF FD FF FF FF C3 F5 48 40 55
```

命令头：AA

时间戳：00 00

数据补码：FF FE FF FD FF FF FF C3 F5 48 40

命令尾：55

为了提高其中数据的有效性，trace模块被设计为，发送数据位宽可选，发送的数据类型可能为

- uint8_t
- int8_t
- uint16_t
- int16_t
- uint32_t
- int32_t
- float

因此解码时，需要根据需求对数据进行解码，此处发送的数据格式为:小端 s8,s16,s32,f32

- FF = -1(int8_t)
- FE FF = -2(int16_t)
- FD FF FF FF = -3(int32_t)
- C3 F5 48 40 = 3.14(float)

### 绘图显示

将 -1，-2，-3，3.14进行绘制



## 软件实现
![img.png](https://cdn.jsdelivr.net/gh/cxk-images/images/202303110016165.png)

主线程：UI界面的显示，读取按钮设置，显示串口数据，设置解析格式等

读取线程：对串口的数据进行读取，放到 class UartAnalyze 的缓存 buffer 中

定时器：对  class UartAnalyze 的缓存 buffer 中的串口数据进行拆包，根据设置的解析格式对收到的数据进行解码。

![串口绘图](https://cdn.jsdelivr.net/gh/cxk-images/images/202303110016828.jpg)

## 例子

串口发送数据如下

```hex
AA 00 00 FF FE FF FD FF FF FF C3 F5 48 40 55 AA 00 00 FE FD FF FC FF FF FF C3 F5 48 40 55 AA 00 00 FD FC FF FB FF FF FF C3 F5 48 40 55 AA 00 00 FC FB FF FA FF FF FF C3 F5 48 40 55 AA 00 00 FB FA FF F9 FF FF FF C3 F5 48 40 55
```

![image-20230311003455488](https://cdn.jsdelivr.net/gh/cxk-images/images/202303110129841.png)

根据以上信息可将该字节流拆包如下

```
AA 00 00 FF FE FF FD FF FF FF C3 F5 48 40 55
```


```
AA 00 00 FE FD FF FC FF FF FF C3 F5 48 40 55
```

```
AA 00 00 FD FC FF FB FF FF FF C3 F5 48 40 55
```

```
AA 00 00 FC FB FF FA FF FF FF C3 F5 48 40 55
```

```
AA 00 00 FB FA FF F9 FF FF FF C3 F5 48 40 55
```

![image-20230311003759595](https://cdn.jsdelivr.net/gh/cxk-images/images/202303110129606.png)

为便于解析，规定发送顺序为s8，u8，s16，u16，s32，u32，f32字节格式。(芯片trace端口可随意组合)

用户设置为 1，0，1，0，1，0，1，小端

根据以上信息进行解码

```
AA + 0000 + FF(-1) + FEFF(-2) + FDFFFFFF(-3) + C3F54840(3.14) + 55
```

```
AA + 0000 + FE(-2) + FDFF(-3) + FCFFFFFF(-4) + C3F54840(3.14) + 55
```

```
AA + 0000 + FD(-3) + FCFF(-4) + FBFFFFFF(-5) + C3F54840(3.14) + 55
```

```
AA + 0000 + FC(-4) + FBFF(-5) + FAFFFFFF(-6) + C3F54840(3.14) + 55
```

```
AA + 0000 + FB(-5) + FAFF(-6) + F9FFFFFF(-7) + C3F54840(3.14) + 55
```

解码出的数据分别进行存储

时间戳：[0000, 0000, 0000, 0000, 0000]

DATA1：[-1, -2, -3, -4, -5]

DATA2：[-2, -3, -4, -5, -6]

DATA3：[-3, -4, -5, -6, -7]

DATA4：[3.14, 3.14, 3.14, 3.14, 3.14]

对DATA1，DATA2，DATA3，DATA4，分别进行绘图如下

![image-20230311005529285](https://cdn.jsdelivr.net/gh/cxk-images/images/202303110129912.png)

## 解码

参考 csapp 第二章

### 大小端

![image-20230311011722043](https://cdn.jsdelivr.net/gh/cxk-images/images/202303110129855.png)

### 整数

#### 无符号数

![image-20230311011845289](https://cdn.jsdelivr.net/gh/cxk-images/images/202303110130217.png)

#### 有符号数

![image-20230311011902338](https://cdn.jsdelivr.net/gh/cxk-images/images/202303110131741.png)

### 浮点表示

![image-20230311012005169](https://cdn.jsdelivr.net/gh/cxk-images/images/202303110131606.png)

对于弱类型语言，如python，建议调用库进行字节流转化，此处使用python的struct库进行实现。

强类型语言，如c，c++，可直接进行转换，c++，c可使用共用体实现。

