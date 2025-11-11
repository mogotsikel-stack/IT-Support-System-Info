import tkinter as tk
from tkinter import ttk
import socket
import platform
import subprocess
import re

class SystemInfoOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.create_widgets()
        self.update_info()
        
    def setup_window(self):
        # Set window properties for overlay
        self.root.overrideredirect(True)  # Remove window decorations
        self.root.attributes('-topmost', True)  # Always on top
        self.root.attributes('-alpha', 0.9)  # Slightly less transparent for better readability
        
        # Position at top-right corner
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"320x160+{screen_width-340}+20")
        
        # Black color scheme
        self.root.configure(bg='#000000')
        
    def create_widgets(self):
        # Title bar with gradient effect
        title_frame = tk.Frame(self.root, bg='#1a1a1a', height=30)
        title_frame.pack(fill='x', padx=1, pady=1)
        title_frame.pack_propagate(False)
        
        title = tk.Label(title_frame, text="System Information", 
                        bg='#1a1a1a', fg='#ffffff', font=('Arial', 11, 'bold'))
        title.pack(expand=True)
        
        # Content frame with dark background
        content = tk.Frame(self.root, bg='#000000')
        content.pack(fill='both', expand=True, padx=15, pady=10)
        
        # Device name
        self.device_label = tk.Label(content, text="Device Name: ", 
                                    bg='#000000', fg='#00ff00', font=('Arial', 10, 'bold'))
        self.device_label.pack(anchor='w', pady=4)
        
        # Network status
        self.network_label = tk.Label(content, text="Network Connected: ", 
                                     bg='#000000', fg='#00ff00', font=('Arial', 10, 'bold'))
        self.network_label.pack(anchor='w', pady=4)
        
        # OS information
        self.os_label = tk.Label(content, text="OS: ", 
                                bg='#000000', fg='#00ff00', font=('Arial', 10, 'bold'))
        self.os_label.pack(anchor='w', pady=4)
        
        # Close button (red for contrast)
        close_btn = tk.Button(self.root, text="✕", command=self.root.destroy,
                             bg='#ff4444', fg='white', font=('Arial', 10, 'bold'), 
                             width=2, relief='flat', bd=0)
        close_btn.place(x=295, y=3)
        
    def get_device_name(self):
        try:
            return socket.gethostname()
        except:
            return "Unknown"
    
    def get_windows_network_name(self):
        """Get the actual WiFi network name (SSID) on Windows"""
        try:
            # Method 1: Using netsh to get current connected network
            result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], 
                                  capture_output=True, text=True, shell=True)
            output = result.stdout
            
            # Look for SSID in the output
            ssid_pattern = r'SSID\s*:\s*(.+)'
            matches = re.findall(ssid_pattern, output)
            
            if matches:
                ssid = matches[0].strip()
                if ssid and not ssid.isspace():
                    return ssid
            
            # Method 2: Check if any network is connected via ipconfig
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, shell=True)
            ip_output = result.stdout
            
            # Check if we have a valid non-local IP
            ip_pattern = r'IPv4 Address[\. ]+: ([\d\.]+)'
            ip_matches = re.findall(ip_pattern, ip_output)
            
            for ip in ip_matches:
                if not ip.startswith('169.254.') and not ip.startswith('127.'):
                    # We have a valid connection but couldn't get SSID
                    return "Ethernet (Wired)"
            
            return "Not Connected"
            
        except Exception as e:
            return "Unknown"
    
    def update_info(self):
        # Update device name
        device_name = self.get_device_name()
        self.device_label.config(text=f"Device Name: {device_name}")
        
        # Update network information
        network_name = self.get_windows_network_name()
        network_status = f"Network Connected: {network_name}"
        
        if "Not Connected" in network_name or "Unknown" in network_name:
            self.network_label.config(text=network_status, fg='#ff4444')  # Red for not connected
        else:
            self.network_label.config(text=network_status, fg='#00ff00')  # Green for connected
        
        # Update OS information
        os_info = f"OS: {platform.system()} {platform.release()}"
        self.os_label.config(text=os_info)
        
        # Schedule next update
        self.root.after(5000, self.update_info)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SystemInfoOverlay()
    app.run()