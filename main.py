import sys
import multiprocessing
import yaml
import configparser
from configupdater import ConfigUpdater
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, 
    QPushButton, QHBoxLayout, QFormLayout, QLabel, QLineEdit, 
    QCheckBox, QFileDialog, QMessageBox, QSpinBox, QComboBox, 
    QGroupBox, QDialog, QTextBrowser, QScrollArea, QFrame, 
    QProgressBar, QTextEdit, QToolButton, QTableWidget, 
    QTableWidgetItem, QAbstractItemView, QSplashScreen, 
    QFileDialog
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QProcess, QTimer, QRect, QMargins, QSettings
from PyQt5.QtGui import QDoubleValidator, QIcon, QFont, QPixmap, QTextCursor, QPainter, QColor
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis

from datetime import datetime

import qdarktheme
import markdown
import re
import urllib.parse
import urllib.request
import base64

# --- FILE PATHS ---
GUI_DEF_FILE = "gui_def.yaml"

# 1. Figure out where main.py currently lives
current_dir = os.path.dirname(os.path.abspath(__file__))
# 2. Look for the bundled model next to it
bundled_sphy_path = os.path.join(current_dir, 'sphy_model', 'sphy.py')

# 3. Dynamically choose the path based on the environment!
if os.path.exists(bundled_sphy_path):
    # If the folder exists, we are running inside the portable deployed app
    SPHY_SCRIPT_PATH = bundled_sphy_path
else:
    # If it doesn't exist, we are in your dev environment! Use the G: drive.
    SPHY_SCRIPT_PATH = r"g:\Otros ordenadores\Mi PC\versions\SPHY-github\sphy.py"
    # SPHY_SCRIPT_PATH = r"c:\research\versions\SPHY-github\sphy.py"


if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Tell the code exactly where the YAML file is
GUI_DEF_FILE = os.path.join(BASE_DIR, "gui_def.yaml")

def get_resource_path(relative_path):
    """Converts a relative path to an absolute path for PyInstaller."""
    # This handles both Windows (\) and Mac/Linux (/) slashes automatically
    return os.path.join(BASE_DIR, os.path.normpath(relative_path))

# CRITICAL: Enable High DPI Scaling (The Modern Way)
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

# FIX: Prevent 150% scaling from rounding up to 200% (The "Bloated" Look)
# This requires PyQt 5.14+
if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
    # We set this environment variable because calling the method directly 
    # needs a QApplication instance or specific import logic.
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

