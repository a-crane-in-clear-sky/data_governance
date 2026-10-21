# import sys
# import os
# from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
#                              QHBoxLayout, QPushButton, QLabel, QStackedWidget,
#                              QFrame, QSplitter, QSizePolicy)
# from PyQt5.QtCore import Qt, QSize
# from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QPixmap

# class TechButton(QPushButton):
#     def __init__(self, text, icon=None):
#         super().__init__(text)
#         self.setFixedHeight(50)
#         self.setMinimumWidth(180)
#         self.setFont(QFont("Segoe UI", 12, QFont.Bold))
#         self.normal_style = """
#             QPushButton {
#                 background-color: rgba(30, 144, 255, 0.3);
#                 color: #e0f0ff;
#                 border: 2px solid #1e90ff;
#                 border-radius: 8px;
#                 text-align: center;
#                 padding: 5px;
#                 margin: 2px;
#             }
#             QPushButton:hover {
#                 background-color: rgba(30, 144, 255, 0.6);
#                 border: 2px solid #00bfff;
#             }
#             QPushButton:pressed {
#                 background-color: rgba(30, 144, 255, 0.8);
#             }
#         """
#         self.active_style = """
#             QPushButton {
#                 background-color: rgba(50, 180, 255, 0.8);
#                 color: #ffffff;
#                 border: 2px solid #00ffff;
#                 border-radius: 8px;
#                 text-align: center;
#                 padding: 5px;
#                 margin: 2px;
#             }
#         """
#         self.setStyleSheet(self.normal_style)
#         if icon:
#             self.setIcon(QIcon(icon))
#             self.setIconSize(QSize(28, 28))

# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("多模态数据科学工具箱")
#         self.setGeometry(300, 100, 1000, 700)
#         if os.path.exists("./icons/CASC-LOGO-transparency.png"):
#             self.setWindowIcon(QIcon("./icons/CASC-LOGO-transparency.png"))
        
#         # 创建主布局
#         main_widget = QWidget()
#         main_widget.setStyleSheet("background-color: #0a1423;")
#         main_layout = QHBoxLayout(main_widget)
#         main_layout.setContentsMargins(0, 0, 0, 0)
#         main_layout.setSpacing(0)
        
#         # 创建可拉动的侧边栏
#         self.splitter = QSplitter(Qt.Horizontal)
#         main_layout.addWidget(self.splitter)
        
#         # 创建侧边栏
#         sidebar = QWidget()
#         sidebar.setMinimumWidth(180)
#         sidebar.setMaximumWidth(350)
#         sidebar.setStyleSheet("background-color: rgba(20, 30, 50, 0.85); border-right: 1px solid #1e3a5f;")
#         sidebar_layout = QVBoxLayout(sidebar)
#         sidebar_layout.setContentsMargins(10, 15, 10, 15)
#         sidebar_layout.setSpacing(15)
        
#         # 添加侧边栏标题
#         title = QLabel("多模态数据治理工具平台")
#         title.setFont(QFont("Segoe UI", 16, QFont.Bold))
#         title.setStyleSheet("color: #4fc3f7; padding: 8px; background-color: rgba(30, 40, 60, 0.5); border-radius: 8px; border: 1px solid #1e90ff;")
#         title.setAlignment(Qt.AlignCenter)
#         title.setWordWrap(True)
#         sidebar_layout.addWidget(title)
        
#         # 添加分隔线
#         separator = QFrame()
#         separator.setFrameShape(QFrame.HLine)
#         separator.setFrameShadow(QFrame.Sunken)
#         separator.setStyleSheet("background-color: #1e3a5f; height: 2px;")
#         sidebar_layout.addWidget(separator)
        
#         # 添加按钮
#         self.btn_select = TechButton("数据筛选", "./icons/CASC-LOGO-transparency.png")
#         self.btn_select.clicked.connect(self.show_data_select)
#         sidebar_layout.addWidget(self.btn_select)
        
#         # 添加数据制备按钮
#         self.btn_generate = TechButton("数据制备", "./icons/CASC-LOGO-transparency.png")
#         self.btn_generate.clicked.connect(self.show_data_generate)
#         sidebar_layout.addWidget(self.btn_generate)
        
#         self.btn_refine = TechButton("数据精炼", "./icons/CASC-LOGO-transparency.png")
#         self.btn_refine.clicked.connect(self.show_data_refine)
#         sidebar_layout.addWidget(self.btn_refine)
        
#         sidebar_layout.addStretch(1)  # 伸缩空间
        
