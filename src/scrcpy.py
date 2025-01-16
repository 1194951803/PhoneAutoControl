import logging
import win32gui
import win32con

class ScrcpyController:
    def __init__(self):
        self.logger = logging.getLogger('ScrcpyController')
        self.window_handle = None
        self._find_scrcpy_window()

    def _find_scrcpy_window(self):
        """查找设备窗口"""
        try:
            self.window_handles = []
            
            def callback(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title:  # 只记录有标题的窗口
                        self.logger.debug(f"找到窗口: {title}")
                        # 匹配设备名称或scrcpy
                        if 'SM-G9730' in title or 'scrcpy' in title.lower():
                            self.window_handles.append(hwnd)
                return True  # 继续枚举

            # 枚举所有窗口
            win32gui.EnumWindows(callback, None)
            
            # 处理找到的窗口
            if self.window_handles:
                self.window_handle = self.window_handles[0]  # 使用第一个匹配的窗口
                self.logger.info(f"找到设备窗口: {self.window_handle}")
                # 获取窗口位置和大小
                self.window_rect = win32gui.GetWindowRect(self.window_handle)
                self.logger.info(f"窗口位置: {self.window_rect}")
            else:
                raise Exception("未找到设备窗口 SM-G9730")

        except Exception as e:
            self.logger.error(f"获取设备窗口失败: {str(e)}")
            raise

    def get_window_rect(self):
        """获取窗口位置和大小"""
        if self.window_handle:
            return self.window_rect
        return None

    def activate_window(self):
        """激活设备窗口"""
        if self.window_handle:
            try:
                # 确保窗口未最小化
                if win32gui.IsIconic(self.window_handle):
                    win32gui.ShowWindow(self.window_handle, win32con.SW_RESTORE)
                # 将窗口置于前台
                win32gui.SetForegroundWindow(self.window_handle)
                # 更新窗口位置信息
                self.window_rect = win32gui.GetWindowRect(self.window_handle)
            except Exception as e:
                self.logger.error(f"激活窗口失败: {str(e)}")

def print_all_windows(hwnd, extra):
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        if title:
            print(f"Window: {title}")
    return True

# 打印所有窗口
win32gui.EnumWindows(print_all_windows, None)