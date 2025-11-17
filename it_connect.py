"""
Customer Support Overlay - Improved Version
Key improvements:
- Better error handling and logging
- Cleaner separation of concerns
- More efficient resource management
- Improved configuration management
- Better threading safety
"""

# Force DPI Awareness for crisp rendering
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
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
import logging
from ctypes import windll, Structure, c_ulong, byref
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import sys
import webbrowser
import getpass
from typing import Optional, Tuple
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class POINT(Structure):
    _fields_ = [("x", c_ulong), ("y", c_ulong)]


@dataclass
class Config:
    """Configuration constants"""
    # Window settings
    MAIN_WINDOW_WIDTH: int = 350
    MAIN_WINDOW_HEIGHT: int = 535
    MAIN_WINDOW_OFFSET: int = 20
    
    # Icon settings
    BASE_ICON_SIZE: int = 50
    MIN_ICON_SIZE: int = 48
    MAX_ICON_SIZE: int = 80
    ICON_MARGIN: int = 25
    ICON_TOP_OFFSET: int = 20
    
    # Colors
    BG_DARK: str = '#2c2c2c'
    BG_DARKER: str = '#1e1e1e'
    BG_SEPARATOR: str = '#555555'
    FG_LIGHT: str = '#ffffff'
    FG_GRAY: str = '#cccccc'
    FG_LINK: str = '#1e90ff'
    FG_SUCCESS: str = '#00ff00'
    FG_ERROR: str = '#ff4444'
    TRANSPARENT_BG: str = '#000001'
    ICON_WHITE: str = '#ffffff'
    ICON_BLUE: str = '#0078d7'
    
    # Timing
    UPDATE_INTERVAL: int = 5000  # ms
    HIDE_DELAY: int = 500  # ms
    CHECK_INTERVAL: int = 100  # ms
    FADE_STEP_DELAY: float = 0.02  # seconds
    
    # Contact info
    SUPPORT_EMAIL: str = "dbshelp@debswana.bw"
    INTERNAL_NUMBER: str = "18222"
    EXTERNAL_NUMBER: str = "+267 364 8222"
    SERVICE_HOURS: str = "0700 - 1645hrs"
    STANDBY_HOURS: str = "1645 - 0700hrs"
    SELF_SERVICE_URL: str = "https://imservicedesk.debswana.bw/sd/SolutionsHome.sd"
    
    # Standby contacts
    STANDBY_CONTACTS: dict = None
    
    def __post_init__(self):
        self.STANDBY_CONTACTS = {
            'DJW': '71382489',
            'DOR': '71313074',
            'DCC': '71320195'
        }


class SystemInfo:
    """Handle system information retrieval"""
    
    @staticmethod
    def get_device_name() -> str:
        try:
            return socket.gethostname()
        except Exception as e:
            logger.error(f"Failed to get device name: {e}")
            return "Unknown"
    
    @staticmethod
    def get_username() -> str:
        try:
            return getpass.getuser()
        except Exception as e:
            logger.error(f"Failed to get username: {e}")
            return "Unknown"
    
    @staticmethod
    def get_domain() -> str:
        try:
            # Try environment variable first
            domain = os.environ.get('USERDOMAIN', '')
            if domain:
                return domain
            
            # Alternative method
            result = subprocess.run(
                ['net', 'config', 'workstation'],
                capture_output=True,
                text=True,
                shell=True,
                timeout=5
            )
            
            for line in result.stdout.split('\n'):
                if 'Workstation domain' in line:
                    return line.split(':')[-1].strip()
            
            return "Unknown Domain"
        except Exception as e:
            logger.error(f"Failed to get domain: {e}")
            return "Unknown Domain"
    
    @staticmethod
    def get_network_name() -> str:
        """Get the actual WiFi network name (SSID) or connection type"""
        try:
            # Check for WiFi connection
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'interfaces'],
                capture_output=True,
                text=True,
                shell=True,
                timeout=5
            )
            
            ssid_pattern = r'SSID\s*:\s*(.+)'
            matches = re.findall(ssid_pattern, result.stdout)
            
            if matches:
                ssid = matches[0].strip()
                if ssid and not ssid.isspace():
                    return ssid
            
            # Check for wired connection
            result = subprocess.run(
                ['ipconfig'],
                capture_output=True,
                text=True,
                shell=True,
                timeout=5
            )
            
            ip_pattern = r'IPv4 Address[\. ]+: ([\d\.]+)'
            ip_matches = re.findall(ip_pattern, result.stdout)
            
            for ip in ip_matches:
                if not ip.startswith('169.254.') and not ip.startswith('127.'):
                    return "Ethernet (Wired)"
            
            return "Not Connected"
        except Exception as e:
            logger.error(f"Failed to get network name: {e}")
            return "Unknown"


