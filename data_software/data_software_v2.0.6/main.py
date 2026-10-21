import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget,
                             QFrame, QSplitter, QSizePolicy, QDialog, QLineEdit,
                             QTextEdit, QPushButton, QMenu)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QPixmap

class TechButton(QPushButton):
    def __init__(self, text, icon=None):
        super().__init__(text)
        self.setMinimumHeight(50)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        font = QFont("Segoe UI", 9, QFont.Bold)
        self.setFont(font)
        self.normal_style = """
            QPushButton {
                background-color: #e6f7ff;
                color: #0066cc;
                border: 1px solid #66b3ff;
                border-radius: 8px;
                text-align: center;
                padding: 5px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #d1e8ff;
                border: 1px solid #3399ff;
            }
            QPushButton:pressed {
                background-color: #b3d9ff;
            }
        """
        self.active_style = """
            QPushButton {
                background-color: #cce6ff;
                color: #004d99;
                border: 1px solid #3399ff;
                border-radius: 8px;
                text-align: center;
                padding: 5px;
                margin: 2px;
            }
        """
        self.setStyleSheet(self.normal_style)
        if icon:
            self.setIcon(QIcon(icon))
            self.setIconSize(QSize(20, 20))
class APIDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API设置")
        layout = QVBoxLayout()
        
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("API_URL:"))
        self.url_edit = QLineEdit()
        url_layout.addWidget(self.url_edit)
        layout.addLayout(url_layout)
        
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API_KEY:"))
        self.key_edit = QLineEdit()
        key_layout.addWidget(self.key_edit)
        layout.addLayout(key_layout)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def get_values(self):
        return self.url_edit.text(), self.key_edit.text()

