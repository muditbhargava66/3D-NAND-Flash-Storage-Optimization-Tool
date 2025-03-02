# src/ui/settings_dialog.py

import os

import yaml
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.utils.config import load_config
from src.utils.logger import get_logger


class SettingsDialog(QDialog):
    """Enhanced settings dialog for configuring the 3D NAND Optimization Tool"""

    # Signal emitted when settings are changed
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.config = None
        self.init_ui()
        self.load_config()

    def init_ui(self):
        """Initialize the dialog user interface"""
        self.setWindowTitle("Settings")
        self.setMinimumSize(750, 600)
        self.setModal(True)

        main_layout = QVBoxLayout(self)

        # Create tab widget for different settings categories
        self.tab_widget = QTabWidget()

        # Create tabs
        self.nand_tab = self.create_nand_tab()
        self.optimization_tab = self.create_optimization_tab()
        self.firmware_tab = self.create_firmware_tab()
        self.ui_tab = self.create_ui_tab()
        self.logging_tab = self.create_logging_tab()

        # Add tabs to the widget
        self.tab_widget.addTab(self.nand_tab, "NAND Configuration")
        self.tab_widget.addTab(self.optimization_tab, "Optimization")
        self.tab_widget.addTab(self.firmware_tab, "Firmware")
        self.tab_widget.addTab(self.ui_tab, "User Interface")
        self.tab_widget.addTab(self.logging_tab, "Logging")

        main_layout.addWidget(self.tab_widget)

        # Create buttons
        buttons_layout = QHBoxLayout()

        self.save_button = QPushButton("Save to File")
        self.save_button.clicked.connect(self.save_config_to_file)

        self.load_button = QPushButton("Load from File")
        self.load_button.clicked.connect(self.load_config_from_file)

        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_to_defaults)

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_settings)

        self.ok_button = QPushButton("OK")
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.accept_settings)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.load_button)
        buttons_layout.addWidget(self.reset_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.apply_button)
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)

        main_layout.addLayout(buttons_layout)

    def create_nand_tab(self):
        """Create the NAND configuration tab"""
        tab = QWidget()

        # Use a scroll area to handle many settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # NAND hardware configuration group
        hw_group = QGroupBox("NAND Hardware Configuration")
        hw_layout = QFormLayout()

        # Create input fields
        self.page_size = QSpinBox()
        self.page_size.setRange(512, 32768)
        self.page_size.setSingleStep(512)
        self.page_size.setSpecialValueText("Default")

        self.block_size = QSpinBox()
        self.block_size.setRange(16, 512)
        self.block_size.setSingleStep(16)
        self.block_size.setSpecialValueText("Default")

        self.num_blocks = QSpinBox()
        self.num_blocks.setRange(1, 100000)
        self.num_blocks.setSingleStep(128)
        self.num_blocks.setSpecialValueText("Default")

        self.oob_size = QSpinBox()
        self.oob_size.setRange(0, 1024)
        self.oob_size.setSingleStep(16)
        self.oob_size.setSpecialValueText("Default")

        self.num_planes = QSpinBox()
        self.num_planes.setRange(1, 8)
        self.num_planes.setSpecialValueText("Default")

        # Add fields to layout
        hw_layout.addRow("Page Size (bytes):", self.page_size)
        hw_layout.addRow("Pages per Block:", self.block_size)
        hw_layout.addRow("Number of Blocks:", self.num_blocks)
        hw_layout.addRow("OOB Size (bytes):", self.oob_size)
        hw_layout.addRow("Number of Planes:", self.num_planes)

        hw_group.setLayout(hw_layout)
        scroll_layout.addWidget(hw_group)

        # Timing configuration group
        timing_group = QGroupBox("Timing Configuration")
        timing_layout = QFormLayout()

        # Create timing fields
        self.read_latency = QDoubleSpinBox()
        self.read_latency.setRange(0.001, 100.0)
        self.read_latency.setDecimals(3)
        self.read_latency.setSingleStep(0.1)
        self.read_latency.setSuffix(" ms")

        self.write_latency = QDoubleSpinBox()
        self.write_latency.setRange(0.01, 1000.0)
        self.write_latency.setDecimals(2)
        self.write_latency.setSingleStep(1.0)
        self.write_latency.setSuffix(" ms")

        self.erase_latency = QDoubleSpinBox()
        self.erase_latency.setRange(0.1, 10000.0)
        self.erase_latency.setDecimals(1)
        self.erase_latency.setSingleStep(10.0)
        self.erase_latency.setSuffix(" ms")

        # Add timing fields to layout
        timing_layout.addRow("Read Latency:", self.read_latency)
        timing_layout.addRow("Write Latency:", self.write_latency)
        timing_layout.addRow("Erase Latency:", self.erase_latency)

        timing_group.setLayout(timing_layout)
        scroll_layout.addWidget(timing_group)

        # Simulation configuration group
        sim_group = QGroupBox("Simulation Configuration")
        sim_layout = QFormLayout()

        # Create simulation fields
        self.error_rate = QDoubleSpinBox()
        self.error_rate.setRange(0.0, 1.0)
        self.error_rate.setDecimals(6)
        self.error_rate.setSingleStep(0.0001)

        self.initial_bad_blocks = QDoubleSpinBox()
        self.initial_bad_blocks.setRange(0.0, 1.0)
        self.initial_bad_blocks.setDecimals(4)
        self.initial_bad_blocks.setSingleStep(0.001)
        self.initial_bad_blocks.setSuffix(" ratio")

        self.simulation_mode = QCheckBox("Enable Simulation Mode")

        # Add simulation fields to layout
        sim_layout.addRow("Error Rate:", self.error_rate)
        sim_layout.addRow("Initial Bad Block Ratio:", self.initial_bad_blocks)
        sim_layout.addRow(self.simulation_mode)

        sim_group.setLayout(sim_layout)
        scroll_layout.addWidget(sim_group)

        # Add some spacing and stretch at the bottom
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)

        # Main tab layout
        layout = QVBoxLayout(tab)
        layout.addWidget(scroll)

        return tab

    def create_optimization_tab(self):
        """Create the optimization configuration tab"""
        tab = QWidget()

        # Use a scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Error Correction configuration
        ecc_group = QGroupBox("Error Correction")
        ecc_layout = QFormLayout()

        # Create ECC fields
        self.ecc_algorithm = QComboBox()
        self.ecc_algorithm.addItems(["BCH", "LDPC", "None"])
        self.ecc_algorithm.currentTextChanged.connect(self.update_ecc_options)

        # BCH parameters
        self.bch_params_group = QGroupBox("BCH Parameters")
        bch_layout = QFormLayout()

        self.bch_m = QSpinBox()
        self.bch_m.setRange(3, 16)
        self.bch_m.setValue(8)
        self.bch_m.valueChanged.connect(self.update_bch_t_max)

        self.bch_t = QSpinBox()
        self.bch_t.setRange(1, 127)
        self.bch_t.setValue(4)

        bch_layout.addRow("m (Galois Field Size):", self.bch_m)
        bch_layout.addRow("t (Error Correction Capability):", self.bch_t)

        self.bch_params_group.setLayout(bch_layout)

        # LDPC parameters
        self.ldpc_params_group = QGroupBox("LDPC Parameters")
        ldpc_layout = QFormLayout()

        self.ldpc_n = QSpinBox()
        self.ldpc_n.setRange(16, 32768)
        self.ldpc_n.setValue(1024)
        self.ldpc_n.setSingleStep(16)

        self.ldpc_dv = QSpinBox()
        self.ldpc_dv.setRange(2, 20)
        self.ldpc_dv.setValue(3)

        self.ldpc_dc = QSpinBox()
        self.ldpc_dc.setRange(2, 100)
        self.ldpc_dc.setValue(6)

        self.ldpc_systematic = QCheckBox("Systematic Code")
        self.ldpc_systematic.setChecked(True)

        ldpc_layout.addRow("n (Codeword Length):", self.ldpc_n)
        ldpc_layout.addRow("d_v (Variable Node Degree):", self.ldpc_dv)
        ldpc_layout.addRow("d_c (Check Node Degree):", self.ldpc_dc)
        ldpc_layout.addRow(self.ldpc_systematic)

        self.ldpc_params_group.setLayout(ldpc_layout)

        # Add to ECC group
        ecc_layout.addRow("Algorithm:", self.ecc_algorithm)
        ecc_group.setLayout(ecc_layout)

        scroll_layout.addWidget(ecc_group)
        scroll_layout.addWidget(self.bch_params_group)
        scroll_layout.addWidget(self.ldpc_params_group)

        # Data Compression configuration
        compression_group = QGroupBox("Data Compression")
        compression_layout = QFormLayout()

        # Create compression fields
        self.compression_enabled = QCheckBox("Enable Compression")
        self.compression_enabled.setChecked(True)
        self.compression_enabled.stateChanged.connect(self.update_compression_options)

        self.compression_algorithm = QComboBox()
        self.compression_algorithm.addItems(["LZ4", "Zstandard"])

        self.compression_level = QSlider(Qt.Horizontal)
        self.compression_level.setRange(1, 9)
        self.compression_level.setValue(3)
        self.compression_level.setTickPosition(QSlider.TicksBelow)
        self.compression_level.setTickInterval(1)

        self.compression_level_label = QLabel("3")
        self.compression_level.valueChanged.connect(lambda v: self.compression_level_label.setText(str(v)))

        # Add to compression group
        compression_layout.addRow(self.compression_enabled)
        compression_layout.addRow("Algorithm:", self.compression_algorithm)

        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Level:"))
        level_layout.addWidget(self.compression_level)
        level_layout.addWidget(self.compression_level_label)

        compression_layout.addRow(level_layout)
        compression_group.setLayout(compression_layout)

        scroll_layout.addWidget(compression_group)

        # Caching configuration
        cache_group = QGroupBox("Caching")
        cache_layout = QFormLayout()

        # Create caching fields
        self.cache_enabled = QCheckBox("Enable Caching")
        self.cache_enabled.setChecked(True)
        self.cache_enabled.stateChanged.connect(self.update_cache_options)

        self.cache_capacity = QSpinBox()
        self.cache_capacity.setRange(1, 10000)
        self.cache_capacity.setValue(1024)
        self.cache_capacity.setSuffix(" entries")

        self.cache_policy = QComboBox()
        self.cache_policy.addItems(["LRU", "LFU", "FIFO", "TTL"])

        self.cache_ttl = QDoubleSpinBox()
        self.cache_ttl.setRange(0.1, 3600.0)
        self.cache_ttl.setValue(60.0)
        self.cache_ttl.setSuffix(" seconds")

        # Add to cache group
        cache_layout.addRow(self.cache_enabled)
        cache_layout.addRow("Capacity:", self.cache_capacity)
        cache_layout.addRow("Eviction Policy:", self.cache_policy)
        cache_layout.addRow("Time-To-Live:", self.cache_ttl)

        cache_group.setLayout(cache_layout)

        scroll_layout.addWidget(cache_group)

        # Wear Leveling configuration
        wl_group = QGroupBox("Wear Leveling")
        wl_layout = QFormLayout()

        # Create wear leveling fields
        self.wl_threshold = QSpinBox()
        self.wl_threshold.setRange(10, 10000)
        self.wl_threshold.setValue(1000)

        self.wl_method = QComboBox()
        self.wl_method.addItems(["Static", "Dynamic", "Hybrid"])

        # Add to wear leveling group
        wl_layout.addRow("Threshold:", self.wl_threshold)
        wl_layout.addRow("Method:", self.wl_method)

        wl_group.setLayout(wl_layout)

        scroll_layout.addWidget(wl_group)

        # Parallelism configuration
        parallelism_group = QGroupBox("Parallelism")
        parallelism_layout = QFormLayout()

        # Create parallelism fields
        self.max_workers = QSpinBox()
        self.max_workers.setRange(1, 32)
        self.max_workers.setValue(4)

        # Add to parallelism group
        parallelism_layout.addRow("Max Worker Threads:", self.max_workers)

        parallelism_group.setLayout(parallelism_layout)

        scroll_layout.addWidget(parallelism_group)

        # Add some spacing and stretch at the bottom
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)

        # Main tab layout
        layout = QVBoxLayout(tab)
        layout.addWidget(scroll)

        return tab

    def create_firmware_tab(self):
        """Create the firmware configuration tab"""
        tab = QWidget()

        layout = QVBoxLayout(tab)

        # Firmware configuration group
        fw_group = QGroupBox("Firmware Configuration")
        fw_layout = QFormLayout()

        # Create firmware fields
        self.fw_version = QLineEdit()
        self.fw_version.setPlaceholderText("e.g., 1.0.0")

        self.read_retry = QCheckBox("Enable Read Retry")
        self.read_retry.setChecked(True)

        self.max_retries = QSpinBox()
        self.max_retries.setRange(1, 10)
        self.max_retries.setValue(3)

        self.data_scrambling = QCheckBox("Enable Data Scrambling")
        self.data_scrambling.setChecked(True)

        self.scrambling_seed = QLineEdit()
        self.scrambling_seed.setPlaceholderText("Hex value (e.g., 0xA5A5A5A5)")

        # Add to firmware group
        fw_layout.addRow("Firmware Version:", self.fw_version)
        fw_layout.addRow(self.read_retry)
        fw_layout.addRow("Max Read Retries:", self.max_retries)
        fw_layout.addRow(self.data_scrambling)
        fw_layout.addRow("Scrambling Seed:", self.scrambling_seed)

        fw_group.setLayout(fw_layout)
        layout.addWidget(fw_group)

        # Template configuration group
        template_group = QGroupBox("Firmware Template")
        template_layout = QVBoxLayout()

        self.template_path = QLineEdit()
        self.template_path.setReadOnly(True)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_template)

        template_path_layout = QHBoxLayout()
        template_path_layout.addWidget(QLabel("Template Path:"))
        template_path_layout.addWidget(self.template_path)
        template_path_layout.addWidget(browse_button)

        template_layout.addLayout(template_path_layout)

        template_group.setLayout(template_layout)
        layout.addWidget(template_group)

        # Add stretch to push groups to the top
        layout.addStretch()

        return tab

    def create_ui_tab(self):
        """Create the user interface configuration tab"""
        tab = QWidget()

        layout = QVBoxLayout(tab)

        # UI configuration group
        ui_group = QGroupBox("UI Configuration")
        ui_layout = QFormLayout()

        # Create UI fields
        self.ui_theme = QComboBox()
        self.ui_theme.addItems(["Light", "Dark", "System"])

        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setValue(12)
        self.font_size.setSuffix(" pt")

        self.update_interval = QSpinBox()
        self.update_interval.setRange(1, 60)
        self.update_interval.setValue(5)
        self.update_interval.setSuffix(" seconds")

        # Window size
        window_size_layout = QHBoxLayout()

        self.window_width = QSpinBox()
        self.window_width.setRange(800, 3840)
        self.window_width.setValue(1200)

        self.window_height = QSpinBox()
        self.window_height.setRange(600, 2160)
        self.window_height.setValue(800)

        window_size_layout.addWidget(self.window_width)
        window_size_layout.addWidget(QLabel("×"))
        window_size_layout.addWidget(self.window_height)

        # Add to UI group
        ui_layout.addRow("Theme:", self.ui_theme)
        ui_layout.addRow("Font Size:", self.font_size)
        ui_layout.addRow("Update Interval:", self.update_interval)
        ui_layout.addRow("Window Size:", window_size_layout)

        ui_group.setLayout(ui_layout)
        layout.addWidget(ui_group)

        # Chart configuration group
        chart_group = QGroupBox("Chart Configuration")
        chart_layout = QFormLayout()

        # Create chart fields
        self.chart_antialiasing = QCheckBox("Enable Anti-aliasing")
        self.chart_antialiasing.setChecked(True)

        self.chart_animations = QCheckBox("Enable Animations")
        self.chart_animations.setChecked(True)

        # Add to chart group
        chart_layout.addRow(self.chart_antialiasing)
        chart_layout.addRow(self.chart_animations)

        chart_group.setLayout(chart_layout)
        layout.addWidget(chart_group)

        # Add stretch to push groups to the top
        layout.addStretch()

        return tab

    def create_logging_tab(self):
        """Create the logging configuration tab"""
        tab = QWidget()

        layout = QVBoxLayout(tab)

        # Logging configuration group
        logging_group = QGroupBox("Logging Configuration")
        logging_layout = QFormLayout()

        # Create logging fields
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level.setCurrentIndex(1)  # INFO by default

        self.log_file = QLineEdit()
        self.log_file.setReadOnly(True)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_log_file)

        log_file_layout = QHBoxLayout()
        log_file_layout.addWidget(self.log_file)
        log_file_layout.addWidget(browse_button)

        self.max_log_size = QSpinBox()
        self.max_log_size.setRange(1, 1000)
        self.max_log_size.setValue(10)
        self.max_log_size.setSuffix(" MB")

        self.backup_count = QSpinBox()
        self.backup_count.setRange(0, 100)
        self.backup_count.setValue(5)

        # Console logging
        self.console_logging = QCheckBox("Enable Console Logging")
        self.console_logging.setChecked(True)

        # Add to logging group
        logging_layout.addRow("Log Level:", self.log_level)
        logging_layout.addRow("Log File:", log_file_layout)
        logging_layout.addRow("Max Log Size:", self.max_log_size)
        logging_layout.addRow("Backup Count:", self.backup_count)
        logging_layout.addRow(self.console_logging)

        logging_group.setLayout(logging_layout)
        layout.addWidget(logging_group)

        # Add stretch to push groups to the top
        layout.addStretch()

        return tab

    def update_ecc_options(self, algorithm):
        """Update ECC options based on selected algorithm"""
        algorithm = algorithm.lower()

        # Show/hide parameter groups based on algorithm
        self.bch_params_group.setVisible(algorithm == "bch")
        self.ldpc_params_group.setVisible(algorithm == "ldpc")

        # Adjust dialog size
        self.adjustSize()

    def update_bch_t_max(self, m_value):
        """Update the maximum value for t based on m"""
        # Maximum t is 2^(m-1) - 1
        max_t = (1 << (m_value - 1)) - 1
        self.bch_t.setMaximum(max_t)

        # If current value is too high, adjust it
        if self.bch_t.value() > max_t:
            self.bch_t.setValue(max_t)

    def update_compression_options(self, state):
        """Update compression options based on checkbox state"""
        enabled = state == Qt.Checked
        self.compression_algorithm.setEnabled(enabled)
        self.compression_level.setEnabled(enabled)
        self.compression_level_label.setEnabled(enabled)

    def update_cache_options(self, state):
        """Update cache options based on checkbox state"""
        enabled = state == Qt.Checked
        self.cache_capacity.setEnabled(enabled)
        self.cache_policy.setEnabled(enabled)
        self.cache_ttl.setEnabled(enabled)

    def browse_template(self):
        """Open a file dialog to select a template file"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select Template File", "", "YAML Files (*.yaml);;All Files (*)")

        if file_path:
            self.template_path.setText(file_path)

    def browse_log_file(self):
        """Open a file dialog to select a log file"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "Select Log File", "", "Log Files (*.log);;All Files (*)")

        if file_path:
            self.log_file.setText(file_path)

    def load_config(self):
        """Load configuration from default file"""
        try:
            # Try to load config from fixed location
            config_path = os.path.join("resources", "config", "config.yaml")
            if os.path.exists(config_path):
                self.config = load_config(config_path)
                self.apply_config_to_ui()
                return

            # If that fails, try an alternate location
            config_path = "config.yaml"
            if os.path.exists(config_path):
                self.config = load_config(config_path)
                self.apply_config_to_ui()
                return

        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")

        # If no config found or error occurred, load defaults
        self.load_default_config()

    def load_default_config(self):
        """Load default configuration"""
        # Create a default configuration
        self.config = {
            "nand_config": {"page_size": 4096, "block_size": 256, "num_blocks": 1024, "oob_size": 64, "num_planes": 1},
            "optimization_config": {
                "error_correction": {
                    "algorithm": "bch",
                    "bch_params": {"m": 8, "t": 4},
                    "ldpc_params": {"n": 1024, "d_v": 3, "d_c": 6, "systematic": True},
                },
                "compression": {"enabled": True, "algorithm": "lz4", "level": 3},
                "caching": {"enabled": True, "capacity": 1024, "policy": "lru", "ttl": 60},
                "wear_leveling": {"threshold": 1000, "method": "dynamic"},
                "parallelism": {"max_workers": 4},
            },
            "firmware_config": {
                "version": "1.0.0",
                "read_retry": True,
                "max_retries": 3,
                "data_scrambling": True,
                "scrambling_seed": "0xA5A5A5A5",
            },
            "ui_config": {
                "theme": "light",
                "font_size": 12,
                "update_interval": 5,
                "window_size": [1200, 800],
                "chart": {"antialiasing": True, "animations": True},
            },
            "logging": {
                "level": "INFO",
                "file": "logs/optimization_tool.log",
                "max_size": 10,
                "backup_count": 5,
                "console": True,
            },
        }

        # Apply default config to UI
        self.apply_config_to_ui()

    def apply_config_to_ui(self):
        """Apply configuration values to UI controls"""
        if not self.config:
            return

        # NAND Configuration
        nand_config = self.config.get("nand_config", {})
        self.page_size.setValue(nand_config.get("page_size", 0))
        self.block_size.setValue(nand_config.get("block_size", 0))
        self.num_blocks.setValue(nand_config.get("num_blocks", 0))
        self.oob_size.setValue(nand_config.get("oob_size", 0))
        self.num_planes.setValue(nand_config.get("num_planes", 0))

        # Timing Configuration (if exists)
        timing_config = self.config.get("timing_config", {})
        self.read_latency.setValue(timing_config.get("read_latency", 0.1))
        self.write_latency.setValue(timing_config.get("write_latency", 0.5))
        self.erase_latency.setValue(timing_config.get("erase_latency", 2.0))

        # Simulation Configuration (if exists)
        sim_config = self.config.get("simulation", {})
        self.error_rate.setValue(sim_config.get("error_rate", 0.0001))
        self.initial_bad_blocks.setValue(sim_config.get("initial_bad_block_rate", 0.002))
        self.simulation_mode.setChecked(sim_config.get("enabled", False))

        # Optimization Configuration
        opt_config = self.config.get("optimization_config", {})

        # Error Correction
        ecc_config = opt_config.get("error_correction", {})
        ecc_algo = ecc_config.get("algorithm", "bch").upper()
        self.ecc_algorithm.setCurrentText(ecc_algo)

        # BCH Parameters
        bch_params = ecc_config.get("bch_params", {})
        self.bch_m.setValue(bch_params.get("m", 8))
        self.bch_t.setValue(bch_params.get("t", 4))

        # LDPC Parameters
        ldpc_params = ecc_config.get("ldpc_params", {})
        self.ldpc_n.setValue(ldpc_params.get("n", 1024))
        self.ldpc_dv.setValue(ldpc_params.get("d_v", 3))
        self.ldpc_dc.setValue(ldpc_params.get("d_c", 6))
        self.ldpc_systematic.setChecked(ldpc_params.get("systematic", True))

        # Update ECC parameter visibility
        self.update_ecc_options(ecc_algo)

        # Compression Configuration
        comp_config = opt_config.get("compression", {})
        self.compression_enabled.setChecked(comp_config.get("enabled", True))
        self.compression_algorithm.setCurrentText(comp_config.get("algorithm", "lz4").capitalize())
        self.compression_level.setValue(comp_config.get("level", 3))

        # Update compression options
        self.update_compression_options(self.compression_enabled.checkState())

        # Caching Configuration
        cache_config = opt_config.get("caching", {})
        self.cache_enabled.setChecked(cache_config.get("enabled", True))
        self.cache_capacity.setValue(cache_config.get("capacity", 1024))
        self.cache_policy.setCurrentText(cache_config.get("policy", "lru").upper())
        self.cache_ttl.setValue(cache_config.get("ttl", 60))

        # Update cache options
        self.update_cache_options(self.cache_enabled.checkState())

        # Wear Leveling Configuration
        wl_config = opt_config.get("wear_leveling", {})
        self.wl_threshold.setValue(wl_config.get("threshold", 1000))
        self.wl_method.setCurrentText(wl_config.get("method", "dynamic").capitalize())

        # Parallelism Configuration
        parallelism_config = opt_config.get("parallelism", {})
        self.max_workers.setValue(parallelism_config.get("max_workers", 4))

        # Firmware Configuration
        fw_config = self.config.get("firmware_config", {})
        self.fw_version.setText(fw_config.get("version", "1.0.0"))
        self.read_retry.setChecked(fw_config.get("read_retry", True))
        self.max_retries.setValue(fw_config.get("max_retries", 3))
        self.data_scrambling.setChecked(fw_config.get("data_scrambling", True))
        self.scrambling_seed.setText(fw_config.get("scrambling_seed", "0xA5A5A5A5"))

        # Template Configuration (if exists)
        template_path = self.config.get("template_path", "")
        self.template_path.setText(template_path)

        # UI Configuration
        ui_config = self.config.get("ui_config", {})
        self.ui_theme.setCurrentText(ui_config.get("theme", "light").capitalize())
        self.font_size.setValue(ui_config.get("font_size", 12))
        self.update_interval.setValue(ui_config.get("update_interval", 5))

        # Window Size
        window_size = ui_config.get("window_size", [1200, 800])
        if isinstance(window_size, list) and len(window_size) >= 2:
            self.window_width.setValue(window_size[0])
            self.window_height.setValue(window_size[1])

        # Chart Configuration
        chart_config = ui_config.get("chart", {})
        self.chart_antialiasing.setChecked(chart_config.get("antialiasing", True))
        self.chart_animations.setChecked(chart_config.get("animations", True))

        # Logging Configuration
        logging_config = self.config.get("logging", {})
        self.log_level.setCurrentText(logging_config.get("level", "INFO"))
        self.log_file.setText(logging_config.get("file", "logs/optimization_tool.log"))
        self.max_log_size.setValue(logging_config.get("max_size", 10))
        self.backup_count.setValue(logging_config.get("backup_count", 5))
        self.console_logging.setChecked(logging_config.get("console", True))

    def get_config_from_ui(self):
        """Get configuration from UI controls"""
        config = {}

        # NAND Configuration
        config["nand_config"] = {
            "page_size": self.page_size.value(),
            "block_size": self.block_size.value(),
            "num_blocks": self.num_blocks.value(),
            "oob_size": self.oob_size.value(),
            "num_planes": self.num_planes.value(),
        }

        # Timing Configuration
        config["timing_config"] = {
            "read_latency": self.read_latency.value(),
            "write_latency": self.write_latency.value(),
            "erase_latency": self.erase_latency.value(),
        }

        # Simulation Configuration
        config["simulation"] = {
            "enabled": self.simulation_mode.isChecked(),
            "error_rate": self.error_rate.value(),
            "initial_bad_block_rate": self.initial_bad_blocks.value(),
        }

        # Optimization Configuration
        config["optimization_config"] = {}

        # Error Correction
        ecc_algo = self.ecc_algorithm.currentText().lower()
        ecc_config = {"algorithm": ecc_algo}

        # BCH Parameters
        if ecc_algo == "bch":
            ecc_config["bch_params"] = {"m": self.bch_m.value(), "t": self.bch_t.value()}

        # LDPC Parameters
        if ecc_algo == "ldpc":
            ecc_config["ldpc_params"] = {
                "n": self.ldpc_n.value(),
                "d_v": self.ldpc_dv.value(),
                "d_c": self.ldpc_dc.value(),
                "systematic": self.ldpc_systematic.isChecked(),
            }

        config["optimization_config"]["error_correction"] = ecc_config

        # Compression Configuration
        config["optimization_config"]["compression"] = {
            "enabled": self.compression_enabled.isChecked(),
            "algorithm": self.compression_algorithm.currentText().lower(),
            "level": self.compression_level.value(),
        }

        # Caching Configuration
        config["optimization_config"]["caching"] = {
            "enabled": self.cache_enabled.isChecked(),
            "capacity": self.cache_capacity.value(),
            "policy": self.cache_policy.currentText().lower(),
            "ttl": self.cache_ttl.value(),
        }

        # Wear Leveling Configuration
        config["optimization_config"]["wear_leveling"] = {
            "threshold": self.wl_threshold.value(),
            "method": self.wl_method.currentText().lower(),
        }

        # Parallelism Configuration
        config["optimization_config"]["parallelism"] = {"max_workers": self.max_workers.value()}

        # Firmware Configuration
        config["firmware_config"] = {
            "version": self.fw_version.text(),
            "read_retry": self.read_retry.isChecked(),
            "max_retries": self.max_retries.value(),
            "data_scrambling": self.data_scrambling.isChecked(),
            "scrambling_seed": self.scrambling_seed.text(),
        }

        # Template Path
        if self.template_path.text():
            config["template_path"] = self.template_path.text()

        # UI Configuration
        config["ui_config"] = {
            "theme": self.ui_theme.currentText().lower(),
            "font_size": self.font_size.value(),
            "update_interval": self.update_interval.value(),
            "window_size": [self.window_width.value(), self.window_height.value()],
            "chart": {"antialiasing": self.chart_antialiasing.isChecked(), "animations": self.chart_animations.isChecked()},
        }

        # Logging Configuration
        config["logging"] = {
            "level": self.log_level.currentText(),
            "file": self.log_file.text(),
            "max_size": self.max_log_size.value(),
            "backup_count": self.backup_count.value(),
            "console": self.console_logging.isChecked(),
        }

        return config

    def load_config_from_file(self):
        """Load configuration from a file"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Load Configuration", "", "YAML Files (*.yaml);;All Files (*)")

        if file_path:
            try:
                self.config = load_config(file_path)
                self.apply_config_to_ui()

                QMessageBox.information(self, "Configuration Loaded", f"Configuration loaded successfully from {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load configuration: {str(e)}")

    def save_config_to_file(self):
        """Save configuration to a file"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "Save Configuration", "", "YAML Files (*.yaml);;All Files (*)")

        if file_path:
            try:
                # Get current config from UI
                config = self.get_config_from_ui()

                # Save to file
                with open(file_path, "w") as f:
                    yaml.safe_dump(config, f, default_flow_style=False)

                QMessageBox.information(self, "Configuration Saved", f"Configuration saved successfully to {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.load_default_config()

            QMessageBox.information(self, "Reset Complete", "All settings have been reset to defaults")

    def apply_settings(self):
        """Apply settings without closing the dialog"""
        config = self.get_config_from_ui()
        self.config = config

        # Emit signal that settings have changed
        self.settings_changed.emit(config)

        QMessageBox.information(self, "Settings Applied", "Settings have been applied successfully")

    def accept_settings(self):
        """Apply settings and close the dialog"""
        self.apply_settings()
        self.accept()

    def get_config(self):
        """Get the current configuration"""
        return self.config
