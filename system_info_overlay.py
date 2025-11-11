import tkinter as tk
import socket
import platform
import subprocess
import re
import time
import threading
from ctypes import windll, Structure, c_ulong, byref
from PIL import Image, ImageTk, ImageDraw
import os
import sys
import webbrowser

class POINT(Structure):
    _fields_ = [("x", c_ulong), ("y", c_ulong)]

class SystemInfoOverlay:
    def __init__(self):
        # Create main overlay window (hidden initially)
        self.root = tk.Tk()
        self.setup_main_window()
        
        # Create icon window - now larger to accommodate text
        self.icon_root = tk.Toplevel()
        self.setup_icon_window()
        
        self.create_widgets()
        self.update_info()
        self.start_desktop_detection()
        
        # Track mouse state
        self.last_mouse_over_icon = False
        self.last_mouse_over_main = False
        self.hide_timer = None
        
    def setup_main_window(self):
        """Setup the main information overlay window"""
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 0.0)  # Start hidden
        self.root.attributes('-topmost', True)
        
        # Position at top-right corner, left of the icon
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"350x180+{screen_width-370}+20")
        self.root.configure(bg='#000000')
        
        self.is_visible = False
        
    def setup_icon_window(self):
        """Setup the icon window - will only show on desktop"""
        self.icon_root.overrideredirect(True)
        self.icon_root.attributes('-topmost', False)  # Don't stay on top
        self.icon_root.attributes('-alpha', 0.0)  # Start hidden
        
        # Position larger window to accommodate text (70x70 for icon + text)
        screen_width = self.icon_root.winfo_screenwidth()
        screen_height = self.icon_root.winfo_screenheight()
        self.icon_root.geometry(f"70x70+{screen_width-80}+20")
        self.icon_root.configure(bg='#000000')
        
        # Make icon click-through (non-interactive)
        self.icon_root.wm_attributes("-disabled", True)
        
        self.icon_visible = False
        
    def create_widgets(self):
        """Create widgets for both windows"""
        self.create_main_widgets()
        self.create_icon_widgets()
        
    def create_main_widgets(self):
        """Widgets for the main overlay window"""
        # Title bar
        title_frame = tk.Frame(self.root, bg='#1a1a1a', height=30)
        title_frame.pack(fill='x', padx=1, pady=1)
        title_frame.pack_propagate(False)
        
        title = tk.Label(title_frame, text="IM Support Dashboard", 
                        bg='#1a1a1a', fg='#ffffff', font=('Microsoft Sans Serif', 11, 'bold'))
        title.pack(expand=True)
        
        # Content frame
        content = tk.Frame(self.root, bg='#000000')
        content.pack(fill='both', expand=True, padx=15, pady=10)
        
        # Device name
        self.device_label = tk.Label(content, text="Device Name: ", 
                                    bg='#000000', fg='#ffffff', font=('Microsoft Sans Serif', 10, 'bold'))
        self.device_label.pack(anchor='w', pady=3)
        
        # Network status
        self.network_label = tk.Label(content, text="Network: ", 
                                     bg='#000000', fg='#00ff00', font=('Microsoft Sans Serif', 10, 'bold'))
        self.network_label.pack(anchor='w', pady=3)
        
        # Self Service Articles with clickable link
        articles_frame = tk.Frame(content, bg='#000000')
        articles_frame.pack(anchor='w', pady=3, fill='x')
        
        articles_label = tk.Label(articles_frame, text="Self Service Articles: ", 
                                 bg='#000000', fg='#ffffff', font=('Microsoft Sans Serif', 10, 'bold'))
        articles_label.pack(side='left')
        
        # Clickable link
        self.articles_link = tk.Label(articles_frame, text="Click Me", 
                                     bg='#000000', fg='#1e90ff', font=('Microsoft Sans Serif', 10, 'bold underline'),
                                     cursor="hand2")
        self.articles_link.pack(side='left')
        self.articles_link.bind("<Button-1>", lambda e: webbrowser.open("https://imservicedesk.debswana.bw/sd/SolutionsHome.sd"))
        
        # Contact Line
        contact_label = tk.Label(content, text="Contact Line: +267 364 8222 / EXT 18222", 
                                bg='#000000', fg='#ffffff', font=('Microsoft Sans Serif', 10, 'bold'))
        contact_label.pack(anchor='w', pady=3)
        
    def get_resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        
        return os.path.join(base_path, relative_path)
        
    def create_icon_image(self, image_path, size):
        """Create an icon image without rounded corners"""
        try:
            # Open and resize the image to specified size
            original_image = Image.open(image_path)
            resized_image = original_image.resize(size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            return ImageTk.PhotoImage(resized_image)
            
        except Exception as e:
            print(f"Error creating icon image: {e}")
            return None
        
    def create_icon_widgets(self):
        """Create icon with logo and Quick Help text"""
        try:
            # Main container for icon and text
            main_container = tk.Frame(self.icon_root, bg='#000000')
            main_container.pack(fill='both', expand=True)
            
            # Try multiple possible locations for the logo
            possible_paths = [
                "logo.png",
                self.get_resource_path("logo.png"),
                os.path.join(os.path.dirname(__file__), "logo.png"),
                os.path.join(os.path.dirname(sys.executable), "logo.png")
            ]
            
            logo_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    logo_path = path
                    break
            
            if logo_path:
                # Create image at 50x50 without rounded corners
                self.logo_image = self.create_icon_image(logo_path, (50, 50))
                
                if self.logo_image:
                    # Create label with the logo
                    self.icon_label = tk.Label(main_container, image=self.logo_image, 
                                             bg='#000000', borderwidth=0)
                    self.icon_label.pack(pady=(2, 0))
                    
                    # Add "Quick Help" text below the logo
                    help_text = tk.Label(main_container, text="Quick Help", 
                                       bg='#000000', fg='#ffffff')
                    help_text.pack(pady=(0, 2))
                    
                    print("Logo and help text loaded successfully!")
                else:
                    print("Failed to create image. Using fallback icon with text.")
                    self.create_fallback_icon_with_text()
            else:
                print("Logo not found. Using fallback icon with text.")
                self.create_fallback_icon_with_text()
                
        except Exception as e:
            print(f"Error loading logo: {e}. Using fallback icon with text.")
            self.create_fallback_icon_with_text()
    
    def create_fallback_icon_with_text(self):
        """Create a fallback icon with Quick Help text"""
        # Main container for icon and text
        main_container = tk.Frame(self.icon_root, bg='#000000')
        main_container.pack(fill='both', expand=True)
        
        # Icon frame
        icon_frame = tk.Frame(main_container, bg='#000000', width=50, height=50)
        icon_frame.pack(pady=(2, 0))
        icon_frame.pack_propagate(False)
        
        self.icon_canvas = tk.Canvas(icon_frame, bg='#000000', width=50, height=50,
                                    highlightthickness=0)
        self.icon_canvas.pack()
        
        # Draw rectangle background (no rounding)
        self.icon_canvas.create_rectangle(2, 2, 48, 48, fill='#01447c', outline='#ffffff', width=2)
        
        # Draw monitor shape (scaled for 50x50)
        self.icon_canvas.create_rectangle(10, 8, 40, 22, fill='#000000', outline='#ffffff', width=1)
        
        # Draw monitor base (scaled for 50x50)
        self.icon_canvas.create_rectangle(23, 22, 27, 28, fill='#000000', outline='')
        
        # Draw wrench icon (scaled for 50x50)
        self.icon_canvas.create_oval(32, 28, 42, 38, fill='#000000', outline='')
        self.icon_canvas.create_rectangle(18, 32, 32, 34, fill='#000000', outline='')
        
        # Add "IT" text (scaled for 50x50)
        self.icon_canvas.create_text(25, 15, text="IM", fill='#ffffff', 
                                   font=('Microsoft Sans Serif', 8, 'bold'))
        
        # Add "Quick Help" text below the icon
        help_text = tk.Label(main_container, text="Quick Help", 
                           bg='#000000', fg='#ffffff')
        help_text.pack(pady=(10, 2))
    
    def is_mouse_over_icon(self):
        """Check if mouse is over the icon window"""
        try:
            pt = POINT()
            windll.user32.GetCursorPos(byref(pt))
            mouse_x, mouse_y = pt.x, pt.y
            
            # Get icon window position and size (now 70x70)
            icon_x = self.icon_root.winfo_x()
            icon_y = self.icon_root.winfo_y()
            icon_width = self.icon_root.winfo_width()
            icon_height = self.icon_root.winfo_height()
            
            # Check if mouse is within icon bounds
            over_icon = (icon_x <= mouse_x <= icon_x + icon_width and
                        icon_y <= mouse_y <= icon_y + icon_height)
            
            return over_icon
        except:
            return False
    
    def is_mouse_over_main_window(self):
        """Check if mouse is over the main overlay window"""
        try:
            pt = POINT()
            windll.user32.GetCursorPos(byref(pt))
            mouse_x, mouse_y = pt.x, pt.y
            
            # Get main window position and size
            main_x = self.root.winfo_x()
            main_y = self.root.winfo_y()
            main_width = self.root.winfo_width()
            main_height = self.root.winfo_height()
            
            # Check if mouse is within main window bounds
            over_main = (main_x <= mouse_x <= main_x + main_width and
                        main_y <= mouse_y <= main_y + main_height)
            
            return over_main
        except:
            return False
    
    def is_desktop_visible(self):
        """Check if desktop is visible by looking for explorer windows"""
        try:
            # Get the foreground window
            foreground_hwnd = windll.user32.GetForegroundWindow()
            
            if foreground_hwnd == 0:
                return True
            
            # Get window text length
            text_length = windll.user32.GetWindowTextLengthW(foreground_hwnd)
            
            # If no window title, likely desktop
            if text_length == 0:
                return True
            
            # Get window class name
            class_name = " " * 256
            windll.user32.GetClassNameW(foreground_hwnd, class_name, 256)
            class_name = class_name.strip()
            
            # Desktop/shell window classes
            desktop_classes = ['Progman', 'WorkerW']
            if class_name in desktop_classes:
                return True
            
            # Check if it's a file explorer window
            if class_name == 'CabinetWClass' or class_name == 'ExploreWClass':
                return False
            
            # Get window text
            window_text = " " * 256
            windll.user32.GetWindowTextW(foreground_hwnd, window_text, 256)
            window_text = window_text.strip()
            
            # If it's a system window with no real title, consider it desktop
            system_windows = ['', 'Program Manager']
            if window_text in system_windows:
                return True
            
            # If we get here, it's likely an application window
            return False
            
        except Exception as e:
            return False
    
    def show_icon(self):
        """Show the icon on desktop"""
        if not self.icon_visible:
            self.icon_visible = True
            # Make sure icon is not on top of other windows
            self.icon_root.attributes('-topmost', False)
            self.icon_root.attributes('-alpha', 1.0)  # Fully visible
    
    def hide_icon(self):
        """Hide the icon when applications are open"""
        if self.icon_visible:
            self.icon_visible = False
            self.icon_root.attributes('-alpha', 0.0)  # Completely hidden
            # Also hide the overlay if it's visible
            if self.is_visible:
                self.hide_overlay()
    
    def show_overlay(self):
        """Show the main overlay with smooth animation"""
        if not self.is_visible:
            self.is_visible = True
            # Bring overlay to top
            self.root.attributes('-topmost', True)
            
            # Smooth fade in
            for alpha in [0.0, 0.3, 0.6, 0.9]:
                self.root.attributes('-alpha', alpha)
                self.root.update()
                time.sleep(0.02)
    
    def hide_overlay(self):
        """Hide the main overlay with smooth animation"""
        if self.is_visible:
            self.is_visible = False
            # Smooth fade out
            for alpha in [0.9, 0.6, 0.3, 0.0]:
                self.root.attributes('-alpha', alpha)
                self.root.update()
                time.sleep(0.02)
    
    def highlight_icon(self, highlight=True):
        """Add highlight effect to icon when hovered"""
        if highlight and self.icon_visible:
            # Add a subtle highlight when hovered
            if hasattr(self, 'icon_label'):
                self.icon_label.configure(bg='#333333')
            elif hasattr(self, 'icon_canvas'):
                self.icon_canvas.configure(bg='#333333')
        elif self.icon_visible:
            # Return to normal
            if hasattr(self, 'icon_label'):
                self.icon_label.configure(bg='#000000')
            elif hasattr(self, 'icon_canvas'):
                self.icon_canvas.configure(bg='#000000')
    
    def check_mouse_position(self):
        """Continuously check mouse position and manage overlay visibility"""
        current_over_icon = self.is_mouse_over_icon()
        current_over_main = self.is_mouse_over_main_window()
        
        # Mouse just entered icon
        if current_over_icon and not self.last_mouse_over_icon:
            self.highlight_icon(True)
            # Start hover timer to show overlay
            self.root.after(300, self.check_hover_duration)
        
        # Mouse just left icon but is over main window
        elif not current_over_icon and self.last_mouse_over_icon and current_over_main:
            # Keep overlay visible since mouse moved to main window
            pass
        
        # Mouse left both icon and main window
        elif not current_over_icon and not current_over_main and (self.last_mouse_over_icon or self.last_mouse_over_main):
            # Start hide timer
            self.schedule_hide()
        
        # Update last known positions
        self.last_mouse_over_icon = current_over_icon
        self.last_mouse_over_main = current_over_main
        
        # Continue checking
        self.root.after(100, self.check_mouse_position)
    
    def check_hover_duration(self):
        """Check if mouse has been hovering long enough to show overlay"""
        if self.is_mouse_over_icon() and not self.is_visible:
            self.show_overlay()
    
    def schedule_hide(self):
        """Schedule the overlay to hide after a delay"""
        # Cancel any existing hide timer
        if self.hide_timer:
            self.root.after_cancel(self.hide_timer)
        
        # Schedule new hide timer
        self.hide_timer = self.root.after(500, self.hide_if_mouse_gone)
    
    def hide_if_mouse_gone(self):
        """Hide overlay if mouse is not over icon or main window"""
        if not self.is_mouse_over_icon() and not self.is_mouse_over_main_window() and self.is_visible:
            self.hide_overlay()
            self.highlight_icon(False)
    
    def start_desktop_detection(self):
        """Monitor desktop state and control icon visibility"""
        def monitor():
            last_desktop_state = False
            
            while True:
                try:
                    # Check if desktop is visible
                    desktop_visible = self.is_desktop_visible()
                    
                    # Desktop state changed
                    if desktop_visible != last_desktop_state:
                        if desktop_visible:
                            self.root.after(0, self.show_icon)
                            # Start mouse tracking when desktop is visible
                            self.root.after(100, self.check_mouse_position)
                        else:
                            self.root.after(0, self.hide_icon)
                        last_desktop_state = desktop_visible
                    
                    time.sleep(0.5)  # Check 2 times per second
                    
                except Exception as e:
                    print(f"Desktop detection error: {e}")
                    time.sleep(0.5)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def get_device_name(self):
        try:
            return socket.gethostname()
        except:
            return "Unknown"
    
    def get_windows_network_name(self):
        """Get the actual WiFi network name (SSID) on Windows"""
        try:
            result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], 
                                  capture_output=True, text=True, shell=True)
            output = result.stdout
            
            ssid_pattern = r'SSID\s*:\s*(.+)'
            matches = re.findall(ssid_pattern, output)
            
            if matches:
                ssid = matches[0].strip()
                if ssid and not ssid.isspace():
                    return ssid
            
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, shell=True)
            ip_output = result.stdout
            
            ip_pattern = r'IPv4 Address[\. ]+: ([\d\.]+)'
            ip_matches = re.findall(ip_pattern, ip_output)
            
            for ip in ip_matches:
                if not ip.startswith('169.254.') and not ip.startswith('127.'):
                    return "Ethernet (Wired)"
            
            return "Not Connected"
            
        except Exception as e:
            return "Unknown"
    
    def update_info(self):
        """Update the system information"""
        device_name = self.get_device_name()
        self.device_label.config(text=f"Device Name: {device_name}")
        
        network_name = self.get_windows_network_name()
        network_status = f"Network: {network_name}"
        
        if "Not Connected" in network_name or "Unknown" in network_name:
            self.network_label.config(text=network_status, fg='#ff4444')
        else:
            self.network_label.config(text=network_status, fg='#00ff00')
        
        self.root.after(5000, self.update_info)
    
    def close_app(self):
        """Close both windows and exit - kept for emergency cleanup"""
        self.root.quit()
        self.root.destroy()
        self.icon_root.destroy()
    
    def run(self):
        """Start the application"""
        try:
            self.root.mainloop()
        except:
            pass

def main():
    app = SystemInfoOverlay()
    app.run()

if __name__ == "__main__":
    main()