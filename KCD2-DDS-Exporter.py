__author__ = "Emil Eldstål - Modified for KCD2 by Casey"
__copyright__ = "Copyright 2023, Emil Eldstål - Modified for KCD2 by Casey"
__version__ = "0.1.1"

import os
import sys
import subprocess
import importlib
import importlib.util
import configparser
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
import substance_painter

def get_substance_painter_python():
    """Finds the correct Substance Painter Python executable."""
    substanceexe_path = sys.executable
    trimmed_path = os.path.dirname(substanceexe_path)

    correct_python = os.path.join(trimmed_path, "resources", "pythonsdk", "python.exe")
    
    if os.path.exists(correct_python):
        print(f"Using Substance Painter Python: {correct_python}")
        return correct_python
    else:
        print("Error: Could not find Substance Painter's Python. Using system Python.")
        return sys.executable  # Fallback

PYTHON_EXE = get_substance_painter_python()

# Ensure Substance Painter's Python has its site-packages in sys.path
python_lib_path = os.path.join(os.path.dirname(PYTHON_EXE), "lib", "site-packages")
if python_lib_path not in sys.path:
    sys.path.append(python_lib_path)
    print(f"Added {python_lib_path} to sys.path")

def is_package_installed(package_name):
    """Check if a package is installed without importing it."""
    try:
        import pkg_resources
        pkg_resources.get_distribution(package_name)
        return True
    except (ImportError, pkg_resources.DistributionNotFound):
        return False

