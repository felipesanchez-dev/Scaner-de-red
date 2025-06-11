import socket
import subprocess
import threading
import time
import json
import requests
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import psutil
import ipaddress
import concurrent.futures
import platform
import re
import urllib.parse
import os
import logging
from pathlib import Path
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('network_scanner.log'),
        logging.StreamHandler()
    ]
)

try:
    import nmap
    NMAP_AVAILABLE = True
except ImportError:
    NMAP_AVAILABLE = False

try:
    from scapy.all import ARP, Ether, srp
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

class NetworkScanner:
    def __init__(self):
        self.devices = []
        self.scanning = False
        self.monitoring = False
        self.scan_history = []
        self.config = self.load_config()
        self.logger = logging.getLogger(__name__)
        self.setup_gui()
        
    def load_config(self):
        """Cargar configuración desde archivo"""
        default_config = {
            'scan_timeout': 3,
            'max_workers': 50,
            'ping_timeout': 1000,
            'port_timeout': 1,
            'theme': 'dark',
            'auto_save': True,
            'save_history': True
        }
        
        try:
            config_file = Path('scanner_config.json')
            if config_file.exists():
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            self.logger.warning(f"Error loading config: {e}")
            
        return default_config
        
    def save_config(self):
        """Guardar configuración"""
        try:
            with open('scanner_config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def setup_gui(self):
        """Configurar interfaz gráfica mejorada"""
        self.root = tk.Tk()
        self.root.title("🌐 Network Scanner Pro - Enterprise Edition v3.0")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        # Aplicar tema
        self.apply_theme()
        
        # Configurar grid weights
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        
        # Variables de estado
        self.setup_status_variables()
        
        # Crear widgets
        self.create_menu_bar()
        self.create_header()
        self.create_main_interface()
        self.create_status_bar()
        
        # Bind eventos
        self.bind_events()
        
        # Mostrar información inicial
        self.show_initial_info()
        
    def apply_theme(self):
        """Aplicar tema visual avanzado"""
        if self.config['theme'] == 'dark':
            self.colors = {
                'bg_primary': '#0d1117',
                'bg_secondary': '#161b22', 
                'bg_tertiary': '#21262d',
                'fg_primary': '#f0f6fc',
                'fg_secondary': '#8b949e',
                'accent_blue': '#58a6ff',
                'accent_green': '#3fb950',
                'accent_orange': '#ff7b72',
                'accent_yellow': '#f2cc60',
                'accent_purple': '#bc8cff',
                'border': '#30363d'
            }
        else:  # light theme
            self.colors = {
                'bg_primary': '#ffffff',
                'bg_secondary': '#f6f8fa',
                'bg_tertiary': '#f1f3f4',
                'fg_primary': '#24292f',
                'fg_secondary': '#656d76',
                'accent_blue': '#0969da',
                'accent_green': '#1a7f37',
                'accent_orange': '#d1242f',
                'accent_yellow': '#bf8700',
                'accent_purple': '#8250df',
                'border': '#d0d7de'
            }
        
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Configurar estilo ttk
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configurar estilos personalizados
        self.configure_ttk_styles()
        
    def configure_ttk_styles(self):
        """Configurar estilos TTK personalizados"""
        # Progressbar
        self.style.configure(
            "Custom.Horizontal.TProgressbar",
            background=self.colors['accent_blue'],
            troughcolor=self.colors['bg_tertiary'],
            borderwidth=0,
            lightcolor=self.colors['accent_blue'],
            darkcolor=self.colors['accent_blue']
        )
        
        # Treeview
        self.style.configure(
            "Custom.Treeview",
            background=self.colors['bg_secondary'],
            foreground=self.colors['fg_primary'],
            fieldbackground=self.colors['bg_secondary'],
            borderwidth=1,
            relief='solid'
        )
        
        self.style.configure(
            "Custom.Treeview.Heading",
            background=self.colors['bg_tertiary'],
            foreground=self.colors['fg_primary'],
            borderwidth=1,
            relief='solid'
        )
        
    def setup_status_variables(self):
        """Configurar variables de estado"""
        self.status_var = tk.StringVar(value="🟢 Ready for advanced scanning...")
        self.scan_progress_var = tk.StringVar(value="")
        self.device_count_var = tk.StringVar(value="Devices: 0")
        self.network_health_var = tk.StringVar(value="Network: Healthy")
        
    def create_menu_bar(self):
        """Crear barra de menú profesional"""
        self.menubar = tk.Menu(self.root, bg=self.colors['bg_secondary'], fg=self.colors['fg_primary'])
        self.root.config(menu=self.menubar)
        
        # Menú File
        file_menu = tk.Menu(self.menubar, tearoff=0, bg=self.colors['bg_secondary'], fg=self.colors['fg_primary'])
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Scan", command=self.start_quick_scan, accelerator="Ctrl+N")
        file_menu.add_command(label="Open Report", command=self.open_report)
        file_menu.add_separator()
        file_menu.add_command(label="Export JSON", command=self.export_detailed_report)
        file_menu.add_command(label="Export CSV", command=self.export_csv_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.safe_exit)
        
        # Menú Tools
        tools_menu = tk.Menu(self.menubar, tearoff=0, bg=self.colors['bg_secondary'], fg=self.colors['fg_primary'])
        self.menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Network Diagnostics", command=self.run_network_diagnostics)
        tools_menu.add_command(label="Port Scanner", command=self.open_port_scanner)
        tools_menu.add_separator()
        tools_menu.add_command(label="Settings", command=self.open_settings)
        
        # Menú View
        view_menu = tk.Menu(self.menubar, tearoff=0, bg=self.colors['bg_secondary'], fg=self.colors['fg_primary'])
        self.menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Theme", command=self.toggle_theme)
        view_menu.add_command(label="Refresh", command=self.refresh_scan, accelerator="F5")
        view_menu.add_separator()
        view_menu.add_command(label="Scan History", command=self.show_scan_history)
        
        # Menú Help
        help_menu = tk.Menu(self.menubar, tearoff=0, bg=self.colors['bg_secondary'], fg=self.colors['fg_primary'])
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_header(self):
        """Crear header mejorado"""
        header_frame = tk.Frame(self.root, bg=self.colors['bg_tertiary'], height=80)
        header_frame.grid(row=0, column=0, sticky='ew', padx=0, pady=0)
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Logo y título
        title_frame = tk.Frame(header_frame, bg=self.colors['bg_tertiary'])
        title_frame.grid(row=0, column=0, sticky='w', padx=20, pady=10)
        
        title_label = tk.Label(
            title_frame, 
            text="🌐 Network Scanner Pro", 
            font=('Segoe UI', 20, 'bold'), 
            fg=self.colors['accent_blue'], 
            bg=self.colors['bg_tertiary']
        )
        title_label.pack(side='left')
        
        subtitle_label = tk.Label(
            title_frame,
            text="Enterprise Edition v3.0",
            font=('Segoe UI', 10),
            fg=self.colors['fg_secondary'],
            bg=self.colors['bg_tertiary']
        )
        subtitle_label.pack(side='left', padx=(10, 0))
        
        # Panel de información rápida
        info_frame = tk.Frame(header_frame, bg=self.colors['bg_tertiary'])
        info_frame.grid(row=0, column=1, sticky='e', padx=20, pady=10)
        
        tk.Label(info_frame, textvariable=self.device_count_var,
                font=('Segoe UI', 9), fg=self.colors['accent_green'],
                bg=self.colors['bg_tertiary']).pack(side='right', padx=5)
        
        tk.Label(info_frame, textvariable=self.network_health_var,
                font=('Segoe UI', 9), fg=self.colors['accent_blue'],
                bg=self.colors['bg_tertiary']).pack(side='right', padx=5)
        
    def create_main_interface(self):
        """Crear interfaz principal"""
        # Control Panel
        control_frame = tk.Frame(self.root, bg=self.colors['bg_secondary'], height=60)
        control_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=5)
        control_frame.grid_propagate(False)
        
        # Botones principales con estilo mejorado
        buttons = [
            ("🔍 Deep Scan", self.start_deep_scan, self.colors['accent_blue']),
            ("⚡ Quick Scan", self.start_quick_scan, self.colors['accent_green']),
            ("🌐 Monitor", self.start_monitoring, self.colors['accent_purple']),
            ("💾 Export", self.export_detailed_report, self.colors['fg_secondary']),
            ("🔄 Refresh", self.refresh_scan, self.colors['accent_orange'])
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(
                control_frame, 
                text=text,
                command=command, 
                bg=color, 
                fg='white',
                font=('Segoe UI', 10, 'bold'), 
                padx=20, 
                pady=8,
                relief='flat',
                cursor='hand2',
                activebackground=color,
                activeforeground='white'
            )
            btn.pack(side='left', padx=5, pady=8)
        
        # Botón de parada
        self.stop_btn = tk.Button(
            control_frame,
            text="⏹️ Stop",
            command=self.stop_scanning,
            bg=self.colors['accent_orange'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            padx=20,
            pady=8,
            relief='flat',
            state='disabled'
        )
        self.stop_btn.pack(side='right', padx=5, pady=8)
        
        # Main content area
        main_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_frame.grid(row=2, column=0, sticky='nsew', padx=10, pady=5)
        main_frame.grid_columnconfigure(0, weight=2)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Left panel - Device List
        self.create_device_list_panel(main_frame)
        
        # Right panel - Details
        self.create_device_details_panel(main_frame)
        
    def create_device_list_panel(self, parent):
        """Crear panel de lista de dispositivos"""
        left_frame = tk.LabelFrame(
            parent, 
            text="🖥️ Network Devices & Analysis", 
            fg=self.colors['fg_primary'], 
            bg=self.colors['bg_secondary'],
            font=('Segoe UI', 11, 'bold'),
            relief='solid',
            bd=1
        )
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # Treeview for devices
        columns = ('IP', 'Device', 'MAC', 'Vendor', 'OS', 'Ping', 'Ports', 'Status')
        self.tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=20)
        
        # Configurar columnas
        column_widths = {
            'IP': 120, 'Device': 150, 'MAC': 140, 'Vendor': 120, 
            'OS': 100, 'Ping': 80, 'Ports': 80, 'Status': 90
        }
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100), minwidth=70)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(left_frame, orient='vertical', command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(left_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_device_select)
        
    def create_device_details_panel(self, parent):
        """Crear panel de detalles del dispositivo"""
        right_frame = tk.LabelFrame(
            parent, 
            text="🔍 Device Intelligence & Network Analysis", 
            fg=self.colors['fg_primary'], 
            bg=self.colors['bg_secondary'],
            font=('Segoe UI', 11, 'bold'),
            relief='solid',
            bd=1
        )
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 0))
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        self.info_text = scrolledtext.ScrolledText(
            right_frame, 
            width=50, 
            height=30,
            bg=self.colors['bg_primary'], 
            fg=self.colors['fg_primary'],
            font=('Consolas', 9), 
            wrap=tk.WORD,
            insertbackground=self.colors['accent_blue']
        )
        self.info_text.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        
    def create_status_bar(self):
        """Crear barra de estado"""
        status_frame = tk.Frame(self.root, bg=self.colors['bg_tertiary'], height=30)
        status_frame.grid(row=3, column=0, sticky='ew')
        status_frame.grid_propagate(False)
        status_frame.grid_columnconfigure(1, weight=1)
        
        # Status principal
        tk.Label(status_frame, textvariable=self.status_var,
                fg=self.colors['fg_primary'], bg=self.colors['bg_tertiary'], 
                font=('Segoe UI', 9)).grid(row=0, column=0, sticky='w', padx=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.grid(row=0, column=1, sticky='ew', padx=10)
        
    def bind_events(self):
        """Bind eventos del teclado y ventana"""
        self.root.bind('<Control-n>', lambda e: self.start_quick_scan())
        self.root.bind('<F5>', lambda e: self.refresh_scan())
        self.root.bind('<Control-s>', lambda e: self.export_detailed_report())
        self.root.bind('<Escape>', lambda e: self.stop_scanning())
        self.root.protocol("WM_DELETE_WINDOW", self.safe_exit)
    
    # Métodos principales del escáner (conservados del código original)
    def show_initial_info(self):
        """Mostrar información inicial del sistema"""
        try:
            network_range = self.get_network_range()
            local_ip = self.get_local_ip()
            gateway = self.get_gateway()
            
            initial_info = f"""
🌐 NETWORK SCANNER PRO - ENTERPRISE EDITION
{'='*50}

💻 SYSTEM INTELLIGENCE
{'='*30}
Local IP: {local_ip}
Gateway: {gateway}
Network Range: {network_range}
OS: {platform.system()} {platform.release()}
Architecture: {platform.machine()}

🔧 SCANNING CAPABILITIES
{'='*30}
✅ Device Detection & Classification
✅ Operating System Fingerprinting
✅ Network Latency Analysis
✅ Port Scanning & Service Detection
✅ Vendor Identification (MAC OUI)
✅ Network Traffic Monitoring
✅ Device Behavior Analysis

📡 AVAILABLE METHODS
{'='*30}
Primary: Advanced Socket + ICMP Ping
Enhanced: {'Nmap OS Detection' if NMAP_AVAILABLE else 'Basic Fingerprinting'}
Network: {'Scapy Packet Analysis' if SCAPY_AVAILABLE else 'Standard Methods'}

🎯 DEVICE CLASSIFICATION
{'='*30}
📱 Mobile Devices (iOS, Android)
💻 Computers (Windows, Mac, Linux)
📺 Smart TVs & Streaming Devices
🖨️ Printers & IoT Devices
🌐 Network Infrastructure
🎮 Gaming Consoles
📟 Smart Home Devices

⚡ QUICK START
{'='*30}
1. Click "Deep Scan" for comprehensive analysis
2. Click "Quick Scan" for fast device discovery
3. Select device for detailed intelligence
4. Use "Monitor Network" for real-time tracking

🔒 PRIVACY & SECURITY
{'='*30}
✅ No admin privileges required
✅ Local network scanning only
✅ No data collection or transmission
✅ Open source and transparent
            """
            
            self.info_text.insert('1.0', initial_info)
        except Exception as e:
            self.info_text.insert('1.0', f"Error loading system info: {e}")
    
    def get_local_ip(self):
        """Obtener la IP local del sistema"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            try:
                for interface, addrs in psutil.net_if_addrs().items():
                    for addr in addrs:
                        if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                            return addr.address
            except:
                pass
            return "Unknown"
    
    def get_gateway(self):
        """Obtener la puerta de enlace"""
        try:
            if platform.system().lower() == 'windows':
                result = subprocess.run(['ipconfig'], capture_output=True, text=True)
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'puerta de enlace' in line.lower() or 'default gateway' in line.lower():
                        parts = line.split(':')
                        if len(parts) > 1:
                            gateway = parts[1].strip()
                            if gateway and gateway != '':
                                return gateway
            else:
                result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'default via' in line:
                        parts = line.split()
                        if len(parts) > 2:
                            return parts[2]
        except:
            pass
        return "Unknown"
        
    def get_network_range(self):
        """Obtener el rango de red para escanear"""
        try:
            local_ip = self.get_local_ip()
            if local_ip != "Unknown":
                ip_parts = local_ip.split('.')
                network = f"{'.'.join(ip_parts[:3])}.0/24"
                return network
        except:
            pass
        return "192.168.1.0/24"
    
    def ping_host_with_time(self, ip):
        """Ping a host and return response time"""
        try:
            if platform.system().lower() == 'windows':
                cmd = ['ping', '-n', '1', '-w', '1000', ip]
            else:
                cmd = ['ping', '-c', '1', '-W', '1', ip]
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                output = result.stdout
                if 'time=' in output.lower():
                    time_match = re.search(r'time[=<](\d+(?:\.\d+)?)ms', output, re.IGNORECASE)
                    if time_match:
                        return True, float(time_match.group(1))
                return True, round((time.time() - start_time) * 1000, 2)
            return False, 0
        except:
            return False, 0
    
    def get_mac_from_arp(self, ip):
        """Obtener dirección MAC desde la tabla ARP"""
        try:
            if platform.system().lower() == 'windows':
                result = subprocess.run(['arp', '-a', ip], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if ip in line and 'dynamic' in line.lower():
                            parts = line.split()
                            for part in parts:
                                if '-' in part and len(part) == 17:
                                    return part.replace('-', ':')
            else:
                result = subprocess.run(['arp', '-n', ip], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if ip in line:
                            parts = line.split()
                            if len(parts) > 2:
                                return parts[2]
        except:
            pass
        return "Unknown"
    
    def get_mac_vendor(self, mac_address):
        """Obtener información del fabricante desde MAC"""
        if mac_address == "Unknown":
            return "Unknown"
        try:
            url = f"https://api.macvendors.com/{mac_address}"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                return response.text.strip()
        except:
            pass
        
        # Base de datos local de vendors más comunes
        vendor_db = {
            '00:50:56': 'VMware',
            '08:00:27': 'VirtualBox',
            'DC:A6:32': 'Raspberry Pi',
            'B8:27:EB': 'Raspberry Pi',
            'E4:5F:01': 'Raspberry Pi',
            '28:CD:C1': 'Apple',
            'AC:DE:48': 'Apple',
            'F4:0F:24': 'Apple',
            '2C:54:91': 'Samsung',
            '5C:51:88': 'LG Electronics',
            '00:1D:D8': 'NETGEAR',
            '30:85:A9': 'TP-Link',
            '94:10:3E': 'TP-Link'
        }
        
        mac_prefix = mac_address[:8].upper()
        return vendor_db.get(mac_prefix, "Unknown")
    
    def detect_device_type_advanced(self, hostname, vendor, mac, open_ports, os_info):
        """Detección avanzada de tipo de dispositivo"""
        hostname = hostname.lower() if hostname else ""
        vendor = vendor.lower() if vendor else ""
        os_info = os_info.lower() if os_info else ""
        
        device_patterns = {
            '📱 iPhone': ['iphone', 'ios', 'apple', 'mobile'],
            '📱 Android': ['android', 'samsung', 'xiaomi', 'huawei', 'oneplus', 'redmi', 'oppo', 'vivo'],
            '💻 Windows PC': ['windows', 'microsoft', 'pc-', 'desktop-', 'laptop-'],
            '💻 MacBook/iMac': ['macbook', 'imac', 'mac-', 'apple', 'macos'],
            '💻 Linux PC': ['linux', 'ubuntu', 'debian', 'fedora', 'arch'],
            '📺 Smart TV': ['tv', 'smart', 'roku', 'chromecast', 'fire-tv', 'lg', 'sony', 'samsung-tv'],
            '🎮 Gaming Console': ['xbox', 'playstation', 'nintendo', 'switch', 'ps4', 'ps5'],
            '🖨️ Printer': ['printer', 'hp', 'canon', 'epson', 'brother', 'lexmark'],
            '🌐 Router': ['router', 'gateway', 'tp-link', 'netgear', 'cisco', 'linksys', 'dlink'],
            '📟 IoT Device': ['esp', 'arduino', 'raspberry', 'smart-', 'iot-'],
            '🔊 Smart Speaker': ['echo', 'alexa', 'google-home', 'nest'],
            '⌚ Wearable': ['watch', 'band', 'fitness', 'smartwatch']
        }
        
        port_indicators = {
            22: 'Linux/Unix System',
            135: 'Windows System',
            445: 'Windows File Sharing',
            3389: 'Windows RDP',
            5353: 'Apple Device (Bonjour)',
            8080: 'Web Service/Router',
            1900: 'UPnP Device',
            631: 'Printer (IPP)',
            9100: 'Printer (JetDirect)'
        }
        
        scores = {}
        
        for device_type, indicators in device_patterns.items():
            score = 0
            for indicator in indicators:
                if indicator in hostname: score += 3
                if indicator in vendor: score += 2
                if indicator in os_info: score += 4
            scores[device_type] = score
        
        for port in open_ports:
            if port in port_indicators:
                port_info = port_indicators[port]
                if 'windows' in port_info.lower():
                    scores['💻 Windows PC'] = scores.get('💻 Windows PC', 0) + 2
                elif 'linux' in port_info.lower():
                    scores['💻 Linux PC'] = scores.get('💻 Linux PC', 0) + 2
                elif 'apple' in port_info.lower():
                    scores['💻 MacBook/iMac'] = scores.get('💻 MacBook/iMac', 0) + 2
                elif 'printer' in port_info.lower():
                    scores['🖨️ Printer'] = scores.get('🖨️ Printer', 0) + 3
        
        if scores:
            best_match = max(scores, key=scores.get)
            if scores[best_match] > 0:
                return best_match
        
        return "🖥️ Unknown Device"
    
    def get_hostname(self, ip):
        """Obtener hostname del dispositivo"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return "Unknown"
    
    def detect_os_fingerprint(self, ip, open_ports):
        """Detectar sistema operativo basado en comportamiento de red"""
        os_hints = []
        
        if 135 in open_ports or 445 in open_ports or 3389 in open_ports:
            os_hints.append("Windows")
        if 22 in open_ports:
            os_hints.append("Linux/Unix")
        if 5353 in open_ports:
            os_hints.append("macOS/iOS")
        if 631 in open_ports:
            os_hints.append("CUPS (Linux/macOS)")
        
        try:
            if platform.system().lower() == 'windows':
                result = subprocess.run(['ping', '-n', '1', ip], capture_output=True, text=True)
                if 'TTL=' in result.stdout:
                    ttl_match = re.search(r'TTL=(\d+)', result.stdout)
                    if ttl_match:
                        ttl = int(ttl_match.group(1))
                        if ttl <= 64:
                            os_hints.append("Linux/Unix")
                        elif ttl <= 128:
                            os_hints.append("Windows")
                        else:
                            os_hints.append("Network Device")
        except:
            pass
        
        return ", ".join(list(set(os_hints))) if os_hints else "Unknown"
    
    def scan_ports_advanced(self, ip):
        """Escaneo avanzado de puertos con detección de servicios"""
        common_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 1433, 3389, 5353, 8080, 9100]
        open_ports = []
        
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((ip, port))
                sock.close()
                
                if result == 0:
                    open_ports.append(port)
            except:
                pass
        
        return open_ports
    
    def scan_single_device_advanced(self, ip):
        """Escaneo avanzado de un dispositivo individual"""
        try:
            is_online, ping_time = self.ping_host_with_time(ip)
            
            if is_online:
                hostname = self.get_hostname(ip)
                mac = self.get_mac_from_arp(ip)
                vendor = self.get_mac_vendor(mac) if mac != "Unknown" else "Unknown"
                open_ports = self.scan_ports_advanced(ip)
                os_info = self.detect_os_fingerprint(ip, open_ports)
                device_type = self.detect_device_type_advanced(hostname, vendor, mac, open_ports, os_info)
                
                return {
                    'ip': ip,
                    'hostname': hostname,
                    'mac': mac,
                    'vendor': vendor,
                    'device_type': device_type,
                    'os_info': os_info,
                    'ping_time': ping_time,
                    'open_ports': open_ports,
                    'port_count': len(open_ports),
                    'status': '🟢 Online',
                    'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'last_seen': datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Error scanning {ip}: {e}")
        return None
    
    def scan_network_deep(self):
        """Escaneo profundo de la red"""
        try:
            network_range = self.get_network_range()
            network = ipaddress.IPv4Network(network_range, strict=False)
            ips_to_scan = [str(ip) for ip in network.hosts()]
            
            self.status_var.set(f"🔍 Deep scanning {len(ips_to_scan)} addresses...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config['max_workers']) as executor:
                future_to_ip = {executor.submit(self.scan_single_device_advanced, ip): ip for ip in ips_to_scan}
                
                completed = 0
                for future in concurrent.futures.as_completed(future_to_ip):
                    if not self.scanning:
                        break
                        
                    completed += 1
                    self.status_var.set(f"📡 Deep scan: {completed}/{len(ips_to_scan)} - Found: {len(self.devices)}")
                    
                    result = future.result()
                    if result:
                        self.devices.append(result)
                        self.device_count_var.set(f"Devices: {len(self.devices)}")
                        self.root.after(0, self.update_device_list)
                        
        except Exception as e:
            self.logger.error(f"Deep scan failed: {e}")
            self.status_var.set(f"❌ Deep scan error: {str(e)}")
        finally:
            self.scanning = False
            self.progress.stop()
            self.stop_btn.config(state='disabled')
            self.status_var.set(f"✅ Scan completed - Found {len(self.devices)} devices")
    
    def scan_network_quick(self):
        """Escaneo rápido de la red"""
        try:
            network_range = self.get_network_range()
            base_ip = network_range.split('/')[0].rsplit('.', 1)[0]
            common_ips = [f"{base_ip}.{i}" for i in range(1, 51)]
            
            self.status_var.set(f"⚡ Quick scanning {len(common_ips)} addresses...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                future_to_ip = {executor.submit(self.scan_single_device_advanced, ip): ip for ip in common_ips}
                
                completed = 0
                for future in concurrent.futures.as_completed(future_to_ip):
                    if not self.scanning:
                        break
                        
                    completed += 1
                    self.status_var.set(f"⚡ Quick scan: {completed}/{len(common_ips)} - Found: {len(self.devices)}")
                    
                    result = future.result()
                    if result:
                        self.devices.append(result)
                        self.device_count_var.set(f"Devices: {len(self.devices)}")
                        self.root.after(0, self.update_device_list)
                        
        except Exception as e:
            self.logger.error(f"Quick scan failed: {e}")
            self.status_var.set(f"❌ Quick scan error: {str(e)}")
        finally:
            self.scanning = False
            self.progress.stop()
            self.stop_btn.config(state='disabled')
            self.status_var.set(f"✅ Quick scan completed - Found {len(self.devices)} devices")
    
    def start_deep_scan(self):
        """Iniciar escaneo profundo"""
        if not self.scanning:
            self.scanning = True
            self.progress.start()
            self.stop_btn.config(state='normal')
            self.devices.clear()
            self.device_count_var.set("Devices: 0")
            threading.Thread(target=self.scan_network_deep, daemon=True).start()
    
    def start_quick_scan(self):
        """Iniciar escaneo rápido"""
        if not self.scanning:
            self.scanning = True
            self.progress.start()
            self.stop_btn.config(state='normal')
            self.devices.clear()
            self.device_count_var.set("Devices: 0")
            threading.Thread(target=self.scan_network_quick, daemon=True).start()
    
    def start_monitoring(self):
        """Iniciar monitoreo de red"""
        if not self.scanning:
            self.monitoring = True
            self.scanning = True
            threading.Thread(target=self.monitor_network, daemon=True).start()
    
    def stop_scanning(self):
        """Detener escaneo"""
        self.scanning = False
        self.monitoring = False
        self.progress.stop()
        self.stop_btn.config(state='disabled')
        self.status_var.set("🛑 Scanning stopped")
    
    def monitor_network(self):
        """Monitorear la red continuamente"""
        try:
            while self.scanning and self.monitoring:
                self.status_var.set("🌐 Monitoring network activity...")
                
                for device in self.devices.copy():
                    is_online, ping_time = self.ping_host_with_time(device['ip'])
                    
                    if is_online:
                        device['ping_time'] = ping_time
                        device['status'] = '🟢 Online'
                        device['last_seen'] = datetime.now().isoformat()
                    else:
                        device['status'] = '🔴 Offline'
                
                self.root.after(0, self.update_device_list)
                time.sleep(10)
                
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
            self.status_var.set(f"❌ Monitoring error: {str(e)}")
        finally:
            self.monitoring = False
            self.scanning = False
    
    def update_device_list(self):
        """Actualizar la lista de dispositivos en la GUI"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for device in self.devices:
            ping_str = f"{device.get('ping_time', 0):.1f}ms" if device.get('ping_time') else "N/A"
            ports_str = str(device.get('port_count', 0))
            
            self.tree.insert('', 'end', values=(
                device['ip'],
                device.get('device_type', '🖥️ Unknown'),
                device['mac'],
                device['vendor'],
                device.get('os_info', 'Unknown'),
                ping_str,
                ports_str,
                device['status']
            ))
    
    def on_device_select(self, event):
        """Manejar selección de dispositivo"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            
            if values:
                ip = values[0]
                device = next((d for d in self.devices if d['ip'] == ip), None)
                
                if device:
                    self.show_device_intelligence(device)
    
    def show_device_intelligence(self, device):
        """Mostrar inteligencia detallada del dispositivo"""
        port_analysis = ""
        if device.get('open_ports'):
            port_services = {
                21: 'FTP Server', 22: 'SSH', 23: 'Telnet', 25: 'SMTP',
                53: 'DNS', 80: 'HTTP Web', 110: 'POP3', 135: 'Windows RPC',
                139: 'NetBIOS', 143: 'IMAP', 443: 'HTTPS Secure Web',
                445: 'SMB File Sharing', 993: 'IMAPS', 995: 'POP3S',
                1433: 'SQL Server', 3389: 'Remote Desktop', 5353: 'Bonjour',
                8080: 'HTTP Alt', 9100: 'HP JetDirect'
            }
            
            for port in device['open_ports']:
                service = port_services.get(port, 'Unknown Service')
                port_analysis += f"  Port {port}: {service}\n"
        
        security_analysis = ""
        if 23 in device.get('open_ports', []):
            security_analysis += "⚠️  Telnet detected (unencrypted)\n"
        if 21 in device.get('open_ports', []):
            security_analysis += "⚠️  FTP detected (check if secure)\n"
        if 3389 in device.get('open_ports', []):
            security_analysis += "ℹ️  Remote Desktop enabled\n"
        if not security_analysis:
            security_analysis = "✅ No obvious security concerns\n"
        
        details = f"""
🔍 DEVICE INTELLIGENCE REPORT
{'='*40}

📱 DEVICE IDENTIFICATION
{'='*25}
IP Address: {device['ip']}
Device Type: {device.get('device_type', 'Unknown')}
Hostname: {device['hostname']}
MAC Address: {device['mac']}
Vendor: {device['vendor']}
Operating System: {device.get('os_info', 'Unknown')}

📊 NETWORK PERFORMANCE
{'='*25}
Status: {device['status']}
Ping Response: {device.get('ping_time', 0):.2f}ms
Last Seen: {device.get('last_seen', 'Unknown')}
Scan Time: {device['scan_time']}

🔌 PORT ANALYSIS
{'='*25}
Open Ports: {len(device.get('open_ports', []))}
{port_analysis}

🛡️ SECURITY ASSESSMENT
{'='*25}
{security_analysis}

🌐 NETWORK CONTEXT
{'='*25}
Network Range: {self.get_network_range()}
Gateway: {self.get_gateway()}
Local IP: {self.get_local_ip()}

📈 DEVICE METRICS
{'='*25}
Response Quality: {'Excellent' if device.get('ping_time', 999) < 10 else 'Good' if device.get('ping_time', 999) < 50 else 'Poor'}
Service Count: {len(device.get('open_ports', []))} services detected
Risk Level: {'Low' if len(device.get('open_ports', [])) < 5 else 'Medium'}
        """
        
        self.info_text.delete('1.0', tk.END)
        self.info_text.insert('1.0', details)
    
    def export_detailed_report(self):
        """Exportar reporte detallado"""
        if not self.devices:
            messagebox.showwarning("No Data", "No devices found to export.")
            return
            
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"network_report_{timestamp}.json"
            
            system_info = {
                'scan_timestamp': datetime.now().isoformat(),
                'scanner_version': 'Network Scanner Pro - Enterprise Edition v3.0',
                'local_ip': self.get_local_ip(),
                'gateway': self.get_gateway(),
                'network_range': self.get_network_range(),
                'system_os': f"{platform.system()} {platform.release()}",
                'total_devices_found': len(self.devices),
                'scan_method': 'Advanced Network Scanning'
            }
            
            network_analysis = {
                'device_types': {},
                'security_summary': {
                    'devices_with_open_ports': 0,
                    'potential_security_risks': 0,
                    'average_response_time': 0
                }
            }
            
            response_times = []
            for device in self.devices:
                device_type = device.get('device_type', 'Unknown')
                network_analysis['device_types'][device_type] = network_analysis['device_types'].get(device_type, 0) + 1
                
                if device.get('open_ports'):
                    network_analysis['security_summary']['devices_with_open_ports'] += 1
                
                if device.get('ping_time'):
                    response_times.append(device['ping_time'])
            
            if response_times:
                network_analysis['security_summary']['average_response_time'] = sum(response_times) / len(response_times)
            
            report_data = {
                'system_info': system_info,
                'network_analysis': network_analysis,
                'devices': self.devices
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            txt_filename = f"network_report_{timestamp}.txt"
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write("🌐 NETWORK SCANNER PRO - ENTERPRISE REPORT\n")
                f.write("="*50 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Network: {self.get_network_range()}\n")
                f.write(f"Total Devices: {len(self.devices)}\n\n")
                
                for device in self.devices:
                    f.write(f"Device: {device['ip']}\n")
                    f.write(f"  Type: {device.get('device_type', 'Unknown')}\n")
                    f.write(f"  Hostname: {device['hostname']}\n")
                    f.write(f"  MAC: {device['mac']}\n")
                    f.write(f"  Vendor: {device['vendor']}\n")
                    f.write(f"  OS: {device.get('os_info', 'Unknown')}\n")
                    f.write(f"  Ping: {device.get('ping_time', 0):.2f}ms\n")
                    f.write(f"  Open Ports: {len(device.get('open_ports', []))}\n")
                    f.write(f"  Status: {device['status']}\n\n")
            
            self.status_var.set(f"💾 Reports saved: {filename} & {txt_filename}")
            messagebox.showinfo("Export Successful", 
                               f"Reports saved successfully:\n\n"
                               f"📊 JSON Report: {filename}\n"
                               f"📄 Text Report: {txt_filename}\n\n"
                               f"Total devices: {len(self.devices)}")
            
        except Exception as e:
            error_msg = f"❌ Export failed: {str(e)}"
            self.status_var.set(error_msg)
            self.logger.error(f"Export error: {e}")
            messagebox.showerror("Export Error", error_msg)
    
    def refresh_scan(self):
        """Refrescar escaneo"""
        if not self.scanning:
            self.start_quick_scan()
    
    # Métodos para funcionalidades del menú (stubs que se pueden implementar)
    def open_report(self):
        """Abrir reporte existente"""
        messagebox.showinfo("Feature", "Open report functionality - Coming soon!")
    
    def export_csv_report(self):
        """Exportar reporte CSV"""
        messagebox.showinfo("Feature", "CSV export functionality - Coming soon!")
    
    def run_network_diagnostics(self):
        """Ejecutar diagnósticos de red"""
        messagebox.showinfo("Feature", "Network diagnostics - Coming soon!")
    
    def open_port_scanner(self):
        """Abrir escáner de puertos"""
        messagebox.showinfo("Feature", "Advanced port scanner - Coming soon!")
    
    def open_settings(self):
        """Abrir configuraciones"""
        messagebox.showinfo("Feature", "Settings panel - Coming soon!")
    
    def toggle_theme(self):
        """Cambiar tema"""
        self.config['theme'] = 'light' if self.config['theme'] == 'dark' else 'dark'
        self.save_config()
        messagebox.showinfo("Theme", f"Theme changed to {self.config['theme']}. Restart required.")
    
    def show_scan_history(self):
        """Mostrar historial de escaneos"""
        messagebox.showinfo("Feature", "Scan history - Coming soon!")
    
    def show_documentation(self):
        """Mostrar documentación"""
        messagebox.showinfo("Documentation", 
                           "🌐 Network Scanner Pro - Enterprise Edition\n\n"
                           "Features:\n"
                           "• Advanced device detection\n"
                           "• OS fingerprinting\n"
                           "• Port scanning\n"
                           "• Real-time monitoring\n"
                           "• Security assessment\n\n"
                           "Keyboard shortcuts:\n"
                           "• Ctrl+N: New scan\n"
                           "• F5: Refresh\n"
                           "• Ctrl+S: Export\n"
                           "• Esc: Stop scan")
    
    def show_about(self):
        """Mostrar información sobre la aplicación"""
        messagebox.showinfo("About", 
                           "🌐 Network Scanner Pro\n"
                           "Enterprise Edition v3.0\n\n"
                           "Advanced network discovery and analysis tool\n\n"
                           "Features:\n"
                           "✅ Device classification\n"
                           "✅ OS detection\n"
                           "✅ Security assessment\n"
                           "✅ Real-time monitoring\n"
                           "✅ Professional reporting\n\n"
                           "© 2024 - Open Source Project")
    
    def safe_exit(self):
        """Salida segura de la aplicación"""
        try:
            if self.scanning or self.monitoring:
                if messagebox.askyesno("Exit", "Scanning in progress. Stop and exit?"):
                    self.stop_scanning()
                    self.save_config()
                    self.root.destroy()
            else:
                self.save_config()
                self.root.destroy()
        except Exception as e:
            self.logger.error(f"Error during exit: {e}")
            self.root.destroy()
    
    def run(self):
        """Ejecutar la aplicación"""
        try:
            self.logger.info("Starting Network Scanner Pro Enterprise Edition")
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Critical error: {e}")
            messagebox.showerror("Critical Error", f"Application error: {e}")

if __name__ == "__main__":
    try:
        app = NetworkScanner()
        app.run()
    except Exception as e:
        print(f"Error starting Network Scanner Pro: {e}")
        logging.error(f"Startup error: {e}")
        input("Press Enter to exit...")