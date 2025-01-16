import logging
from ppadb.client import Client as AdbClient
import time

class ADBController:
    def __init__(self):
        self.logger = logging.getLogger('ADBController')
        self.client = AdbClient(host="127.0.0.1", port=5037)
        self._connect_device()

    def _connect_device(self):
        """连接设备"""
        try:
            devices = self.client.devices()
            if not devices:
                raise Exception("未检测到设备连接")
            self.device = devices[0]  # 使用第一个连接的设备
            self.logger.info("ADB连接成功")
        except Exception as e:
            self.logger.error(f"ADB连接失败: {str(e)}")
            raise

    def start_app(self, package_name):
        """启动指定应用"""
        try:
            # 检查应用是否已启动
            result = self.device.shell(f'pm list packages {package_name}')
            if package_name not in result:
                self.logger.error(f"未安装应用: {package_name}")
                return False

            # 启动应用
            cmd = f'monkey -p {package_name} -c android.intent.category.LAUNCHER 1'
            self.device.shell(cmd)
            self.logger.info(f"启动应用 {package_name}")
            return True
        except Exception as e:
            self.logger.error(f"启动应用失败: {str(e)}")
            return False

    def tap(self, x, y):
        """点击指定坐标"""
        try:
            self.device.shell(f'input tap {x} {y}')
            self.logger.info(f"点击坐标 ({x}, {y})")
            return True
        except Exception as e:
            self.logger.error(f"点击失败: {str(e)}")
            return False

    def get_screen_size(self):
        """获取屏幕分辨率"""
        try:
            # 使用dumpsys window displays命令获取分辨率
            output = self.device.shell('dumpsys window displays')
            for line in output.split('\n'):
                if 'cur=' in line and 'app=' in line:
                    # 格式: cur=1440x3040 app=1440x3040
                    size = line.split('cur=')[1].split(' ')[0]
                    width, height = map(int, size.split('x'))
                    self.logger.info(f"获取屏幕分辨率: {width}x{height}")
                    return width, height
            
            # 如果上面的方法失败，尝试wm size命令
            output = self.device.shell('wm size')
            if 'Physical size:' in output:
                size_line = output.split('\n')[0]
                size = size_line.split(':')[1].strip()
                width, height = map(int, size.split('x'))
                self.logger.info(f"获取屏幕分辨率: {width}x{height}")
                return width, height

            # 都失败则使用默认值
            default_width, default_height = 1440, 3040  # 根据你的手机实际分辨率设置
            self.logger.info(f"使用默认分辨率: {default_width}x{default_height}")
            return default_width, default_height

        except Exception as e:
            self.logger.error(f"获取屏幕分辨率失败: {str(e)}")
            default_width, default_height = 1440, 3040
            self.logger.info(f"使用默认分辨率: {default_width}x{default_height}")
            return default_width, default_height

    def force_stop_app(self, package_name):
        """强制停止应用"""
        try:
            self.device.shell(f'am force-stop {package_name}')
            self.logger.info(f"关闭应用 {package_name}")
            return True
        except Exception as e:
            self.logger.error(f"关闭应用失败: {str(e)}")
            return False

    def check_screen_state(self):
        """检查屏幕状态"""
        try:
            # 检查屏幕是否亮起
            result = self.device.shell('dumpsys power | grep "Display Power: state="')
            return 'ON' in result
        except Exception as e:
            self.logger.error(f"检查屏幕状态失败: {str(e)}")
            return False

    def wake_screen(self):
        """唤醒屏幕"""
        try:
            # 按电源键
            self.device.shell('input keyevent 26')
            time.sleep(1)  # 等待屏幕亮起
            self.logger.info("唤醒屏幕")
            return True
        except Exception as e:
            self.logger.error(f"唤醒屏幕失败: {str(e)}")
            return False

    def swipe_unlock(self):
        """滑动解锁"""
        try:
            # 获取屏幕尺寸
            size = self.get_screen_size()
            if not size:
                return False
            
            width, height = size
            # 从屏幕中间底部向上滑动
            start_x = width // 2
            start_y = height - 200
            end_x = width // 2
            end_y = height // 3
            
            # 执行滑动
            self.device.shell(f'input swipe {start_x} {start_y} {end_x} {end_y} 300')
            time.sleep(1)  # 等待解锁动画
            self.logger.info("滑动解锁完成")
            return True
        except Exception as e:
            self.logger.error(f"滑动解锁失败: {str(e)}")
            return False

    def input_password(self, password):
        """输入密码"""
        try:
            for digit in str(password):
                self.device.shell(f'input keyevent KEYCODE_NUMPAD_{digit}')
                time.sleep(0.2)
            self.device.shell('input keyevent 66')  # 回车键
            self.logger.info("输入密码完成")
            return True
        except Exception as e:
            self.logger.error(f"输入密码失败: {str(e)}")
            return False