class IconCreator:
    """Handle icon creation with proper scaling"""
    
    def __init__(self, size: int, config: Config):
        self.size = size
        self.config = config
    
    def create_text_icon(self) -> Optional[ImageTk.PhotoImage]:
        """Create a text-based 'IT' icon with white rounded box"""
        try:
            image = Image.new('RGBA', (self.size, self.size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Calculate proportional sizes
            box_margin = max(4, int(self.size * 0.08))
            corner_radius = max(8, int(self.size * 0.13))
            font_size = max(16, int(self.size * 0.35))
            
            # Draw rounded rectangle background
            self._draw_rounded_rectangle(draw, box_margin, corner_radius)
            
            # Draw text
            self._draw_text(draw, "IT", font_size)
            
            return ImageTk.PhotoImage(image)
        except Exception as e:
            logger.error(f"Error creating text icon: {e}")
            return None
    
    def _draw_rounded_rectangle(self, draw: ImageDraw.Draw, margin: int, radius: int):
        """Draw a rounded rectangle"""
        box_coords = [margin, margin, self.size - margin, self.size - margin]
        
        # Draw corner circles
        positions = [
            (box_coords[0], box_coords[1]),  # Top-left
            (box_coords[2] - radius * 2, box_coords[1]),  # Top-right
            (box_coords[0], box_coords[3] - radius * 2),  # Bottom-left
            (box_coords[2] - radius * 2, box_coords[3] - radius * 2)  # Bottom-right
        ]
        
        for x, y in positions:
            draw.ellipse([x, y, x + radius * 2, y + radius * 2], 
                        fill=self.config.ICON_WHITE)
        
        # Fill rectangle areas
        draw.rectangle([box_coords[0], box_coords[1] + radius,
                       box_coords[2], box_coords[3] - radius],
                      fill=self.config.ICON_WHITE)
        draw.rectangle([box_coords[0] + radius, box_coords[1],
                       box_coords[2] - radius, box_coords[3]],
                      fill=self.config.ICON_WHITE)
    
    def _draw_text(self, draw: ImageDraw.Draw, text: str, font_size: int):
        """Draw centered text on the icon"""
        font = self._get_font(font_size)
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = (self.size - text_width) // 2
        text_y = (self.size - text_height) // 2 - 2
        
        draw.text((text_x, text_y), text, fill=self.config.ICON_BLUE, font=font)
    
    @staticmethod
    def _get_font(size: int) -> ImageFont.FreeTypeFont:
        """Get the best available font"""
        font_options = ["arialbd.ttf", "arial.ttf", "segoeuib.ttf"]
        
        for font_name in font_options:
            try:
                return ImageFont.truetype(font_name, size)
            except:
                continue
        
        return ImageFont.load_default()


class CustomerSupportOverlay:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.system_info = SystemInfo()
        
        # Window state
        self.is_visible = False
        self.hide_timer = None
        
        # Create windows
        self.root = tk.Tk()
        self.setup_main_window()
        
        self.icon_root = tk.Toplevel()
        self.setup_icon_window()
        
        self.create_widgets()
        self.update_info()
    
    def get_icon_size(self) -> int:
        """Calculate appropriate icon size based on DPI"""
        try:
            hdc = windll.user32.GetDC(0)
            dpi = windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
            windll.user32.ReleaseDC(0, hdc)
            
            scale_factor = dpi / 96.0
            scaled_size = int(self.config.BASE_ICON_SIZE * scale_factor)
            
            return max(self.config.MIN_ICON_SIZE, 
                      min(scaled_size, self.config.MAX_ICON_SIZE))
        except Exception as e:
            logger.error(f"Error detecting icon size: {e}")
            return self.config.BASE_ICON_SIZE
    
    def setup_main_window(self):
        """Setup the main information overlay window"""
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 0.0)
        self.root.attributes('-topmost', True)
        
        screen_width = self.root.winfo_screenwidth()
        x_pos = screen_width - self.config.MAIN_WINDOW_WIDTH - self.config.MAIN_WINDOW_OFFSET
        
        geometry = (f"{self.config.MAIN_WINDOW_WIDTH}x{self.config.MAIN_WINDOW_HEIGHT}"
                   f"+{x_pos}+{self.config.MAIN_WINDOW_OFFSET}")
        self.root.geometry(geometry)
        self.root.configure(bg=self.config.BG_DARK)
    
    def setup_icon_window(self):
        """Setup the icon window"""
        self.icon_root.overrideredirect(True)
        self.icon_root.attributes('-topmost', False)
        self.icon_root.attributes('-alpha', 1.0)
        
        self.icon_size = self.get_icon_size()
        
        screen_width = self.icon_root.winfo_screenwidth()
        x_pos = screen_width - self.icon_size - self.config.ICON_MARGIN
        
        geometry = (f"{self.icon_size}x{self.icon_size}"
                   f"+{x_pos}+{self.config.ICON_TOP_OFFSET}")
        self.icon_root.geometry(geometry)
        self.icon_root.configure(bg=self.config.TRANSPARENT_BG)
        self.icon_root.wm_attributes("-transparentcolor", self.config.TRANSPARENT_BG)
        
        self.make_desktop_window()
    
    def make_desktop_window(self):
        """Make the window behave like a desktop icon"""
        try:
            hwnd = windll.user32.FindWindowW(None, self.icon_root.title())
            
            GWL_EXSTYLE = -20
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_NOACTIVATE = 0x08000000
            
            current_style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            new_style = current_style | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
            windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
        except Exception as e:
            logger.error(f"Window style error: {e}")
    
    def create_widgets(self):
        """Create widgets for both windows"""
        self.create_main_widgets()
        self.create_icon_widgets()
    
    def create_main_widgets(self):
        """Widgets for the main overlay window"""
        main_frame = tk.Frame(self.root, bg=self.config.BG_DARK)
        main_frame.pack(fill='both', expand=True)
        
        # Title bar
        self._create_title_bar(main_frame)
        
        # Content
        content = tk.Frame(main_frame, bg=self.config.BG_DARK)
        content.pack(fill='both', expand=True, padx=10, pady=10)
        
        # System info section
        self._create_system_info_section(content)
        
        # Separator
        self._create_separator(content)
        
        # Service desk section
        self._create_service_desk_section(content)
        
        # Separator
        self._create_separator(content)
        
        # Standby section
        self._create_standby_section(content)
        
        # Bind mouse events
        self.root.bind("<Enter>", self.on_enter_main_window)
        self.root.bind("<Leave>", self.on_leave_main_window)
    
    def _create_title_bar(self, parent):
        """Create title bar"""
        title_frame = tk.Frame(parent, bg=self.config.BG_DARKER, height=40)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        title = tk.Label(
            title_frame,
            text="Need IT Support?",
            bg=self.config.BG_DARKER,
            fg=self.config.FG_LIGHT,
            font=('Microsoft Sans Serif', 10, 'bold')
        )
        title.pack(expand=True, pady=10)
    
    def _create_info_row(self, parent, label_text: str, is_value_bold: bool = True):
        """Create a labeled info row and return the value label"""
        frame = tk.Frame(parent, bg=self.config.BG_DARK)
        frame.pack(fill='x', pady=2)
        
        label = tk.Label(
            frame,
            text=label_text,
            bg=self.config.BG_DARK,
            fg=self.config.FG_GRAY,
            font=('Microsoft Sans Serif', 9),
            anchor='w',
            width=15
        )
        label.pack(side='left')
        
        font_weight = 'bold' if is_value_bold else 'normal'
        value_label = tk.Label(
            frame,
            text="",
            bg=self.config.BG_DARK,
            fg=self.config.FG_LIGHT,
            font=('Microsoft Sans Serif', 9, font_weight),
            anchor='w'
        )
        value_label.pack(side='left', fill='x', expand=True)
        
        return value_label
    
    def _create_system_info_section(self, parent):
        """Create system information section"""
        sys_info_frame = tk.Frame(parent, bg=self.config.BG_DARK)
        sys_info_frame.pack(fill='x', pady=(0, 5))
        
        self.device_value = self._create_info_row(sys_info_frame, "Device Name:")
        self.user_value = self._create_info_row(sys_info_frame, "Username:")
        self.domain_value = self._create_info_row(sys_info_frame, "Domain:")
        self.network_value = self._create_info_row(sys_info_frame, "Network:")
    
    def _create_separator(self, parent):
        """Create a separator line"""
        separator = tk.Frame(parent, bg=self.config.BG_SEPARATOR, height=1)
        separator.pack(fill='x', pady=8)
    
    def _create_service_desk_section(self, parent):
        """Create service desk section"""
        service_frame = tk.Frame(parent, bg=self.config.BG_DARK)
        service_frame.pack(fill='x', pady=(0, 10))
        
        # Title
        title = tk.Label(
            service_frame,
            text="Service Desk",
            bg=self.config.BG_DARK,
            fg=self.config.FG_LIGHT,
            font=('Microsoft Sans Serif', 10, 'bold'),
            anchor='w'
        )
        title.pack(anchor='w', pady=(0, 5))
        
        # Info rows
        hours_label = self._create_info_row(service_frame, "Operating Hours:")
        hours_label.config(text=self.config.SERVICE_HOURS)
        
        # Self service link
        self._create_link_row(service_frame, "Self Service Articles:", 
                             "Click Me", self.config.SELF_SERVICE_URL)
        
        email_label = self._create_info_row(service_frame, "Email:")
        email_label.config(text=self.config.SUPPORT_EMAIL)
        
        internal_label = self._create_info_row(service_frame, "Internal Number:")
        internal_label.config(text=self.config.INTERNAL_NUMBER)
        
        external_label = self._create_info_row(service_frame, "External Number:")
        external_label.config(text=self.config.EXTERNAL_NUMBER)
    
    def _create_link_row(self, parent, label_text: str, link_text: str, url: str):
        """Create a row with a clickable link"""
        frame = tk.Frame(parent, bg=self.config.BG_DARK)
        frame.pack(fill='x', pady=2)
        
        label = tk.Label(
            frame,
            text=label_text,
            bg=self.config.BG_DARK,
            fg=self.config.FG_GRAY,
            font=('Microsoft Sans Serif', 9),
            anchor='w',
            width=15
        )
        label.pack(side='left')
        
        link = tk.Label(
            frame,
            text=link_text,
            bg=self.config.BG_DARK,
            fg=self.config.FG_LINK,
            font=('Microsoft Sans Serif', 9, 'underline'),
            cursor="hand2"
        )
        link.pack(side='left')
        link.bind("<Button-1>", lambda e: webbrowser.open(url))
    
    def _create_standby_section(self, parent):
        """Create standby section"""
        standby_frame = tk.Frame(parent, bg=self.config.BG_DARK)
        standby_frame.pack(fill='x', pady=(0, 10))
        
        # Title
        title = tk.Label(
            standby_frame,
            text="Standby",
            bg=self.config.BG_DARK,
            fg=self.config.FG_LIGHT,
            font=('Microsoft Sans Serif', 10, 'bold'),
            anchor='w'
        )
        title.pack(anchor='w', pady=(0, 3))
        
        # Hours
        hours_label = self._create_info_row(standby_frame, "Operating Hours:")
        hours_label.config(text=self.config.STANDBY_HOURS)
        
        # Contacts
        for name, number in self.config.STANDBY_CONTACTS.items():
            contact_label = self._create_info_row(standby_frame, f"{name}:")
            contact_label.config(text=number)
    
    def create_icon_widgets(self):
        """Create icon widget"""
        try:
            icon_creator = IconCreator(self.icon_size, self.config)
            self.icon_image = icon_creator.create_text_icon()
            
            if self.icon_image:
                icon_container = tk.Frame(
                    self.icon_root,
                    bg=self.config.TRANSPARENT_BG,
                    borderwidth=0,
                    highlightthickness=0
                )
                icon_container.pack(fill='both', expand=True)
                
                self.icon_label = tk.Label(
                    icon_container,
                    image=self.icon_image,
                    bg=self.config.TRANSPARENT_BG,
                    borderwidth=0,
                    highlightthickness=0,
                    cursor="hand2"
                )
                self.icon_label.pack(expand=True, fill='both')
                self.icon_label.bind("<Button-1>", self.toggle_overlay)
                
                self.icon_root.update_idletasks()
                logger.info(f"Icon created successfully! Size: {self.icon_size}x{self.icon_size}")
            else:
                self._create_fallback_icon()
        except Exception as e:
            logger.error(f"Error creating icon: {e}")
            self._create_fallback_icon()
    
    def _create_fallback_icon(self):
        """Create a fallback text icon using tkinter canvas"""
        logger.info("Using fallback icon")
        
        icon_container = tk.Frame(
            self.icon_root,
            bg=self.config.TRANSPARENT_BG,
            borderwidth=0,
            highlightthickness=0
        )
        icon_container.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(
            icon_container,
            bg=self.config.TRANSPARENT_BG,
            width=self.icon_size,
            height=self.icon_size,
            highlightthickness=0,
            borderwidth=0,
            cursor="hand2"
        )
        canvas.pack(expand=True, fill='both')
        canvas.bind("<Button-1>", self.toggle_overlay)
        
        # Draw rounded rectangle
        margin = max(4, int(self.icon_size * 0.08))
        radius = max(8, int(self.icon_size * 0.13))
        font_size = max(16, int(self.icon_size * 0.35))
        
        # Main rectangles
        canvas.create_rectangle(
            margin + radius, margin,
            self.icon_size - margin - radius, self.icon_size - margin,
            fill=self.config.ICON_WHITE, outline=''
        )
        canvas.create_rectangle(
            margin, margin + radius,
            self.icon_size - margin, self.icon_size - margin - radius,
            fill=self.config.ICON_WHITE, outline=''
        )
        
        # Corner circles
        corners = [
            (margin, margin),
            (self.icon_size - margin - radius * 2, margin),
            (margin, self.icon_size - margin - radius * 2),
            (self.icon_size - margin - radius * 2, self.icon_size - margin - radius * 2)
        ]
        
        for x, y in corners:
            canvas.create_oval(
                x, y, x + radius * 2, y + radius * 2,
                fill=self.config.ICON_WHITE, outline=''
            )
        
        # Text
        canvas.create_text(
            self.icon_size // 2, self.icon_size // 2,
            text="IT",
            fill=self.config.ICON_BLUE,
            font=('Arial', font_size, 'bold'),
            justify='center'
        )
        
        self.icon_root.update_idletasks()
    
    def update_info(self):
        """Update the system information"""
        try:
            self.device_value.config(text=self.system_info.get_device_name())
            self.user_value.config(text=self.system_info.get_username())
            self.domain_value.config(text=self.system_info.get_domain())
            
            network_name = self.system_info.get_network_name()
            
            # Update color based on status
            if "Not Connected" in network_name or "Unknown" in network_name:
                color = self.config.FG_ERROR
            else:
                color = self.config.FG_SUCCESS
            
            self.network_value.config(text=network_name, fg=color)
        except Exception as e:
            logger.error(f"Error updating info: {e}")
        finally:
            self.root.after(self.config.UPDATE_INTERVAL, self.update_info)
    
    def is_mouse_over_window(self, window) -> bool:
        """Check if mouse is over a specific window"""
        try:
            pt = POINT()
            windll.user32.GetCursorPos(byref(pt))
            
            x = window.winfo_x()
            y = window.winfo_y()
            width = window.winfo_width()
            height = window.winfo_height()
            
            return (x <= pt.x <= x + width and y <= pt.y <= y + height)
        except Exception as e:
            logger.error(f"Error checking mouse position: {e}")
            return False
    
    def on_enter_main_window(self, event=None):
        """Mouse entered the main window"""
        if self.hide_timer:
            self.root.after_cancel(self.hide_timer)
            self.hide_timer = None
    
    def on_leave_main_window(self, event=None):
        """Mouse left the main window"""
        if self.is_visible:
            self.hide_timer = self.root.after(
                self.config.HIDE_DELAY,
                self.check_mouse_position
            )
    
    def check_mouse_position(self):
        """Check if mouse is still away and hide if needed"""
        over_main = self.is_mouse_over_window(self.root)
        over_icon = self.is_mouse_over_window(self.icon_root)
        
        if not over_main and not over_icon:
            self.hide_overlay()
        else:
            self.hide_timer = self.root.after(
                self.config.CHECK_INTERVAL,
                self.check_mouse_position
            )
    
    def toggle_overlay(self, event=None):
        """Toggle the information panel"""
        if self.is_visible:
            self.hide_overlay()
        else:
            self.show_overlay()
    
    def show_overlay(self):
        """Show the main overlay with smooth animation"""
        if not self.is_visible:
            self.is_visible = True
            self.root.attributes('-topmost', True)
            
            if self.hide_timer:
                self.root.after_cancel(self.hide_timer)
                self.hide_timer = None
            
            # Smooth fade in
            for alpha in [0.0, 0.3, 0.6, 0.9]:
                self.root.attributes('-alpha', alpha)
                self.root.update()
                time.sleep(self.config.FADE_STEP_DELAY)
    
    def hide_overlay(self):
        """Hide the main overlay with smooth animation"""
        if self.is_visible:
            self.is_visible = False
            
            if self.hide_timer:
                self.root.after_cancel(self.hide_timer)
                self.hide_timer = None
            
            # Smooth fade out
            for alpha in [0.9, 0.6, 0.3, 0.0]:
                self.root.attributes('-alpha', alpha)
                self.root.update()
                time.sleep(self.config.FADE_STEP_DELAY)
    
    def run(self):
        """Start the application"""
        try:
            logger.info("Starting Customer Support Overlay")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.hide_timer:
                self.root.after_cancel(self.hide_timer)
            self.root.destroy()
            self.icon_root.destroy()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


def main():
    try:
        app = CustomerSupportOverlay()
        app.run()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()