#         # 作者信息部分
#         author_frame = QFrame()
#         author_frame.setStyleSheet("background-color: rgba(30, 40, 60, 0.5); border-radius: 8px; padding: 8px;")
#         author_layout = QVBoxLayout(author_frame)
        
#         org_label = QLabel("中国航天科技\n体系与创新研究院\n航天智能前沿所\n大模型技术研究室\n多模态模型组")
#         org_label.setFont(QFont("Segoe UI", 10))
#         org_label.setStyleSheet("color: #90caf9;")
#         org_label.setAlignment(Qt.AlignCenter)
#         org_label.setWordWrap(True)
#         author_layout.addWidget(org_label)
        
#         copyright_label = QLabel("@2025 版权所有")
#         copyright_label.setFont(QFont("Segoe UI", 9))
#         copyright_label.setStyleSheet("color: #64b5f6;")
#         copyright_label.setAlignment(Qt.AlignCenter)
#         copyright_label.setWordWrap(True)
#         author_layout.addWidget(copyright_label)
        
#         author_label = QLabel("作者: Lin, X")
#         author_label.setFont(QFont("Segoe UI", 10))
#         author_label.setStyleSheet("color: #90caf9;")
#         author_label.setAlignment(Qt.AlignCenter)
#         author_label.setWordWrap(True)
#         author_layout.addWidget(author_label)
        
#         sidebar_layout.addWidget(author_frame)
        
#         # 添加Logo
#         logo_frame = QFrame()
#         logo_frame.setStyleSheet("background: transparent;")
#         logo_layout = QVBoxLayout(logo_frame)
#         logo_layout.setAlignment(Qt.AlignCenter)
        
#         if os.path.exists("./icons/CASC-LOGO-transparency.png"):
#             logo_label = QLabel()
#             logo_pixmap = QPixmap("./icons/CASC-LOGO-transparency.png").scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
#             logo_label.setPixmap(logo_pixmap)
#             logo_label.setAlignment(Qt.AlignCenter)
#             logo_layout.addWidget(logo_label)
        
#         sidebar_layout.addWidget(logo_frame)
        
#         # 创建主内容区
#         self.content = QStackedWidget()
#         self.content.setStyleSheet("""
#             QWidget {
#                 background-color: #0a1423;
#                 color: #e0f0ff;
#                 font-size: 16px;
#                 border: 2px solid #00ffff;
#                 border-radius: 10px;
#             }
#             QLabel {
#                 color: #ffffff;
#                 font-size: 18px;
#             }
#             QPushButton {
#                 background-color: rgba(30, 144, 255, 0.5);
#                 color: #ffffff;
#                 border: 1px solid #00ffff;
#                 border-radius: 5px;
#                 padding: 8px;
#                 font-size: 16px;
#             }
#             QPushButton:hover {
#                 background-color: rgba(30, 144, 255, 0.8);
#             }
#             QLineEdit, QTextEdit, QComboBox {
#                 background-color: rgba(10, 20, 35, 0.7);
#                 color: #ffffff;
#                 border: 1px solid #1e90ff;
#                 border-radius: 5px;
#                 padding: 5px;
#                 font-size: 16px;
#             }
#         """)
        
#         # 添加初始页面
#         self.init_page = QWidget()
#         self.init_page.setStyleSheet("background: transparent;")
#         init_layout = QVBoxLayout(self.init_page)
#         init_layout.addStretch()
        
#         welcome = QLabel("欢迎使用多模态数据科学工具箱")
#         welcome.setFont(QFont("Segoe UI", 24, QFont.Bold))
#         welcome.setStyleSheet("color: #e0f0ff; padding: 15px;")
#         welcome.setAlignment(Qt.AlignCenter)
#         init_layout.addWidget(welcome)
        
#         hint = QLabel("请从侧边栏选择功能模块")
#         hint.setFont(QFont("Segoe UI", 14))
#         hint.setStyleSheet("color: #a0a0c0; padding: 15px;")
#         hint.setAlignment(Qt.AlignCenter)
#         init_layout.addWidget(hint)
        
#         if os.path.exists("./icons/CASC-LOGO-transparency.png"):
#             icon_label = QLabel()
#             icon_pixmap = QPixmap("./icons/CASC-LOGO-transparency.png").scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
#             icon_label.setPixmap(icon_pixmap)
#             icon_label.setAlignment(Qt.AlignCenter)
#             init_layout.addWidget(icon_label)
        
#         init_layout.addStretch()
        
#         # 添加功能页面
#         self.select_page = QWidget()
#         self.generate_page = QWidget()
#         self.refine_page = QWidget()
        
