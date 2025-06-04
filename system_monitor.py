import psutil
import datetime
import time

class SystemMonitor:
    def __init__(self):
        # For network speed, we need to store the previous values
        self.last_net_io = psutil.net_io_counters()
        self.last_time = time.time()

    def get_current_time(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_memory_usage(self):
        # Returns memory usage as a percentage
        memory = psutil.virtual_memory()
        return memory.percent

    def get_network_speed(self):
        # Returns download and upload speed in KB/s
        current_net_io = psutil.net_io_counters()
        current_time = time.time()

        time_diff = current_time - self.last_time
        bytes_sent_diff = current_net_io.bytes_sent - self.last_net_io.bytes_sent
        bytes_recv_diff = current_net_io.bytes_recv - self.last_net_io.bytes_recv

        if time_diff == 0: # Avoid division by zero if called too rapidly
            # Could return previous values or 0,0. For simplicity, 0,0 if no time diff.
            return 0.0, 0.0

        # Convert bytes per second to KB per second
        upload_speed_kbps = (bytes_sent_diff / time_diff) / 1024
        download_speed_kbps = (bytes_recv_diff / time_diff) / 1024

        self.last_net_io = current_net_io
        self.last_time = current_time

        return download_speed_kbps, upload_speed_kbps

# Example Usage (for testing this module directly)
if __name__ == '__main__':
    monitor = SystemMonitor()
    print(f"Current Time: {monitor.get_current_time()}")
    print(f"Memory Usage: {monitor.get_memory_usage()}%")

    # Test network speed (call twice to see changes)
    print("Network Speed (1st call): ↓%.2f KB/s ↑%.2f KB/s" % monitor.get_network_speed())
    time.sleep(1) # Wait for 1 second
    print("Network Speed (2nd call): ↓%.2f KB/s ↑%.2f KB/s" % monitor.get_network_speed())
    time.sleep(1)
    print("Network Speed (3rd call): ↓%.2f KB/s ↑%.2f KB/s" % monitor.get_network_speed())
