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
        self.setMinimumHeight(50)
        self.setMaximumHeight(100)  # 设置最大高度以允许文本换行
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)  # 修改为Preferred防止过度扩展
        
        # 设置字体
        font = QFont("Segoe UI", 9, QFont.Bold)
        font.setStyleStrategy(QFont.PreferAntialias)
        self.setFont(font)
        
        # 淡蓝色科技风格按钮
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
        
        # # 正确设置文本自动换行
        # self.setWordWrap(True)  # 使用QPushButton的内置方法

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多模态数据科学工具箱")
        self.setGeometry(300, 100, 1000, 700)
        if os.path.exists("./icons/CASC-LOGO-transparency.png"):
            self.setWindowIcon(QIcon("./icons/CASC-LOGO-transparency.png"))
        
        # 创建主布局 - 白色背景
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: #ffffff;")
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建可拉动的侧边栏
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # 创建侧边栏 - 淡蓝色背景
        sidebar = QWidget()
        sidebar.setMinimumWidth(150)
        sidebar.setMaximumWidth(250)
        sidebar.setStyleSheet("background-color: #f0f9ff; border-right: 1px solid #cce6ff;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(5, 5, 5, 5)
        sidebar_layout.setSpacing(5)
        
        # 创建标题栏（Logo和标题在同一行）
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)
        
        # 添加Logo（在标题左侧）
        if os.path.exists("./icons/CASC-LOGO-transparency.png"):
            logo_label = QLabel()
            logo_pixmap = QPixmap("./icons/CASC-LOGO-transparency.png").scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            title_layout.addWidget(logo_label)
        
        # 添加标题文本 - 深蓝色文字
        title = QLabel("多模态数据治理工具平台")
        title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        title.setStyleSheet("color: #0059b3; padding: 6px; background-color: #e6f2ff; border-radius: 8px; border: 1px solid #99ccff;")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        title_layout.addWidget(title)
        
        sidebar_layout.addLayout(title_layout)
        
        # 添加分隔线 - 淡蓝色
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #99ccff; height: 2px;")
        sidebar_layout.addWidget(separator)
        
        # 按钮容器
        button_container = QWidget()
        button_container.setStyleSheet("background-color: transparent;")
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)
        
        # 创建按钮（全部支持自动换行）
        self.btn_select = TechButton("数据筛选", "./icons/CASC-LOGO-transparency.png")
        self.btn_select.clicked.connect(self.show_data_select)
        button_layout.addWidget(self.btn_select)
        
        self.btn_generate = TechButton("数据制备", "./icons/CASC-LOGO-transparency.png")
        self.btn_generate.clicked.connect(self.show_data_generate)
        button_layout.addWidget(self.btn_generate)
        
        self.btn_refine = TechButton("数据精炼", "./icons/CASC-LOGO-transparency.png")
        self.btn_refine.clicked.connect(self.show_data_refine)
        button_layout.addWidget(self.btn_refine)
        
        sidebar_layout.addWidget(button_container)
        
        sidebar_layout.addStretch(1)
        
        # 作者信息部分 - 淡蓝色背景
        author_frame = QFrame()
        author_frame.setStyleSheet("background-color: #e6f2ff; border-radius: 8px; padding: 6px; border: 1px solid #cce6ff;")
        author_layout = QVBoxLayout(author_frame)
        
        org_label = QLabel("中国航天科技\n体系与创新研究院\n航天智能前沿所\n大模型技术研究室\n多模态模型组")
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
        
        # 创建主内容区 - 白色背景
        self.content = QStackedWidget()
        self.content.setStyleSheet("background-color: #ffffff;")
        
        # 添加初始页面
        self.init_page = QWidget()
        self.init_page.setStyleSheet("background-color: #ffffff;")
        init_layout = QVBoxLayout(self.init_page)
        init_layout.addStretch()
        
        # 欢迎文字 - 深蓝色
        welcome = QLabel("欢迎使用多模态数据科学工具箱")
        welcome.setFont(QFont("Segoe UI", 18, QFont.Bold))
        welcome.setStyleSheet("color: #0059b3; padding: 15px;")
        welcome.setAlignment(Qt.AlignCenter)
        init_layout.addWidget(welcome)
        
        # 提示文字 - 蓝色
        hint = QLabel("请从侧边栏选择功能模块")
        hint.setFont(QFont("Segoe UI", 10))
        hint.setStyleSheet("color: #3399ff; padding: 15px;")
        hint.setAlignment(Qt.AlignCenter)
        init_layout.addWidget(hint)
        
        # 添加Logo - 居中显示
        if os.path.exists("./icons/CASC-LOGO-transparency.png"):
            icon_label = QLabel()
            icon_pixmap = QPixmap("./icons/CASC-LOGO-transparency.png").scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
            icon_label.setAlignment(Qt.AlignCenter)
            init_layout.addWidget(icon_label)
        
        init_layout.addStretch()
        
        # 添加功能页面
        self.select_page = QWidget()
        self.select_page.setStyleSheet("background-color: #ffffff;")
        self.generate_page = QWidget()
        self.generate_page.setStyleSheet("background-color: #ffffff;")
        self.refine_page = QWidget()
        self.refine_page.setStyleSheet("background-color: #ffffff;")
        
        # 设置统一边框样式 - 淡蓝色
        self.select_page.setStyleSheet("border: 1px solid #cce6ff; border-radius: 10px; background-color: #ffffff;")
        self.generate_page.setStyleSheet("border: 1px solid #cce6ff; border-radius: 10px; background-color: #ffffff;")
        self.refine_page.setStyleSheet("border: 1px solid #cce6ff; border-radius: 10px; background-color: #ffffff;")
        
        self.content.addWidget(self.init_page)
        self.content.addWidget(self.select_page)
        self.content.addWidget(self.generate_page)
        self.content.addWidget(self.refine_page)
        
        # 将侧边栏和内容添加到分割器
        self.splitter.addWidget(sidebar)
        self.splitter.addWidget(self.content)
        self.splitter.setSizes([150, 850])
        
        # 设置分割器手柄样式 - 淡蓝色
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
                
                # 修复图像预览区域背景色
                self.data_select_window.image_display.setStyleSheet(
                    "border: 1px solid #cce6ff; background-color: #ffffff;")
                
                # 统一所有按钮样式
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
                
                # 统一所有按钮样式
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
                
                # 修复卡片区域背景色 - 白色背景
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
                
                # 统一所有按钮样式
                self.apply_button_style(self.data_refine_window)
                
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
        """递归应用统一按钮样式到所有子控件"""
        for child in widget.findChildren(QPushButton):
            if not isinstance(child, TechButton):  # 避免覆盖侧边栏按钮
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
    
    # 设置全局白底黑字、淡蓝色科技风格
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
    
    # 设置全局按钮样式
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