#         self.content.addWidget(self.init_page)
#         self.content.addWidget(self.select_page)
#         self.content.addWidget(self.generate_page)
#         self.content.addWidget(self.refine_page)
        
#         # 将侧边栏和内容添加到分割器
#         self.splitter.addWidget(sidebar)
#         self.splitter.addWidget(self.content)
#         self.splitter.setSizes([220, 780])
        
#         # 设置分割器手柄样式
#         self.splitter.setStyleSheet("""
#             QSplitter::handle {
#                 background-color: #1e3a5f;
#                 width: 5px;
#             }
#             QSplitter::handle:hover {
#                 background-color: #00bfff;
#             }
#         """)
        
#         self.setCentralWidget(main_widget)
        
#         # 初始化模块状态
#         self.data_select_imported = False
#         self.data_generate_imported = False
#         self.data_refine_imported = False
#         self.data_select_window = None
#         self.data_generate_window = None
#         self.data_refine_window = None
    
#     def show_data_select(self):
#         if not self.data_select_imported:
#             try:
#                 import importlib
#                 data_select = importlib.import_module('data_select')
#                 self.data_select_imported = True
#                 self.data_select_window = data_select.ImageDataCleaner()
#                 layout = QVBoxLayout(self.select_page)
#                 layout.setContentsMargins(0, 0, 0, 0)
#                 layout.addWidget(self.data_select_window)
#             except Exception as e:
#                 error_label = QLabel(f"导入错误: {str(e)}")
#                 error_label.setAlignment(Qt.AlignCenter)
#                 error_label.setStyleSheet("color: #ff5555; font-size: 16px;")
#                 layout = QVBoxLayout(self.select_page)
#                 layout.addWidget(error_label)
#         self.content.setCurrentIndex(1)
    
#     def show_data_generate(self):
#         if not self.data_generate_imported:
#             try:
#                 import importlib
#                 data_generate = importlib.import_module('data_generate')
#                 self.data_generate_imported = True
#                 self.data_generate_window = data_generate.DataGenerator()
#                 layout = QVBoxLayout(self.generate_page)
#                 layout.setContentsMargins(0, 0, 0, 0)
#                 layout.addWidget(self.data_generate_window)
#             except Exception as e:
#                 error_label = QLabel(f"导入错误: {str(e)}")
#                 error_label.setAlignment(Qt.AlignCenter)
#                 error_label.setStyleSheet("color: #ff5555; font-size: 16px;")
#                 layout = QVBoxLayout(self.generate_page)
#                 layout.addWidget(error_label)
#         self.content.setCurrentIndex(2)
    
#     def show_data_refine(self):
#         if not self.data_refine_imported:
#             try:
#                 import importlib
#                 data_refine = importlib.import_module('data_refine')
#                 self.data_refine_imported = True
#                 self.data_refine_window = data_refine.ImageTextAnnotator()
#                 layout = QVBoxLayout(self.refine_page)
#                 layout.setContentsMargins(0, 0, 0, 0)
#                 layout.addWidget(self.data_refine_window)
#             except Exception as e:
#                 error_label = QLabel(f"导入错误: {str(e)}")
#                 error_label.setAlignment(Qt.AlignCenter)
#                 error_label.setStyleSheet("color: #ff5555; font-size: 16px;")
#                 layout = QVBoxLayout(self.refine_page)
#                 layout.addWidget(error_label)
#         self.content.setCurrentIndex(3)

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     app.setStyle("Fusion")
#     palette = app.palette()
#     palette.setColor(QPalette.Window, QColor(10, 20, 35))
#     palette.setColor(QPalette.WindowText, QColor(200, 220, 255))
#     palette.setColor(QPalette.Button, QColor(30, 40, 60))
#     palette.setColor(QPalette.ButtonText, QColor(200, 220, 255))
#     palette.setColor(QPalette.Highlight, QColor(30, 144, 255))
#     palette.setColor(QPalette.HighlightedText, Qt.white)
#     app.setPalette(palette)
    
#     if os.path.exists("./icons/CASC-LOGO-transparency.png"):
#         app.setWindowIcon(QIcon("./icons/CASC-LOGO-transparency.png"))
    
#     window = MainWindow()
#     window.show()
#     sys.exit(app.exec_())


import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget,
                             QFrame, QSplitter, QSizePolicy)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QPixmap

