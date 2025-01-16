import cv2
import numpy as np
import logging
from PIL import ImageGrab
import win32gui

class CVController:
    def __init__(self):
        self.logger = logging.getLogger('CVController')

    def capture_window(self, window_rect):
        """截取指定窗口区域"""
        try:
            # 使用PIL截图
            screenshot = ImageGrab.grab(bbox=window_rect)
            # 转换为opencv格式
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            return screenshot, screenshot.shape[1], screenshot.shape[0]  # 返回截图和尺寸
        except Exception as e:
            self.logger.error(f"截图失败: {str(e)}")
            return None, None, None

    def find_image(self, template_path, screenshot, window_rect, screen_size):
        """在截图中查找目标图片位置并转换为实际手机坐标"""
        try:
            # 读取模板图片
            template = cv2.imread(template_path)
            if template is None:
                raise Exception(f"无法读取模板图片: {template_path}")

            # 进行模板匹配
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            # 设置匹配阈值
            if max_val < 0.8:
                self.logger.warning(f"未找到匹配图片: {template_path} (匹配度: {max_val})")
                return None

            # 计算窗口中的中心点坐标
            h, w = template.shape[:2]
            window_x = max_loc[0] + w//2
            window_y = max_loc[1] + h//2

            # 获取窗口和屏幕的尺寸
            window_width = window_rect[2] - window_rect[0]
            window_height = window_rect[3] - window_rect[1]
            screen_width, screen_height = screen_size

            # 计算缩放比例
            scale_x = screen_width / window_width
            scale_y = screen_height / window_height

            # 转换为手机实际坐标
            phone_x = int(window_x * scale_x)
            phone_y = int(window_y * scale_y)

            self.logger.info(f"找到匹配图片，窗口坐标: ({window_x}, {window_y}), 手机坐标: ({phone_x}, {phone_y})")
            return phone_x, phone_y

        except Exception as e:
            self.logger.error(f"图像识别失败: {str(e)}")
            return None