class HelpDialog(QDialog):
    def __init__(self, help_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("使用帮助")
        self.setGeometry(100, 100, 500, 600)
        
        layout = QVBoxLayout(self)
        
        # 添加三个模块按钮
        btn_layout = QHBoxLayout()
        self.btn_select = QPushButton("数据筛选使用说明")
        self.btn_select.clicked.connect(lambda: self.show_help_content("data_select"))
        btn_layout.addWidget(self.btn_select)
        
        self.btn_generate = QPushButton("数据制备使用说明")
        self.btn_generate.clicked.connect(lambda: self.show_help_content("data_generate"))
        btn_layout.addWidget(self.btn_generate)
        
        self.btn_refine = QPushButton("数据精炼使用说明")
        self.btn_refine.clicked.connect(lambda: self.show_help_content("data_refine"))
        btn_layout.addWidget(self.btn_refine)
        
        layout.addLayout(btn_layout)
        
        # 帮助内容区域
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        
        # 关闭按钮
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
        
        # 存储帮助数据
        self.help_data = help_data
    
    def show_help_content(self, module):
        content = self.help_data.get(module, "帮助内容未找到")
        self.text_edit.setPlainText(content)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多模态数据科学工具箱")
        self.setGeometry(300, 100, 1000, 700)
        # if os.path.exists("./icons/star.png"):
        #     self.setWindowIcon(QIcon("./icons/star.png"))
        
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: #ffffff;")
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)
        
        sidebar = QWidget()
        sidebar.setMinimumWidth(150)
        sidebar.setMaximumWidth(250)
        sidebar.setStyleSheet("background-color: #f0f9ff; border-right: 1px solid #cce6ff;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(5, 5, 5, 5)
        sidebar_layout.setSpacing(5)
        
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)
        
        if os.path.exists("./icons/star.png"):
            logo_label = QLabel()
            logo_pixmap = QPixmap("./icons/star.png").scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            title_layout.addWidget(logo_label)
        
        title = QLabel("多模态数据治理工具平台")
        title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        title.setStyleSheet("color: #0059b3; padding: 6px; background-color: #e6f2ff; border-radius: 8px; border: 1px solid #99ccff;")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        title_layout.addWidget(title)
        sidebar_layout.addLayout(title_layout)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #99ccff; height: 2px;")
        sidebar_layout.addWidget(separator)
        
        button_container = QWidget()
        button_container.setStyleSheet("background-color: transparent;")
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)
        
        self.btn_select = TechButton("数据筛选", "./icons/set_icon.png")
        self.btn_select.clicked.connect(self.show_data_select)
        button_layout.addWidget(self.btn_select)
        
        self.btn_generate = TechButton("数据制备", "./icons/set_icon.png")
        self.btn_generate.clicked.connect(self.show_data_generate)
        button_layout.addWidget(self.btn_generate)
        
        self.btn_refine = TechButton("数据精炼", "./icons/set_icon.png")
        self.btn_refine.clicked.connect(self.show_data_refine)
        button_layout.addWidget(self.btn_refine)
        
        self.btn_api = TechButton("API设置", "./icons/set_icon.png")
        self.btn_api.clicked.connect(self.show_api_dialog)
        button_layout.addWidget(self.btn_api)
        
        self.btn_help = TechButton("帮助", "./icons/set_icon.png")
        self.btn_help.clicked.connect(self.show_help)
        button_layout.addWidget(self.btn_help)
        
        sidebar_layout.addWidget(button_container)
        sidebar_layout.addStretch(1)
        
        author_frame = QFrame()
        author_frame.setStyleSheet("background-color: #e6f2ff; border-radius: 8px; padding: 6px; border: 1px solid #cce6ff;")
        author_layout = QVBoxLayout(author_frame)
        
        org_label = QLabel("多模态模型组")
        org_label.setFont(QFont("Segoe UI", 8))
        org_label.setStyleSheet("color: #0066cc;")
        org_label.setAlignment(Qt.AlignCenter)
        org_label.setWordWrap(True)
        author_layout.addWidget(org_label)
        
        copyright_label = QLabel("@2025 版权所有")
        copyright_label.setFont(QFont("Segoe UI", 7))
        copyright_label.setStyleSheet("color: #3399ff;")
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setWordWrap(True)
        author_layout.addWidget(copyright_label)
        
        author_label = QLabel("作者: Lin, X")
        author_label.setFont(QFont("Segoe UI", 8))
        author_label.setStyleSheet("color: #0066cc;")
        author_label.setAlignment(Qt.AlignCenter)
        author_label.setWordWrap(True)
        author_layout.addWidget(author_label)
        
        sidebar_layout.addWidget(author_frame)
        
        self.content = QStackedWidget()
        self.content.setStyleSheet("background-color: #ffffff;")
        
        self.init_page = QWidget()
        self.init_page.setStyleSheet("background-color: #ffffff;")
        init_layout = QVBoxLayout(self.init_page)
        init_layout.addStretch()
        
        welcome = QLabel("欢迎使用多模态数据科学工具箱")
        welcome.setFont(QFont("Segoe UI", 18, QFont.Bold))
        welcome.setStyleSheet("color: #0059b3; padding: 15px;")
        welcome.setAlignment(Qt.AlignCenter)
        init_layout.addWidget(welcome)
        
        hint = QLabel("请从侧边栏选择功能模块")
        hint.setFont(QFont("Segoe UI", 10))
        hint.setStyleSheet("color: #3399ff; padding: 15px;")
        hint.setAlignment(Qt.AlignCenter)
        init_layout.addWidget(hint)
        
        if os.path.exists("./icons/lulingqi.png"):
            icon_label = QLabel()
            icon_pixmap = QPixmap("./icons/lulingqi.png").scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
            icon_label.setAlignment(Qt.AlignCenter)
            init_layout.addWidget(icon_label)
        
        init_layout.addStretch()
        
        self.select_page = QWidget()
        self.select_page.setStyleSheet("background-color: #ffffff;")
        self.generate_page = QWidget()
        self.generate_page.setStyleSheet("background-color: #ffffff;")
        self.refine_page = QWidget()
        self.refine_page.setStyleSheet("background-color: #ffffff;")
        
        self.select_page.setStyleSheet("border: 1px solid #cce6ff; border-radius: 10px; background-color: #ffffff;")
        self.generate_page.setStyleSheet("border: 1px solid #cce6ff; border-radius: 10px; background-color: #ffffff;")
        self.refine_page.setStyleSheet("border: 1px solid #cce6ff; border-radius: 10px; background-color: #ffffff;")
        
        self.content.addWidget(self.init_page)
        self.content.addWidget(self.select_page)
        self.content.addWidget(self.generate_page)
        self.content.addWidget(self.refine_page)
        
        self.splitter.addWidget(sidebar)
        self.splitter.addWidget(self.content)
        self.splitter.setSizes([150, 850])
        
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #cce6ff;
                width: 5px;
            }
            QSplitter::handle:hover {
                background-color: #99ccff;
            }
        """)
        
        self.setCentralWidget(main_widget)
        
        self.data_select_imported = False
        self.data_generate_imported = False
        self.data_refine_imported = False
        self.data_select_window = None
        self.data_generate_window = None
        self.data_refine_window = None
        self.api_url = "http://localhost:8089/v1"
        self.api_key = "no-api-key-required"
    
    def show_api_dialog(self):
        dialog = APIDialog(self)
        dialog.url_edit.setText(self.api_url)
        dialog.key_edit.setText(self.api_key)
        if dialog.exec_():
            self.api_url, self.api_key = dialog.get_values()
            if self.data_refine_window:
                self.data_refine_window.vlm_api_url = self.api_url
                self.data_refine_window.api_key = self.api_key
            if self.data_generate_window:
                # 更新数据制备的API设置
                pass
    
    def show_help(self):
        """显示帮助对话框"""
        try:
            with open('help.json', 'r', encoding='utf-8') as f:
                help_data = json.load(f)
        except:
            help_data = {
                "data_select": "数据筛选模块帮助内容未加载",
                "data_generate": "数据制备模块帮助内容未加载",
                "data_refine": "数据精炼模块帮助内容未加载"
            }
        
        dialog = HelpDialog(help_data, self)
        dialog.exec_()
    
    def show_data_select(self):
        if not self.data_select_imported:
            try:
                import importlib
                data_select = importlib.import_module('data_select')
                self.data_select_imported = True
                self.data_select_window = data_select.ImageDataCleaner()
                self.data_select_window.image_display.setStyleSheet(
                    "border: 1px solid #cce6ff; background-color: #ffffff;")
                self.apply_button_style(self.data_select_window)
                layout = QVBoxLayout(self.select_page)
                layout.setContentsMargins(10, 10, 10, 10)
                layout.addWidget(self.data_select_window)
            except Exception as e:
                error_label = QLabel(f"导入错误: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet("color: #ff5555; font-size: 16px;")
                layout = QVBoxLayout(self.select_page)
                layout.setContentsMargins(10, 10, 10, 10)
                layout.addWidget(error_label)
        self.content.setCurrentIndex(1)
    
    def show_data_generate(self):
        if not self.data_generate_imported:
            try:
                import importlib
                data_generate = importlib.import_module('data_generate')
                self.data_generate_imported = True
                self.data_generate_window = data_generate.DataGenerator()
                self.apply_button_style(self.data_generate_window)
                layout = QVBoxLayout(self.generate_page)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.data_generate_window)
            except Exception as e:
                error_label = QLabel(f"导入错误: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet("color: #ff5555; font-size: 16px;")
                layout = QVBoxLayout(self.generate_page)
                layout.addWidget(error_label)
        self.content.setCurrentIndex(2)
    
    def show_data_refine(self):
        if not self.data_refine_imported:
            try:
                import importlib
                data_refine = importlib.import_module('data_refine')
                self.data_refine_imported = True
                self.data_refine_window = data_refine.ImageTextAnnotator()
                self.data_refine_window.setStyleSheet("""
                    QFrame, QGroupBox, QWidget {
                        background-color: #ffffff;
                        color: #000000;
                    }
                    QTextEdit, QLineEdit, QListWidget {
                        background-color: #ffffff;
                        color: #000000;
                        border: 1px solid #cce6ff;
                    }
                """)
                self.apply_button_style(self.data_refine_window)
                
                # 移除帮助菜单
                help_menu = self.data_refine_window.menuBar().findChild(QMenu, "帮助")
                if help_menu:
                    self.data_refine_window.menuBar().removeAction(help_menu.menuAction())
                
                layout = QVBoxLayout(self.refine_page)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.data_refine_window)
            except Exception as e:
                error_label = QLabel(f"导入错误: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet("color: #ff5555; font-size: 16px;")
                layout = QVBoxLayout(self.refine_page)
                layout.addWidget(error_label)
        self.content.setCurrentIndex(3)
    
    def apply_button_style(self, widget):
        for child in widget.findChildren(QPushButton):
            if not isinstance(child, TechButton):
                child.setStyleSheet("""
                    QPushButton {
                        background-color: #e6f7ff;
                        color: #0066cc;
                        border: 1px solid #66b3ff;
                        border-radius: 8px;
                        padding: 5px;
                        margin: 2px;
                        font: bold 9pt "Segoe UI";
                    }
                    QPushButton:hover {
                        background-color: #d1e8ff;
                        border: 1px solid #3399ff;
                    }
                    QPushButton:pressed {
                        background-color: #b3d9ff;
                    }
                """)
                child.setFont(QFont("Segoe UI", 9, QFont.Bold))
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(255, 255, 255))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(240, 249, 255))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.Button, QColor(230, 247, 255))
    palette.setColor(QPalette.ButtonText, QColor(0, 89, 179))
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(0, 102, 204))
    palette.setColor(QPalette.Highlight, QColor(204, 230, 255))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)
    
    app.setStyleSheet("""
        QPushButton {
            background-color: #e6f7ff;
            color: #0066cc;
            border: 1px solid #66b3ff;
            border-radius: 8px;
            padding: 5px;
            margin: 2px;
            font: bold 9pt "Segoe UI";
        }
        QPushButton:hover {
            background-color: #d1e8ff;
            border: 1px solid #3399ff;
        }
        QPushButton:pressed {
            background-color: #b3d9ff;
        }
    """)
    
    if os.path.exists("./icons/CASC-LOGO-transparency.png"):
        app.setWindowIcon(QIcon("./icons/CASC-LOGO-transparency.png"))
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