class TechButton(QPushButton):
    def __init__(self, text, icon=None):
        super().__init__(text)
        self.setFixedHeight(50)
        self.setMinimumWidth(180)
        self.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.normal_style = """
            QPushButton {
                background-color: rgba(30, 144, 255, 0.3);
                color: #e0f0ff;
                border: 2px solid #1e90ff;
                border-radius: 8px;
                text-align: center;
                padding: 5px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: rgba(30, 144, 255, 0.6);
                border: 2px solid #00bfff;
            }
            QPushButton:pressed {
                background-color: rgba(30, 144, 255, 0.8);
            }
        """
        self.active_style = """
            QPushButton {
                background-color: rgba(50, 180, 255, 0.8);
                color: #ffffff;
                border: 2px solid #00ffff;
                border-radius: 8px;
                text-align: center;
                padding: 5px;
                margin: 2px;
            }
        """
        self.setStyleSheet(self.normal_style)
        if icon:
            self.setIcon(QIcon(icon))
            self.setIconSize(QSize(28, 28))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多模态数据科学工具箱")
        self.setGeometry(300, 100, 1000, 700)
        if os.path.exists("./icons/CASC-LOGO-transparency.png"):
            self.setWindowIcon(QIcon("./icons/CASC-LOGO-transparency.png"))
        
        # 创建主布局
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: #0a1423;")
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建可拉动的侧边栏
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # 创建侧边栏
        sidebar = QWidget()
        sidebar.setMinimumWidth(180)
        sidebar.setMaximumWidth(350)
        sidebar.setStyleSheet("background-color: rgba(20, 30, 50, 0.85); border-right: 1px solid #1e3a5f;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 15, 10, 15)
        sidebar_layout.setSpacing(15)
        
        # 添加侧边栏标题
        title = QLabel("多模态数据治理工具平台")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #4fc3f7; padding: 8px; background-color: rgba(30, 40, 60, 0.5); border-radius: 8px; border: 1px solid #1e90ff;")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        sidebar_layout.addWidget(title)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #1e3a5f; height: 2px;")
        sidebar_layout.addWidget(separator)
        
        # 添加按钮
        self.btn_select = TechButton("数据筛选", "./icons/CASC-LOGO-transparency.png")
        self.btn_select.clicked.connect(self.show_data_select)
        sidebar_layout.addWidget(self.btn_select)
        
        # 添加数据制备按钮
        self.btn_generate = TechButton("数据制备", "./icons/CASC-LOGO-transparency.png")
        self.btn_generate.clicked.connect(self.show_data_generate)
        sidebar_layout.addWidget(self.btn_generate)
        
        self.btn_refine = TechButton("数据精炼", "./icons/CASC-LOGO-transparency.png")
        self.btn_refine.clicked.connect(self.show_data_refine)
        sidebar_layout.addWidget(self.btn_refine)
        
        sidebar_layout.addStretch(1)
        
        # 作者信息部分
        author_frame = QFrame()
        author_frame.setStyleSheet("background-color: rgba(30, 40, 60, 0.5); border-radius: 8px; padding: 8px;")
        author_layout = QVBoxLayout(author_frame)
        
        org_label = QLabel("中国航天科技\n体系与创新研究院\n航天智能前沿所\n大模型技术研究室\n多模态模型组")
        org_label.setFont(QFont("Segoe UI", 10))
        org_label.setStyleSheet("color: #90caf9;")
        org_label.setAlignment(Qt.AlignCenter)
        org_label.setWordWrap(True)
        author_layout.addWidget(org_label)
        
        copyright_label = QLabel("@2025 版权所有")
        copyright_label.setFont(QFont("Segoe UI", 9))
        copyright_label.setStyleSheet("color: #64b5f6;")
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setWordWrap(True)
        author_layout.addWidget(copyright_label)
        
        author_label = QLabel("作者: Lin, X")
        author_label.setFont(QFont("Segoe UI", 10))
        author_label.setStyleSheet("color: #90caf9;")
        author_label.setAlignment(Qt.AlignCenter)
        author_label.setWordWrap(True)
        author_layout.addWidget(author_label)
        
        sidebar_layout.addWidget(author_frame)
        
        # 添加Logo
        logo_frame = QFrame()
        logo_frame.setStyleSheet("background: transparent;")
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setAlignment(Qt.AlignCenter)
        
        if os.path.exists("./icons/CASC-LOGO-transparency.png"):
            logo_label = QLabel()
            logo_pixmap = QPixmap("./icons/CASC-LOGO-transparency.png").scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            logo_layout.addWidget(logo_label)
        
        sidebar_layout.addWidget(logo_frame)
        
        # 创建主内容区
        self.content = QStackedWidget()
        
        # 添加初始页面
        self.init_page = QWidget()
        init_layout = QVBoxLayout(self.init_page)
        init_layout.addStretch()
        
        welcome = QLabel("欢迎使用多模态数据科学工具箱")
        welcome.setFont(QFont("Segoe UI", 24, QFont.Bold))
        welcome.setStyleSheet("color: #e0f0ff; padding: 15px;")
        welcome.setAlignment(Qt.AlignCenter)
        init_layout.addWidget(welcome)
        
        hint = QLabel("请从侧边栏选择功能模块")
        hint.setFont(QFont("Segoe UI", 14))
        hint.setStyleSheet("color: #a0a0c0; padding: 15px;")
        hint.setAlignment(Qt.AlignCenter)
        init_layout.addWidget(hint)
        
        if os.path.exists("./icons/CASC-LOGO-transparency.png"):
            icon_label = QLabel()
            icon_pixmap = QPixmap("./icons/CASC-LOGO-transparency.png").scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
            icon_label.setAlignment(Qt.AlignCenter)
            init_layout.addWidget(icon_label)
        
        init_layout.addStretch()
        
        # 添加功能页面
        self.select_page = QWidget()
        self.generate_page = QWidget()
        self.refine_page = QWidget()
        
        # 应用样式到各页面
        self.content.setStyleSheet("""
            QWidget {
                background-color: #0a1423;
                color: #e0f0ff;
                font-size: 16px;
            }
        """)
        self.generate_page.setStyleSheet("""
            background-color: #0a1423;
            border: 2px solid #00ffff;
            border-radius: 10px;
        """)
        self.refine_page.setStyleSheet("""
            background-color: #0a1423;
            border: 2px solid #00ffff;
            border-radius: 10px;
        """)
        
        self.content.addWidget(self.init_page)
        self.content.addWidget(self.select_page)
        self.content.addWidget(self.generate_page)
        self.content.addWidget(self.refine_page)
        
        # 将侧边栏和内容添加到分割器
        self.splitter.addWidget(sidebar)
        self.splitter.addWidget(self.content)
        self.splitter.setSizes([220, 780])
        
        # 设置分割器手柄样式
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #1e3a5f;
                width: 5px;
            }
            QSplitter::handle:hover {
                background-color: #00bfff;
            }
        """)
        
        self.setCentralWidget(main_widget)
        
        # 初始化模块状态
        self.data_select_imported = False
        self.data_generate_imported = False
        self.data_refine_imported = False
        self.data_select_window = None
        self.data_generate_window = None
        self.data_refine_window = None
    
    def show_data_select(self):
        if not self.data_select_imported:
            try:
                import importlib
                data_select = importlib.import_module('data_select')
                self.data_select_imported = True
                self.data_select_window = data_select.ImageDataCleaner()
                layout = QVBoxLayout(self.select_page)
                layout.setContentsMargins(10, 10, 10, 10)  # 添加边距避免遮挡
                layout.addWidget(self.data_select_window)
            except Exception as e:
                error_label = QLabel(f"导入错误: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet("color: #ff5555; font-size: 16px;")
                layout = QVBoxLayout(self.select_page)
                layout.setContentsMargins(10, 10, 10, 10)  # 错误页面也添加边距
                layout.addWidget(error_label)
        self.content.setCurrentIndex(1)
    
    def show_data_generate(self):
        if not self.data_generate_imported:
            try:
                import importlib
                data_generate = importlib.import_module('data_generate')
                self.data_generate_imported = True
                self.data_generate_window = data_generate.DataGenerator()
                layout = QVBoxLayout(self.generate_page)
                layout.setContentsMargins(0, 0, 0, 0)  # 保持原样
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
                layout = QVBoxLayout(self.refine_page)
                layout.setContentsMargins(0, 0, 0, 0)  # 保持原样
                layout.addWidget(self.data_refine_window)
            except Exception as e:
                error_label = QLabel(f"导入错误: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet("color: #ff5555; font-size: 16px;")
                layout = QVBoxLayout(self.refine_page)
                layout.addWidget(error_label)
        self.content.setCurrentIndex(3)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(10, 20, 35))
    palette.setColor(QPalette.WindowText, QColor(200, 220, 255))
    palette.setColor(QPalette.Button, QColor(30, 40, 60))
    palette.setColor(QPalette.ButtonText, QColor(200, 220, 255))
    palette.setColor(QPalette.Highlight, QColor(30, 144, 255))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(palette)
    
    if os.path.exists("./icons/CASC-LOGO-transparency.png"):
        app.setWindowIcon(QIcon("./icons/CASC-LOGO-transparency.png"))
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

