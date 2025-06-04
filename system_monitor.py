import psutil
import time

class SystemMonitor:
    def __init__(self):
        try:
            self.last_net_io = psutil.net_io_counters()
        except Exception as e:
            print(f"无法初始化网络监控: {e}. 网络速度将不可用。")
            self.last_net_io = None # 标记网络监控不可用
        self.last_time = time.time()

    def get_memory_usage(self):
        try:
            return psutil.virtual_memory().percent
        except Exception as e:
            print(f"获取内存使用情况失败: {e}")
            return 0.0 # 返回默认值

    def get_network_speed(self):
        if not self.last_net_io: # 如果初始化失败
            return 0.0, 0.0

        try:
            current_net_io = psutil.net_io_counters()
            current_time = time.time()

            time_diff = current_time - self.last_time
            if time_diff <= 0: # 避免除以零或负数
                return 0.0, 0.0

            bytes_sent_diff = current_net_io.bytes_sent - self.last_net_io.bytes_sent
            bytes_recv_diff = current_net_io.bytes_recv - self.last_net_io.bytes_recv

            upload_speed_kbps = (bytes_sent_diff / time_diff) / 1024
            download_speed_kbps = (bytes_recv_diff / time_diff) / 1024

            self.last_net_io = current_net_io
            self.last_time = current_time

            return download_speed_kbps, upload_speed_kbps
        except Exception as e:
            print(f"获取网络速度失败: {e}")
            # 重置以避免连续错误，如果需要
            # self.last_net_io = psutil.net_io_counters()
            # self.last_time = time.time()
            return 0.0, 0.0 # 返回默认值
