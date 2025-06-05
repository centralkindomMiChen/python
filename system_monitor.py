import psutil
import datetime
import time

class SystemMonitor:
    """Provides methods to monitor system metrics like time, memory, and network speed."""
    def __init__(self):
        """Initializes the SystemMonitor.
        Sets up baseline values for calculating network speed.
        """
        self.last_net_io = psutil.net_io_counters()
        self.last_time = time.time()
        # No previous process times needed for global CPU usage.
        # If per-process CPU was needed, initialization would occur where process PID is known.

    def get_current_time(self):
        """Returns the current system time formatted as 'YYYY-MM-DD HH:MM:SS'."""
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_memory_usage_percent(self):
        """Returns the system-wide virtual memory usage as a percentage."""
        try:
            memory = psutil.virtual_memory()
            return memory.percent
        except Exception as e:
            # print(f"Error getting memory usage: {e}") # Keep for module testing
            return 0.0 # Return a default value on error

    def get_network_speed_kbytes_per_sec(self):
        """Calculates and returns network download and upload speeds in KB/s.
        This method is stateful and calculates speed based on changes since its last call.

        Returns:
            tuple: (download_speed_kbps, upload_speed_kbps). Returns (0.0, 0.0) on error or if
                   called too rapidly for a meaningful difference.
        """
        try:
            current_net_io = psutil.net_io_counters()
            current_time = time.time()

            time_diff = current_time - self.last_time
            bytes_sent_diff = current_net_io.bytes_sent - self.last_net_io.bytes_sent
            bytes_recv_diff = current_net_io.bytes_recv - self.last_net_io.bytes_recv

            # Update stored values for the next calculation
            self.last_net_io = current_net_io
            self.last_time = current_time

            if time_diff <= 0: # Avoid division by zero or negative time if system clock changed
                return 0.0, 0.0

            # Convert bytes per second to Kilobytes per second
            upload_speed_kbps = (bytes_sent_diff / time_diff) / 1024.0
            download_speed_kbps = (bytes_recv_diff / time_diff) / 1024.0

            # Ensure speeds are not negative (can happen with counter resets or anomalies)
            return max(0.0, download_speed_kbps), max(0.0, upload_speed_kbps)
        except Exception as e:
            # print(f"Error getting network speed: {e}") # Keep for module testing
            return 0.0, 0.0 # Return default values on error

# Example Usage (for testing this module directly)
if __name__ == '__main__':
    print("--- Testing SystemMonitor ---")
    monitor = SystemMonitor()

    # Test current time
    current_time_str = monitor.get_current_time()
    print(f"Current Time: {current_time_str}")
    assert len(current_time_str) == 19, "Time format seems incorrect."

    # Test memory usage
    mem_percent = monitor.get_memory_usage_percent()
    print(f"Memory Usage: {mem_percent}%")
    assert 0 <= mem_percent <= 100, "Memory percentage out of bounds."

    # Test network speed (call a few times to see changes)
    print("\nTesting network speed (call multiple times to observe changes)...")
    # First call initializes and might show 0 or high values if system just started network activity
    # or if this is the first time psutil.net_io_counters() is called after a long pause.
    down_speed, up_speed = monitor.get_network_speed_kbytes_per_sec()
    print(f"Network Speed (1st call): Download: {down_speed:.2f} KB/s, Upload: {up_speed:.2f} KB/s")
    assert down_speed >= 0 and up_speed >= 0, "Network speed (1st call) cannot be negative."

    print("Waiting 1 second for next network speed test...")
    time.sleep(1.0) # Use floating point for sleep
    down_speed, up_speed = monitor.get_network_speed_kbytes_per_sec()
    print(f"Network Speed (2nd call): Download: {down_speed:.2f} KB/s, Upload: {up_speed:.2f} KB/s")
    assert down_speed >= 0 and up_speed >= 0, "Network speed (2nd call) cannot be negative."

    print("Waiting 1 second for next network speed test...")
    time.sleep(1.0)
    down_speed, up_speed = monitor.get_network_speed_kbytes_per_sec()
    print(f"Network Speed (3rd call): Download: {down_speed:.2f} KB/s, Upload: {up_speed:.2f} KB/s")
    assert down_speed >= 0 and up_speed >= 0, "Network speed (3rd call) cannot be negative."

    # Test rapid calls to network speed (should ideally return 0 or handle gracefully)
    print("\nTesting rapid network speed calls...")
    down_speed_rapid, up_speed_rapid = monitor.get_network_speed_kbytes_per_sec() # Call immediately after previous
    print(f"Network Speed (Rapid call): Download: {down_speed_rapid:.2f} KB/s, Upload: {up_speed_rapid:.2f} KB/s")
    assert down_speed_rapid >= 0 and up_speed_rapid >= 0, "Rapid call network speed cannot be negative."


    print("\n--- SystemMonitor testing finished. ---")