def ensure_dependency_installed(package_name):
    """Ensures a Python package is installed in the Substance Painter environment."""
    if is_package_installed(package_name):
        print(f"{package_name} is already installed.")
    else:
        print(f"{package_name} not found. Installing...")
        result = subprocess.run(
            [PYTHON_EXE, "-m", "pip", "install", package_name], 
            check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print("STDOUT:\n", result.stdout.decode())
        print("STDERR:\n", result.stderr.decode())
        
        if result.returncode == 0:
            print(f"{package_name} installed successfully.")
        else:
            print(f"Failed to install {package_name}.")


# Ensure required dependencies are installed
ensure_dependency_installed("imageio")
ensure_dependency_installed("Pillow")  # Correct capitalization

# Import packages after ensuring installation
import imageio.v3 as iio
from PIL import Image

def get_rc_exe_path(overwrite=False):
    """Retrieves or sets the path to CryEngine's rc.exe in a settings INI file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ini_file_path = os.path.join(script_dir, "KCD2-DDS-Exporter-PluginSettings.ini")
    
    config = configparser.ConfigParser()

    if os.path.exists(ini_file_path):
        config.read(ini_file_path)
        
        if 'General' in config and 'rc_exe_path' in config['General']:
            if not config['General']['rc_exe_path'] or overwrite:
                new_path = choose_rc_folder()
                if new_path:  # Ensure a valid path was selected
                    config['General']['rc_exe_path'] = new_path
            rc_exe_path = config['General']['rc_exe_path']
        else:
            new_path = choose_rc_folder()
            if new_path:  # Ensure a valid path was selected
                config['General'] = {}
                config['General']['rc_exe_path'] = new_path
            rc_exe_path = config['General'].get('rc_exe_path', None)
    
        with open(ini_file_path, 'w') as configfile:
            config.write(configfile)
    else:
        new_path = choose_rc_folder()
        if new_path:  # Ensure a valid path was selected
            with open(ini_file_path, 'w') as configfile:
                config['General'] = {}
                config['General']['rc_exe_path'] = new_path
                config.write(configfile)
        rc_exe_path = new_path if new_path else None
    
    return rc_exe_path

def choose_rc_folder():
    path = QtWidgets.QFileDialog.getExistingDirectory(
        substance_painter.ui.get_main_window(), "Choose RC directory")
    if not path:  # Ensure canceling doesn't return 'rc.exe'
        return None
    return path.replace('\\', '/') + '/rc.exe'

def process_texture_export(rc_path, source_tif):
    """Processes Substance Painter export to convert different texture types to DDS for CryEngine."""
    if not rc_path:
        print("Error: No valid rc.exe path found.")
        return
    
    texture_type = None
    for key in ["ddna", "diff", "spec", "id", "bgs","mask"]:
        if key in source_tif:
            texture_type = key
            break

    if not texture_type:
        print(f"Warning: Could not determine texture type for {source_tif}. Using default conversion.")
        texture_type = "default"
    
    output_dds = source_tif.replace(".tif", ".dds")
    
    convert_tif_to_dds_with_rc(rc_path, source_tif, output_dds, texture_type)

def convert_tif_to_dds_with_rc(rc_path, source_tif, output_dds, texture_type):
    """Converts a TIF to DDS using CryEngine's Resource Compiler (rc.exe) with correct presets."""

    config = configparser.ConfigParser()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ini_file_path = os.path.join(script_dir, "KCD2-DDS-Exporter-PluginSettings.ini")
    config.read(ini_file_path)
    selected_diff = config.get("General", "diff_type", fallback="Alpha")

    try:
        preset_mapping = {
            "ddna": "NormalsWithSmoothness",
            "diff": "AlbedoWithOpacity" if selected_diff == "Alpha" else "Albedo",
            "spec": "Reflectance",
            "id": "IDMask",
            "bgs": "BloodGrimeScratchMask",
            "weapon_mask": "Atlas_Mask"
        }
        
        preset = preset_mapping.get(texture_type, "Default")

        rc_cmd = [
            rc_path.replace("\\", "/"),  # Ensure forward slashes
            source_tif.replace("\\", "/"),
            f"-preset={preset}",
            "-o", output_dds
        ]

        subprocess.run(rc_cmd, shell=True, check=True)
        print(f"DDS successfully created with CryEngine RC: {output_dds} using preset: {preset}")
    except subprocess.CalledProcessError as e:
        print(f"Error converting TIF to DDS using CryEngine RC: {e}")

class KCD2DDSPlugin:
    def __init__(self):
        self.export = True
        self.overwrite = True
        self.version = "1.0.1"
        self.window = QtWidgets.QWidget()
        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)
        self.rc_exe_path = get_rc_exe_path()

        # Load settings from INI file
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.ini_file_path = os.path.join(self.script_dir, "KCD2-DDS-Exporter-PluginSettings.ini")
        self.config = configparser.ConfigParser()
        self.config.read(self.ini_file_path)
        
        # Get saved dropdown value or default to alpha
        saved_diff_type = self.config.get("General", "diff_type", fallback="Alpha")
        
        # Create main layout
        main_layout = QtWidgets.QVBoxLayout()

        # Create top section with dropdown and buttons
        top_layout = QtWidgets.QHBoxLayout()
        top_layout.setSpacing(2)

        # Create label and dropdown
        label = QtWidgets.QLabel("Diffuse Type:")
        label.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        self.diff_dropdown = QtWidgets.QComboBox()
        saved_diff_type = self.config.get("General", "diff_type", fallback="Alpha")
        self.diff_dropdown.setCurrentText(saved_diff_type)  # Set saved value
        self.diff_dropdown.addItems(['Alpha', 'No Alpha'])
        self.diff_dropdown.setCurrentText(saved_diff_type)  # Set saved value
        
        # Create buttons
        button_rc = QtWidgets.QPushButton("Choose RC Location")
        button_clear = QtWidgets.QPushButton("Clear Log")
        
        # Add widgets to the top layout
        top_layout.addWidget(label)
        top_layout.addWidget(self.diff_dropdown)
        top_layout.addStretch(1)  # Pushes buttons to the right
        top_layout.addWidget(button_rc)
        top_layout.addWidget(button_clear)
        
        # Create bottom section for log and version label
        bottom_layout = QtWidgets.QVBoxLayout()
        version_label = QtWidgets.QLabel(f"Version: {self.version}")
        
        # Add widgets to bottom layout
        bottom_layout.addWidget(self.log)
        bottom_layout.addWidget(version_label)

        # Add all layouts to the main layout
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)

        self.window.setLayout(main_layout)
        self.window.setWindowTitle("KCD2 DDS Auto Converter")

        # Connects buttons to click events
        self.diff_dropdown.currentIndexChanged.connect(self.diff_changed)
        button_rc.clicked.connect(self.button_rc_clicked)
        button_clear.clicked.connect(self.button_clear_clicked)

        # Adds Qt as dockable widget to Substance Painter
        substance_painter.ui.add_dock_widget(self.window)
        self.log.append(f"RC Path: {self.rc_exe_path}")
        
        connections = {
            substance_painter.event.ExportTexturesEnded: self.on_export_finished
        }
        for event, callback in connections.items():
            substance_painter.event.DISPATCHER.connect(event, callback)

    def button_rc_clicked(self):
        self.rc_exe_path = get_rc_exe_path(True)
        self.log.append("New Resourse Compiler Path: {}".format(self.rc_exe_path))

    def diff_changed(self):
        selected_diff = self.diff_dropdown.currentText()
        self.log.append(f"New diff type selected: {selected_diff}")
        
        # Save selection to INI file
        self.config.read(self.ini_file_path)
        if "General" not in self.config:
            self.config["General"] = {}
        self.config["General"]["diff_type"] = selected_diff
        with open(self.ini_file_path, "w") as configfile:
            self.config.write(configfile)

    def button_clear_clicked(self):
        self.log.clear()
    
    def on_export_finished(self, res):
        if self.export:
            self.log.append(res.message)
            for file_list in res.textures.values():
                for file_path in file_list:
                    output_dds = file_path.replace(".tif", ".dds")
                    process_texture_export(self.rc_exe_path, file_path)
                    self.log.append("  DDS File Generated: {}".format(output_dds))

KCD2_DDS_PLUGIN = None

def start_plugin():
    global KCD2_DDS_PLUGIN
    if KCD2_DDS_PLUGIN is not None:
        print("KCD2 DDS Exporter Plugin is already initialized! Skipping re-initialization.")
        return  # Prevent duplicate initialization
    
    print("KCD2 DDS Exporter Plugin Initialized")
    KCD2_DDS_PLUGIN = KCD2DDSPlugin()

def close_plugin():
    print("KCD2 DDS Exporter Plugin Shutdown")
    global KCD2_DDS_PLUGIN
    del KCD2_DDS_PLUGIN

if __name__ == "__main__":
    start_plugin()