# 1. DATA LOADER
def load_gui_definition(filepath):
    """Reads the hierarchical YAML file and returns the 'tabs' dictionary."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        if 'tabs' not in data:
            raise ValueError("YAML file missing 'tabs' key")
        return data['tabs']
    except Exception as e:
        print(f"Error loading GUI definition: {e}")
        return None

# 2. BASE COMPOUND WIDGET (Abstract Base Class)
class _BaseRelativePathWidget(QWidget):
    def __init__(self, initial_value, get_inputdir_callback):
        super().__init__()
        self._folder = "" 
        self._component = "" 
        self._get_inputdir = get_inputdir_callback
        
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setContentsMargins(0, 0, 0, 0)

        self.display_edit = QLineEdit(initial_value)
        self.display_edit.setReadOnly(True) 
        self.h_layout.addWidget(self.display_edit)

        self.browse_btn = QPushButton("Sample File")
        self.browse_btn.setFixedWidth(100)
        self.browse_btn.clicked.connect(self._select_file_and_extract)
        self.h_layout.addWidget(self.browse_btn)

        self.set_value(initial_value) 

    def _select_file_and_extract(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("All Files (*)") 
        
        if dialog.exec():
            selected_file = dialog.selectedFiles()[0]
            inputdir_path = self._get_inputdir()
            full_folder_path = os.path.dirname(selected_file)
            
            try:
                new_folder = os.path.relpath(full_folder_path, inputdir_path)
                if new_folder == '.':
                    new_folder = ''
            except ValueError as e:
                new_folder = os.path.basename(full_folder_path.rstrip(os.path.sep))
                print(f"Warning: Failed to calculate relative path. Using folder name: {new_folder}. Error: {e}")

            new_component = self._extract_component_from_file(selected_file)
            self._folder = new_folder
            self._component = new_component
            self.display_edit.setText(self.get_value()) 

    def get_value(self):
        folder_clean = self._folder.strip('/').strip('\\') 
        component_clean = self._component.strip('/').strip('\\')
        if not folder_clean or folder_clean == '.':
            return component_clean
        return f"{folder_clean.replace(os.path.sep, '/')}/{component_clean}"

    def set_value(self, combined_path_str):
        if not combined_path_str or '/' not in combined_path_str:
            self._folder = ""
            self._component = combined_path_str
            self.display_edit.setText(combined_path_str)
            return
        last_slash = combined_path_str.rfind('/')
        self._folder = combined_path_str[:last_slash].strip()
        self._component = combined_path_str[last_slash + 1:].strip()
        self.display_edit.setText(combined_path_str)

    def _extract_component_from_file(self, selected_file):
        raise NotImplementedError("Subclass must implement _extract_component_from_file()")

class CombinedPathWidget(_BaseRelativePathWidget):
    def _extract_component_from_file(self, selected_file):
        file_name_with_ext = os.path.basename(selected_file)
        file_base, file_ext = os.path.splitext(file_name_with_ext)
        if len(file_base) >= 4:
            return file_base[:4]
        else:
            return file_base

class FileInputWidget(QWidget):
    # Added on_edit_callback parameter
    def __init__(self, initial_value, get_inputdir_callback, path_style, file_mode, extension_filter="*", on_edit_callback=None):
        super().__init__()
        self.path_style = path_style.lower() 
        self.file_mode = file_mode           
        self.extension_filter = extension_filter
        self._get_inputdir = get_inputdir_callback
        
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setContentsMargins(0, 0, 0, 0) 
        
        self.line_edit = QLineEdit(initial_value)
        self.h_layout.addWidget(self.line_edit)
        
        # --- NEW: Add "Edit Table" button for .tbl files ---
        if ("*.tbl" in self.extension_filter or "*.csv" in self.extension_filter) and on_edit_callback:
            self.edit_btn = QPushButton("Edit Table")
            self.edit_btn.setCursor(Qt.PointingHandCursor)
            # Pass the current text from line_edit to the callback
            self.edit_btn.clicked.connect(lambda: on_edit_callback(self.line_edit.text()))
            self.h_layout.addWidget(self.edit_btn)
        # ---------------------------------------------------

        button_text = "Browse" 
        if self.file_mode == "Directory":
            button_text = "Select Folder"
        elif self.file_mode == "ExistingFile":
            button_text = "Select File"
        self.browse_btn = QPushButton(button_text)
        self.browse_btn.setFixedWidth(100)
        self.browse_btn.clicked.connect(self._select_path)
        self.h_layout.addWidget(self.browse_btn)

    # ... (Keep the rest of the methods: _get_qfiledialog_mode, get_value, _select_path exactly as they were) ...
    def _get_qfiledialog_mode(self):
        if self.file_mode == "Directory":
            return QFileDialog.FileMode.Directory
        return QFileDialog.FileMode.ExistingFile

    def get_value(self):
        current_path = self.line_edit.text().strip()
        if not current_path:
            return ""
        
        # Standardize separators to forward slashes
        current_path = current_path.replace('\\', '/')
        
        final_path = current_path

        # 1. Full Path Mode
        if self.path_style == 'full':
            final_path = os.path.abspath(current_path).replace('\\', '/')

        # 2. Relative Path Logic
        # If it is already relative (e.g. just "precip.nc"), keep it as is.
        elif not os.path.isabs(current_path):
            final_path = current_path
            
        # 3. Convert Absolute -> Relative (only if necessary)
        else:
            inputdir = self._get_inputdir()
            try:
                abs_input_dir = os.path.abspath(inputdir)
                relative_path = os.path.relpath(current_path, abs_input_dir)
                final_path = relative_path.replace('\\', '/')
            except ValueError:
                # Fallback for different drives
                final_path = current_path

        # --- CRITICAL FIX: Force trailing slash for Directory variables ---
        # This ensures inputdir and outputdir always end with "/" in the config file
        if self.file_mode == 'Directory' and final_path and not final_path.endswith('/'):
            final_path += '/'
            
        return final_path
    
    def _select_path(self):
        mode = self._get_qfiledialog_mode()
        filter_str = self.extension_filter
        dialog = QFileDialog()
        dialog.setFileMode(mode)
        if mode != QFileDialog.FileMode.Directory:
            dialog.setNameFilter(filter_str)
        if dialog.exec():
            selected_path_abs = dialog.selectedFiles()[0]
            if self.path_style == 'full':
                display_path = selected_path_abs.replace(os.path.sep, '/')
            else: 
                inputdir = self._get_inputdir()
                try:
                    display_path = os.path.relpath(selected_path_abs, inputdir)
                    display_path = display_path.replace(os.path.sep, '/')
                except ValueError:
                    display_path = selected_path_abs.replace(os.path.sep, '/')
            self.line_edit.setText(display_path)
            
class FileControlPanel(QWidget):
    def __init__(self, parent_editor):
        super().__init__()
        self.editor = parent_editor 
        
        # 1. Main Vertical Layout (Label on top, buttons on bottom)
        self.v_layout = QVBoxLayout(self)
        self.v_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add the label to the top row
        self.v_layout.addWidget(QLabel("Config File (*.cfg):"))
        
        # 2. Horizontal Layout for the input and all buttons
        self.h_input_layout = QHBoxLayout()
        
        # --- Config Line Edit ---
        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        self.line_edit.textChanged.connect(self._update_path)
        self.h_input_layout.addWidget(self.line_edit)

        # --- Browse Button ---
        self.browse_btn = QPushButton("Select File")
        self.browse_btn.setFixedHeight(28) # Match the height of the save buttons
        self.browse_btn.clicked.connect(self._open_browser)
        self.h_input_layout.addWidget(self.browse_btn)

        # --- Save Button ---
        custom_icon_save = QIcon(get_resource_path('icons/save_24dp_1F1F1F_FILL0_wght400_GRAD0_opsz24.svg'))
        self.save_btn = QPushButton("Save Config  ")
        self.save_btn.setIcon(custom_icon_save)
        self.save_btn.setFixedHeight(28)
        self.save_btn.setLayoutDirection(Qt.RightToLeft)
        # Notice we call self.editor.save_config because the function lives in the main window!
        self.save_btn.clicked.connect(self.editor.save_config) 
        self.h_input_layout.addWidget(self.save_btn)

        # --- Save As Button ---
        custom_icon_save_as = QIcon(get_resource_path('icons/save_as_24dp_1F1F1F_FILL0_wght400_GRAD0_opsz24.svg'))
        self.save_as_btn = QPushButton("Save Config As  ")
        self.save_as_btn.setIcon(custom_icon_save_as)
        self.save_as_btn.setFixedHeight(28)
        self.save_as_btn.setLayoutDirection(Qt.RightToLeft)
        self.save_as_btn.clicked.connect(self.editor.save_config_as)
        self.h_input_layout.addWidget(self.save_as_btn)

        # 3. Add the horizontal row to the main vertical layout
        self.v_layout.addLayout(self.h_input_layout)

        self.config_path = ""
        self.script_path = SPHY_SCRIPT_PATH
        
    def _open_browser(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("Config Files (*.cfg)")
        if dialog.exec():
            selected_file = dialog.selectedFiles()[0]
            selected_file = os.path.normpath(selected_file).replace(os.path.sep, '/')
            self.line_edit.setText(selected_file)
            self.editor.load_config(selected_file) # Tell the main window to load it

    def _update_path(self, path):
        self.config_path = path
        
    def get_config_path(self):
        return self.config_path

    def get_script_path(self):
        return self.script_path
        
class DateInputWidget(QWidget):
    def __init__(self, default_values, names):
        super().__init__()
        self.names = names 
        self.default_values = [int(v) for v in default_values] if default_values else [2023, 1, 1]
        
        h_layout = QHBoxLayout(self)
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        h_layout.addWidget(QLabel("Y:"))
        self.year_edit = IntegerInputWidget(
            default_value=self.default_values[0], min_val=1900, max_val=2100
        )
        h_layout.addWidget(self.year_edit)

        h_layout.addWidget(QLabel("M:"))
        self.month_edit = IntegerInputWidget(
            default_value=self.default_values[1], min_val=1, max_val=12
        )
        h_layout.addWidget(self.month_edit)

        h_layout.addWidget(QLabel("D:"))
        self.day_edit = IntegerInputWidget(
            default_value=self.default_values[2], min_val=1, max_val=31
        )
        h_layout.addWidget(self.day_edit)
        h_layout.addStretch(1)

    def get_values(self):
        return {
            self.names['year_name']: self.year_edit.get_value(),
            self.names['month_name']: self.month_edit.get_value(),
            self.names['day_name']: self.day_edit.get_value()
        }

    def set_values(self, values):
        self.year_edit.set_value(values.get(self.names['year_name'], self.default_values[0]))
        self.month_edit.set_value(values.get(self.names['month_name'], self.default_values[1]))
        self.day_edit.set_value(values.get(self.names['day_name'], self.default_values[2]))

class IntegerInputWidget(QSpinBox):
    def __init__(self, default_value, min_val=-2147483647, max_val=2147483647):
        super().__init__()
        self.setRange(min_val, max_val)
        self.setValue(default_value)
        self.setFixedWidth(70)

    def get_value(self):
        return self.value()

    def set_value(self, value):
        if isinstance(value, str) and value.isdigit():
            value = int(value)
        if isinstance(value, int):
            self.setValue(value)

class SelectionInputWidget(QComboBox):
    selection_changed = pyqtSignal(str) 

    def __init__(self, options, default_value, parent=None):
        super().__init__(parent)
        
        # 1. Populate the ComboBox
        if isinstance(options, list):
            for opt in options:
                # Check for New Style: {'label': 'Name', 'value': 1}
                if isinstance(opt, dict) and 'label' in opt and 'value' in opt:
                    self.addItem(str(opt['label']), opt['value'])
                
                # Fallback for Old Style: Simple list [1, 2, "A"]
                else:
                    self.addItem(str(opt), opt)
        
        # 2. Connect changes to the signal
        self.currentIndexChanged.connect(self._emit_selection_change)
        
        # 3. Set the initial value
        self.set_value(default_value)

    def _emit_selection_change(self, index):
        if index < 0: return
        val = self.itemData(index)
        self.selection_changed.emit(str(val))

    def get_value(self):
        return self.currentData()

    def set_value(self, value):
        # Search for the item that holds this specific DATA/VALUE
        target_val_str = str(value).strip()
        
        for i in range(self.count()):
            item_data = self.itemData(i)
            # Compare as strings to ensure int(1) matches str("1")
            if str(item_data) == target_val_str:
                self.setCurrentIndex(i)
                return
        
        # Fallback: Try matching by text label (for backward compatibility)
        index = self.findText(target_val_str)
        if index >= 0:
            self.setCurrentIndex(index)
        else:
            # Build diagnostic info showing visible labels and underlying values
            items_info = [
                f"'{self.itemText(i)}' (data: {self.itemData(i)})" 
                for i in range(self.count())
            ]
            print(f"Warning: Could not find option with value '{value}'. Available options in this dropdown: {items_info}")
                       
class CompositeInputWidget(QWidget):
    def __init__(self, components_def, initial_value, parent_editor, max_label_width=0):
        super().__init__()
        self.components_def = components_def
        self.component_widgets = []
        self.editor = parent_editor 
        self.max_label_width = max_label_width 
        
        self.v_layout = QVBoxLayout(self)
        self.v_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout = QFormLayout()
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.setVerticalSpacing(0)
        self.form_layout.setLabelAlignment(Qt.AlignLeft) 
        self.v_layout.addLayout(self.form_layout)
        
        for i, component_param in enumerate(self.components_def):
            component_widget = _create_widget_for_param(component_param, self.editor, max_label_width=0) 
            label_text = component_param.get('label', component_param['name'])
            component_label = QLabel(label_text)
            if self.max_label_width > 0:
                component_label.setMinimumWidth(self.max_label_width) 
                component_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            else:
                 component_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            self.form_layout.addRow(component_label, component_widget)
            self.component_widgets.append(component_widget)
            
            if i < len(self.components_def) - 1: 
                component_spacer = QWidget()
                component_spacer.setFixedHeight(6) 
                self.form_layout.addRow(component_spacer)

        self.v_layout.addStretch(1)
        self.set_value(initial_value)
        
    def get_value(self):
        values = []
        for i, widget in enumerate(self.component_widgets):
            param_type = self.components_def[i]['type']
            if param_type == 'selection':
                value = widget.get_value()
            elif param_type == 'integer_input':
                value = str(widget.get_value())
            elif param_type == 'scalar' or param_type == 'text_input':
                value = widget.text() 
            elif hasattr(widget, 'get_value'): 
                value = widget.get_value()
            else:
                value = "" 
            values.append(str(value))
        return ",".join(values)

    def set_value(self, combined_str):
        if not combined_str or not isinstance(combined_str, str):
            return 
        values = [v.strip() for v in combined_str.split(',')]
        for i, widget in enumerate(self.component_widgets):
            if i < len(values):
                value = values[i]
                param_type = self.components_def[i]['type']
                try:
                    if param_type in ['selection', 'integer_input']:
                        widget.set_value(value)
                    elif param_type in ['scalar', 'text_input']: 
                        widget.setText(value)
                    elif hasattr(widget, 'set_value'):
                        widget.set_value(value)
                except Exception as e:
                    print(f"Error setting value '{value}' for component {i} ({param_type}): {e}")

class TextInputWidget(QLineEdit):
    def __init__(self, initial_value=""):
        super().__init__(initial_value)
    def get_value(self):
        return self.text()
    def set_value(self, value):
        self.setText(str(value))

# 3. WIDGET CREATION HELPER
def _create_widget_for_param(param, parent_window, max_label_width=0):
    param_type = param['type']
    WIDGET_MAPPING = {"combined_path": CombinedPathWidget}
    
    if param_type == "composite_input":
        widget = CompositeInputWidget(
            components_def=param.get('components', []),
            initial_value=param.get('default', ''),
            parent_editor=parent_window,
            max_label_width=max_label_width 
        )
    elif param_type == "text_input":
        widget = TextInputWidget(str(param.get('default', '')))
    elif param_type == "selection":
        widget = SelectionInputWidget(
            options=param.get('options', []),
            default_value=param.get('default', '')
        )
    elif param_type == "date_input":
        widget = DateInputWidget(
            default_values=param.get('default'),
            names=param.get('params') 
        )
    elif param_type == "integer_input":
        widget = IntegerInputWidget(
            default_value=int(param.get('default', 0)),
            min_val=param.get('min', -2147483647),
            max_val=2147483647
        )
    elif param_type == "scalar":
        widget = QLineEdit(str(param.get('default', '0.0')))
        validator = QDoubleValidator()
        widget.setValidator(validator)
    elif param_type == "file_input":
        widget = FileInputWidget(
            initial_value=param.get('default', ''),
            get_inputdir_callback=parent_window.get_inputdir_value,
            path_style=param.get('path_style', 'relative'),
            file_mode=param.get('file_mode', 'ExistingFile'),
            extension_filter=param.get('extension', 'All Files (*)'),
            # --- NEW: Pass the callback from the parent window ---
            on_edit_callback=getattr(parent_window, 'open_table_from_ui', None)
        )
    elif param_type in WIDGET_MAPPING:
        WidgetClass = WIDGET_MAPPING[param_type]
        widget = WidgetClass(param.get('default', ''), parent_window.get_inputdir_value)
        widget.setProperty("config_key_name", param['name'])
    elif param_type == "flag":
        widget = QCheckBox()
        widget.setChecked(param.get('default', False))
    else:
        widget = QLineEdit(f"UNKNOWN TYPE: {param_type}")
        
    if 'name' in param:
        widget.setProperty("param_name", param['name'])
    if 'section' in param:
        widget.setProperty("param_section", param['section'])
        
    widget.setProperty("param_type", param_type)
    return widget

# 4. HELP VIEWER DIALOG
class HelpDialog(QDialog):
    def __init__(self, title, markdown_file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Help: {title}")
        self.resize(750, 600)
        
        main_layout = QVBoxLayout(self)
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setStyleSheet("font-size: 14px; font-family: 'Segoe UI', sans-serif;")
        main_layout.addWidget(self.text_browser)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        main_layout.addWidget(close_button)
        
        self._load_markdown(markdown_file_path)

    def _render_math_to_img_tag(self, math_str, is_inline=True):
        """
        Uses the free CodeCogs API to render LaTeX to a transparent PNG.
        Zero local dependencies required.
        """
        # URL-encode the math string so it's safe for web requests
        encoded_math = urllib.parse.quote(math_str.strip())
        
        # \dpi{120} scales the image nicely for desktop screens
        url = f"https://latex.codecogs.com/png.latex?\\dpi{{120}}{encoded_math}"
        
        # Adjust height: inline math matches text height, block math sits naturally
        height = "1.8em" if is_inline else "auto"
        style = f"vertical-align:middle; height: {height};" if is_inline else "display:block; margin: 10px auto;"
        
        return f'<img src="{url}" style="{style}" />'

    def _load_markdown(self, file_path):
        if not os.path.exists(file_path):
            self.text_browser.setHtml(f"<h1>Error</h1><p>File not found: {file_path}</p>")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Separate replacers so we know if it's block ($$) or inline ($)
        def replacer_block(match):
            return self._render_math_to_img_tag(match.group(1), is_inline=False)

        def replacer_inline(match):
            return self._render_math_to_img_tag(match.group(1), is_inline=True)

        # Regex for $$...$$ and $...$
        text = re.sub(r'\$\$(.*?)\$\$', replacer_block, text, flags=re.DOTALL)
        text = re.sub(r'(?<!\$)\$(.+?)\$(?!\$)', replacer_inline, text)

        html = markdown.markdown(text, extensions=['extra'])
        
        full_html = f"""
        <html>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; font-size: 14px; line-height: 1.6; padding: 15px; }}
            h1, h2 {{ color: #2c3e50; border-bottom: 1px solid #ddd; }}
            code {{ background-color: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
        </style>
        <body>
            {html}
        </body>
        </html>
        """
        self.text_browser.setHtml(full_html)

# 4. TABLE EDITOR WIDGET
class TableEditorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file_path = None
        
        # --- LAYOUT ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Toolbar (Open / Save / Status)
        toolbar_layout = QHBoxLayout()
        
        self.btn_open = QPushButton("Open Table...")
        self.btn_open.setCursor(Qt.PointingHandCursor)
        self.btn_open.clicked.connect(self.open_file_dialog)
        
        self.btn_save = QPushButton("Save Changes")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self.save_file)
        self.btn_save.setEnabled(False) # Disabled until file loaded
        
        self.lbl_filename = QLabel("No file loaded")
        self.lbl_filename.setStyleSheet("color: #808080; font-style: italic; margin-left: 10px;")
        
        toolbar_layout.addWidget(self.btn_open)
        toolbar_layout.addWidget(self.btn_save)
        toolbar_layout.addWidget(self.lbl_filename)
        toolbar_layout.addStretch() # Push buttons to left
        
        # 2. The Table Grid
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        # Style the grid to look clean
        # self.table.setStyleSheet("""
        #     QTableWidget { border: none; gridline-color: #D0D0D0; }
        #     QHeaderView::section { background-color: #E0E0E0; border: 1px solid #C0C0C0; padding: 4px; }
        # """)

        # A. Disable Multi-Selection (Only one cell at a time)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # B. Enable Single-Click Editing
        # 'AllEditTriggers' allows editing on single click, key press, etc.
        self.table.setEditTriggers(QAbstractItemView.AllEditTriggers)

        # --- HIDE HEADERS (The Fix) ---
        self.table.verticalHeader().setVisible(False)   # Hides Row Numbers
        self.table.horizontalHeader().setVisible(False) # Hides Column Numbers
        
        # # Optional: Make the grid stretch to fill the space
        # self.table.horizontalHeader().setStretchLastSection(True) 

        layout.addLayout(toolbar_layout)
        layout.addWidget(self.table)

    def open_file_dialog(self):
        # Open file picker starting in current directory
        path, _ = QFileDialog.getOpenFileName(self, "Open Table File", "", "Table Files (*.tbl *.csv);;All Files (*)")
        if path:
            self.load_table(path)

    def load_table(self, file_path):
        try:
            self.current_file_path = file_path
            
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
            if not lines:
                return

            # 1. Parse Data (Modified to handle CSV)
            # Check if file is CSV
            if file_path.lower().endswith('.csv'):
                # Split by comma for CSV files
                data = [line.strip().split(',') for line in lines if line.strip()]
            else:
                # Split by whitespace (tabs/spaces) for .tbl and others
                data = [line.strip().split() for line in lines if line.strip()]
            
            if not data:
                return

            rows = len(data)
            cols = max(len(row) for row in data) # Handle ragged rows safely

            # 2. Setup Table
            self.table.setRowCount(rows)
            self.table.setColumnCount(cols)
            
            # Disable headers (using simple 1,2,3...)
            # self.table.horizontalHeader().setVisible(False) 
            
            # 3. Fill Data
            self.table.blockSignals(True) # Prevent signals during load
            for r, row_data in enumerate(data):
                for c, value in enumerate(row_data):
                    item = QTableWidgetItem(value)
                    self.table.setItem(r, c, item)
            self.table.blockSignals(False)
            
            # 4. Update UI
            self.lbl_filename.setText(os.path.basename(file_path))
            self.btn_save.setEnabled(True)
            self.table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load file:\n{str(e)}")

    def save_file(self, silent=False):
        """Saves the current table to file. If silent=True, suppresses the success popup."""
        if not self.current_file_path: 
            return
            
        try:
            with open(self.current_file_path, 'w') as f:
                rows = self.table.rowCount()
                cols = self.table.columnCount()
                
                for r in range(rows):
                    row_data = []
                    for c in range(cols):
                        item = self.table.item(r, c)
                        text = item.text() if item else "0"
                        row_data.append(text)
                    
                    # Write with tabs
                    if self.current_file_path.lower().endswith('.csv'):
                        f.write(",".join(row_data) + "\n")
                    else:
                        f.write("\t".join(row_data) + "\n")

            # Only show the popup if NOT in silent mode
            if not silent:
                QMessageBox.information(self, "Saved", "File saved successfully!")
            else:
                print(f"Auto-saved table: {self.current_file_path}")
                
        except Exception as e:
            # Always show errors, even in silent mode
            QMessageBox.critical(self, "Error", f"Could not save file:\n{str(e)}")

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # --- Content ---
        info_label = QLabel(
            "<h2 style='margin-bottom: 0px;'>SPHY Model GUI</h2>"
            "<p style='margin-top: 0px; color: #7f8c8d;'>Version 1.0</p>"
            "<p>A graphical user interface for configuring and running the Spatial Processes in HYdrology (SPHY) model.</p>"
            "<p><b>Model Engine:</b> This GUI runs a modified version of SPHY v3.0. The specific source code can be found on <a href='https://github.com/FutureWater/SPHY/tree/channel_module'>GitHub</a>.</p>"
            "<p><b>Documentation:</b> <a href='https://futurewater.gitbook.io/sphy-manual/'>SPHY Manual</a></p>"
            "<p><b>SPHY Website:</b> <a href='https://sphymodel.com/'>sphymodel.com</a></p>"
            "<br>"
            "<p><b>GUI Developed by:</b> <a href='https://www.joriseekhout.com/'>Joris Eekhout</a> (CEBAS-CSIC & University of Murcia)</p>"
            "<p style='font-size: 11px; color: #7f8c8d;'>"
            "This software is open-source and distributed under the "
            "<a href='https://www.gnu.org/licenses/gpl-3.0.html' style='color: #7f8c8d;'>GNU General Public License (GPL)</a>."
            "</p>"
        )
        info_label.setOpenExternalLinks(True) # Makes the links clickable
        info_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        info_label.setWordWrap(True)
        
        # --- Close Button ---
        btn_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        
        layout.addWidget(info_label)
        layout.addLayout(btn_layout)
        
# 4. THE MAIN GUI CLASS
class ConfigEditor(QMainWindow):
    def __init__(self, config_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SPHY Model GUI v1.0")
        
        self.tabs_data = config_data 
        self.widgets = {}
        self.param_dependencies = {}
        self.select_dependencies = {}
        self.tab_dependencies = {}
        self.flag_controls = {} # New: Stores advanced flag control rules
        self.is_stopped_by_user = False

        self.config_data = configparser.ConfigParser() 
        self.current_config = {} 

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_v_layout = QVBoxLayout(self.central_widget)
        self.main_v_layout.setContentsMargins(10, 10, 10, 10) 

        self.create_button_bar()
        self.main_v_layout.addLayout(self.button_h_layout) 

        self.file_control_panel = FileControlPanel(self)
        self.main_v_layout.addWidget(self.file_control_panel) 

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabBar::scroller { 
                width: 50px;
                height: 100%;
            }

            QTabBar QToolButton {
                border: 1px solid #999999;
                background-color: #f0f0f0;
                border-radius: 4px;
                
                width: 24px;
                height: 24px;
                
                margin: 2px;
            }

            QTabBar QToolButton:hover {
                background-color: #e0e0e0;
                border-color: #666666;
            }
        """)
        self.tab_widget.tabBar().setStyleSheet("""
            QTabBar::scroller { width: 50px; background: red; subcontrol-position: right; }
        """)
        self.main_v_layout.addWidget(self.tab_widget, 1)
        # self.main_v_layout.addStretch(1) 
        
        # # 1. Create a Header Layout (Button + Label)
        # console_header_layout = QHBoxLayout()
        # console_header_layout.setContentsMargins(0, 10, 0, 0) # Top margin only
        
        # # The Toggle Button (Arrow)
        # self.console_toggle_btn = QPushButton()
        # self.console_toggle_btn.setFixedWidth(25)
        # self.console_toggle_btn.setFlat(True) # Make it look like just an icon
        # self.console_toggle_btn.setCursor(Qt.PointingHandCursor)
        
        # # Set Default Icon (Down Arrow = Open)
        # # We use standard Qt icons to avoid loading external files
        # self.icon_expanded = self.style().standardIcon(QStyle.SP_ArrowDown)
        # self.icon_collapsed = self.style().standardIcon(QStyle.SP_ArrowUp)
        # self.console_toggle_btn.setIcon(self.icon_expanded)
        
        # self.console_toggle_btn.clicked.connect(self.toggle_console)
        # console_header_layout.addWidget(self.console_toggle_btn)

        # # The Label (Clicking it also toggles)
        # self.log_label = QPushButton("Model Output Log")
        # self.log_label.setFlat(True)
        # self.log_label.setStyleSheet("font-weight: bold; text-align: left;")
        # self.log_label.setCursor(Qt.PointingHandCursor)
        # self.log_label.clicked.connect(self.toggle_console)
        # console_header_layout.addWidget(self.log_label)
        
        # console_header_layout.addStretch() # Push everything to the left
        # self.main_v_layout.addLayout(console_header_layout)

        # # 2. The Text Widget (The Console)
        # self.console_log = QTextEdit()
        # self.console_log.setReadOnly(True)
        # self.console_log.setMinimumHeight(150)

        # # 3. Style it to look like a Terminal
        # self.console_log.setStyleSheet("""
        #     QTextEdit {
        #         background-color: #5b5b5b;
        #         color: #f4f4f4;
        #         font-family: Consolas, 'Courier New', monospace;
        #         font-size: 11px;
        #         border: 1px solid #333;
        #         border-radius: 4px;
        #         padding: 5px;
        #     }
        # """)
        # self.main_v_layout.addWidget(self.console_log)

        # self.toggle_console()

        # 1. The Tab Widget
        self.info_tabs = QTabWidget()
        self.info_tabs.setFixedHeight(200) # Default expanded height
        
        # # Style (Keep your existing style, maybe tweak borders)
        # self.info_tabs.setStyleSheet("""
        #     QTabWidget::pane { border: 1px solid #A0A0A0; top: -1px; background: #2b2b2b; }
        #     QTabBar::tab { padding: 5px 15px; background: #E0E0E0; border: 1px solid #A0A0A0; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
        #     QTabBar::tab:selected { background: white; border-bottom: 1px solid white; font-weight: bold; }
        # """)

        # Simple stylesheet: Just ensure the "Pane" (the box behind the text) is invisible
        self.info_tabs.setStyleSheet("""
            QTabWidget::pane { 
                border: 0;               /* No border around the content area */
                background: transparent; /* No background color behind the text */
            }
        """)
        
        # 2. The Toggle Button (Now inside the Tab Bar!)
        self.info_toggle_btn = QToolButton() # ToolButton fits better in tab bars
        self.info_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.info_toggle_btn.setAutoRaise(True) # Removes border unless hovered
        self.info_toggle_btn.setToolTip("Toggle Console/Help View")
        
        self.info_toggle_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background: transparent;
                padding: 0px;
            }
            QToolButton:hover {
                background: #D0D0D0; /* Optional: Slight highlight on hover */
                border-radius: 2px;
            }
        """)

        # Icons
        # self.icon_expanded = self.style().standardIcon(QStyle.SP_TitleBarMinButton) # Dash or Down Arrow
        # self.icon_collapsed = self.style().standardIcon(QStyle.SP_TitleBarMaxButton) # Box or Up Arrow
        # icon_path = os.path.join(os.path.dirname(sys.argv[0]), 'icons', 'keyboard_arrow_down_24dp_333333_FILL0_wght400_GRAD0_opsz24.svg')
        # self.icon_expanded = QIcon(get_resource_path(icon_path))        
        self.icon_expanded = QIcon(get_resource_path('icons/keyboard_arrow_down_24dp_333333_FILL0_wght400_GRAD0_opsz24.svg'))

        # icon_path = os.path.join(os.path.dirname(sys.argv[0]), 'icons', 'keyboard_arrow_up_24dp_333333_FILL0_wght400_GRAD0_opsz24.svg')
        # self.icon_collapsed = QIcon(get_resource_path(icon_path))        
        self.icon_collapsed = QIcon(get_resource_path('icons/keyboard_arrow_up_24dp_333333_FILL0_wght400_GRAD0_opsz24.svg'))

        self.info_toggle_btn.setIcon(self.icon_expanded)
        self.info_toggle_btn.setIconSize(QSize(24, 24))
        self.info_toggle_btn.clicked.connect(self.toggle_info_pane)

        # CRITICAL: Place button in the top-right corner of the tabs
        self.info_tabs.setCornerWidget(self.info_toggle_btn, Qt.TopRightCorner)
            
        # 3. Add the Tabs (Console & Help)
        # --- TAB 1: CONSOLE ---
        self.console_log = QTextEdit()
        self.console_log.setReadOnly(True)
        self.console_log.setStyleSheet("""
            QTextEdit { background-color: #4b4b4b; color: #D4D4D4; font-family: Consolas, monospace; font-size: 11px; border: none; }
        """)
        self.info_tabs.addTab(self.console_log, "Console Log")

        # --- TAB 2: HELP ---
        self.help_browser = QTextBrowser()
        self.help_browser.setOpenExternalLinks(True)
        # self.help_browser.setStyleSheet("background-color: white; padding: 10px;")
        self.help_browser.setStyleSheet("""
            QScrollBar::handle:vertical { min-height: 20px; }
        """)
        self.info_tabs.addTab(self.help_browser, "Help Documentation")


        # # --- TAB 3: RESULTS (Plotting) ---
        # self.results_tab = QWidget()
        
        # # 1. Apply Layout with Padding
        # # We add margins (padding) so the canvas doesn't touch the edges.
        # # This reveals the background and creates the "floating card" look.
        # self.results_layout = QVBoxLayout(self.results_tab)
        # self.results_layout.setContentsMargins(0, 0, 0, 0)
        
        # # 2. Create Figure
        # self.figure = Figure(figsize=(5, 3), dpi=100)
        # self.figure.patch.set_facecolor('none') # Transparent figure background
        # # self.figure.patch.set_facecolor('#FFFFFF') # White background for the plot area
        # # self.canvas = FigureCanvas(self.figure)
        
        # # 3. Create Canvas
        # self.canvas = FigureCanvas(self.figure)
        # self.canvas.setStyleSheet("""
        #     background-color: white;
        #     border: 1px solid #A0A0A0;
        #     border-radius: 6px;
        # """)
        
        # self.results_layout.addWidget(self.canvas)
        # self.info_tabs.addTab(self.results_tab, "Model Results")

        # --- TAB 3: RESULTS (Plotting) ---
        self.results_tab = QWidget()
        
        # 1. Main Layout (Controls spacing from the window edges)
        self.results_layout = QVBoxLayout(self.results_tab)
        # Use (2, 2, 2, 2) to keep it compact
        self.results_layout.setContentsMargins(1, 1, 1, 1) 
        
        # 2. The "Card" Container (QFrame)
        # This widget creates the "Rounded Look"
        self.results_card = QFrame()
        self.results_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px; /* The rounded corners */
            }
        """)
        
        # Layout inside the card (holds the plot)
        # We add a small margin (e.g., 2px) so the plot doesn't overlap the border curve
        card_layout = QVBoxLayout(self.results_card)
        card_layout.setContentsMargins(2, 2, 2, 2) 
        
        # 3. The Plot (PyQtChart replacing Matplotlib)
        self.chart = QChart()
        self.chart.legend().hide()
        self.chart.setBackgroundVisible(False) # Transparent background so your Card shows through!
        self.chart.layout().setContentsMargins(0, 0, 0, 0)
        self.chart.setMargins(QMargins(10, 10, 10, 10)) # Gives breathing room inside the Card

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing) # Smooth, crisp lines
        self.chart_view.setStyleSheet("background: transparent; border: none;")
        
        # Assemble
        card_layout.addWidget(self.chart_view)       # Put ChartView in Card
        self.results_layout.addWidget(self.results_card) # Put Card in Tab
        
        self.info_tabs.addTab(self.results_tab, "Model Results")

        # If the pane is currently collapsed (not expanded), toggle it open.
        self.info_tabs.tabBarClicked.connect(lambda index: self.toggle_info_pane() if not self.info_pane_expanded else None)

        # Add to main layout (as before)
        self.main_v_layout.addWidget(self.info_tabs)
        
        # Track state
        self.info_pane_expanded = True

        # --- TAB 4: TABLE EDITOR ---
        self.table_editor = TableEditorWidget()
        
        # Add to the Info Tabs
        self.info_tabs.addTab(self.table_editor, "Table Editor")

        # create tabs
        self._create_tabs()

        self.update_all_dependencies()
        self.tab_widget.currentChanged.connect(self.update_all_dependencies)

        # Add this line to start with a decent size:
        self.resize(1000, 700)
        
        # --- SET ICON ---
        icon_path = get_resource_path('icon_window.png')
        
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: {icon_path} not found")
        
        # --- QSETTINGS: Remember Last Config ---
        # "SPHY_Model" is the organization name, "GUI" is the app name
        self.settings = QSettings("SPHY_Model", "GUI") 
        
        last_config = self.settings.value("last_config_path", "")
        
        if last_config and os.path.exists(last_config):
            print(f"Restoring last used configuration: {last_config}")
            # Update the visual text box
            self.file_control_panel.config_path = last_config
            self.file_control_panel.line_edit.setText(last_config)
            # Actually load the data into the GUI
            self.load_config(last_config)

    def create_button_bar(self):
        self.button_h_layout = QHBoxLayout()
        self.button_h_layout.setContentsMargins(0, 0, 0, 10) 

        # --- 1. Run Button ---
        custom_icon = QIcon(get_resource_path('icons/play_circle_24dp_WHITE_FILL0_wght400_GRAD0_opsz24.svg'))
        self.run_btn = QPushButton("Run Model  ")
        self.run_btn.setIcon(custom_icon)
        self.run_btn.setFixedHeight(28)
        self.run_btn.setFixedWidth(100)
        self.run_btn.setLayoutDirection(Qt.RightToLeft)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #70A13A;
                color: white;
                border: 1px solid #5D8630;
                border-radius: 4px;
                padding: 3px 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #638E33; border: 1px solid #557A2B; }
            QPushButton:pressed { background-color: #557A2B; border: 1px solid #486624; }
            QPushButton:disabled { background-color: #E0E0E0; color: #A0A0A0; border: 1px solid #C0C0C0; }
        """)
        self.run_btn.clicked.connect(self.run_model)

        # --- 2. Stop Button ---
        custom_icon = QIcon(get_resource_path('icons/stop_circle_24dp_FFFFFF_FILL0_wght400_GRAD0_opsz24.svg'))
        self.stop_btn = QPushButton("Stop Model  ")
        self.stop_btn.setIcon(custom_icon)
        self.stop_btn.setFixedHeight(28)
        self.stop_btn.setLayoutDirection(Qt.RightToLeft)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_model)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: white;
                border: 1px solid #B71C1C;
                border-radius: 4px;
                padding: 3px 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #C62828; border: 1px solid #B71C1C; }
            QPushButton:pressed { background-color: #B71C1C; border: 1px solid #8E0000; }
            QPushButton:disabled { background-color: #E0E0E0; color: #A0A0A0; border: 1px solid #C0C0C0; }
        """)

        # --- 3. Progress Bar ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #A0A0A0;
                border-radius: 4px;
                text-align: center;
                background-color: white;
                margin-top: 2px;
            }
            QProgressBar::chunk { background-color: #8AB3E6; }
        """)

        # --- 4. Logo ---
        logo_path = get_resource_path("icon_GUI.png") 
        logo_label = None
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path).scaledToHeight(28, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setContentsMargins(0, 0, 10, 0) # Margin on the right to separate from About
        else:
            print(f"Warning: Could not find logo at {logo_path}")

        # --- 5. About Button ---
        custom_icon = QIcon(get_resource_path('icons/info_24dp_333333_FILL0_wght400_GRAD0_opsz24.svg'))
        self.btn_about = QPushButton()
        self.btn_about.setIcon(custom_icon) 
        self.btn_about.setIconSize(QSize(24, 24))
        self.btn_about.setFixedSize(QSize(28, 28)) 
        self.btn_about.setToolTip(f"About the SPHY Model GUI")
        self.btn_about.setCursor(Qt.PointingHandCursor)
        self.btn_about.clicked.connect(self.show_about_dialog)

        # ==========================================
        # ASSEMBLE THE TOP ROW (Left to Right)
        # ==========================================
        # Left Side
        self.button_h_layout.addWidget(self.run_btn)
        self.button_h_layout.addWidget(self.stop_btn)
        self.button_h_layout.addWidget(self.progress_bar, 0, Qt.AlignVCenter)
        
        # The Spring (pushes everything else to the right)
        self.button_h_layout.addStretch()
        
        # Right Side
        if logo_label:
            self.button_h_layout.addWidget(logo_label)
        self.button_h_layout.addWidget(self.btn_about)

    def _create_tabs(self):
        # --- Helper: Calculate label width for alignment ---
        def _get_max_label_width(parameters, font):
            from PyQt5.QtGui import QFontMetrics
            fm = QFontMetrics(font)
            max_pixels = 0
            
            for param in parameters:
                # 1. Measure current label
                text = param.get('label', param['name'])
                width = fm.width(text) # use fm.horizontalAdvance(text) for PyQt6
                if width > max_pixels:
                    max_pixels = width
                
                # 2. RECURSE: Look inside Group Boxes and Rows
                if 'parameters' in param:
                    child_max = _get_max_label_width(param['parameters'], font)
                    if child_max > max_pixels:
                        max_pixels = child_max
                        
            return max_pixels + 5 # Add padding buffer

        # --- Helper: Add parameters to a specific layout ---
        # (This matches your existing logic, but defined locally to be safe)
        def _add_parameters_to_layout(parameters, target_layout, max_lbl_width):
            for param in parameters:
                if param['type'] == 'group_box':
                    # 1. Create the Group Box (using your existing helper)
                    group_box = create_group_box(param, max_lbl_width)

                    # 2. --- NEW: Register the GroupBox for Dependencies ---
                    # We treat the GroupBox itself as a "widget" that can be toggled
                    param_name = param.get('name')
                    
                    if param_name:
                        # A. Save reference to the group box widget
                        self.widgets[param_name] = group_box
                        
                        # B. Check if the Group ITSELF has a dependency rule
                        # This handles both single string "FlagA" and lists ["FlagA", "FlagB"]
                        if 'depends_on' in param:
                            self.param_dependencies[param_name] = param['depends_on']
                    # ------------------------------------------------------                    # ... (Group Box Logic) ...
                    # group_box = create_group_box(param, max_lbl_width)
                    target_layout.addRow(group_box)
                    
                elif param['type'] == 'horizontal_row':
                    # ... (Horizontal Row Logic) ...
                    row_widget = QWidget()
                    row_layout = QHBoxLayout(row_widget)
                    row_layout.setContentsMargins(0, 0, 0, 0)
                    _add_parameters_to_layout(param.get('parameters', []), row_layout, max_lbl_width)
                    target_layout.addRow(row_widget)
                    
                else:
                    # ... (Standard Parameter Logic) ...
                    widget = _create_widget_for_param(param, self, max_lbl_width)
                    label = QLabel(param.get('label', param['name']))
                    
                    # --- CRITICAL ALIGNMENT FIXES ---
                    label.setMinimumWidth(max_lbl_width)
                    label.setMaximumWidth(max_lbl_width) # Force exact width
                    label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    
                    # ... (Keep your dependency logic here) ...
                    self.widgets[param['name']] = widget
                    self.widgets[param['name'] + '_label'] = label
                    if 'depends_on' in param:
                        self.param_dependencies[param['name']] = param['depends_on']
                    if 'select_depends_on' in param:
                        self.select_dependencies[param['name']] = param['select_depends_on']
                    if param['type'] == 'flag':
                        # 1. Store the control rules if they exist
                        if 'controls' in param:
                            self.flag_controls[param['name']] = param['controls']
                            # REMOVED: widget.stateChanged.connect(self.update_flag_dependencies)
                        
                        # 2. Connect to the MAIN update function
                        # This function now handles BOTH 'depends_on' and 'controls' logic simultaneously.
                        widget.stateChanged.connect(self.update_all_dependencies)
                    if isinstance(widget, SelectionInputWidget):
                        widget.selection_changed.connect(self.update_select_dependencies)

                    target_layout.addRow(label, widget)

        # ... (Keep create_group_box helper) ...
        def create_group_box(param_def, max_lbl_width):
            group_box = QGroupBox(param_def['label'])

            help_id = param_def.get('help_id')
            if help_id:
                custom_icon = QIcon(get_resource_path('icons/help_24dp_1F1F1F_FILL0_wght400_GRAD0_opsz24.svg'))
                help_button = QPushButton()
                # help_button = QIcon(get_resource_path('icons/help_24dp_1F1F1F_FILL0_wght400_GRAD0_opsz24.svg'))
                help_button.setIcon(custom_icon)
                help_button.setIconSize(QSize(24, 24))
                help_button.setFixedSize(QSize(28, 28)) 
                help_button.setToolTip(f"Show help for {param_def['label']}")
                
                # def show_help():
                #     help_file = os.path.join(os.path.dirname(sys.argv[0]), 'help', f'{help_id}.md')
                #     dialog = HelpDialog(param_def['label'], help_file, self)
                #     dialog.exec_()
                def show_help():
                    # 1. Construct the path
                    # (Uses existing logic, ensuring we find the 'help' folder)
                    # base_dir = os.path.dirname(sys.argv[0])
                    # help_file = os.path.join(base_dir, 'help', f'{help_id}.md')
                    help_file = get_resource_path(f'help/{help_id}.md')
                    
                    # 2. Call the new method on the main window (self)
                    # This loads the file, renders equations, and switches to the Help tab
                    self.display_help_in_tab(help_file)

                help_button.clicked.connect(show_help)

            gb_layout = QVBoxLayout(group_box)
            gb_layout.setContentsMargins(10, 20, 10, 10) # Adjust margins

            if help_id:
                button_hbox = QHBoxLayout()
                button_hbox.addStretch(1) 
                button_hbox.addWidget(help_button)
                gb_layout.addLayout(button_hbox)

            gb_form = QFormLayout()
            gb_form.setContentsMargins(0, 0, 0, 0)
            gb_form.setVerticalSpacing(5)
            gb_layout.addLayout(gb_form)
            
            _add_parameters_to_layout(param_def.get('parameters', []), gb_form, max_lbl_width)
            return group_box

        # --- Main Loop to Create Tabs ---
        # Robust iteration (handles both List and Dict structures in YAML)
        if isinstance(self.tabs_data, list):
            items = [(t.get('name', str(i)), t) for i, t in enumerate(self.tabs_data)]
        else: 
            items = self.tabs_data.items()

        for index, (tab_id, tab_info) in enumerate(items):
            # PASS SELF.FONT() to calculation
            max_label_width = _get_max_label_width(tab_info['parameters'], self.font())
            
            # 1. The Tab Page (Outer container)
            tab_page = QWidget()
            tab_layout = QVBoxLayout(tab_page)
            tab_layout.setContentsMargins(0,0,0,0)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(10, 10, 10, 10)
            
            main_form_layout = QFormLayout()
            main_form_layout.setContentsMargins(0, 0, 0, 0)
            main_form_layout.setVerticalSpacing(5)
            content_layout.addLayout(main_form_layout)
            
            _add_parameters_to_layout(tab_info['parameters'], main_form_layout, max_label_width)
            content_layout.addStretch(1)
            
            scroll.setWidget(content_widget)
            tab_layout.addWidget(scroll)
            self.tab_widget.addTab(tab_page, tab_info['label'])
            
            if 'depends_on' in tab_info:
                self.tab_dependencies[index] = tab_info['depends_on']

    def update_select_dependencies(self, selected_value):
        sender_widget = self.sender()
        if not sender_widget:
            return
        param_name = sender_widget.property("param_name")
        if param_name not in self.select_dependencies:
            return

        dependency_rules = self.select_dependencies[param_name]
        for rule_key, rule_targets in dependency_rules.items():
            is_match = (rule_key == selected_value)
            for target_param_name in rule_targets:
                target_widget = self.widgets.get(target_param_name)
                target_label = self.widgets.get(target_param_name + '_label') 
                target_spacer = self.widgets.get(target_param_name + '_spacer')
                
                if target_widget:
                    target_widget.setVisible(is_match)
                    if target_label: target_label.setVisible(is_match)
                    if target_spacer: target_spacer.setVisible(is_match)
                                
        self.update_all_dependencies()

    def _get_control_overrides(self):
        """
        Calculates the desired state of widgets based on 'controls' logic.
        Returns a dictionary: { 'widget_name': True/False }
        """
        overrides = {}
        
        # Iterate over all flags that have 'controls' rules
        for flag_name, controls in self.flag_controls.items():
            flag_widget = self.widgets.get(flag_name)
            if not flag_widget: continue
            
            # Check state (handle CheckBox or GroupBox)
            if isinstance(flag_widget, (QCheckBox, QGroupBox)):
                is_checked = flag_widget.isChecked()
            else:
                is_checked = True 

            # Get the actions for the current state (Checked vs Unchecked)
            actions = controls.get('checked') if is_checked else controls.get('unchecked')
            
            if not actions: continue

            # 1. Collect Force Enables
            for target in actions.get('enable', []):
                overrides[target] = True
            
            # 2. Collect Force Disables (These take priority in the dict if conflicting)
            for target in actions.get('disable', []):
                overrides[target] = False
                
        return overrides

    def update_all_dependencies(self):
        """Checks both 'depends_on' and 'controls' rules and updates UI."""
        
        # 1. Get the 'controls' overrides (force enable/disable)
        control_overrides = self._get_control_overrides()
        
        # --- Helpers ---
        def is_flag_on(flag_name):
            w = self.widgets.get(flag_name)
            if not w: return True 
            return w.isChecked() if isinstance(w, (QCheckBox, QGroupBox)) else True

        def check_condition(dependency):
            if isinstance(dependency, list):
                return all(is_flag_on(f) for f in dependency)
            return is_flag_on(dependency)
        # ----------------

        # 2. Apply Dependencies (Merged with Overrides)
        for param_name, dependency in self.param_dependencies.items():
            # A. Calculate strictly based on dependencies (The "Requirements")
            requirements_met = check_condition(dependency)
            
            # B. Check if a 'control' rule wants to override this
            if param_name in control_overrides:
                override_state = control_overrides[param_name]
                
                # LOGIC: 
                # If dependency says NO, it stays NO (Requirements not met).
                # If dependency says YES, but Control says DISABLE, it becomes NO.
                # If dependency says YES, and Control says ENABLE (or nothing), it stays YES.
                final_state = requirements_met and override_state
                
                # Remove from dict so we don't process it again later
                del control_overrides[param_name]
            else:
                final_state = requirements_met

            # C. Apply State
            widget = self.widgets.get(param_name)
            if widget:
                widget.setEnabled(final_state)

        # 3. Apply Remaining Overrides 
        # (Widgets that are controlled by a flag but have no 'depends_on' requirements)
        for param_name, state in control_overrides.items():
            widget = self.widgets.get(param_name)
            if widget:
                widget.setEnabled(state)

        # 4. Handle Tab Dependencies (Same as before)
        for tab_idx, dependency in self.tab_dependencies.items():
            state = check_condition(dependency)
            self.tab_widget.setTabEnabled(tab_idx, state)

    def get_inputdir_value(self):
        inputdir_widget = self.widgets.get('inputdir')
        path = ""
        if inputdir_widget:
            line_edit = inputdir_widget.layout().itemAt(0).widget()
            if hasattr(line_edit, 'text'):
                path = line_edit.text()
                # Use raw text first, but fallback to normalization if empty
                if not path:
                    path = ""
        
        if not path and self.config_data.has_option('DIRS', 'inputdir'):
            path = self.config_data.get('DIRS', 'inputdir')
            
        if not path:
             path = './input'

        # --- FIX START: Don't strip slash, ensure it exists ---
        # We normalize to fix separators, but then force the slash back
        path = os.path.normpath(path)
        if not path.endswith(os.path.sep):
            path += os.path.sep
        return path
        # --- FIX END ---
    
    def load_config(self, config_file_path):
        print(f"Loading data from {config_file_path}...")
        try:
            global CONFIG_FILE
            CONFIG_FILE = config_file_path
            
            # from configupdater import ConfigUpdater
            self.config_data = ConfigUpdater()
            self.config_data.read(config_file_path)
            
            print(f"Successfully loaded {config_file_path}.")
            self.settings.setValue("last_config_path", config_file_path)
            self.tab_widget.setEnabled(True)
            self.file_control_panel.save_btn.setEnabled(True)
            self.run_btn.setEnabled(True)
        except Exception as e:
            print(f"Could not read {config_file_path}. Error: {e}")
            self.tab_widget.setEnabled(False)
            self.file_control_panel.save_btn.setEnabled(False)
            self.run_btn.setEnabled(False)
            return

        inputdir_value = None
        if 'DIRS' in self.config_data:
            # --- THE FIX: Create a case-insensitive lookup map ---
            dir_keys = {k.lower(): k for k in self.config_data['DIRS'].keys()}
            if 'inputdir' in dir_keys:
                actual_key = dir_keys['inputdir']
                raw_val = self.config_data['DIRS'][actual_key].value
                if raw_val is not None:
                    inputdir_value = raw_val.strip()
            
            inputdir_widget = self.widgets.get('inputdir')
            if inputdir_widget:
                line_edit = inputdir_widget.layout().itemAt(0).widget()
                if hasattr(line_edit, 'setText') and inputdir_value:
                    line_edit.setText(inputdir_value)
        
        if inputdir_value:
            inputdir_value = os.path.normpath(inputdir_value)
            if not inputdir_value.endswith(os.path.sep):
                inputdir_value += os.path.sep
        else:
            inputdir_value = os.path.normpath(os.getcwd())

        for param_name, widget in self.widgets.items():
            section = widget.property("param_section")
            param_type = widget.property("param_type")

            if not section or section not in self.config_data:
                continue
            
            # --- THE FIX: Map lowercase widget names to the TRUE case in the file ---
            section_keys = {k.lower(): k for k in self.config_data[section].keys()}

            if param_type == 'date_input' and isinstance(widget, DateInputWidget):
                date_values = {}
                names = widget.names
                for key, config_name in names.items(): 
                    lower_config_name = config_name.lower()
                    if lower_config_name in section_keys:
                        actual_key = section_keys[lower_config_name]
                        try:
                            raw_val = self.config_data[section][actual_key].value
                            if raw_val is not None:
                                date_values[config_name] = int(raw_val.strip())
                        except ValueError:
                            pass 
                if date_values:
                    widget.set_values(date_values)
                
            else:
                lower_param_name = param_name.lower()
                if lower_param_name in section_keys:
                    actual_key = section_keys[lower_param_name]
                    raw_val = self.config_data[section][actual_key].value
                    value = raw_val.strip() if raw_val is not None else ""

                    if param_name == 'inputdir':
                        continue

                    if param_type == 'flag':
                        widget.setChecked(value.lower() in ['1', 'true', 't', 'y', 'yes'])
                    elif param_type == 'selection':
                        if isinstance(widget, SelectionInputWidget):
                            widget.set_value(value) 
                    elif param_type in ['scalar', 'text_input']:
                        widget.setText(value)
                    elif param_type == 'integer_input':
                        widget.set_value(value) 
                    elif param_type == 'composite_input':
                        if isinstance(widget, CompositeInputWidget):
                            widget.set_value(value)
                    elif param_type in ['file_input', 'combined_path']:
                        if hasattr(widget, 'line_edit'):
                            widget.line_edit.setText(value)
                        elif hasattr(widget, 'set_value'):
                            widget.set_value(value)

        self.update_all_dependencies()


    def save_config(self):
        current_config_path = self.file_control_panel.get_config_path()
        if not current_config_path:
            # from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Please select a configuration file first.")
            return

        print(f"Saving current configuration to {current_config_path}...")
        
        try:
            # from configupdater import ConfigUpdater
            # import os
            updater = ConfigUpdater()
            if os.path.exists(current_config_path):
                updater.read(current_config_path)
            
            for param_name, widget in self.widgets.items():
                section = widget.property("param_section")
                param_type = widget.property("param_type")
                
                # --- THE FIX: Skip any GUI widgets that don't belong in the config file! ---
                if not section:
                    continue
                
                if section not in updater:
                    updater.add_section(section)

                section_keys = {k.lower(): k for k in updater[section].keys()}
                value = None

                if param_type == 'date_input':
                    date_values = widget.get_values()
                    for name, val in date_values.items():
                        str_val = str(val)
                        lower_name = name.lower()
                        if lower_name in section_keys:
                            actual_key = section_keys[lower_name]
                            updater[section][actual_key].value = str_val
                        else:
                            updater[section][name] = str_val
                    continue
                elif param_type == 'flag':
                    value = '1' if widget.isChecked() else '0'
                elif param_type in ['scalar', 'text_input']:
                    value = widget.text()
                elif param_type == 'integer_input':
                    value = str(widget.get_value())
                elif param_type in ['selection', 'composite_input', 'file_input', 'combined_path']:
                    value = str(widget.get_value())

                if value is not None:
                    str_value = str(value)
                    lower_param = param_name.lower()
                    if lower_param in section_keys:
                        actual_key = section_keys[lower_param]
                        updater[section][actual_key].value = str_value
                    else:
                        updater[section][param_name] = str_value
            
            os.makedirs(os.path.dirname(current_config_path), exist_ok=True)
            updater.update_file()
            print(f"Successfully saved configuration to {current_config_path}.")
            self.settings.setValue("last_config_path", current_config_path)

        except Exception as e:
            print(f"Error saving configuration: {e}")


    def save_config_as(self):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import os
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration As...", "", "Config Files (*.cfg);;All Files (*)"
        )
        if file_path:
            try:
                if not file_path.lower().endswith(('.cfg', '.ini')):
                    file_path += '.cfg'
                
                current_config_path = self.file_control_panel.get_config_path()
                
                # from configupdater import ConfigUpdater
                updater = ConfigUpdater()
                if current_config_path and os.path.exists(current_config_path):
                    updater.read(current_config_path)
                
                for param_name, widget in self.widgets.items():
                    section = widget.property("param_section")
                    param_type = widget.property("param_type")
                    
                    # --- THE FIX: Skip any GUI widgets that don't belong in the config file! ---
                    if not section:
                        continue
                    
                    if section not in updater:
                        updater.add_section(section)

                    section_keys = {k.lower(): k for k in updater[section].keys()}
                    value = None

                    if param_type == 'date_input':
                        date_values = widget.get_values()
                        for name, val in date_values.items():
                            str_val = str(val)
                            lower_name = name.lower()
                            if lower_name in section_keys:
                                actual_key = section_keys[lower_name]
                                updater[section][actual_key].value = str_val
                            else:
                                updater[section][name] = str_val
                        continue
                    elif param_type == 'flag':
                        value = '1' if widget.isChecked() else '0'
                    elif param_type in ['scalar', 'text_input']:
                        value = widget.text()
                    elif param_type == 'integer_input':
                        value = str(widget.get_value())
                    elif param_type in ['selection', 'composite_input', 'file_input', 'combined_path']:
                        value = str(widget.get_value())

                    if value is not None:
                        str_value = str(value)
                        lower_param = param_name.lower()
                        if lower_param in section_keys:
                            actual_key = section_keys[lower_param]
                            updater[section][actual_key].value = str_value
                        else:
                            updater[section][param_name] = str_value
                
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'w') as configfile:
                    updater.write(configfile)

                self.file_control_panel.config_path = file_path
                self.file_control_panel.line_edit.setText(file_path)

                self.settings.setValue("last_config_path", current_config_path)

                # QMessageBox.information(self, "Success", f"Configuration saved successfully to:\n{file_path}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save configuration:\n{e}")

    # def run_model(self):
    #     self.save_config() 
    #     config_path = self.file_control_panel.get_config_path()
    #     script_path = self.file_control_panel.get_script_path()

    #     if not config_path or not script_path:
    #         QMessageBox.warning(self, "Error", "Please select both the configuration file and the model script.")
    #         return

    #     import subprocess
    #     command = f'python "{script_path}" "{config_path}"'
    #     print("--- Running Model ---")
    #     print(f"Executing command: {command}")
        
    #     try:
    #         subprocess.run(command, shell=True, check=True, stdout=sys.stdout, stderr=sys.stderr)
    #         print("Model run complete.")
    #     except subprocess.CalledProcessError as e:
    #         QMessageBox.critical(self, "Model Error", f"Model execution failed with exit code {e.returncode}.\nCommand: {command}")
    #         print(f"Model execution failed: {e}")
    #     except FileNotFoundError:
    #         QMessageBox.critical(self, "Error", "Python interpreter not found. Ensure 'python' is in your system PATH.")    

    # --- NEW: Process & Progress Logic ---
    def run_model(self):
        self.error_occurred = False

        """Starts the model in a separate process to keep GUI responsive."""
        script_path = self.file_control_panel.get_script_path()
        config_path = self.file_control_panel.get_config_path()

        if not script_path or not config_path:
            QMessageBox.warning(self, "Missing Files", "Please select both a script and a config file.")
            return

        if not self.info_pane_expanded:
            self.toggle_info_pane()
            
        # 1. Save changes before running
        self.save_config()

        # If the user is editing a table, save it before running so the model uses new data.
        if hasattr(self, 'table_editor'):
            self.table_editor.save_file(silent=True)

        # Switch to Console Tab (Index 0)
        self.info_tabs.setCurrentIndex(2)
        self.info_tabs.setCurrentIndex(0)

        # NEW: Clear previous logs
        self.console_log.clear() 
        self.console_log.append("<i>Starting model run...</i><br>")

        # 2. Calculate Total Days (for the progress bar)
        self.total_days = self.calculate_total_duration()
        self.progress_bar.setValue(0)

        # Reset the bar color back to green for next time
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #A0A0A0;
                border-radius: 4px;
                text-align: center;
                background-color: white;
            }
            QProgressBar::chunk {
                background-color: #70A13A; 
            }
        """)

        # 3. Setup the Process
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.readyReadStandardError.connect(self.handle_error)
        self.process.finished.connect(self.process_finished)
        self.is_stopped_by_user = False

        # --- SMART ROUTING: DEV vs RELEASE ---
        if getattr(sys, 'frozen', False):
            # ---------------------------------------------------------
            # RELEASE MODE: The GUI is compiled as an .exe
            # ---------------------------------------------------------
            base_dir = os.path.dirname(sys.executable)
            program = os.path.join(base_dir, 'sphy_model', 'sphy_model.exe')
            arguments = [config_path] 
            
        else:
            # ---------------------------------------------------------
            # DEVELOPMENT MODE: Direct Python Executable
            # ---------------------------------------------------------
            # We bypass conda.bat entirely and point straight to the engine's Python!
            program = "python"
            
            # The arguments are now just the script and the config
            arguments = [script_path, config_path]

        # 4. Start the background process!
        self.process.start(program, arguments)

        # Disable run button to prevent double-clicking
        self.run_btn.setEnabled(False)
        self.run_btn.setText("Running...  ")
        self.stop_btn.setEnabled(True)

    def stop_model(self):
        """Stops the running process."""
        if hasattr(self, 'process') and self.process.state() == QProcess.Running:
            self.is_stopped_by_user = True
            self.process.kill()  # Forcefully stops the script
            self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #E0E0E0; }")
            
            # Reset UI
            self.stop_btn.setEnabled(False)
            self.run_btn.setEnabled(True)
            self.run_btn.setText("Run Model  ")
            
            # Optional: Show message in terminal or status
            print("\n>>> Model run stopped by user.")
            QMessageBox.information(self, "Stopped", "Model run stopped by user.")

    def calculate_total_duration(self):
        """Reads start/end dates directly from the live GUI widgets to calc 100% progress."""
        from datetime import datetime
        
        try:
            # 1. Gather all live date values directly from the UI widgets
            live_dates = {}
            for param_name, widget in self.widgets.items():
                if widget.property("param_type") == 'date_input':
                    # This grabs the current state of the date boxes in the GUI
                    live_dates.update(widget.get_values())
            
            # Create a case-insensitive dictionary for easy lookup
            gui_keys = {k.lower(): k for k in live_dates.keys()}

            # 2. Helper to safely grab the live GUI value, or fallback to default
            def get_val(key, fallback):
                lower_key = key.lower()
                if lower_key in gui_keys:
                    return int(live_dates[gui_keys[lower_key]])
                return int(fallback)

            # 3. Extract the integers directly from the live widget data
            start_year = get_val('StartYear', 2000)
            start_month = get_val('StartMonth', 1)
            start_day = get_val('StartDay', 1)
            
            end_year = get_val('EndYear', 2000)
            end_month = get_val('EndMonth', 1)
            end_day = get_val('EndDay', 1)

            # 4. Calculate the duration
            start = datetime(start_year, start_month, start_day)
            end = datetime(end_year, end_month, end_day)
            
            self.start_date = start # Store for later calculation
            
            duration = (end - start).days
            
            # Safety check: if the user accidentally makes the end date before the start date
            return duration if duration > 0 else 1 
            
        except Exception as e:
            print(f"Could not calculate duration: {e}")
            return 1 # Avoid division by zero

    def show_about_dialog(self):
        """Opens the About pop-up window."""
        dialog = AboutDialog(self)
        dialog.exec_() # exec_() makes it a modal window (blocks main window until closed)

    def toggle_info_pane(self):
        """Toggles between full view and just the tab headers."""
        if self.info_pane_expanded:
            # --- COLLAPSE ---
            # 1. Calculate the height of just the tab bar
            # We use sizeHint() for better accuracy across different styles
            bar_height = self.info_tabs.tabBar().sizeHint().height()
            
            # 2. CRITICAL FIX: Unlock the minimum height!
            # We set min_height to the bar_height so it CAN shrink.
            self.info_tabs.setMinimumHeight(bar_height)
            
            # 3. Lock the max height to just the bar
            self.info_tabs.setMaximumHeight(bar_height)
            
            self.info_toggle_btn.setIcon(self.icon_collapsed)
            self.info_pane_expanded = False
        else:
            # --- EXPAND ---
            # Force height to exactly 200px
            self.info_tabs.setFixedHeight(200)
            self.info_toggle_btn.setIcon(self.icon_expanded)
            self.info_pane_expanded = True
            
            # Ensure text cursor is visible if on console tab
            if self.info_tabs.currentIndex() == 0:
                self.console_log.ensureCursorVisible()

    def display_help_in_tab(self, markdown_file):
        """Loads markdown and ensures the tab pane is expanded."""
        # 1. Force Expand if currently collapsed
        if not self.info_pane_expanded:
            self.toggle_info_pane()
        self.info_tabs.setCurrentIndex(1) # Index 1 is the Help Tab

        # 2. Check file
        if not os.path.exists(markdown_file):
            self.help_browser.setHtml(f"<h3 style='color:red'>Error</h3><p>File not found: {markdown_file}</p>")
            return

        # 3. Read and Render
        try:
            with open(markdown_file, 'r', encoding='utf-8') as f:
                text = f.read()

            # Render Math
            def replacer(match):
                return self._render_math_to_base64(match.group(1))
            
            text = re.sub(r'\$\$(.*?)\$\$', replacer, text, flags=re.DOTALL)
            text = re.sub(r'(?<!\$)\$(.+?)\$(?!\$)', replacer, text)

            # Convert Markdown to HTML
            html = markdown.markdown(text, extensions=['extra'])
            
            # Wrap in style
            full_html = f"""
            <html>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; font-size: 14px; line-height: 120%; margin: 10px; }}
                h1, h2 {{ color: #2c3e50; border-bottom: 1px solid #ddd; margin-top: 15px; margin-bottom: 5px; }}
                code {{ background-color: #f4f4f4; padding: 2px 5px; }}
                table {{
                    border-collapse: collapse; /* Merges borders into single lines */
                    width: 100%;               /* Stretch table to fit width */
                    margin-top: 10px;
                    margin-bottom: 10px;
                    background-color: #fafafa; /* Light gray background */
                }}
                th, td {{
                    padding: 8px 12px;         /* Space around text (Columns/Rows) */
                    border: 1px solid #e0e0e0; /* Thin light gray lines */
                }}
                th {{
                    background-color: #ececec; /* Slightly darker header */
                    font-weight: bold;
                    text-align: left;
                }}
            </style>
            <body>
                <div align="justify">
                    {html}
                </div>
            </body>
            </html>
            """
            self.help_browser.setHtml(full_html)
            
        except Exception as e:
            self.help_browser.setHtml(f"<p>Error loading help: {e}</p>")

    def plot_model_output(self):
        """Parses QAllDTS.tss with variable header length and plots the discharge."""
        
        # --- Helper to safely and case-insensitively grab config values ---
        def get_cfg(section, key, fallback):
            if section in self.config_data:
                keys = {k.lower(): k for k in self.config_data[section].keys()}
                if key.lower() in keys:
                    actual_key = keys[key.lower()]
                    val = self.config_data[section][actual_key].value
                    return val.strip() if val is not None else fallback
            return fallback

        # 1. Check if Routing was enabled
        rout_flag = get_cfg('MODULES', 'RoutFLAG', '0')
        if rout_flag != '1':
            # THE FIX: Use QtCharts to show the message instead of Matplotlib!
            self.chart.removeAllSeries()
            for axis in self.chart.axes():
                self.chart.removeAxis(axis)
            self.chart.setTitle("Routing (RoutFLAG) is disabled. No output generated.")
            return

        # 2. Construct Path
        output_dir_name = get_cfg('DIRS', 'outputdir', 'output')
        
        # Handle case where OutputDir is not absolute
        import os
        if not os.path.isabs(output_dir_name):
            base_path = os.path.dirname(self.file_control_panel.get_config_path())
            output_dir = os.path.join(base_path, output_dir_name)
        else:
            output_dir = output_dir_name
            
        results_file = os.path.join(output_dir, 'QAllDTS.tss')

        if not os.path.exists(results_file):
            # THE FIX: Use QtCharts to show the error
            self.chart.removeAllSeries()
            for axis in self.chart.axes():
                self.chart.removeAxis(axis)
            self.chart.setTitle("Output file not found: QAllDTS.tss")
            return

        # 3. Read Data (Robust parsing)
        try:
            # --- 1. PURE PYTHON DATA READING (NO PANDAS) ---
            from datetime import datetime, timedelta

            with open(results_file, 'r') as f:
                lines = f.readlines()
                
            # Extract header info to know how many lines to skip
            num_cols = int(lines[1].strip())
            lines_to_skip = num_cols + 2

            # Generate Start Date (Using the new ConfigUpdater getter)
            start_year = int(get_cfg('TIMING', 'StartYear', '2000'))
            start_month = int(get_cfg('TIMING', 'StartMonth', '1'))
            start_day = int(get_cfg('TIMING', 'StartDay', '1'))
            start_date_obj = datetime(start_year, start_month, start_day)
            
            # Calculate Spin-Up Cutoff
            spin_up_years = int(get_cfg('TIMING', 'SpinUpYears', '0'))
            cutoff_date = start_date_obj + timedelta(days=spin_up_years * 365)

            plot_dates = []
            plot_discharge = []

            # Loop through the data lines and split by whitespace
            for line in lines[lines_to_skip:]:
                parts = line.strip().split()
                if not parts:
                    continue  # Skip blank lines
                
                t = int(parts[0])
                q = float(parts[1])  # Column 1 is the first station
                
                current_date = start_date_obj + timedelta(days=t-1)
                
                # Apply spin-up filter
                if current_date > cutoff_date:
                    plot_dates.append(current_date)
                    plot_discharge.append(q)

            if not plot_dates:
                raise ValueError("No data left after spin-up.")

            # --- 2. PYQTCHART PLOTTING (NO MATPLOTLIB) ---
            from PyQt5.QtChart import QLineSeries, QDateTimeAxis, QValueAxis
            from PyQt5.QtGui import QColor
            from PyQt5.QtCore import Qt

            # Clear any old data/axes from the chart before drawing a new one
            self.chart.removeAllSeries()
            for axis in self.chart.axes():
                self.chart.removeAxis(axis)
            
            self.chart.setTitle("Outlet Discharge")

            # Create the Line Series
            series = QLineSeries()
            series.setName("Discharge")
            
            # Style the line (Matching your old '#4575B3' color)
            pen = series.pen()
            pen.setWidth(2)
            pen.setColor(QColor('#4575B3'))
            series.setPen(pen)

            min_val = float('inf')
            max_val = float('-inf')

            # Add the data points (QtCharts requires milliseconds since Epoch for Dates)
            for d, q in zip(plot_dates, plot_discharge):
                series.append(int(d.timestamp() * 1000), q)
                if q < min_val: min_val = q
                if q > max_val: max_val = q

            self.chart.addSeries(series)

            # Setup X Axis (Dates)
            axis_x = QDateTimeAxis()
            axis_x.setFormat("yyyy-MM")
            axis_x.setTickCount(5) # Number of date labels to show on the bottom
            self.chart.addAxis(axis_x, Qt.AlignBottom)
            series.attachAxis(axis_x)

            # Setup Y Axis (Discharge)
            axis_y = QValueAxis()
            axis_y.setTitleText("Q (m³/s)")
            
            # Set Y limits slightly above and below your data min/max so it doesn't touch the edges
            if min_val == float('inf'): min_val, max_val = 0, 1 # Safety fallback
            axis_y.setRange(max(0, min_val * 0.9), max_val * 1.1) 
            
            self.chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_y)

            # Show Legend
            self.chart.legend().hide()
            
            # Automatically switch to the results tab when finished
            # (Make sure the index matches where your chart actually lives!)
            self.info_tabs.setCurrentIndex(2)
            if not self.info_pane_expanded:
                self.toggle_info_pane()

        except Exception as e:
            # If something breaks, clear the chart and show the error in the title
            self.chart.removeAllSeries()
            for axis in self.chart.axes():
                self.chart.removeAxis(axis)
            self.chart.setTitle(f"Error plotting data: {str(e)}")

    def open_table_from_ui(self, relative_path):
        """Opens the file specified in the UI line edit into the Table Editor tab."""
        if not relative_path.strip():
            QMessageBox.warning(self, "No File", "Please select a file path first.")
            return

        # 1. Construct Absolute Path
        # Use the Input Directory as the base, not just the config folder.
        # This matches the logic used by FileInputWidget.
        if hasattr(self, 'get_inputdir_value'):
            base_path = self.get_inputdir_value()
        else:
            # Fallback if the helper method isn't found
            # Assumes InputDir is in GENERAL section and relative to config file
            conf_dir = os.path.dirname(self.file_control_panel.get_config_path())
            input_dir_setting = self.config_data.get('GENERAL', 'InputDir', fallback='')
            base_path = os.path.join(conf_dir, input_dir_setting)

        # Sanity check to ensure we have a valid path to join
        if not base_path:
             QMessageBox.warning(self, "Error", "Could not determine Input Directory.")
             return

        full_path = os.path.join(base_path, relative_path)
        
        # 2. Check if file exists
        if not os.path.exists(full_path):
            reply = QMessageBox.question(self, "File Not Found", 
                                       f"The file '{relative_path}' does not exist.\n\n"
                                       f"looked in: {base_path}\n\n"
                                       "Do you want to create a new empty table?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    # Create empty file
                    with open(full_path, 'w') as f:
                        f.write("") 
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not create file:\n{e}")
                    return
            else:
                return

        # 3. Load into Editor
        self.table_editor.load_table(full_path)
        
        # 4. Switch View (Assumes Table Editor is the 4th tab)
        self.info_tabs.setCurrentWidget(self.table_editor)
        
        # 5. Ensure Pane is Open
        if not self.info_pane_expanded:
            self.toggle_info_pane()

    def _render_math_to_base64(self, math_str):
        """Helper to render LaTeX to image via CodeCogs API, embedded as Base64."""
        try:
            # 1. Encode the math string for the URL
            encoded_math = urllib.parse.quote(math_str.strip())
            url = f"https://latex.codecogs.com/png.latex?\\dpi{{110}}{encoded_math}"
            
            # 2. Have Python download the image (using a User-Agent so CodeCogs doesn't block us)
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                image_data = response.read()
                
            # 3. Convert the downloaded image into a Base64 string
            img_str = base64.b64encode(image_data).decode('utf-8')
            
            # 4. Return the exact Base64 HTML structure that QTextBrowser natively supports!
            # (Using 'align="middle"' instead of CSS, as PyQt parses standard HTML attributes much better)
            return f'<img src="data:image/png;base64,{img_str}" align="middle" />'
            
        except Exception as e:
            print(f"Error rendering math via API: {e}")
            return f'<span style="color:red">{math_str}</span>'
                
    def handle_output(self):
        """Reads the terminal output line by line to find dates."""
        data = self.process.readAllStandardOutput()
        stdout = bytes(data).decode("utf8", errors='replace')
        print(stdout, end="") # Print to actual terminal so you can still see it

        # 1. Update the Progress Bar (Your existing logic)
        # ------------------------------------------------
        match = re.search(r"(\d{1,2}-\d{1,2}-\d{4})", stdout)
        if match and hasattr(self, 'total_days') and self.total_days > 0:
            current_date_str = match.group(1)
            try:
                current_date = datetime.strptime(current_date_str, "%d-%m-%Y")
                if hasattr(self, 'start_date'):
                    days_elapsed = (current_date - self.start_date).days
                    percent = int((days_elapsed / self.total_days) * 100)
                    self.progress_bar.setValue(max(0, min(100, percent)))
            except ValueError:
                pass 
        # ------------------------------------------------

        # 2. NEW: Append to Console
        # We move cursor to end -> insert text -> scroll to bottom
        cursor = self.console_log.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(stdout)
        self.console_log.setTextCursor(cursor)
        self.console_log.ensureCursorVisible()

    # def handle_error(self):
    #     data = self.process.readAllStandardError()
    #     stderr = bytes(data).decode("utf8")
    #     print(stderr, end="") # Print errors to terminal
    
    def handle_error(self):
        """Reads standard error and prints to GUI console in RED."""
        data = self.process.readAllStandardError()
        # Use 'replace' to prevent crashes if a character is cut in half
        stderr = bytes(data).decode("utf8", errors="replace")

        # 1. Print to Console (Always show red text for warnings/errors)
        formatted_error = f"<span style='color:#FF5555;'>{stderr}</span>".replace("\n", "<br>")
        self.console_log.moveCursor(QTextCursor.End)
        self.console_log.insertHtml(formatted_error)
        self.console_log.ensureCursorVisible()

        # 2. Smart Error Detection
        # Only flag as a failure if we see "Traceback" or "Error" 
        # OR if the text is substantial (this prevents flagging minor warnings)
        lower_err = stderr.lower()
        if "traceback" in lower_err or "error" in lower_err or "exception" in lower_err:
             self.error_occurred = True

    def process_finished(self, exit_code, exit_status):
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False) # Assuming you have a stop button
        
        # Logic: 
        # If Exit Code is non-zero -> It definitely crashed.
        # If Exit Code is 0 BUT we saw a "Traceback" -> It likely crashed silently.
        # Otherwise -> Success (even if there were minor warnings).
        
        # is_crash = (exit_code != 0) or (exit_status != QProcess.NormalExit)
        
        if getattr(self, 'is_stopped_by_user', False):
            # QMessageBox.information(self, "Stopped", "Model run was successfully stopped.")
            self.is_stopped_by_user = False  # Reset the flag
            return  # Stop here, do not show the error message!
        
        # if is_crash or self.error_occurred:
        #     # Change progress bar to red
        #     self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #d9534f; }")
            
        #     msg = "The model stopped unexpectedly."
        #     if exit_code != 0:
        #         msg += f"\nExit Code: {exit_code}"
            
        #     QMessageBox.critical(self, "Model Failed", f"{msg}\nCheck the console output for details.")
            
            # # --- FAILURE CASE ---
            # self.progress_bar.setValue(0)
            
        if exit_status == QProcess.NormalExit and exit_code == 0:
            # QMessageBox.information(self, "Success", "Model run completed successfully!")
            # self.console_log.append("\n--- Model run successful ---")
            # --- SUCCESS CASE ---
            self.run_btn.setText("Run Model")
            self.progress_bar.setValue(100)
            
            # Trigger your plot and show success
            self.plot_model_output() 
            self.info_tabs.setCurrentIndex(2)
            
            QMessageBox.information(self, "Finished", "Model run complete!")

        else:
            self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #d9534f; }")
            self.run_btn.setText("Run Model")
            
            msg = "The model stopped unexpectedly."
            if exit_code != 0:
                msg += f"\nExit Code: {exit_code}"
            
            QMessageBox.critical(self, "Model Failed", f"{msg}\nCheck the console output for details.")



if __name__ == "__main__":
    multiprocessing.freeze_support()

    # NORMAL MODE: Launch the GUI
    app = QApplication(sys.argv)

    # 1. Create a blank white canvas (Width: 400px, Height: 250px)
    splash_pixmap = QPixmap(400, 250)
    splash_pixmap.fill(QColor("white")) # Or any hex color like QColor("#F0F0F0")

    # 2. Start painting on the canvas
    painter = QPainter(splash_pixmap)
    
    # 3. Draw the Logo
    logo_path = get_resource_path("icon_GUI.png") 
    if os.path.exists(logo_path):
        # Scale logo to 100x100 pixels
        logo = QPixmap(logo_path).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        # Position it at (x=150, y=30) to center it on the 400px wide canvas
        painter.drawPixmap(100, 30, logo)

    # 4. Draw the Text
    painter.setPen(QColor("#333333")) # Dark grey text
    
    # Title
    painter.setFont(QFont("Segoe UI", 16, QFont.Bold))
    painter.drawText(QRect(0, 140, 400, 40), Qt.AlignCenter, "SPHY Model GUI")
    
    # Version Info
    painter.setFont(QFont("Segoe UI", 10))
    painter.drawText(QRect(0, 180, 400, 30), Qt.AlignCenter, "GUI Version: 1.0  |  SPHY Version: 3.0")
    
    # Loading message
    painter.setFont(QFont("Segoe UI", 9, QFont.StyleItalic))
    painter.setPen(QColor("#777777"))
    painter.drawText(QRect(0, 210, 400, 30), Qt.AlignCenter, "Loading interface and configuration...")

    painter.end() # ALWAYS call this when done drawing!

    # 5. Show the dynamically created splash screen
    splash = QSplashScreen(splash_pixmap, Qt.WindowStaysOnTopHint)
    splash.show()
    
    # 3. FORCE the app to draw the splash screen immediately before doing heavy work
    app.processEvents() 
    # --------------------------

    tabs_data = load_gui_definition(GUI_DEF_FILE)
    if tabs_data:
        # if os.name == 'nt':
        #     myappid = 'sphy.gui.app.1.0' # This can be any string you want!
        #     ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        # app = QApplication(sys.argv)

        default_font = QFont("Segoe UI", 8) 
        app.setFont(default_font)

        my_colors = { "primary": "#4575B3" }

        my_styles = """
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: white; border: 1px solid #c0c0c0; color: #333333;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border: 1px solid #4575B3;
            }
            QCheckBox { outline: none; border: none; background: none; }
            QCheckBox:hover { border: none; }
            QPushButton { background: #E0E0E0; border: 1px solid #A0A0A0; border-radius: 4px; padding: 4px 10px; color: black; }
        """
        
        qdarktheme.setup_theme(theme="light", custom_colors=my_colors, corner_shape="rounded", additional_qss=my_styles)

        window = ConfigEditor(tabs_data)
        window.show()
        QTimer.singleShot(0, splash.close)
        sys.exit(app.exec())
    else:
        print("Cannot start GUI without a valid definition file.")