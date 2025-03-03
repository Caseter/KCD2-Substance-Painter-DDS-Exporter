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
import substance_painter.ui
import substance_painter.event

def get_substance_painter_python():
    """Finds the correct Substance Painter Python executable."""
    correct_python = r"C:\\Program Files\\Adobe\\Adobe Substance 3D Painter\\resources\\pythonsdk\\python.exe"
    
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

def get_rc_exe_path():
    """Retrieves or sets the path to CryEngine's rc.exe in a settings INI file."""
    ini_path = os.path.join(os.path.dirname(__file__), "KCD2-DDS-Exporter-PluginSettings.ini")
    config = configparser.ConfigParser()
    
    if os.path.exists(ini_path):
        config.read(ini_path)
        if "General" in config and "rc_exe_path" in config["General"]:
            return config["General"]["rc_exe_path"]
    
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    
    file_dialog = QtWidgets.QFileDialog()
    file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
    file_dialog.setNameFilter("Executable Files (*.exe)")
    file_dialog.setWindowTitle("Select CryEngine rc.exe Path")
    
    if file_dialog.exec_():
        rc_path = file_dialog.selectedFiles()[0]
        config["General"] = {"rc_exe_path": rc_path}
        with open(ini_path, "w") as configfile:
            config.write(configfile)
        return rc_path
    
    print("Error: No rc.exe path provided. Plugin cannot proceed.")
    return None

def process_texture_export(rc_path, source_tif):
    """Processes Substance Painter export to convert different texture types to DDS for CryEngine."""
    if not rc_path:
        print("Error: No valid rc.exe path found.")
        return
    
    texture_type = None
    for key in ["ddna", "diff", "spec", "id", "bgs"]:
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
    try:
        preset_mapping = {
            "ddna": "NormalsWithSmoothness",
            "diff": "Diffuse",
            "spec": "Specular",
            "id": "IDMap",
            "bgs": "Background"
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
        self.version = "0.1.1"
        self.log = QtWidgets.QTextEdit()
        self.window = QtWidgets.QWidget()
        self.rc_exe_path = get_rc_exe_path()
        
        layout = QtWidgets.QVBoxLayout()
        self.log.setReadOnly(True)
        self.window.setLayout(layout)
        self.window.setWindowTitle("KCD2 DDS Auto Converter")
        
        substance_painter.ui.add_dock_widget(self.window)
        self.log.append("RC Path: {}".format(self.rc_exe_path))
        
        connections = {
            substance_painter.event.ExportTexturesEnded: self.on_export_finished
        }
        for event, callback in connections.items():
            substance_painter.event.DISPATCHER.connect(event, callback)
    
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
    print("KCD2 DDS Exporter Plugin Initialized")
    global KCD2_DDS_PLUGIN
    KCD2_DDS_PLUGIN = KCD2DDSPlugin()

def close_plugin():
    print("KCD2 DDS Exporter Plugin Shutdown")
    global KCD2_DDS_PLUGIN
    del KCD2_DDS_PLUGIN

if __name__ == "__main__":
    start_plugin()
