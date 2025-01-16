import logging
import yaml
import time
import schedule
from datetime import datetime
from src.adb import ADBController
from src.scrcpy import ScrcpyController
from src.cv import CVController
import numpy as np
import cv2

"""配置日志"""
logging.basicConfig(
  level=logging.DEBUG,
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Main')

class AutoController:
  def __init__(self):
    self.logger = logging.getLogger('AutoController')
    self.adb = ADBController()
    self.scrcpy = ScrcpyController()
    self.cv = CVController()
    self.load_config()
  def load_config(self):
    """加载配置文件"""
    try:
      with open('config.yaml', 'r', encoding='utf-8') as f:
        self.config = yaml.safe_load(f)
        if not isinstance(self.config, dict) or 'tasks' not in self.config:
          raise ValueError("配置文件格式错误：缺少 'tasks' 配置")
        if not isinstance(self.config['tasks'], list):
          raise ValueError("配置文件格式错误：'tasks' 必须是列表")
        logger.info("配置加载成功")
    except Exception as e:
      logger.error(f"加载配置失败: {str(e)}")
      # 抛出异常,终止程序执行
      # raise 关键字用于抛出一个异常,会将前面捕获到的异常继续向上层抛出
      # 这里抛出异常是因为配置文件加载失败是致命错误,程序无法继续运行
      raise
  def execute_task(self, task):
    """执行单个任务"""
    try:
        # 检查屏幕状态并唤醒
        if not self.adb.check_screen_state():
            self.logger.info("屏幕未亮起，尝试唤醒")
            if not self.adb.wake_screen():
                return
            time.sleep(1)
            # 滑动解锁
            if not self.adb.swipe_unlock():
                return
            time.sleep(2)  # 等待解锁完成

        # 获取手机屏幕尺寸
        screen_size = self.adb.get_screen_size()
        if not screen_size:
            return

        # 启动应用
        if not self.adb.start_app(task['app_package']):
            return
        
        # 等待应用启动并加载完成
        startup_wait = task.get('startup_wait', 5)  # 默认等待5秒
        self.logger.info(f"等待应用启动: {startup_wait}秒")
        time.sleep(startup_wait)

        # 激活scrcpy窗口
        self.scrcpy.activate_window()
        window_rect = self.scrcpy.get_window_rect()
        if not window_rect:
            return

        # 执行动作序列
        for action in task['actions']:
            if action['type'] == 'click':
                # 设置重试次数
                max_retries = action.get('retries', 3)  # 默认重试3次
                retry_interval = action.get('retry_interval', 1)  # 默认重试间隔1秒
                
                for retry in range(max_retries):
                    # 获取窗口截图
                    screenshot, width, height = self.cv.capture_window(window_rect)
                    if screenshot is None:
                        continue

                    # 查找并点击目标
                    coords = self.cv.find_image(
                        f"images/{action['image']}", 
                        screenshot,
                        window_rect,
                        screen_size
                    )
                    if coords:
                        self.adb.tap(*coords)
                        time.sleep(action.get('wait', 1))
                        break
                    else:
                        if retry < max_retries - 1:  # 如果不是最后一次重试
                            self.logger.info(f"未找到目标，等待{retry_interval}秒后重试 ({retry + 1}/{max_retries})")
                            time.sleep(retry_interval)
                        else:
                            self.logger.warning(f"达到最大重试次数，跳过动作: {action['image']}")

            elif action['type'] == 'wait':
                time.sleep(action['duration'])
            elif action['type'] == 'close_app':
                time.sleep(action.get('wait', 0))
                self.adb.force_stop_app(task['app_package'])

    except Exception as e:
        self.logger.error(f"执行任务失败: {str(e)}")
  def run(self):
    """运行自动化控制"""
    try:
        if not self.config or 'tasks' not in self.config:
            raise ValueError("未找到有效的任务配置")

        # 设置定时任务
        for task in self.config['tasks']:
            if not isinstance(task, dict):
                self.logger.error(f"无效的任务配置: {task}")
                continue
            
            # 检查必要字段
            if 'app_package' not in task:
                self.logger.error(f"任务配置缺少必要字段 app_package: {task}")
                continue
            
            # 获取时间表
            schedules = task.get('schedules', [])  # 支持多个时间
            if not schedules:
                schedules = [task.get('schedule')]  # 兼容旧配置
            
            if not schedules or not any(schedules):
                self.logger.error(f"任务配置缺少时间设置: {task}")
                continue
            
            # 为每个时间点设置任务
            for schedule_time in schedules:
                if not schedule_time:
                    continue
                    
                schedule.every().day.at(schedule_time).do(
                    self.execute_task, task
                )
                self.logger.info(f"已设置定时任务: {task['name']} 在 {schedule_time}")

        # 运行定时任务
        while True:
            schedule.run_pending()
            time.sleep(1)

    except KeyboardInterrupt:
        self.logger.info("程序终止")
    except Exception as e:
        self.logger.error(f"运行失败: {str(e)}")
        raise

if __name__ == "__main__":
  controller = AutoController()
  controller.run()