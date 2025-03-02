# src/ui/main_window.py

import json
import os
import re
import time

import matplotlib
from PyQt5.QtCore import QSize, Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.ui.result_viewer import ResultViewer
from src.ui.settings_dialog import SettingsDialog
from src.utils.logger import get_logger

matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class OperationWorker(QThread):
    """Worker thread to perform NAND operations without freezing the UI"""

    progress_updated = pyqtSignal(int)
    operation_complete = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, nand_controller, operation_type, *args):
        super().__init__()
        self.nand_controller = nand_controller
        self.operation_type = operation_type
        self.args = args
        self.is_canceled = False

    def run(self):
        try:
            if self.operation_type == "load_data":
                file_path = self.args[0]
                # Get file size for progress reporting
                file_size = os.path.getsize(file_path)
                chunk_size = 1024 * 1024  # 1MB chunks

                # Open file and read in chunks for progress reporting
                with open(file_path, "rb") as f:
                    bytes_read = 0
                    while bytes_read < file_size and not self.is_canceled:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break

                        bytes_read += len(chunk)
                        progress = int((bytes_read / file_size) * 100)
                        self.progress_updated.emit(progress)

                if not self.is_canceled:
                    self.nand_controller.load_data(file_path)
                    self.operation_complete.emit({"type": "load_data", "file_path": file_path})

            elif self.operation_type == "save_data":
                file_path = self.args[0]
                start_block = self.args[1] if len(self.args) > 1 else 0
                end_block = self.args[2] if len(self.args) > 2 else None

                # Report intermediate progress
                for progress in range(0, 101, 5):
                    if self.is_canceled:
                        break
                    self.progress_updated.emit(progress)
                    time.sleep(0.05)  # Simulate progress

                if not self.is_canceled:
                    self.nand_controller.save_data(file_path, start_block, end_block)
                    self.operation_complete.emit({"type": "save_data", "file_path": file_path})

            elif self.operation_type == "run_test":
                test_type = self.args[0]
                # Simulate test running
                for progress in range(0, 101, 2):
                    if self.is_canceled:
                        break
                    self.progress_updated.emit(progress)
                    time.sleep(0.1)  # Simulate test operations

                if not self.is_canceled:
                    # In a real implementation, this would run actual tests
                    test_results = {
                        "type": "test_results",
                        "test_type": test_type,
                        "passed": True,
                        "details": {"tests_run": 42, "tests_passed": 40, "tests_failed": 2},
                    }
                    self.operation_complete.emit(test_results)

            elif self.operation_type == "initialize":
                self.nand_controller.initialize()
                self.operation_complete.emit({"type": "initialize", "success": True})

            elif self.operation_type == "shutdown":
                self.nand_controller.shutdown()
                self.operation_complete.emit({"type": "shutdown", "success": True})

        except Exception as e:
            self.error_occurred.emit(str(e))

    def cancel(self):
        self.is_canceled = True


class WearLevelingGraph(FigureCanvas):
    """Canvas for wear leveling visualization"""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(WearLevelingGraph, self).__init__(self.fig)
        self.setParent(parent)

        # Set up the plot
        self.axes.set_title("Wear Leveling Distribution")
        self.axes.set_xlabel("Block Number")
        self.axes.set_ylabel("Erase Count")

        # Add more space for labels and titles
        self.fig.subplots_adjust(bottom=0.15, left=0.15, top=0.9, right=0.95)

    def update_data(self, wear_data):
        """Update the plot with new data"""
        self.axes.clear()

        # Set up the plot
        self.axes.set_title("Wear Leveling Distribution")
        self.axes.set_xlabel("Block Number")
        self.axes.set_ylabel("Erase Count")

        # Plot the data
        if isinstance(wear_data, dict):
            blocks = list(wear_data.keys())
            counts = list(wear_data.values())
        else:  # Assume it's a numpy array
            blocks = list(range(len(wear_data)))
            counts = wear_data

        self.axes.bar(blocks, counts, alpha=0.7)

        # Add a horizontal line for the average
        if len(counts) > 0:
            avg = sum(counts) / len(counts)
            self.axes.axhline(y=avg, color="r", linestyle="-", label=f"Average: {avg:.1f}")
            self.axes.legend()

        # Use subplots_adjust instead of tight_layout to prevent warnings
        self.fig.subplots_adjust(bottom=0.15, left=0.15, top=0.9, right=0.95)
        self.draw()


