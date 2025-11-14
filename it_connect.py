# Force DPI Awareness for crisp rendering - MUST BE AT THE VERY TOP
import ctypes
try:
    # Set DPI awareness for Windows 8.1 and above
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PER_MONITOR_DPI_AWARE = 2
except Exception:
    try:
        # Fallback for Windows 8 and below
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import tkinter as tk
import socket
import platform
import subprocess
import re
import time
import threading
from ctypes import windll, Structure, c_ulong, byref
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import sys
import webbrowser
import getpass

class POINT(Structure):
    _fields_ = [("x", c_ulong), ("y", c_ulong)]

class CustomerSupportOverlay:
    def __init__(self):
        # Create main overlay window (hidden initially)
        self.root = tk.Tk()
        self.setup_main_window()
        
        # Create icon window
        self.icon_root = tk.Toplevel()
        self.setup_icon_window()
        
        self.create_widgets()
        self.update_info()
        
        # Track window state
        self.is_visible = False
        self.hide_timer = None
        
    def get_windows_icon_size(self):
        """Get the appropriate icon size based on Windows desktop icon settings"""
        try:
            # Windows desktop icon sizes:
            # Small: 32x32, Medium: 48x48, Large: 64x64, Extra Large: 96x96
            
            # For Medium setting, use 48x48 as base but scale for better visibility
            # Using 60x60 for Medium size as it provides good visibility while fitting well
            base_size = 50
            
            # Get DPI scaling factor
            hdc = windll.user32.GetDC(0)
            dpi = windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
            windll.user32.ReleaseDC(0, hdc)
            
            # Calculate scaled size based on DPI
            scale_factor = dpi / 96.0  # 96 is standard DPI
            scaled_size = int(base_size * scale_factor)
            
            # Ensure reasonable bounds
            scaled_size = max(48, min(scaled_size, 80))
            
            return scaled_size
            
        except Exception as e:
            print(f"Error detecting icon size: {e}, using default 60x60")
            return 60
    
    def setup_main_window(self):
        """Setup the main information overlay window"""
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 0.0)  # Start hidden
        self.root.attributes('-topmost', True)
        
        # Position at top-right corner, left of the icon
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"350x530+{screen_width-370}+20")  # Adjusted size to fit content
        self.root.configure(bg='#2c2c2c')
        
    def setup_icon_window(self):
        """Setup the icon window - behaves like desktop shortcuts (Edge, Adobe)"""
        self.icon_root.overrideredirect(True)
        self.icon_root.attributes('-topmost', False)  # Don't stay on top of apps
        self.icon_root.attributes('-alpha', 1.0)  # Always visible on desktop
        
        # Get scaled icon size for Windows Medium setting
        self.icon_size = self.get_windows_icon_size()
        
        # Position at top-right corner with proper spacing
        screen_width = self.icon_root.winfo_screenwidth()
        screen_height = self.icon_root.winfo_screenheight()
        
        # Calculate position to align with desktop icons
        x_position = screen_width - self.icon_size - 25  # 20px margin from right edge
        y_position = 20  # 40px from top
        
        self.icon_root.geometry(f"{self.icon_size}x{self.icon_size}+{x_position}+{y_position}")
        self.icon_root.configure(bg='#000001')  # Use a very dark color that's almost black
        self.icon_root.wm_attributes("-transparentcolor", "#000001")  # Make this specific color transparent
        
        # Make it a proper desktop-level window
        self.make_desktop_window()
        
    def make_desktop_window(self):
        """Make the window behave like a desktop icon"""
        try:
            # Get the window handle
            hwnd = windll.user32.FindWindowW(None, self.icon_root.title())
            
            # Set window style to make it a desktop-level window
            # This makes it behave like desktop icons
            GWL_EXSTYLE = -20
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_NOACTIVATE = 0x08000000
            
            # Get current style
            current_style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            
            # Add toolwindow and noactivate styles
            new_style = current_style | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
            windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            
        except Exception as e:
            print(f"Window style error: {e}")
    
    def create_widgets(self):
        """Create widgets for both windows"""
        self.create_main_widgets()
        self.create_icon_widgets()
        
    def create_main_widgets(self):
        """Widgets for the main overlay window"""
        # Main content frame - no scrollbar
        main_frame = tk.Frame(self.root, bg='#2c2c2c')
        main_frame.pack(fill='both', expand=True, padx=0, pady=0)
        
        # Title bar with "Need IT Support?" text
        title_frame = tk.Frame(main_frame, bg='#1e1e1e', height=40)
        title_frame.pack(fill='x', padx=0, pady=0)
        title_frame.pack_propagate(False)
        
        title = tk.Label(title_frame, text="Need IT Support?", 
                        bg='#1e1e1e', fg='#ffffff', font=('Microsoft Sans Serif', 10, 'bold'))
        title.pack(expand=True, pady=10)
        
        # Content frame
        content = tk.Frame(main_frame, bg='#2c2c2c')
        content.pack(fill='both', expand=True, padx=10, pady=10)
        
        # System Information Section
        sys_info_frame = tk.Frame(content, bg='#2c2c2c')
        sys_info_frame.pack(fill='x', pady=(0, 5))
        
        # Device name
        device_frame = tk.Frame(sys_info_frame, bg='#2c2c2c')
        device_frame.pack(fill='x', pady=2)
        
        device_label = tk.Label(device_frame, text="Device Name:", 
                               bg='#2c2c2c', fg='#cccccc', font=('Microsoft Sans Serif', 9),
                               anchor='w', width=15)
        device_label.pack(side='left')
        
        self.device_value = tk.Label(device_frame, text="", 
                                    bg='#2c2c2c', fg='#ffffff', font=('Microsoft Sans Serif', 9, 'bold'),
                                    anchor='w')
        self.device_value.pack(side='left', fill='x', expand=True)
        
        # Username
        user_frame = tk.Frame(sys_info_frame, bg='#2c2c2c')
        user_frame.pack(fill='x', pady=2)
        
        user_label = tk.Label(user_frame, text="Username:", 
                             bg='#2c2c2c', fg='#cccccc', font=('Microsoft Sans Serif', 9),
                             anchor='w', width=15)
        user_label.pack(side='left')
        
        self.user_value = tk.Label(user_frame, text="", 
                                  bg='#2c2c2c', fg='#ffffff', font=('Microsoft Sans Serif', 9, 'bold'),
                                  anchor='w')
        self.user_value.pack(side='left', fill='x', expand=True)
        
        # Domain
        domain_frame = tk.Frame(sys_info_frame, bg='#2c2c2c')
        domain_frame.pack(fill='x', pady=2)
        
        domain_label = tk.Label(domain_frame, text="Domain:", 
                               bg='#2c2c2c', fg='#cccccc', font=('Microsoft Sans Serif', 9),
                               anchor='w', width=15)
        domain_label.pack(side='left')
        
        self.domain_value = tk.Label(domain_frame, text="", 
                                    bg='#2c2c2c', fg='#ffffff', font=('Microsoft Sans Serif', 9, 'bold'),
                                    anchor='w')
        self.domain_value.pack(side='left', fill='x', expand=True)
        
        # Network
        network_frame = tk.Frame(sys_info_frame, bg='#2c2c2c')
        network_frame.pack(fill='x', pady=2)
        
        network_label = tk.Label(network_frame, text="Network:", 
                                bg='#2c2c2c', fg='#cccccc', font=('Microsoft Sans Serif', 9),
                                anchor='w', width=15)
        network_label.pack(side='left')
        
        self.network_value = tk.Label(network_frame, text="", 
                                     bg='#2c2c2c', fg='#ffffff', font=('Microsoft Sans Serif', 9, 'bold'),
                                     anchor='w')
        self.network_value.pack(side='left', fill='x', expand=True)
        
        # Separator
        separator1 = tk.Frame(content, bg='#555555', height=1)
        separator1.pack(fill='x', pady=8)
        
        # Service Desk Section
        service_desk_frame = tk.Frame(content, bg='#2c2c2c')
        service_desk_frame.pack(fill='x', pady=(0, 10))
        
        # Service Desk Title
        service_title = tk.Label(service_desk_frame, text="Service Desk", 
                                bg='#2c2c2c', fg='#ffffff', font=('Microsoft Sans Serif', 10, 'bold'),
                                anchor='w')
        service_title.pack(anchor='w', pady=(0, 5))
        
        # Operating Hours
        hours_frame = tk.Frame(service_desk_frame, bg='#2c2c2c')
        hours_frame.pack(fill='x', pady=2)
        
        hours_label = tk.Label(hours_frame, text="Operating Hours:", 
                              bg='#2c2c2c', fg='#cccccc', font=('Microsoft Sans Serif', 9),
                              anchor='w', width=15)
        hours_label.pack(side='left')
        
        hours_value = tk.Label(hours_frame, text="0700 - 1645hrs", 
                              bg='#2c2c2c', fg='#ffffff', font=('Microsoft Sans Serif', 9, 'bold'),
                              anchor='w')
        hours_value.pack(side='left', fill='x', expand=True)
        
        # Self Service Articles
        articles_frame = tk.Frame(service_desk_frame, bg='#2c2c2c')
        articles_frame.pack(fill='x', pady=2)
        
        articles_label = tk.Label(articles_frame, text="Self Service Articles:", 
                                 bg='#2c2c2c', fg='#cccccc', font=('Microsoft Sans Serif', 9),
                                 anchor='w', width=15)
        articles_label.pack(side='left')
        
        # Clickable link
        self.articles_link = tk.Label(articles_frame, text="Click Me", 
                                     bg='#2c2c2c', fg='#1e90ff', font=('Microsoft Sans Serif', 9, 'underline'),
                                     cursor="hand2")
        self.articles_link.pack(side='left')
        self.articles_link.bind("<Button-1>", lambda e: webbrowser.open("https://imservicedesk.debswana.bw/sd/SolutionsHome.sd"))
        
        # Email
        email_frame = tk.Frame(service_desk_frame, bg='#2c2c2c')
        email_frame.pack(fill='x', pady=2)
        
        email_label = tk.Label(email_frame, text="Email:", 
                              bg='#2c2c2c', fg='#cccccc', font=('Microsoft Sans Serif', 9),
                              anchor='w', width=15)
        email_label.pack(side='left')
        
        email_value = tk.Label(email_frame, text="dbshelp@debswana.bw", 
                              bg='#2c2c2c', fg='#ffffff', font=('Microsoft Sans Serif', 9, 'bold'),
                              anchor='w')
        email_value.pack(side='left', fill='x', expand=True)
        
        # Internal Number
        internal_frame = tk.Frame(service_desk_frame, bg='#2c2c2c')
        internal_frame.pack(fill='x', pady=2)
        
        internal_label = tk.Label(internal_frame, text="Internal Number:", 
                                 bg='#2c2c2c', fg='#cccccc', font=('Microsoft Sans Serif', 9),
                                 anchor='w', width=15)
        internal_label.pack(side='left')
        
        internal_value = tk.Label(internal_frame, text="18222", 
                                 bg='#2c2c2c', fg='#ffffff', font=('Microsoft Sans Serif', 9, 'bold'),
                                 anchor='w')
        internal_value.pack(side='left', fill='x', expand=True)
        
        # External Number
        external_frame = tk.Frame(service_desk_frame, bg='#2c2c2c')
        external_frame.pack(fill='x', pady=2)
        
        external_label = tk.Label(external_frame, text="External Number:", 
                                 bg='#2c2c2c', fg='#cccccc', font=('Microsoft Sans Serif', 9),
                                 anchor='w', width=15)
        external_label.pack(side='left')
        
        external_value = tk.Label(external_frame, text="+267 364 8222", 
                                 bg='#2c2c2c', fg='#ffffff', font=('Microsoft Sans Serif', 9, 'bold'),
                                 anchor='w')
        external_value.pack(side='left', fill='x', expand=True)
        
        # Separator
        separator2 = tk.Frame(content, bg='#555555', height=1)
        separator2.pack(fill='x', pady=8)
        
        # Standby Section
        standby_frame = tk.Frame(content, bg='#2c2c2c')
        standby_frame.pack(fill='x', pady=(0, 10))
        
        # Standby Title
        standby_title = tk.Label(standby_frame, text="Standby", 
                               bg='#2c2c2c', fg='#ffffff', font=('Microsoft Sans Serif', 10, 'bold'),
                               anchor='w')
        standby_title.pack(anchor='w', pady=(0, 3))
        
        # Standby Operating Hours
        standby_hours_frame = tk.Frame(standby_frame, bg='#2c2c2c')
        standby_hours_frame.pack(fill='x', pady=2)
        
        standby_hours_label = tk.Label(standby_hours_frame, text="Operating Hours:", 
                                      bg='#2c2c2c', fg='#cccccc', font=('Microsoft Sans Serif', 9),
                                      anchor='w', width=15)
        standby_hours_label.pack(side='left')
        
        standby_hours_value = tk.Label(standby_hours_frame, text="1645 - 0700hrs", 
                                      bg='#2c2c2c', fg='#ffffff', font=('Microsoft Sans Serif', 9, 'bold'),
                                      anchor='w')
        standby_hours_value.pack(side='left', fill='x', expand=True)
        
        # Standby Contacts
        # DJW
        djw_frame = tk.Frame(standby_frame, bg='#2c2c2c')
        djw_frame.pack(fill='x', pady=0)
        
        djw_label = tk.Label(djw_frame, text="DJW:", 
                            bg='#2c2c2c', fg='#cccccc', font=('Microsoft Sans Serif', 9),
                            anchor='w', width=15)
        djw_label.pack(side='left')
        
        djw_value = tk.Label(djw_frame, text="71382489", 
                            bg='#2c2c2c', fg='#ffffff', font=('Microsoft Sans Serif', 9, 'bold'),
                            anchor='w')
        djw_value.pack(side='left', fill='x', expand=True)
        
        # DOR
        dor_frame = tk.Frame(standby_frame, bg='#2c2c2c')
        dor_frame.pack(fill='x', pady=1)
        
        dor_label = tk.Label(dor_frame, text="DOR:", 
                            bg='#2c2c2c', fg='#cccccc', font=('Microsoft Sans Serif', 9),
                            anchor='w', width=15)
        dor_label.pack(side='left')
        
        dor_value = tk.Label(dor_frame, text="71313074", 
                            bg='#2c2c2c', fg='#ffffff', font=('Microsoft Sans Serif', 9, 'bold'),
                            anchor='w')
        dor_value.pack(side='left', fill='x', expand=True)
        
        # DCC
        dcc_frame = tk.Frame(standby_frame, bg='#2c2c2c')
        dcc_frame.pack(fill='x', pady=1)
        
        dcc_label = tk.Label(dcc_frame, text="DCC:", 
                            bg='#2c2c2c', fg='#cccccc', font=('Microsoft Sans Serif', 9),
                            anchor='w', width=15)
        dcc_label.pack(side='left')
        
        dcc_value = tk.Label(dcc_frame, text="71320195", 
                            bg='#2c2c2c', fg='#ffffff', font=('Microsoft Sans Serif', 9, 'bold'),
                            anchor='w')
        dcc_value.pack(side='left', fill='x', expand=True)
        
        # Bind mouse events to the main window for auto-hide
        self.root.bind("<Enter>", self.on_enter_main_window)
        self.root.bind("<Leave>", self.on_leave_main_window)
        
    def create_text_icon(self):
        """Create a text-based 'IM' icon with white rounded box that scales with Windows icon size"""
        size = (self.icon_size, self.icon_size)
        image = Image.new('RGBA', size, (0, 0, 0, 0))  # Transparent background
        draw = ImageDraw.Draw(image)
        
        # Calculate proportional sizes based on icon size
        box_margin = max(4, int(self.icon_size * 0.08))  # 8% margin
        corner_radius = max(8, int(self.icon_size * 0.13))  # 13% for corner radius
        font_size = max(16, int(self.icon_size * 0.35))  # 35% of icon size for font
        
        # White rounded rectangle background
        box_coords = [
            box_margin, 
            box_margin, 
            size[0] - box_margin, 
            size[1] - box_margin
        ]
        
        # Draw rounded rectangle (create by drawing circles at corners and filling)
        # Top-left circle
        draw.ellipse([box_coords[0], box_coords[1], 
                     box_coords[0] + corner_radius * 2, box_coords[1] + corner_radius * 2], 
                    fill='#ffffff')
        # Top-right circle
        draw.ellipse([box_coords[2] - corner_radius * 2, box_coords[1], 
                     box_coords[2], box_coords[1] + corner_radius * 2], 
                    fill='#ffffff')
        # Bottom-left circle
        draw.ellipse([box_coords[0], box_coords[3] - corner_radius * 2, 
                     box_coords[0] + corner_radius * 2, box_coords[3]], 
                    fill='#ffffff')
        # Bottom-right circle
        draw.ellipse([box_coords[2] - corner_radius * 2, box_coords[3] - corner_radius * 2, 
                     box_coords[2], box_coords[3]], 
                    fill='#ffffff')
        
        # Fill the rectangle areas
        draw.rectangle([box_coords[0], box_coords[1] + corner_radius, 
                       box_coords[2], box_coords[3] - corner_radius], 
                      fill='#ffffff')
        draw.rectangle([box_coords[0] + corner_radius, box_coords[1], 
                       box_coords[2] - corner_radius, box_coords[3]], 
                      fill='#ffffff')
        
        # Draw "IM" text in blue, bold
        try:
            # Try to use a bold font
            font = ImageFont.truetype("arialbd.ttf", font_size)  # Bold Arial
        except:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)  # Regular Arial
            except:
                try:
                    # Try Segoe UI which is common on Windows
                    font = ImageFont.truetype("segoeuib.ttf", font_size)
                except:
                    font = ImageFont.load_default()
        
        text = "IT"
        # Calculate text position to center it
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (size[0] - text_width) // 2
        text_y = (size[1] - text_height) // 2 - 2  # Slight vertical adjustment
        
        draw.text((text_x, text_y), text, fill='#0078d7', font=font)
        
        return ImageTk.PhotoImage(image)
    
    def create_icon_widgets(self):
        """Create text-based icon with 'IM' in white rounded box"""
        try:
            # Create the text icon
            self.icon_image = self.create_text_icon()
            
            if self.icon_image:
                # Create a container frame
                icon_container = tk.Frame(self.icon_root, bg='#000001', borderwidth=0, highlightthickness=0)
                icon_container.pack(fill='both', expand=True)
                
                # Create label with the text icon
                self.icon_label = tk.Label(icon_container, image=self.icon_image, 
                                         bg='#000001', borderwidth=0, highlightthickness=0,
                                         cursor="hand2")
                self.icon_label.pack(expand=True, fill='both')
                self.icon_label.bind("<Button-1>", self.toggle_overlay)
                
                # Force window update for better rendering
                self.icon_root.update_idletasks()
                
                print(f"Text-based 'IM' icon created successfully! Size: {self.icon_size}x{self.icon_size}")
            else:
                print("Failed to create text icon. Using fallback.")
                self.create_fallback_text_icon()
                
        except Exception as e:
            print(f"Error creating text icon: {e}. Using fallback.")
            self.create_fallback_text_icon()
    
    def create_fallback_text_icon(self):
        """Create a fallback text icon using tkinter canvas"""
        # Create a container frame
        icon_container = tk.Frame(self.icon_root, bg='#000001', borderwidth=0, highlightthickness=0)
        icon_container.pack(fill='both', expand=True)
        
        # Create a canvas with transparent background
        canvas = tk.Canvas(icon_container, bg='#000001', width=self.icon_size, height=self.icon_size,
                          highlightthickness=0, borderwidth=0, cursor="hand2")
        canvas.pack(expand=True, fill='both')
        canvas.bind("<Button-1>", self.toggle_overlay)
        
        # Calculate proportional sizes
        box_margin = max(4, int(self.icon_size * 0.08))
        corner_radius = max(8, int(self.icon_size * 0.13))
        font_size = max(16, int(self.icon_size * 0.35))
        
        # Draw white rounded rectangle
        canvas.create_rectangle(box_margin + corner_radius, box_margin,
                               self.icon_size - box_margin - corner_radius, self.icon_size - box_margin,
                               fill='#ffffff', outline='')
        canvas.create_rectangle(box_margin, box_margin + corner_radius,
                               self.icon_size - box_margin, self.icon_size - box_margin - corner_radius,
                               fill='#ffffff', outline='')
        
        # Draw rounded corners (circles)
        canvas.create_oval(box_margin, box_margin,
                          box_margin + corner_radius * 2, box_margin + corner_radius * 2,
                          fill='#ffffff', outline='')
        canvas.create_oval(self.icon_size - box_margin - corner_radius * 2, box_margin,
                          self.icon_size - box_margin, box_margin + corner_radius * 2,
                          fill='#ffffff', outline='')
        canvas.create_oval(box_margin, self.icon_size - box_margin - corner_radius * 2,
                          box_margin + corner_radius * 2, self.icon_size - box_margin,
                          fill='#ffffff', outline='')
        canvas.create_oval(self.icon_size - box_margin - corner_radius * 2, self.icon_size - box_margin - corner_radius * 2,
                          self.icon_size - box_margin, self.icon_size - box_margin,
                          fill='#ffffff', outline='')
        
        # Draw "IM" text in blue, bold
        canvas.create_text(self.icon_size // 2, self.icon_size // 2, text="IT", fill='#0078d7', 
                          font=('Arial', font_size, 'bold'), justify='center')
        
        # Force window update for better rendering
        self.icon_root.update_idletasks()
               
    def get_device_name(self):
        try:
            return socket.gethostname()
        except:
            return "Unknown"
    
    def get_username(self):
        try:
            return getpass.getuser()
        except:
            return "Unknown"
    
    def get_domain(self):
        try:
            # Try to get domain name from environment variables
            domain = os.environ.get('USERDOMAIN', '')
            if domain:
                return domain
            
            # Alternative method for domain detection
            result = subprocess.run(['net', 'config', 'workstation'], 
                                  capture_output=True, text=True, shell=True)
            output = result.stdout
            
            # Look for domain in the output
            for line in output.split('\n'):
                if 'Workstation domain' in line:
                    return line.split(':')[-1].strip()
            
            return "Unknown Domain"
            
        except:
            return "Unknown Domain"
    
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
        self.device_value.config(text=device_name)
        
        username = self.get_username()
        self.user_value.config(text=username)
        
        domain = self.get_domain()
        self.domain_value.config(text=domain)
        
        network_name = self.get_windows_network_name()
        network_status = network_name
        
        # Update network color based on connection status
        if "Not Connected" in network_name or "Unknown" in network_name:
            self.network_value.config(text=network_status, fg='#ff4444')
        else:
            self.network_value.config(text=network_status, fg='#00ff00')
        
        self.root.after(5000, self.update_info)  # Update every 5 seconds
    
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
    
    def is_mouse_over_icon(self):
        """Check if mouse is over the icon window"""
        try:
            pt = POINT()
            windll.user32.GetCursorPos(byref(pt))
            mouse_x, mouse_y = pt.x, pt.y
            
            # Get icon window position and size
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
    
    def on_enter_main_window(self, event=None):
        """Mouse entered the main window - cancel any hide timer"""
        if self.hide_timer:
            self.root.after_cancel(self.hide_timer)
            self.hide_timer = None
    
    def on_leave_main_window(self, event=None):
        """Mouse left the main window - start hide timer"""
        # Schedule the overlay to hide after a short delay
        if self.is_visible:
            self.hide_timer = self.root.after(500, self.check_mouse_position)
    
    def check_mouse_position(self):
        """Check if mouse is still away from both windows and hide if needed"""
        if not self.is_mouse_over_main_window() and not self.is_mouse_over_icon():
            self.hide_overlay()
        else:
            # Mouse is still over one of the windows, check again
            self.hide_timer = self.root.after(100, self.check_mouse_position)
    
    def toggle_overlay(self, event=None):
        """Toggle the information panel on click"""
        if self.is_visible:
            self.hide_overlay()
        else:
            self.show_overlay()
    
    def show_overlay(self):
        """Show the main overlay with smooth animation"""
        if not self.is_visible:
            self.is_visible = True
            self.root.attributes('-topmost', True)
            
            # Cancel any existing hide timer
            if self.hide_timer:
                self.root.after_cancel(self.hide_timer)
                self.hide_timer = None
            
            # Smooth fade in
            for alpha in [0.0, 0.3, 0.6, 0.9]:
                self.root.attributes('-alpha', alpha)
                self.root.update()
                time.sleep(0.02)
    
    def hide_overlay(self):
        """Hide the main overlay with smooth animation"""
        if self.is_visible:
            self.is_visible = False
            
            # Cancel any existing hide timer
            if self.hide_timer:
                self.root.after_cancel(self.hide_timer)
                self.hide_timer = None
            
            # Smooth fade out
            for alpha in [0.9, 0.6, 0.3, 0.0]:
                self.root.attributes('-alpha', alpha)
                self.root.update()
                time.sleep(0.02)
    
    def close_app(self):
        """Close both windows and exit"""
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
    app = CustomerSupportOverlay()
    app.run()

if __name__ == "__main__":
    main()