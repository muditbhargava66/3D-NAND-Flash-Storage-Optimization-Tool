# src/ui/result_viewer.py

import json

import matplotlib
import yaml
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.utils.logger import get_logger

matplotlib.use("Qt5Agg")
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ResultVisualizer(FigureCanvas):
    """Enhanced canvas for visualizing various result data"""

    def __init__(self, parent=None, width=6, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

        # Set up the plot with improved styling
        self.fig.patch.set_facecolor("#f8f9fa")
        self.axes.grid(True, linestyle="--", alpha=0.7)
        self.axes.set_title("No Data Available")
        self.axes.set_facecolor("#f8f9fa")

        # Use subplots_adjust instead of tight_layout
        self.fig.subplots_adjust(bottom=0.15, left=0.15, top=0.9, right=0.95)

    def plot_bad_block_distribution(self, bad_blocks):
        """Plot the distribution of bad blocks with improved visualization"""
        self.axes.clear()

        # Set up the plot
        self.axes.set_title("Bad Block Distribution")
        self.axes.set_xlabel("Block Number")
        self.axes.set_ylabel("Status")

        # Plot each bad block as a vertical line
        if isinstance(bad_blocks, list) and bad_blocks:
            # Get the range of blocks
            if len(bad_blocks) > 0:
                max_block = max(bad_blocks)

                # Create a base array of good blocks (zeros)
                all_blocks = np.zeros(max_block + 1)

                # Mark bad blocks (set to 1)
                for block in bad_blocks:
                    if 0 <= block < len(all_blocks):
                        all_blocks[block] = 1

                # Create a more visible representation
                # Use bar chart with color coding
                self.axes.bar(
                    range(len(all_blocks)),
                    all_blocks,
                    color=["red" if x > 0 else "green" for x in all_blocks],
                    alpha=0.7,
                    width=1.0,
                )

                # Set y-axis limits
                self.axes.set_ylim(0, 1.2)

                # Add legend
                from matplotlib.patches import Patch

                legend_elements = [
                    Patch(facecolor="green", alpha=0.7, label="Good Block"),
                    Patch(facecolor="red", alpha=0.7, label="Bad Block"),
                ]
                self.axes.legend(handles=legend_elements, loc="upper right")

                # Add text with count
                self.axes.text(
                    0.05,
                    0.95,
                    f"Bad Blocks: {len(bad_blocks)}",
                    transform=self.axes.transAxes,
                    fontsize=12,
                    verticalalignment="top",
                    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
                )
            else:
                # No bad blocks, show empty plot
                self.axes.text(
                    0.5,
                    0.5,
                    "No bad blocks found",
                    transform=self.axes.transAxes,
                    fontsize=12,
                    horizontalalignment="center",
                    verticalalignment="center",
                )
        else:
            # No bad blocks, show empty plot
            self.axes.text(
                0.5,
                0.5,
                "No bad blocks found",
                transform=self.axes.transAxes,
                fontsize=12,
                horizontalalignment="center",
                verticalalignment="center",
            )

        # Set x-axis limits with a small margin
        if len(bad_blocks) > 0:
            self.axes.set_xlim(-max_block * 0.02, max_block * 1.02)

        # Update the figure
        self.fig.subplots_adjust(bottom=0.15, left=0.15, top=0.9, right=0.95)
        self.draw()

    def plot_wear_leveling(self, wear_data):
        """Plot wear leveling distribution"""
        self.axes.clear()

        # Set up the plot
        self.axes.set_title("Wear Leveling Distribution")
        self.axes.set_xlabel("Erase Count")
        self.axes.set_ylabel("Frequency")

        if isinstance(wear_data, dict) and wear_data:
            # Calculate histogram data
            min_val = wear_data.get("min", 0)
            max_val = wear_data.get("max", 1000)
            avg_val = wear_data.get("mean", 500)

            # Generate some synthetic data for visualization
            # In a real implementation, you would use actual erase count data
            data = np.random.normal(avg_val, (max_val - min_val) / 6, 1000)
            data = np.clip(data, min_val, max_val)

            # Plot histogram
            self.axes.hist(data, bins=30, alpha=0.7, color="blue")

            # Add vertical lines for min, max, avg
            self.axes.axvline(x=min_val, color="g", linestyle="--", label=f"Min: {min_val}")
            self.axes.axvline(x=max_val, color="r", linestyle="--", label=f"Max: {max_val}")
            self.axes.axvline(x=avg_val, color="k", linestyle="-", label=f"Avg: {avg_val:.1f}")

            self.axes.legend()
        else:
            # No wear data, show empty plot
            self.axes.text(
                0.5,
                0.5,
                "No wear leveling data available",
                transform=self.axes.transAxes,
                fontsize=12,
                horizontalalignment="center",
                verticalalignment="center",
            )

        self.fig.tight_layout()
        self.draw()

    def plot_test_results(self, test_results):
        """Plot test results"""
        self.axes.clear()

        # Set up the plot
        self.axes.set_title("Test Results")

        if isinstance(test_results, dict) and test_results:
            # Extract test data
            test_type = test_results.get("test_type", "Unknown")
            details = test_results.get("details", {})

            # Plot bar chart for test results
            labels = []
            values = []
            colors = []

            if "tests_run" in details:
                labels.append("Run")
                values.append(details["tests_run"])
                colors.append("blue")

            if "tests_passed" in details:
                labels.append("Passed")
                values.append(details["tests_passed"])
                colors.append("green")

            if "tests_failed" in details:
                labels.append("Failed")
                values.append(details["tests_failed"])
                colors.append("red")

            if labels and values:
                self.axes.bar(labels, values, color=colors)

                # Add percentages
                for i, v in enumerate(values):
                    self.axes.text(i, v + 0.5, f"{v}", ha="center")

                # Add title with test type
                self.axes.set_title(f"Test Results: {test_type}")
            else:
                # No specific test data, show a simple text
                self.axes.text(
                    0.5,
                    0.5,
                    f"Test completed: {test_type}",
                    transform=self.axes.transAxes,
                    fontsize=12,
                    horizontalalignment="center",
                    verticalalignment="center",
                )
        else:
            # No test data, show empty plot
            self.axes.text(
                0.5,
                0.5,
                "No test results available",
                transform=self.axes.transAxes,
                fontsize=12,
                horizontalalignment="center",
                verticalalignment="center",
            )

        self.fig.tight_layout()
        self.draw()

    def plot_performance(self, performance_data):
        """Plot performance metrics"""
        self.axes.clear()

        # Set up the plot
        self.axes.set_title("Performance Metrics")

        if isinstance(performance_data, dict) and performance_data:
            # Extract performance metrics
            metrics = []
            values = []

            for key, value in performance_data.items():
                if isinstance(value, (int, float)):
                    metrics.append(key)
                    values.append(value)

            if metrics and values:
                # Create horizontal bar chart
                y_pos = np.arange(len(metrics))
                self.axes.barh(y_pos, values, align="center")
                self.axes.set_yticks(y_pos)
                self.axes.set_yticklabels(metrics)
                self.axes.invert_yaxis()  # Labels read top-to-bottom

                # Add values as text
                for i, v in enumerate(values):
                    self.axes.text(v + 0.1, i, f"{v:.2f}", va="center")
            else:
                # No specific metrics, show a simple text
                self.axes.text(
                    0.5,
                    0.5,
                    "Performance data available but no metrics to plot",
                    transform=self.axes.transAxes,
                    fontsize=12,
                    horizontalalignment="center",
                    verticalalignment="center",
                )
        else:
            # No performance data, show empty plot
            self.axes.text(
                0.5,
                0.5,
                "No performance metrics available",
                transform=self.axes.transAxes,
                fontsize=12,
                horizontalalignment="center",
                verticalalignment="center",
            )

        self.fig.tight_layout()
        self.draw()


class ResultViewer(QWidget):
    """
    Enhanced viewer for NAND optimization tool results
    Provides visualization, analysis, and export functionality
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.current_results = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout(self)

        # Create tab widget for different result views
        self.result_tabs = QTabWidget()

        # Summary tab
        self.summary_tab = self.create_summary_tab()

        # Details tab
        self.details_tab = self.create_details_tab()

        # Visualization tab
        self.visualization_tab = self.create_visualization_tab()

        # Raw data tab
        self.raw_data_tab = self.create_raw_data_tab()

        # Add tabs to the widget
        self.result_tabs.addTab(self.summary_tab, "Summary")
        self.result_tabs.addTab(self.details_tab, "Details")
        self.result_tabs.addTab(self.visualization_tab, "Visualization")
        self.result_tabs.addTab(self.raw_data_tab, "Raw Data")

        main_layout.addWidget(self.result_tabs)

        # Add controls at the bottom
        controls_layout = QHBoxLayout()

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_results)

        export_button = QPushButton("Export Results")
        export_button.clicked.connect(self.export_results)

        self.visualization_type = QComboBox()
        self.visualization_type.addItems(["Bad Block Distribution", "Wear Leveling", "Test Results", "Performance Metrics"])
        self.visualization_type.currentTextChanged.connect(self.update_visualization)

        controls_layout.addWidget(QLabel("Visualization:"))
        controls_layout.addWidget(self.visualization_type)
        controls_layout.addStretch()
        controls_layout.addWidget(refresh_button)
        controls_layout.addWidget(export_button)

        main_layout.addLayout(controls_layout)

    def create_summary_tab(self):
        """Create the summary tab content"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Summary text browser
        self.summary_text = QTextBrowser()
        self.summary_text.setOpenExternalLinks(True)

        # Set default content
        self.summary_text.setHtml(
            """
        <h2>NAND Optimization Results Summary</h2>
        <p>No results available yet. Use the NAND controller to generate results.</p>
        <p>The summary will show key metrics and findings from the optimization process.</p>
        """
        )

        layout.addWidget(self.summary_text)

        return tab

    def create_details_tab(self):
        """Create the details tab content"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Create tree widget for hierarchical display of details
        self.details_tree = QTreeWidget()
        self.details_tree.setHeaderLabels(["Parameter", "Value"])
        self.details_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.details_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)

        # Add some default items
        root = QTreeWidgetItem(self.details_tree, ["Results", "No data available"])

        layout.addWidget(self.details_tree)

        return tab

    def create_visualization_tab(self):
        """Create the visualization tab content"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Create plotting canvas
        self.result_visualizer = ResultVisualizer(tab, width=8, height=6)

        # Add to layout
        layout.addWidget(self.result_visualizer)

        return tab

    def create_raw_data_tab(self):
        """Create the raw data tab content"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Create text editor for raw data
        self.raw_data_text = QTextEdit()
        self.raw_data_text.setReadOnly(True)
        self.raw_data_text.setFont(QFont("Courier New", 10))

        # Format options
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))

        self.format_combo = QComboBox()
        self.format_combo.addItems(["JSON", "YAML", "Text"])
        self.format_combo.currentTextChanged.connect(self.update_raw_data_format)

        self.pretty_print = QCheckBox("Pretty Print")
        self.pretty_print.setChecked(True)
        self.pretty_print.toggled.connect(self.update_raw_data_format)

        format_layout.addWidget(self.format_combo)
        format_layout.addWidget(self.pretty_print)
        format_layout.addStretch()

        # Add to layout
        layout.addLayout(format_layout)
        layout.addWidget(self.raw_data_text)

        return tab

    def update_results(self, results):
        """Update the viewer with new results, with better error handling"""
        self.logger.debug("Updating results in viewer")

        try:
            # Store the results for future use
            self.current_results = results

            # Update summary tab
            try:
                self.update_summary()
            except Exception as e:
                self.logger.error(f"Error updating summary tab: {str(e)}")
                # Fallback to a simple display
                self.summary_text.setHtml(f"<h2>NAND Optimization Results</h2><p>Error displaying summary: {str(e)}</p>")

            # Update details tab
            try:
                self.update_details()
            except Exception as e:
                self.logger.error(f"Error updating details tab: {str(e)}")
                # Clear the tree
                self.details_tree.clear()
                # Add an error item
                error_item = QTreeWidgetItem(self.details_tree, ["Error", str(e)])
                error_item.setForeground(1, QColor(255, 0, 0))

            # Update visualization tab
            try:
                self.update_visualization()
            except Exception as e:
                self.logger.error(f"Error updating visualization tab: {str(e)}")
                # Show error message in the visualization
                self.result_visualizer.axes.clear()
                self.result_visualizer.axes.text(0.5, 0.5, f"Error creating visualization: {str(e)}", ha="center", va="center", fontsize=12, color="red")
                self.result_visualizer.fig.canvas.draw()

            # Update raw data tab
            try:
                self.update_raw_data()
            except Exception as e:
                self.logger.error(f"Error updating raw data tab: {str(e)}")
                # Fallback to a simple display
                self.raw_data_text.setText(f"Error displaying raw data: {str(e)}\n\nRaw results:\n{str(results)}")

        except Exception as e:
            self.logger.error(f"Critical error updating results: {str(e)}")
            self.summary_text.setHtml(f"<h2>Error Displaying Results</h2><p>A critical error occurred: {str(e)}</p>")

    def update_summary(self):
        """Update the summary tab with current results, with improved formatting and error handling"""
        if not self.current_results:
            self.summary_text.setHtml("<h2>NAND Optimization Results Summary</h2><p>No results available yet.</p>")
            return

        # Create HTML summary based on result type
        html = "<h2>NAND Optimization Results Summary</h2>"

        result_type = self.current_results.get("type", "")

        if result_type == "firmware_spec":
            # Firmware specification summary
            spec = self.current_results.get("spec", "")
            if spec:
                html += "<h3>Firmware Specification Generated</h3>"
                html += "<p>A firmware specification has been successfully generated.</p>"

                # Try to parse YAML for nicer display
                try:
                    spec_data = yaml.safe_load(spec)
                    if isinstance(spec_data, dict):
                        # Add firmware version
                        if "firmware_version" in spec_data:
                            html += f"<p><strong>Firmware Version:</strong> {spec_data['firmware_version']}</p>"

                        # Add NAND config summary
                        if "nand_config" in spec_data:
                            nand_config = spec_data["nand_config"]
                            html += "<h4>NAND Configuration</h4>"
                            html += "<ul>"
                            for key, value in nand_config.items():
                                html += f"<li><strong>{key}:</strong> {value}</li>"
                            html += "</ul>"

                        # Add ECC config summary
                        if "ecc_config" in spec_data:
                            ecc_config = spec_data["ecc_config"]
                            html += "<h4>Error Correction</h4>"
                            html += "<ul>"
                            for key, value in ecc_config.items():
                                html += f"<li><strong>{key}:</strong> {value}</li>"
                            html += "</ul>"

                        # Add Bad Block Management config
                        if "bbm_config" in spec_data:
                            bbm_config = spec_data["bbm_config"]
                            html += "<h4>Bad Block Management</h4>"
                            html += "<ul>"
                            for key, value in bbm_config.items():
                                html += f"<li><strong>{key}:</strong> {value}</li>"
                            html += "</ul>"

                        # Add Wear Leveling config
                        if "wl_config" in spec_data:
                            wl_config = spec_data["wl_config"]
                            html += "<h4>Wear Leveling</h4>"
                            html += "<ul>"
                            for key, value in wl_config.items():
                                html += f"<li><strong>{key}:</strong> {value}</li>"
                            html += "</ul>"
                except Exception:
                    # If parsing fails, just show a portion of the raw spec but with syntax highlighting
                    html += "<p>Firmware specification preview:</p>"
                    html += f"<pre style='background-color: #f5f5f5; padding: 10px; border-radius: 5px;'>{spec[:1000]}...</pre>"

                # Add button for downloading the spec
                html += "<p><button onclick=\"alert('Use the Save option from the toolbar to save the specification')\">Download Specification</button></p>"

            else:
                html += "<p>No firmware specification data available.</p>"

        elif "config" in self.current_results:
            # Device information and statistics
            html += "<h3>Device Information</h3>"

            # Add configuration summary
            config = self.current_results.get("config", {})
            if config:
                html += "<h4>Configuration</h4>"
                html += "<ul>"
                for key, value in config.items():
                    if isinstance(value, dict):
                        continue  # Skip nested dictionaries for summary
                    html += f"<li><strong>{key}:</strong> {value}</li>"
                html += "</ul>"

            # Add firmware summary
            firmware = self.current_results.get("firmware", {})
            if firmware:
                html += "<h4>Firmware</h4>"
                html += "<ul>"
                for key, value in firmware.items():
                    if isinstance(value, dict):
                        continue  # Skip nested dictionaries for summary
                    html += f"<li><strong>{key}:</strong> {value}</li>"
                html += "</ul>"

            # Add statistics summary
            stats = self.current_results.get("statistics", {})
            if stats:
                html += "<h3>Performance Statistics</h3>"

                # Operation counts
                html += "<div style='display: flex; flex-wrap: wrap;'>"
                html += "<div style='flex: 1; min-width: 300px;'>"
                html += "<h4>Operations</h4>"
                html += "<ul>"
                for op in ["reads", "writes", "erases", "ecc_corrections"]:
                    if op in stats:
                        html += f"<li><strong>{op.capitalize()}:</strong> {stats[op]}</li>"
                html += "</ul>"
                html += "</div>"

                # Performance metrics
                if "performance" in stats:
                    perf = stats["performance"]
                    html += "<div style='flex: 1; min-width: 300px;'>"
                    html += "<h4>Performance</h4>"
                    html += "<ul>"
                    for key, value in perf.items():
                        if isinstance(value, float):
                            html += f"<li><strong>{key}:</strong> {value:.2f}</li>"
                        else:
                            html += f"<li><strong>{key}:</strong> {value}</li>"
                    html += "</ul>"
                    html += "</div>"

                html += "</div>"  # Close flex container

                # Second row of stats
                html += "<div style='display: flex; flex-wrap: wrap;'>"

                # Cache metrics
                if "cache" in stats:
                    cache = stats["cache"]
                    html += "<div style='flex: 1; min-width: 300px;'>"
                    html += "<h4>Cache</h4>"
                    html += "<ul>"
                    for key, value in cache.items():
                        if key == "hit_ratio":
                            html += f"<li><strong>Hit Ratio:</strong> {value:.2f}%</li>"
                        else:
                            html += f"<li><strong>{key}:</strong> {value}</li>"
                    html += "</ul>"
                    html += "</div>"

                # Bad block metrics
                if "bad_blocks" in stats:
                    bb = stats["bad_blocks"]
                    html += "<div style='flex: 1; min-width: 300px;'>"
                    html += "<h4>Bad Blocks</h4>"
                    html += "<ul>"
                    for key, value in bb.items():
                        if key == "percentage":
                            html += f"<li><strong>Percentage:</strong> {value:.2f}%</li>"
                        else:
                            html += f"<li><strong>{key}:</strong> {value}</li>"
                    html += "</ul>"
                    html += "</div>"

                html += "</div>"  # Close flex container

                # Wear leveling metrics
                if "wear_leveling" in stats:
                    wl = stats["wear_leveling"]
                    html += "<h4>Wear Leveling</h4>"
                    html += "<ul>"
                    for key, value in wl.items():
                        if isinstance(value, float):
                            html += f"<li><strong>{key}:</strong> {value:.2f}</li>"
                        else:
                            html += f"<li><strong>{key}:</strong> {value}</li>"
                    html += "</ul>"

        elif result_type == "test_results":
            # Test results summary
            html += "<h3>Test Results</h3>"

            test_type = self.current_results.get("test_type", "Unknown")
            passed = self.current_results.get("passed", False)

            html += f"<p><strong>Test Type:</strong> {test_type}</p>"

            if passed:
                html += "<p style='color: green; font-weight: bold; font-size: 1.2em;'>Test Result: PASSED ✓</p>"
            else:
                html += "<p style='color: red; font-weight: bold; font-size: 1.2em;'>Test Result: FAILED ✗</p>"

            # Add test details
            details = self.current_results.get("details", {})
            if details:
                html += "<h4>Test Details</h4>"
                html += "<ul>"
                for key, value in details.items():
                    html += f"<li><strong>{key}:</strong> {value}</li>"
                html += "</ul>"

                # Add visual representation if available
                if "tests_run" in details and "tests_passed" in details and "tests_failed" in details:
                    tests_run = details["tests_run"]
                    tests_passed = details["tests_passed"]
                    tests_failed = details["tests_failed"]

                    if tests_run > 0:
                        passed_percent = (tests_passed / tests_run) * 100
                        failed_percent = (tests_failed / tests_run) * 100

                        html += "<div style='margin-top: 20px; margin-bottom: 20px;'>"
                        html += "<div style='height: 30px; background-color: #f5f5f5; border-radius: 15px; overflow: hidden;'>"

                        if passed_percent > 0:
                            html += f"<div style='height: 100%; width: {passed_percent}%; background-color: #28a745; float: left;'></div>"

                        if failed_percent > 0:
                            html += f"<div style='height: 100%; width: {failed_percent}%; background-color: #dc3545; float: left;'></div>"

                        html += "</div>"
                        html += (
                            f"<div style='text-align: center; margin-top: 5px;'>"
                            f"{tests_passed} passed ({passed_percent:.1f}%), "
                            f"{tests_failed} failed ({failed_percent:.1f}%)</div>"
                        )
                        html += "</div>"

        else:
            # Generic summary for other types of results
            html += "<p>Results available. Select the Details tab for more information.</p>"

            # Print keys from the results
            html += "<p>Result contains the following data:</p>"
            html += "<ul>"
            for key in self.current_results.keys():
                html += f"<li>{key}</li>"
            html += "</ul>"

        # Set the HTML content
        self.summary_text.setHtml(html)

    def update_details(self):
        """Update the details tree with current results"""
        if not self.current_results:
            return

        # Clear the tree
        self.details_tree.clear()

        # Helper function to recursively add items
        def add_items(parent, key, value):
            if isinstance(value, dict):
                item = QTreeWidgetItem(parent, [key, ""])
                for k, v in value.items():
                    add_items(item, k, v)
            elif isinstance(value, list):
                item = QTreeWidgetItem(parent, [key, f"Array ({len(value)} items)"])
                for i, v in enumerate(value):
                    add_items(item, f"[{i}]", v)
            else:
                item = QTreeWidgetItem(parent, [key, str(value)])

                # Color-code certain values
                if key.lower() in ["status", "state"]:
                    if str(value).lower() in ["good", "ready", "passed", "true"]:
                        item.setForeground(1, QColor(0, 128, 0))  # Green
                    elif str(value).lower() in ["bad", "error", "failed", "false"]:
                        item.setForeground(1, QColor(255, 0, 0))  # Red

        # Add top-level items
        for key, value in self.current_results.items():
            add_items(self.details_tree, key, value)

        # Expand top-level items
        for i in range(self.details_tree.topLevelItemCount()):
            self.details_tree.topLevelItem(i).setExpanded(True)

    def update_visualization(self, vis_type=None):
        """Update the visualization with current results, with improved error handling and display options"""
        if not self.current_results:
            # Clear the visualization
            self.result_visualizer.axes.clear()
            self.result_visualizer.axes.text(0.5, 0.5, "No data available for visualization", ha="center", va="center", fontsize=12)
            self.result_visualizer.fig.canvas.draw()
            return

        # Use parameter if provided, otherwise use combo box
        if vis_type is None:
            vis_type = self.visualization_type.currentText()

        # Determine what to visualize based on the visualization type and results
        if vis_type == "Bad Block Distribution":
            # Find bad block data in results
            if "statistics" in self.current_results:
                stats = self.current_results["statistics"]
                if "bad_blocks" in stats:
                    bad_blocks = stats["bad_blocks"]
                    count = bad_blocks.get("count", 0)

                    # Generate some dummy block numbers for visualization if needed
                    if count > 0:
                        bad_block_list = []

                        # Try to extract actual bad block numbers if available
                        try:
                            if "list" in bad_blocks:
                                bad_block_list = bad_blocks["list"]
                            else:
                                # In a real implementation, you'd use actual bad block numbers
                                # Here we generate some for visualization
                                num_blocks = self.current_results.get("config", {}).get("num_blocks", 1024)
                                bad_block_list = sorted([int(num_blocks * i / count) for i in range(count)])
                        except Exception as e:
                            self.logger.warning(f"Could not extract bad block list: {str(e)}")
                            # Generate dummy block numbers
                            num_blocks = self.current_results.get("config", {}).get("num_blocks", 1024)
                            bad_block_list = sorted([int(num_blocks * i / count) for i in range(count)])

                        self.result_visualizer.plot_bad_block_distribution(bad_block_list)
                    else:
                        self.result_visualizer.plot_bad_block_distribution([])
                else:
                    self.result_visualizer.plot_bad_block_distribution([])
            else:
                self.result_visualizer.plot_bad_block_distribution([])

        elif vis_type == "Wear Leveling":
            # Find wear leveling data in results
            if "statistics" in self.current_results:
                stats = self.current_results["statistics"]
                if "wear_leveling" in stats:
                    wear_data = stats["wear_leveling"]

                    # Add distribution data if available
                    if "distribution" not in wear_data:
                        # Generate synthetic distribution based on min/max/avg
                        min_val = wear_data.get("min_erase_count", 0)
                        max_val = wear_data.get("max_erase_count", 0)
                        avg_val = wear_data.get("avg_erase_count", 0)
                        std_dev = wear_data.get("std_dev", 0)

                        # Simple distribution approximation
                        distribution = {}
                        num_blocks = self.current_results.get("config", {}).get("num_blocks", 1024)

                        # Create a more realistic looking distribution if we have std_dev
                        if std_dev > 0:
                            import numpy as np

                            try:
                                # Create a normal distribution around avg with std_dev
                                samples = np.random.normal(avg_val, std_dev, 20)
                                # Clip values between min and max
                                samples = np.clip(samples, min_val, max_val)

                                # Create a distribution with 20 points
                                for i, val in enumerate(samples):
                                    distribution[i] = int(val)
                            except:
                                # Fallback to simple approximation
                                for i in range(20):
                                    # Linear interpolation between min and max
                                    val = min_val + (max_val - min_val) * (i / 19)
                                    distribution[i] = int(val)
                        else:
                            # Simple linear distribution
                            for i in range(20):
                                # Linear interpolation between min and max
                                val = min_val + (max_val - min_val) * (i / 19)
                                distribution[i] = int(val)

                        wear_data["distribution"] = distribution

                    self.result_visualizer.plot_wear_leveling(wear_data)
                else:
                    self.result_visualizer.plot_wear_leveling({})
            else:
                self.result_visualizer.plot_wear_leveling({})

        elif vis_type == "Test Results":
            # Check if we have test results
            if "test_type" in self.current_results:
                self.result_visualizer.plot_test_results(self.current_results)
            else:
                self.result_visualizer.plot_test_results({})

        elif vis_type == "Performance Metrics":
            # Find performance metrics in results
            if "statistics" in self.current_results:
                stats = self.current_results["statistics"]
                if "performance" in stats:
                    perf_data = stats["performance"]
                    self.result_visualizer.plot_performance(perf_data)
                else:
                    self.result_visualizer.plot_performance({})
            else:
                self.result_visualizer.plot_performance({})

    def update_raw_data_format(self):
        """Update the raw data display based on selected format"""
        if not self.current_results:
            return

        format_type = self.format_combo.currentText()
        pretty = self.pretty_print.isChecked()

        try:
            if format_type == "JSON":
                if pretty:
                    text = json.dumps(self.current_results, indent=2)
                else:
                    text = json.dumps(self.current_results)
            elif format_type == "YAML":
                text = yaml.safe_dump(self.current_results, default_flow_style=not pretty)
            else:  # Text
                text = str(self.current_results)

            self.raw_data_text.setText(text)
        except Exception as e:
            self.raw_data_text.setText(f"Error formatting data: {str(e)}")

    def update_raw_data(self):
        """Update the raw data display"""
        self.update_raw_data_format()  # This will update based on current format settings

    def refresh_results(self):
        """Refresh the results display"""
        self.logger.debug("Refreshing results display")

        # Re-apply current results to update all views
        if self.current_results:
            self.update_results(self.current_results)

    def export_results(self):
        """Export results to a file"""
        if not self.current_results:
            QMessageBox.warning(self, "No Results", "There are no results to export.")
            return

        # Ask for file format
        format_type = self.format_combo.currentText()

        # Get file extension based on format
        if format_type == "JSON":
            file_filter = "JSON Files (*.json);;All Files (*)"
            default_ext = ".json"
        elif format_type == "YAML":
            file_filter = "YAML Files (*.yaml *.yml);;All Files (*)"
            default_ext = ".yaml"
        else:  # Text
            file_filter = "Text Files (*.txt);;All Files (*)"
            default_ext = ".txt"

        # Open file dialog
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "Export Results", f"results{default_ext}", file_filter)

        if file_path:
            try:
                # Ensure file has correct extension
                if not file_path.endswith(default_ext):
                    file_path += default_ext

                # Write results to file
                with open(file_path, "w") as f:
                    if format_type == "JSON":
                        pretty = self.pretty_print.isChecked()
                        if pretty:
                            json.dump(self.current_results, f, indent=2)
                        else:
                            json.dump(self.current_results, f)
                    elif format_type == "YAML":
                        yaml.safe_dump(self.current_results, f, default_flow_style=not self.pretty_print.isChecked())
                    else:  # Text
                        f.write(str(self.current_results))

                QMessageBox.information(self, "Export Successful", f"Results exported successfully to {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to export results: {str(e)}")