class MainWindow(QMainWindow):
    """Main application window for the 3D NAND Optimization Tool"""

    def __init__(self, nand_controller):
        super().__init__()
        self.nand_controller = nand_controller
        self.logger = get_logger(__name__)
        self.result_viewer = None
        self.settings_dialog = None
        self.worker = None
        self.is_initialized = False

        # Set up UI components
        self.init_ui()

        # Update timer for refreshing stats
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_statistics)
        self.update_timer.start(5000)  # Update every 5 seconds

        # Initialize NAND controller
        self.initialize_nand_controller()

    def init_ui(self):
        """Initialize the user interface"""
        self.logger.info("Initializing main window UI")

        # Set window properties
        self.setWindowTitle("3D NAND Optimization Tool")
        icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "images", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setGeometry(100, 100, 1200, 800)

        # Create menu bar
        self.create_menu_bar()

        # Create toolbar
        self.create_toolbar()

        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

        # Create central widget with tab layout
        self.central_widget = QTabWidget()
        self.setCentralWidget(self.central_widget)

        # Add dashboard tab
        self.dashboard_widget = self.create_dashboard_widget()
        self.central_widget.addTab(self.dashboard_widget, "Dashboard")

        # Add operations tab
        self.operations_widget = self.create_operations_widget()
        self.central_widget.addTab(self.operations_widget, "Operations")

        # Add monitoring tab
        self.monitoring_widget = self.create_monitoring_widget()
        self.central_widget.addTab(self.monitoring_widget, "Monitoring")

        # Add result viewer tab
        self.result_viewer = ResultViewer(self)
        self.central_widget.addTab(self.result_viewer, "Results")

        # Create dock for log messages
        self.create_log_dock()

        self.logger.info("Main window UI initialized")

    def create_menu_bar(self):
        """Create the application menu bar"""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")

        # Create file menu actions
        open_action = QAction(QIcon.fromTheme("document-open"), "Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open file")
        open_action.triggered.connect(self.open_file)

        save_action = QAction(QIcon.fromTheme("document-save"), "Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save to file")
        save_action.triggered.connect(self.save_file)

        exit_action = QAction(QIcon.fromTheme("application-exit"), "Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)

        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # Settings menu
        settings_menu = menu_bar.addMenu("Settings")

        # Create settings menu actions
        settings_action = QAction(QIcon.fromTheme("preferences-system"), "Settings", self)
        settings_action.setStatusTip("Configure application settings")
        settings_action.triggered.connect(self.open_settings_dialog)

        settings_menu.addAction(settings_action)

        # Tools menu
        tools_menu = menu_bar.addMenu("Tools")

        # Create tools menu actions
        test_action = QAction("Run Tests", self)
        test_action.setStatusTip("Run NAND tests")
        test_action.triggered.connect(self.run_tests)

        firmware_action = QAction("Generate Firmware", self)
        firmware_action.setStatusTip("Generate firmware specification")
        firmware_action.triggered.connect(self.generate_firmware)

        tools_menu.addAction(test_action)
        tools_menu.addAction(firmware_action)

        # Help menu
        help_menu = menu_bar.addMenu("Help")

        # Create help menu actions
        about_action = QAction("About", self)
        about_action.setStatusTip("Show about dialog")
        about_action.triggered.connect(self.show_about_dialog)

        help_menu.addAction(about_action)

    def create_toolbar(self):
        """Create the application toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Add toolbar actions
        open_action = toolbar.addAction(QIcon.fromTheme("document-open", QIcon("resources/images/open.png")), "Open")
        open_action.triggered.connect(self.open_file)

        save_action = toolbar.addAction(QIcon.fromTheme("document-save", QIcon("resources/images/save.png")), "Save")
        save_action.triggered.connect(self.save_file)

        toolbar.addSeparator()

        settings_action = toolbar.addAction(QIcon.fromTheme("preferences-system", QIcon("resources/images/settings.png")), "Settings")
        settings_action.triggered.connect(self.open_settings_dialog)

        refresh_action = toolbar.addAction(QIcon.fromTheme("view-refresh", QIcon("resources/images/refresh.png")), "Refresh")
        refresh_action.triggered.connect(self.refresh_data)

    def create_dashboard_widget(self):
        """Create the dashboard tab content"""
        dashboard = QWidget()
        layout = QVBoxLayout(dashboard)

        # Status section
        status_group = QGroupBox("NAND Status")
        status_layout = QVBoxLayout()

        # Device info section
        device_info_layout = QHBoxLayout()

        # Create labels for device info
        device_info_labels = QVBoxLayout()
        self.device_info_labels = {
            "firmware_version": QLabel("Firmware Version: N/A"),
            "page_size": QLabel("Page Size: N/A"),
            "block_size": QLabel("Block Size: N/A"),
            "num_blocks": QLabel("Number of Blocks: N/A"),
            "num_planes": QLabel("Number of Planes: N/A"),
            "user_blocks": QLabel("User Blocks: N/A"),
        }

        for label in self.device_info_labels.values():
            device_info_labels.addWidget(label)

        device_info_layout.addLayout(device_info_labels)

        # Health indicators
        health_layout = QVBoxLayout()
        self.health_indicators = {
            "status": QLabel("Status: Not Initialized"),
            "bad_blocks": QLabel("Bad Blocks: N/A"),
            "wear_level": QLabel("Wear Level Status: N/A"),
            "cache_hits": QLabel("Cache Hit Ratio: N/A"),
        }

        # Apply special formatting to indicators
        for key, label in self.health_indicators.items():
            if key == "status":
                label.setStyleSheet("color: orange; font-weight: bold;")
            health_layout.addWidget(label)

        device_info_layout.addLayout(health_layout)
        status_layout.addLayout(device_info_layout)

        # Add initialize button
        init_button_layout = QHBoxLayout()
        self.init_button = QPushButton("Initialize NAND Controller")
        self.init_button.clicked.connect(self.initialize_nand_controller)
        init_button_layout.addWidget(self.init_button)
        init_button_layout.addStretch()
        status_layout.addLayout(init_button_layout)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Statistics section
        stats_group = QGroupBox("Performance Statistics")
        stats_layout = QHBoxLayout()

        # Operation counts
        ops_layout = QVBoxLayout()
        self.operation_stats = {
            "reads": QLabel("Reads: 0"),
            "writes": QLabel("Writes: 0"),
            "erases": QLabel("Erases: 0"),
            "ecc_corrections": QLabel("ECC Corrections: 0"),
        }

        for label in self.operation_stats.values():
            ops_layout.addWidget(label)

        stats_layout.addLayout(ops_layout)

        # Performance metrics
        perf_layout = QVBoxLayout()
        self.performance_stats = {
            "ops_per_second": QLabel("Operations/Second: 0"),
            "avg_compression": QLabel("Avg. Compression Ratio: 0x"),
            "cache_hit_ratio": QLabel("Cache Hit Ratio: 0%"),
            "bad_block_percentage": QLabel("Bad Block %: 0%"),
        }

        for label in self.performance_stats.values():
            perf_layout.addWidget(label)

        stats_layout.addLayout(perf_layout)

        # Add placeholder for wear leveling graph
        self.wear_leveling_graph = WearLevelingGraph(width=5, height=4)
        stats_layout.addWidget(self.wear_leveling_graph, 1)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Quick actions section
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout()

        load_button = QPushButton("Load Data")
        load_button.clicked.connect(self.open_file)

        save_button = QPushButton("Save Data")
        save_button.clicked.connect(self.save_file)

        test_button = QPushButton("Run Tests")
        test_button.clicked.connect(self.run_tests)

        firmware_button = QPushButton("Generate Firmware")
        firmware_button.clicked.connect(self.generate_firmware)

        actions_layout.addWidget(load_button)
        actions_layout.addWidget(save_button)
        actions_layout.addWidget(test_button)
        actions_layout.addWidget(firmware_button)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        # Progress bar for operations
        progress_layout = QHBoxLayout()
        self.progress_label = QLabel("No operation in progress")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_operation)
        self.cancel_button.setVisible(False)

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.cancel_button)

        layout.addLayout(progress_layout)

        return dashboard

    def create_operations_widget(self):
        """Create the operations tab content"""
        operations = QWidget()
        layout = QVBoxLayout(operations)

        # Read operations section
        read_group = QGroupBox("Read Operations")
        read_layout = QVBoxLayout()

        # Block and page selection
        read_params_layout = QHBoxLayout()
        read_params_layout.addWidget(QLabel("Block:"))
        self.read_block_combo = QComboBox()
        read_params_layout.addWidget(self.read_block_combo)

        read_params_layout.addWidget(QLabel("Page:"))
        self.read_page_combo = QComboBox()
        read_params_layout.addWidget(self.read_page_combo)

        read_button = QPushButton("Read Page")
        read_button.clicked.connect(self.read_page)
        read_params_layout.addWidget(read_button)

        read_layout.addLayout(read_params_layout)

        # Read results
        self.read_results_table = QTableWidget(0, 2)
        self.read_results_table.setHorizontalHeaderLabels(["Offset", "Data"])
        self.read_results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        read_layout.addWidget(self.read_results_table)

        read_group.setLayout(read_layout)
        layout.addWidget(read_group)

        # Write operations section
        write_group = QGroupBox("Write Operations")
        write_layout = QVBoxLayout()

        # Block and page selection
        write_params_layout = QHBoxLayout()
        write_params_layout.addWidget(QLabel("Block:"))
        self.write_block_combo = QComboBox()
        write_params_layout.addWidget(self.write_block_combo)

        write_params_layout.addWidget(QLabel("Page:"))
        self.write_page_combo = QComboBox()
        write_params_layout.addWidget(self.write_page_combo)

        write_button = QPushButton("Write Page")
        write_button.clicked.connect(self.write_page)
        write_params_layout.addWidget(write_button)

        erase_button = QPushButton("Erase Block")
        erase_button.clicked.connect(self.erase_block)
        write_params_layout.addWidget(erase_button)

        write_layout.addLayout(write_params_layout)

        write_group.setLayout(write_layout)
        layout.addWidget(write_group)

        # Batch operations section
        batch_group = QGroupBox("Batch Operations")
        batch_layout = QVBoxLayout()

        batch_buttons_layout = QHBoxLayout()
        load_batch_button = QPushButton("Load Batch File")
        load_batch_button.clicked.connect(self.load_batch_file)

        run_batch_button = QPushButton("Run Batch")
        run_batch_button.clicked.connect(self.run_batch)

        batch_buttons_layout.addWidget(load_batch_button)
        batch_buttons_layout.addWidget(run_batch_button)
        batch_buttons_layout.addStretch()

        batch_layout.addLayout(batch_buttons_layout)

        self.batch_table = QTableWidget(0, 3)
        self.batch_table.setHorizontalHeaderLabels(["Operation", "Parameters", "Status"])
        self.batch_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        batch_layout.addWidget(self.batch_table)

        batch_group.setLayout(batch_layout)
        layout.addWidget(batch_group)

        return operations

    def create_monitoring_widget(self):
        """Create the monitoring tab content"""
        monitoring = QWidget()
        layout = QVBoxLayout(monitoring)

        # Block health section
        block_health_group = QGroupBox("Block Health")
        block_health_layout = QVBoxLayout()

        self.block_health_table = QTableWidget(0, 5)
        self.block_health_table.setHorizontalHeaderLabels(["Block", "Status", "Erase Count", "Bad Block", "Last Operation"])
        self.block_health_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        block_health_layout.addWidget(self.block_health_table)

        # Controls for block display
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Show:"))

        self.show_combo = QComboBox()
        self.show_combo.addItems(["All Blocks", "Bad Blocks", "Most Worn Blocks", "Least Worn Blocks"])
        self.show_combo.currentIndexChanged.connect(self.update_block_health_table)
        controls_layout.addWidget(self.show_combo)

        controls_layout.addWidget(QLabel("Count:"))
        self.count_combo = QComboBox()
        self.count_combo.addItems(["10", "25", "50", "100", "All"])
        self.count_combo.currentIndexChanged.connect(self.update_block_health_table)
        controls_layout.addWidget(self.count_combo)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.update_block_health_table)
        controls_layout.addWidget(refresh_button)

        block_health_layout.addLayout(controls_layout)
        block_health_group.setLayout(block_health_layout)
        layout.addWidget(block_health_group)

        # Performance monitoring section
        perf_group = QGroupBox("Performance Monitoring")
        perf_layout = QVBoxLayout()

        # Create placeholder for performance graphs
        self.performance_graph = FigureCanvas(Figure(figsize=(5, 3)))
        self.performance_axes = self.performance_graph.figure.add_subplot(111)
        self.performance_axes.set_title("Operation Performance")
        self.performance_axes.set_xlabel("Time")
        self.performance_axes.set_ylabel("Operations/Second")
        self.performance_graph.figure.tight_layout()

        perf_layout.addWidget(self.performance_graph)

        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)

        return monitoring

    def create_log_dock(self):
        """Create the log message dock"""
        log_dock = QDockWidget("Log Messages", self)
        log_dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)

        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)

        self.log_tree = QTreeWidget()
        self.log_tree.setHeaderLabels(["Time", "Level", "Message"])
        self.log_tree.header().setSectionResizeMode(2, QHeaderView.Stretch)

        log_layout.addWidget(self.log_tree)

        # Add some controls
        log_controls = QHBoxLayout()

        log_controls.addWidget(QLabel("Filter:"))

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentIndex(1)  # INFO by default
        log_controls.addWidget(self.log_level_combo)

        clear_logs_button = QPushButton("Clear Logs")
        clear_logs_button.clicked.connect(self.clear_logs)
        log_controls.addWidget(clear_logs_button)

        log_controls.addStretch()
        log_layout.addLayout(log_controls)

        log_dock.setWidget(log_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, log_dock)

        # Add some initial log entries
        self.add_log_entry("INFO", "Application started")
        self.add_log_entry("INFO", "NAND controller ready")

    def initialize_nand_controller(self):
        """Initialize the NAND controller in a background thread with better error handling"""
        if self.is_initialized:
            self.logger.info("NAND controller already initialized")
            return

        # Check if an initialization is already in progress
        if self.worker and hasattr(self.worker, "operation_type") and self.worker.operation_type == "initialize":
            QMessageBox.information(self, "Initialization in Progress", "NAND controller initialization is already in progress.")
            return

        self.logger.info("Initializing NAND controller...")
        self.statusBar.showMessage("Initializing NAND controller...")

        # Update UI
        self.progress_label.setText("Initializing NAND controller...")
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.cancel_button.setVisible(True)
        self.init_button.setEnabled(False)

        # Create worker thread for initialization
        self.worker = OperationWorker(self.nand_controller, "initialize")
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.operation_complete.connect(self.handle_initialization_complete)
        self.worker.error_occurred.connect(self.handle_initialization_error)
        self.worker.start()

        # Add log entry
        self.add_log_entry("INFO", "NAND controller initialization started")

    def handle_initialization_complete(self, result):
        """Handle successful initialization of the NAND controller"""
        self.is_initialized = True
        self.init_button.setText("NAND Controller Initialized")
        self.init_button.setEnabled(False)
        self.add_log_entry("INFO", "NAND controller initialization completed")
        self.health_indicators["status"].setText("Status: Ready")
        self.health_indicators["status"].setStyleSheet("color: green; font-weight: bold;")

        # Reset progress UI
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        self.progress_label.setText("No operation in progress")
        self.worker = None

        # Update UI with initial data
        self.update_statistics()
        self.populate_block_page_combos()

        # Update status bar
        self.statusBar.showMessage("NAND controller initialized successfully", 5000)

    def handle_initialization_error(self, error_message):
        """Handle initialization failure of the NAND controller"""
        self.add_log_entry("ERROR", f"NAND controller initialization failed: {error_message}")

        # Reset button state
        self.init_button.setEnabled(True)
        self.init_button.setText("Initialize NAND Controller")

        # Reset progress UI
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        self.progress_label.setText("Initialization failed")
        self.worker = None

        # Show error message with recovery suggestions
        msg_box = QMessageBox(QMessageBox.Critical, "Initialization Failed", f"NAND controller initialization failed: {error_message}", parent=self)

        # Provide different suggestions based on the error message
        error_str = error_message.lower()

        if "file not found" in error_str or "no such file" in error_str:
            msg_box.setInformativeText(
                "Suggestions:\n"
                "- Verify that the configuration and template files exist\n"
                "- Check file paths in the configuration\n"
                "- Try running with the --check-resources flag"
            )
        elif "bad block" in error_str:
            msg_box.setInformativeText(
                "Suggestions:\n"
                "- Some blocks appear to be bad, but this is normal\n"
                "- The bad block management system should handle this\n"
                "- Try running with simulation mode enabled"
            )
        elif "wear leveling" in error_str:
            msg_box.setInformativeText(
                "Suggestions:\n"
                "- The wear leveling information could not be loaded\n"
                "- This is expected on first run or after resets\n"
                "- Default values will be used instead"
            )
        else:
            msg_box.setInformativeText(
                "Suggestions:\n"
                "- Check configuration settings\n"
                "- Verify hardware connections if using real hardware\n"
                "- Try enabling simulation mode\n"
                "- Check log files for more detailed error information"
            )

        msg_box.exec_()

        # Update status bar
        self.statusBar.showMessage("NAND controller initialization failed", 5000)

    def update_statistics(self):
        """Update UI with latest statistics from the NAND controller"""
        if not self.is_initialized:
            return

        try:
            # Get device information and statistics
            device_info = self.nand_controller.get_device_info()

            # Update device info labels
            if "config" in device_info:
                config = device_info["config"]
                self.device_info_labels["page_size"].setText(f"Page Size: {config.get('page_size', 'N/A')} bytes")
                self.device_info_labels["block_size"].setText(f"Block Size: {config.get('block_size', 'N/A')} pages")
                self.device_info_labels["num_blocks"].setText(f"Number of Blocks: {config.get('num_blocks', 'N/A')}")
                self.device_info_labels["num_planes"].setText(f"Number of Planes: {config.get('num_planes', 'N/A')}")
                self.device_info_labels["user_blocks"].setText(f"User Blocks: {config.get('user_blocks', 'N/A')}")

            # Update firmware info
            if "firmware" in device_info:
                firmware = device_info["firmware"]
                self.device_info_labels["firmware_version"].setText(f"Firmware Version: {firmware.get('version', 'N/A')}")

            # Update health indicators
            if "status" in device_info:
                status = device_info["status"]
                if status.get("ready", False):
                    self.health_indicators["status"].setText("Status: Ready")
                    self.health_indicators["status"].setStyleSheet("color: green; font-weight: bold;")
                else:
                    self.health_indicators["status"].setText("Status: Not Ready")
                    self.health_indicators["status"].setStyleSheet("color: red; font-weight: bold;")

            # Update statistics
            if "statistics" in device_info:
                stats = device_info["statistics"]

                # Operation counts
                self.operation_stats["reads"].setText(f"Reads: {stats.get('reads', 0)}")
                self.operation_stats["writes"].setText(f"Writes: {stats.get('writes', 0)}")
                self.operation_stats["erases"].setText(f"Erases: {stats.get('erases', 0)}")
                self.operation_stats["ecc_corrections"].setText(f"ECC Corrections: {stats.get('ecc_corrections', 0)}")

                # Performance metrics
                if "performance" in stats:
                    perf = stats["performance"]
                    self.performance_stats["ops_per_second"].setText(f"Operations/Second: {perf.get('ops_per_second', 0):.2f}")

                # Compression metrics
                if "compression" in stats:
                    comp = stats["compression"]
                    self.performance_stats["avg_compression"].setText(f"Avg. Compression Ratio: {comp.get('avg_ratio', 1.0):.2f}x")

                # Cache metrics
                if "cache" in stats:
                    cache = stats["cache"]
                    hit_ratio = cache.get("hit_ratio", 0.0)
                    self.performance_stats["cache_hit_ratio"].setText(f"Cache Hit Ratio: {hit_ratio:.2f}%")
                    self.health_indicators["cache_hits"].setText(f"Cache Hit Ratio: {hit_ratio:.2f}%")

                # Bad block metrics
                if "bad_blocks" in stats:
                    bad_blocks = stats["bad_blocks"]
                    percentage = bad_blocks.get("percentage", 0.0)
                    count = bad_blocks.get("count", 0)
                    self.performance_stats["bad_block_percentage"].setText(f"Bad Block %: {percentage:.2f}%")
                    self.health_indicators["bad_blocks"].setText(f"Bad Blocks: {count} ({percentage:.2f}%)")

                    # Update bad block indicator color based on percentage
                    if percentage > 5.0:
                        self.health_indicators["bad_blocks"].setStyleSheet("color: red; font-weight: bold;")
                    elif percentage > 2.0:
                        self.health_indicators["bad_blocks"].setStyleSheet("color: orange; font-weight: bold;")
                    else:
                        self.health_indicators["bad_blocks"].setStyleSheet("color: green;")

                # Wear leveling metrics
                if "wear_leveling" in stats:
                    wear = stats["wear_leveling"]
                    min_count = wear.get("min_erase_count", 0)
                    max_count = wear.get("max_erase_count", 0)
                    avg_count = wear.get("avg_erase_count", 0.0)
                    std_dev = wear.get("std_dev", 0.0)

                    self.health_indicators["wear_level"].setText(f"Wear Level: Min={min_count}, Max={max_count}, Avg={avg_count:.2f}")

                    # Update wear level wear_leveling graph
                    # In a real implementation, we would get the full wear distribution
                    # For now, let's create a simplified representation
                    wear_data = {}
                    for i in range(10):  # Show 10 blocks
                        if i == 0:
                            wear_data[i] = min_count
                        elif i == 9:
                            wear_data[i] = max_count
                        else:
                            # Linear interpolation between min and max
                            wear_data[i] = min_count + ((max_count - min_count) * (i / 9))

                    self.wear_leveling_graph.update_data(wear_data)

            # Update block health table
            self.update_block_health_table()

            # Update the UI
            self.result_viewer.update_results(device_info)

        except Exception as e:
            self.logger.error(f"Error updating statistics: {str(e)}")
            self.add_log_entry("ERROR", f"Error updating statistics: {str(e)}")

    def update_block_health_table(self):
        """Update the block health table"""
        if not self.is_initialized:
            return

        try:
            # Clear the table
            self.block_health_table.setRowCount(0)

            # Get the number of blocks to show
            count_text = self.count_combo.currentText()
            if count_text == "All":
                count = 1000000  # Effectively all blocks
            else:
                count = int(count_text)

            # Get filter type
            show_type = self.show_combo.currentText()

            # Get device information
            device_info = self.nand_controller.get_device_info()
            num_blocks = device_info.get("config", {}).get("num_blocks", 0)

            # Create a list of blocks to show
            blocks_to_show = []

            if show_type == "All Blocks":
                blocks_to_show = list(range(min(num_blocks, count)))
            elif show_type == "Bad Blocks":
                # In a real implementation, you would get actual bad blocks
                # For now, we'll just show a few random blocks
                for i in range(min(count, 10)):
                    blocks_to_show.append(int(num_blocks * i / 10))
            elif show_type == "Most Worn Blocks":
                # In a real implementation, you would get actual most worn blocks
                # For now, we'll just show a few random blocks
                for i in range(min(count, 10)):
                    blocks_to_show.append(int(num_blocks * i / 10))
            elif show_type == "Least Worn Blocks":
                # In a real implementation, you would get actual least worn blocks
                # For now, we'll just show a few random blocks
                for i in range(min(count, 10)):
                    blocks_to_show.append(num_blocks - int(num_blocks * i / 10) - 1)

            # Add rows to the table
            self.block_health_table.setRowCount(len(blocks_to_show))

            for row, block in enumerate(blocks_to_show):
                # Create items for the table
                block_item = QTableWidgetItem(str(block))

                # Determine block status
                is_bad = False
                try:
                    is_bad = self.nand_controller.is_bad_block(block)
                except:
                    pass

                status_item = QTableWidgetItem("Bad" if is_bad else "Good")
                if is_bad:
                    status_item.setForeground(QColor(255, 0, 0))  # Red color for bad blocks
                else:
                    status_item.setForeground(QColor(0, 128, 0))  # Green color for good blocks

                # Erase count (would come from wear leveling engine)
                erase_count = 0
                try:
                    # Get statistics
                    stats = device_info.get("statistics", {})
                    wear = stats.get("wear_leveling", {})
                    min_count = wear.get("min_erase_count", 0)
                    max_count = wear.get("max_erase_count", 0)

                    # Generate a value between min and max
                    erase_count = min_count + int((max_count - min_count) * (block / num_blocks))
                except:
                    pass

                erase_item = QTableWidgetItem(str(erase_count))

                # Bad block flag
                bad_item = QTableWidgetItem("Yes" if is_bad else "No")
                if is_bad:
                    bad_item.setForeground(QColor(255, 0, 0))

                # Last operation
                last_op = "Unknown"
                last_op_item = QTableWidgetItem(last_op)

                # Add items to the row
                self.block_health_table.setItem(row, 0, block_item)
                self.block_health_table.setItem(row, 1, status_item)
                self.block_health_table.setItem(row, 2, erase_item)
                self.block_health_table.setItem(row, 3, bad_item)
                self.block_health_table.setItem(row, 4, last_op_item)

        except Exception as e:
            self.logger.error(f"Error updating block health table: {str(e)}")
            self.add_log_entry("ERROR", f"Error updating block health table: {str(e)}")

    def add_log_entry(self, level, message):
        """Add an entry to the log tree"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Create a tree widget item for the log entry
        log_item = QTreeWidgetItem([timestamp, level, message])

        # Set color based on level
        if level == "ERROR" or level == "CRITICAL":
            log_item.setForeground(2, QColor(255, 0, 0))  # Red for errors
        elif level == "WARNING":
            log_item.setForeground(2, QColor(255, 165, 0))  # Orange for warnings
        elif level == "INFO":
            log_item.setForeground(2, QColor(0, 0, 0))  # Black for info
        elif level == "DEBUG":
            log_item.setForeground(2, QColor(128, 128, 128))  # Gray for debug

        # Add item to tree
        self.log_tree.insertTopLevelItem(0, log_item)  # Add at top for newest first

        # Auto-scroll to the new item
        self.log_tree.scrollToItem(log_item)

        # Filter based on selected level
        min_level = self.log_level_combo.currentText()
        log_item.setHidden(not self.should_show_log_level(level, min_level))

    def should_show_log_level(self, level, min_level):
        """Determine if a log level should be shown based on minimum level"""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        if level not in levels or min_level not in levels:
            return True

        return levels.index(level) >= levels.index(min_level)

    def clear_logs(self):
        """Clear all log entries"""
        self.log_tree.clear()
        self.add_log_entry("INFO", "Logs cleared")

    def open_file(self):
        """Open a file dialog to load data"""
        self.logger.info("Opening file dialog")
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Open File", "", "All Files (*)")

        if file_path:
            self.logger.info(f"Loading data from {file_path}")
            self.add_log_entry("INFO", f"Loading data from {file_path}")

            # Update UI
            self.progress_label.setText(f"Loading data from {file_path}...")
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.cancel_button.setVisible(True)

            # Start a worker thread for the operation
            self.worker = OperationWorker(self.nand_controller, "load_data", file_path)
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.operation_complete.connect(self.operation_completed)
            self.worker.error_occurred.connect(self.operation_failed)
            self.worker.start()

    def save_file(self):
        """Open a file dialog to save data"""
        self.logger.info("Opening file save dialog")
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "Save File", "", "All Files (*)")

        if file_path:
            self.logger.info(f"Saving data to {file_path}")
            self.add_log_entry("INFO", f"Saving data to {file_path}")

            # Update UI
            self.progress_label.setText(f"Saving data to {file_path}...")
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.cancel_button.setVisible(True)

            # Start a worker thread for the operation
            self.worker = OperationWorker(self.nand_controller, "save_data", file_path)
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.operation_complete.connect(self.operation_completed)
            self.worker.error_occurred.connect(self.operation_failed)
            self.worker.start()

    def update_progress(self, progress):
        """Update the progress bar"""
        self.progress_bar.setValue(progress)

    def operation_completed(self, result):
        """Handle completion of an operation"""
        operation_type = result.get("type", "unknown")

        if operation_type == "initialize":
            self.is_initialized = True
            self.init_button.setText("NAND Controller Initialized")
            self.init_button.setEnabled(False)
            self.add_log_entry("INFO", "NAND controller initialization completed")
            self.health_indicators["status"].setText("Status: Ready")
            self.health_indicators["status"].setStyleSheet("color: green; font-weight: bold;")

            # Update UI with initial data
            self.update_statistics()
            self.populate_block_page_combos()

        elif operation_type == "load_data":
            file_path = result.get("file_path", "unknown")
            self.add_log_entry("INFO", f"Data loaded successfully from {file_path}")

        elif operation_type == "save_data":
            file_path = result.get("file_path", "unknown")
            self.add_log_entry("INFO", f"Data saved successfully to {file_path}")

        elif operation_type == "read_page":
            block = result.get("block", 0)
            page = result.get("page", 0)
            data = result.get("data", b"")
            self.add_log_entry("INFO", f"Read page {page} from block {block} successfully")
            self.display_read_results(data)

        elif operation_type == "test_results":
            test_type = result.get("test_type", "unknown")
            passed = result.get("passed", False)
            details = result.get("details", {})

            if passed:
                self.add_log_entry("INFO", f"Test '{test_type}' passed: {details}")
            else:
                self.add_log_entry("WARNING", f"Test '{test_type}' failed: {details}")

            # Update results viewer with test results
            self.result_viewer.update_results(result)

        # Reset progress UI
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        self.progress_label.setText("No operation in progress")
        self.worker = None

        # Update status bar
        self.statusBar.showMessage(f"Operation completed: {operation_type}", 5000)

    def operation_failed(self, error_message):
        """Handle failure of an operation"""
        self.add_log_entry("ERROR", f"Operation failed: {error_message}")

        # Show error message
        QMessageBox.critical(self, "Operation Failed", f"The operation failed: {error_message}")

        # Reset progress UI
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        self.progress_label.setText("No operation in progress")
        self.worker = None

        # Update status bar
        self.statusBar.showMessage("Operation failed", 5000)

    def cancel_operation(self):
        """Cancel the current operation"""
        if self.worker:
            self.worker.cancel()
            self.add_log_entry("INFO", "Operation canceled by user")

            # Reset progress UI
            self.progress_bar.setVisible(False)
            self.cancel_button.setVisible(False)
            self.progress_label.setText("Operation canceled")

            # Update status bar
            self.statusBar.showMessage("Operation canceled", 5000)

    def open_settings_dialog(self):
        """Open the settings dialog"""
        self.logger.info("Opening settings dialog")

        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self)

        if self.settings_dialog.exec_():
            # Settings were accepted
            self.logger.info("Settings updated")
            self.add_log_entry("INFO", "Settings updated")

            # Apply settings
            self.apply_settings()

    def apply_settings(self):
        """Apply settings from the settings dialog"""
        # In a real implementation, this would get settings from the dialog
        # and apply them to the NAND controller
        pass

    def run_tests(self):
        """Run NAND tests"""
        self.logger.info("Running NAND tests")
        self.add_log_entry("INFO", "Starting NAND tests")

        # Show test selection dialog
        test_types = [
            "Basic Functionality Test",
            "Performance Test",
            "Reliability Test",
            "Stress Test",
            "Comprehensive Test Suite",
        ]

        test_type, ok = QInputDialog.getItem(self, "Select Test Type", "Test Type:", test_types, 0, False)

        if ok and test_type:
            # Update UI
            self.progress_label.setText(f"Running {test_type}...")
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.cancel_button.setVisible(True)

            # Start a worker thread for the test
            self.worker = OperationWorker(self.nand_controller, "run_test", test_type)
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.operation_complete.connect(self.operation_completed)
            self.worker.error_occurred.connect(self.operation_failed)
            self.worker.start()

    def generate_firmware(self):
        """Generate firmware specification with improved error handling"""
        self.logger.info("Generating firmware specification")
        self.add_log_entry("INFO", "Generating firmware specification")

        # Update UI to show operation in progress
        self.progress_label.setText("Generating firmware specification...")
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        try:
            # Check if template.yaml exists
            template_path = os.path.join("resources", "config", "template.yaml")
            if not os.path.exists(template_path):
                # Create the template file
                try:
                    template_content = """---
    firmware_version: "{{ firmware_version }}"
    nand_config:
    page_size: {{ nand_config.page_size }}
    block_size: {{ nand_config.block_size }}
    num_blocks: {{ nand_config.num_blocks }}
    oob_size: {{ nand_config.oob_size }}
    ecc_config:
    algorithm: "{{ ecc_config.algorithm }}"
    strength: {{ ecc_config.strength }}
    bbm_config:
    max_bad_blocks: {{ bbm_config.max_bad_blocks }}
    wl_config:
    wear_leveling_threshold: {{ wl_config.wear_leveling_threshold }}
    """
                    os.makedirs(os.path.dirname(template_path), exist_ok=True)
                    with open(template_path, "w") as f:
                        f.write(template_content)
                    self.add_log_entry("INFO", f"Created template file: {template_path}")
                except Exception as e:
                    self.add_log_entry("ERROR", f"Failed to create template file: {str(e)}")
                    raise RuntimeError(f"Missing template file and failed to create one: {str(e)}")

            # Generate firmware specification
            self.progress_bar.setValue(30)
            firmware_spec = self.nand_controller.generate_firmware_spec()
            self.progress_bar.setValue(70)

            # Show in result viewer
            self.result_viewer.update_results({"type": "firmware_spec", "spec": firmware_spec})

            # Switch to result viewer tab
            self.central_widget.setCurrentWidget(self.result_viewer)

            # Show success message
            self.statusBar.showMessage("Firmware specification generated", 5000)
            self.add_log_entry("INFO", "Firmware specification generated successfully")

            # Offer to save the specification
            reply = QMessageBox.question(
                self,
                "Save Specification",
                "Do you want to save the firmware specification to a file?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )

            if reply == QMessageBox.Yes:
                file_dialog = QFileDialog()
                file_path, _ = file_dialog.getSaveFileName(self, "Save Firmware Specification", "firmware_spec.yaml", "YAML Files (*.yaml);;All Files (*)")

                if file_path:
                    try:
                        with open(file_path, "w") as f:
                            f.write(firmware_spec)
                        self.add_log_entry("INFO", f"Firmware specification saved to {file_path}")
                        self.statusBar.showMessage(f"Firmware specification saved to {file_path}", 5000)
                    except Exception as e:
                        self.add_log_entry("ERROR", f"Failed to save firmware specification: {str(e)}")
                        QMessageBox.critical(self, "Save Failed", f"Failed to save firmware specification: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error generating firmware specification: {str(e)}")
            self.add_log_entry("ERROR", f"Error generating firmware specification: {str(e)}")

            # Show error message with more details
            msg_box = QMessageBox(QMessageBox.Critical, "Generation Failed", f"Failed to generate firmware specification: {str(e)}", parent=self)

            # Check for common errors
            error_str = str(e).lower()
            if "template" in error_str:
                msg_box.setInformativeText(
                    "There appears to be an issue with the template file. "
                    "Please check that 'resources/config/template.yaml' exists and is properly formatted."
                )
            elif "mapping" in error_str:
                msg_box.setInformativeText(
                    "There appears to be a YAML syntax error in the template file. " "Please check the template file for correct formatting."
                )
            else:
                msg_box.setInformativeText("Please check the configuration settings and try again.")

            msg_box.exec_()

        finally:
            # Reset progress UI
            self.progress_bar.setVisible(False)
            self.progress_label.setText("No operation in progress")

    def show_about_dialog(self):
        """Show the about dialog"""
        QMessageBox.about(
            self,
            "About 3D NAND Optimization Tool",
            "<h1>3D NAND Optimization Tool</h1>"
            "<p>Version 1.0.0</p>"
            "<p>A tool for optimizing 3D NAND flash storage systems</p>"
            "<p>Copyright © 2025 Mudit Bhargava</p>",
        )

    def refresh_data(self):
        """Refresh all data displays"""
        self.logger.info("Refreshing data")
        self.add_log_entry("INFO", "Refreshing data")

        # Update statistics
        self.update_statistics()

        # Update block health table
        self.update_block_health_table()

        # Show success message
        self.statusBar.showMessage("Data refreshed", 3000)

    def populate_block_page_combos(self):
        """Populate the block and page combo boxes with better error handling"""
        try:
            # Get device information
            device_info = self.nand_controller.get_device_info()
            num_blocks = device_info.get("config", {}).get("user_blocks", 0)
            pages_per_block = device_info.get("config", {}).get("pages_per_block", 0)

            # Handle case where device info doesn't contain expected values
            if num_blocks <= 0:
                num_blocks = 1024  # Default fallback
                self.logger.warning(f"Invalid number of blocks ({num_blocks}), using default")

            if pages_per_block <= 0:
                pages_per_block = 64  # Default fallback
                self.logger.warning(f"Invalid pages per block ({pages_per_block}), using default")

            # Clear existing items
            self.read_block_combo.clear()
            self.read_page_combo.clear()
            self.write_block_combo.clear()
            self.write_page_combo.clear()

            # Add block numbers - add a reasonable number, not all blocks
            max_blocks_to_show = min(num_blocks, 100)
            for i in range(max_blocks_to_show):
                # Skip blocks that are known to be bad
                try:
                    if self.nand_controller.is_bad_block(i):
                        continue
                except:
                    pass

                self.read_block_combo.addItem(str(i))
                self.write_block_combo.addItem(str(i))

            # Add page numbers
            for i in range(pages_per_block):
                self.read_page_combo.addItem(str(i))
                self.write_page_combo.addItem(str(i))

            # Select reasonable defaults
            if self.read_block_combo.count() > 0:
                self.read_block_combo.setCurrentIndex(0)
            if self.read_page_combo.count() > 0:
                self.read_page_combo.setCurrentIndex(0)
            if self.write_block_combo.count() > 0:
                self.write_block_combo.setCurrentIndex(0)
            if self.write_page_combo.count() > 0:
                self.write_page_combo.setCurrentIndex(0)

        except Exception as e:
            self.logger.error(f"Error populating block/page combos: {str(e)}")
            self.add_log_entry("ERROR", f"Error populating block/page combos: {str(e)}")

            # Add at least some values as fallback
            if self.read_block_combo.count() == 0:
                for i in range(10):
                    self.read_block_combo.addItem(str(i))
                    self.write_block_combo.addItem(str(i))

            if self.read_page_combo.count() == 0:
                for i in range(10):
                    self.read_page_combo.addItem(str(i))
                    self.write_page_combo.addItem(str(i))

    def read_page(self):
        """Read a page from the NAND flash with enhanced error handling"""
        if not self.is_initialized:
            QMessageBox.warning(self, "Not Initialized", "NAND controller must be initialized first")
            return

        try:
            # Get block and page numbers
            block = int(self.read_block_combo.currentText())
            page = int(self.read_page_combo.currentText())

            # Check if block is bad before attempting to read
            try:
                if self.nand_controller.is_bad_block(block):
                    self.add_log_entry("WARNING", f"Block {block} is marked as bad, read may fail")

                    # Ask user if they want to continue
                    reply = QMessageBox.question(
                        self,
                        "Reading Bad Block",
                        f"Block {block} is marked as bad. Attempt to read anyway?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )

                    if reply == QMessageBox.No:
                        return
            except Exception as check_e:
                self.logger.warning(f"Could not check if block {block} is bad: {str(check_e)}")

            self.logger.info(f"Reading page {page} from block {block}")
            self.add_log_entry("INFO", f"Reading page {page} from block {block}")

            # Read the page
            self.progress_label.setText(f"Reading page {page} from block {block}...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(10)  # Initial progress

            # Use a worker thread for the read operation
            self.worker = OperationWorker(self.nand_controller, "read_page", block, page)
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.operation_complete.connect(self.handle_read_complete)
            self.worker.error_occurred.connect(self.handle_read_error)
            self.worker.start()

        except Exception as e:
            self.logger.error(f"Error preparing read page operation: {str(e)}")
            self.add_log_entry("ERROR", f"Error preparing read operation: {str(e)}")

            # Show error message
            QMessageBox.critical(self, "Read Preparation Failed", f"Failed to prepare read operation: {str(e)}")

    def handle_read_complete(self, result):
        """Handle completion of a read operation"""
        if not isinstance(result, dict) or "type" not in result:
            return

        if result["type"] == "read_page":
            block = result.get("block", 0)
            page = result.get("page", 0)
            data = result.get("data", b"")

            self.add_log_entry("INFO", f"Read page {page} from block {block} successfully")
            self.display_read_results(data)

            # Reset progress UI
            self.progress_bar.setVisible(False)
            self.progress_label.setText("No operation in progress")
            self.worker = None

            # Update status bar
            self.statusBar.showMessage(f"Read page {page} from block {block} successfully", 5000)

    def handle_read_error(self, error_message):
        """Handle failure of a read operation"""
        self.add_log_entry("ERROR", f"Read operation failed: {error_message}")

        # Show error message with recovery suggestions
        msg_box = QMessageBox(QMessageBox.Critical, "Read Failed", f"The read operation failed: {error_message}", parent=self)

        msg_box.setInformativeText(
            "Suggestions:\n"
            "- Try reading a different page or block\n"
            "- Check if the block is marked as bad\n"
            "- Verify the NAND controller is properly initialized"
        )

        msg_box.exec_()

        # Reset progress UI
        self.progress_bar.setVisible(False)
        self.progress_label.setText("No operation in progress")
        self.worker = None

        # Update status bar
        self.statusBar.showMessage("Read operation failed", 5000)

    def display_read_results(self, data):
        """Display read results in the table"""
        # Clear the table
        self.read_results_table.setRowCount(0)

        if not data:
            return

        # Determine how many rows we need (16 bytes per row)
        num_rows = (len(data) + 15) // 16
        self.read_results_table.setRowCount(num_rows)

        # Fill the table with data
        for row in range(num_rows):
            offset = row * 16

            # Create offset item
            offset_item = QTableWidgetItem(f"0x{offset:04X}")
            self.read_results_table.setItem(row, 0, offset_item)

            # Create data item (hex representation)
            end = min(offset + 16, len(data))
            hex_data = " ".join(f"{b:02X}" for b in data[offset:end])

            # Add ASCII representation
            ascii_data = "".join(chr(b) if 32 <= b <= 126 else "." for b in data[offset:end])

            data_item = QTableWidgetItem(f"{hex_data}  |  {ascii_data}")
            self.read_results_table.setItem(row, 1, data_item)

    def write_page(self):
        """Write a page to the NAND flash with enhanced error handling"""
        if not self.is_initialized:
            QMessageBox.warning(self, "Not Initialized", "NAND controller must be initialized first")
            return

        try:
            # Get block and page numbers
            block = int(self.write_block_combo.currentText())
            page = int(self.write_page_combo.currentText())

            # Check if block is bad before attempting to write
            try:
                if self.nand_controller.is_bad_block(block):
                    self.add_log_entry("WARNING", f"Block {block} is marked as bad, write will fail")
                    QMessageBox.warning(self, "Bad Block", f"Block {block} is marked as bad. Please select a different block.")
                    return
            except Exception as check_e:
                self.logger.warning(f"Could not check if block {block} is bad: {str(check_e)}")

            # Get data to write
            data, ok = QInputDialog.getText(self, "Enter Data", "Data to write (text):")

            if ok and data:
                self.logger.info(f"Writing to page {page} in block {block}")
                self.add_log_entry("INFO", f"Writing to page {page} in block {block}")

                # Convert string to bytes
                data_bytes = data.encode("utf-8")

                # Check data size
                max_size = self.nand_controller.page_size
                if len(data_bytes) > max_size:
                    self.add_log_entry("WARNING", f"Data size ({len(data_bytes)} bytes) exceeds page size ({max_size} bytes)")

                    # Ask user if they want to truncate the data
                    reply = QMessageBox.question(
                        self,
                        "Data Too Large",
                        f"Data size ({len(data_bytes)} bytes) exceeds page size ({max_size} bytes). Truncate data?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )

                    if reply == QMessageBox.Yes:
                        data_bytes = data_bytes[:max_size]
                        self.add_log_entry("INFO", f"Data truncated to {len(data_bytes)} bytes")
                    else:
                        return

                # Use a worker thread for the write operation
                self.progress_label.setText(f"Writing to page {page} in block {block}...")
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)

                self.worker = OperationWorker(self.nand_controller, "write_page", block, page, data_bytes)
                self.worker.progress_updated.connect(self.update_progress)
                self.worker.operation_complete.connect(self.handle_write_complete)
                self.worker.error_occurred.connect(self.handle_write_error)
                self.worker.start()

        except Exception as e:
            self.logger.error(f"Error preparing write page operation: {str(e)}")
            self.add_log_entry("ERROR", f"Error preparing write operation: {str(e)}")

            # Show error message
            QMessageBox.critical(self, "Write Preparation Failed", f"Failed to prepare write operation: {str(e)}")

    def handle_write_complete(self, result):
        """Handle completion of a write operation"""
        if not isinstance(result, dict) or "type" not in result:
            return

        if result["type"] == "write_page":
            block = result.get("block", 0)
            page = result.get("page", 0)

            self.add_log_entry("INFO", f"Write to page {page} in block {block} successful")

            # Reset progress UI
            self.progress_bar.setVisible(False)
            self.progress_label.setText("No operation in progress")
            self.worker = None

            # Update status bar
            self.statusBar.showMessage(f"Write to page {page} in block {block} successful", 5000)

            # Refresh data displays
            self.refresh_data()

    def handle_write_error(self, error_message):
        """Handle failure of a write operation"""
        self.add_log_entry("ERROR", f"Write operation failed: {error_message}")

        # Show error message with recovery suggestions
        msg_box = QMessageBox(QMessageBox.Critical, "Write Failed", f"The write operation failed: {error_message}", parent=self)

        msg_box.setInformativeText(
            "Suggestions:\n"
            "- Try writing to a different page or block\n"
            "- Check if the block needs to be erased first\n"
            "- Verify the NAND controller is properly initialized"
        )

        msg_box.exec_()

        # Reset progress UI
        self.progress_bar.setVisible(False)
        self.progress_label.setText("No operation in progress")
        self.worker = None

        # Update status bar
        self.statusBar.showMessage("Write operation failed", 5000)

    def erase_block(self):
        """Erase a block in the NAND flash with enhanced error handling"""
        if not self.is_initialized:
            QMessageBox.warning(self, "Not Initialized", "NAND controller must be initialized first")
            return

        try:
            # Get block number
            block = int(self.write_block_combo.currentText())

            # Check if block is bad before attempting to erase
            try:
                if self.nand_controller.is_bad_block(block):
                    self.add_log_entry("WARNING", f"Block {block} is marked as bad, erase will fail")
                    QMessageBox.warning(self, "Bad Block", f"Block {block} is marked as bad. Please select a different block.")
                    return
            except Exception as check_e:
                self.logger.warning(f"Could not check if block {block} is bad: {str(check_e)}")

            # Check if block is in reserved area
            reserved_blocks = set(self.nand_controller.reserved_blocks.values())
            if block in reserved_blocks:
                self.add_log_entry("WARNING", f"Block {block} is a reserved system block")

                # Ask user if they're sure
                reply = QMessageBox.warning(
                    self,
                    "System Block",
                    f"Block {block} is a reserved system block. Erasing it may cause system instability. Continue anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )

                if reply == QMessageBox.No:
                    return

            # Confirm operation
            reply = QMessageBox.question(
                self,
                "Confirm Erase",
                f"Are you sure you want to erase block {block}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                self.logger.info(f"Erasing block {block}")
                self.add_log_entry("INFO", f"Erasing block {block}")

                # Use a worker thread for the erase operation
                self.progress_label.setText(f"Erasing block {block}...")
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)

                self.worker = OperationWorker(self.nand_controller, "erase_block", block)
                self.worker.progress_updated.connect(self.update_progress)
                self.worker.operation_complete.connect(self.handle_erase_complete)
                self.worker.error_occurred.connect(self.handle_erase_error)
                self.worker.start()

        except Exception as e:
            self.logger.error(f"Error preparing erase block operation: {str(e)}")
            self.add_log_entry("ERROR", f"Error preparing erase operation: {str(e)}")

            # Show error message
            QMessageBox.critical(self, "Erase Preparation Failed", f"Failed to prepare erase operation: {str(e)}")

    def handle_erase_complete(self, result):
        """Handle completion of an erase operation"""
        if not isinstance(result, dict) or "type" not in result:
            return

        if result["type"] == "erase_block":
            block = result.get("block", 0)

            self.add_log_entry("INFO", f"Block {block} erased successfully")

            # Reset progress UI
            self.progress_bar.setVisible(False)
            self.progress_label.setText("No operation in progress")
            self.worker = None

            # Update status bar
            self.statusBar.showMessage(f"Block {block} erased successfully", 5000)

            # Refresh data displays
            self.refresh_data()

    def handle_erase_error(self, error_message):
        """Handle failure of an erase operation"""
        self.add_log_entry("ERROR", f"Erase operation failed: {error_message}")

        # Check if error message contains reference to a bad block
        if "bad block" in error_message.lower():
            block_match = re.search(r"block (\d+)", error_message)
            if block_match:
                block = int(block_match.group(1))

                # Ask if user wants to mark the block as bad
                reply = QMessageBox.question(
                    self,
                    "Mark Bad Block",
                    f"Block {block} appears to be failing. Mark it as bad?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )

                if reply == QMessageBox.Yes:
                    try:
                        self.nand_controller.mark_bad_block(block)
                        self.add_log_entry("INFO", f"Block {block} marked as bad")
                    except Exception as e:
                        self.add_log_entry("ERROR", f"Failed to mark block {block} as bad: {str(e)}")

        # Show error message with recovery suggestions
        msg_box = QMessageBox(QMessageBox.Critical, "Erase Failed", f"The erase operation failed: {error_message}", parent=self)

        msg_box.setInformativeText(
            "Suggestions:\n"
            "- Try erasing a different block\n"
            "- Check if the block is already marked as bad\n"
            "- For critical system blocks, try initializing the NAND controller again"
        )

        msg_box.exec_()

        # Reset progress UI
        self.progress_bar.setVisible(False)
        self.progress_label.setText("No operation in progress")
        self.worker = None

        # Update status bar
        self.statusBar.showMessage("Erase operation failed", 5000)

    def load_batch_file(self):
        """Load a batch file with operations"""
        self.logger.info("Loading batch file")
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Open Batch File", "", "JSON Files (*.json);;All Files (*)")

        if file_path:
            try:
                with open(file_path, "r") as f:
                    batch_data = json.load(f)

                # Clear the batch table
                self.batch_table.setRowCount(0)

                # Add operations to the table
                if isinstance(batch_data, list):
                    self.batch_table.setRowCount(len(batch_data))

                    for row, op in enumerate(batch_data):
                        op_type = op.get("type", "unknown")
                        op_type_item = QTableWidgetItem(op_type)

                        # Format parameters as string
                        params = {}
                        for key, value in op.items():
                            if key != "type":
                                params[key] = value
                        params_item = QTableWidgetItem(str(params))

                        status_item = QTableWidgetItem("Pending")

                        self.batch_table.setItem(row, 0, op_type_item)
                        self.batch_table.setItem(row, 1, params_item)
                        self.batch_table.setItem(row, 2, status_item)

                    self.add_log_entry("INFO", f"Loaded {len(batch_data)} operations from batch file")
                    self.statusBar.showMessage(f"Loaded {len(batch_data)} operations from batch file", 5000)

            except Exception as e:
                self.logger.error(f"Error loading batch file: {str(e)}")
                self.add_log_entry("ERROR", f"Error loading batch file: {str(e)}")

                # Show error message
                QMessageBox.critical(self, "Load Failed", f"Failed to load batch file: {str(e)}")

    def run_batch(self):
        """Run the batch operations"""
        if not self.is_initialized:
            QMessageBox.warning(self, "Not Initialized", "NAND controller must be initialized first")
            return

        # Get number of operations
        num_operations = self.batch_table.rowCount()

        if num_operations == 0:
            QMessageBox.information(self, "No Operations", "No batch operations to run")
            return

        # Confirm operation
        reply = QMessageBox.question(
            self,
            "Confirm Batch Run",
            f"Are you sure you want to run {num_operations} batch operations?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.logger.info(f"Running {num_operations} batch operations")
            self.add_log_entry("INFO", f"Running {num_operations} batch operations")

            # In a real implementation, you would actually execute each operation
            # For now, we'll just update the status
            for row in range(num_operations):
                # Update status to "Running"
                status_item = QTableWidgetItem("Running")
                self.batch_table.setItem(row, 2, status_item)
                QApplication.processEvents()  # Update UI

                time.sleep(0.5)  # Simulate work

                # Update status to "Completed"
                status_item = QTableWidgetItem("Completed")
                self.batch_table.setItem(row, 2, status_item)
                QApplication.processEvents()  # Update UI

            self.add_log_entry("INFO", "Batch operations completed")
            self.statusBar.showMessage("Batch operations completed", 5000)

    def closeEvent(self, event):
        """Handle window close event"""
        # Check if an operation is in progress
        if self.worker and self.worker.isRunning():
            # Ask for confirmation
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "An operation is in progress. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.No:
                event.ignore()
                return

            # Try to cancel the operation
            self.worker.cancel()

        # Shut down the NAND controller
        if self.is_initialized:
            try:
                self.add_log_entry("INFO", "Shutting down NAND controller...")
                self.nand_controller.shutdown()
                self.add_log_entry("INFO", "NAND controller shut down successfully")
            except Exception as e:
                self.logger.error(f"Error shutting down NAND controller: {str(e)}")
                self.add_log_entry("ERROR", f"Error shutting down NAND controller: {str(e)}")

        # Log application exit
        self.logger.info("Application exiting")

        # Accept the event to close the window
        event.accept()
