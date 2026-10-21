import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QLinearGradient, QPainter, QPalette

class TechButton(QPushButton):
    """自定义科技感按钮"""
    def __init__(self, text, icon=None):
        super().__init__(text)
        self.setFixedHeight(50)
        self.setMinimumWidth(150)
        self.setFont(QFont("Segoe UI", 12))
        
        # 设置按钮样式
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 144, 255, 0.2);
                color: #e0e0ff;
                border: 1px solid #1e90ff;
                border-radius: 5px;
                text-align: left;
                padding-left: 20px;
            }
            QPushButton:hover {
                background-color: rgba(30, 144, 255, 0.4);
                border: 1px solid #00bfff;
            }
            QPushButton:pressed {
                background-color: rgba(30, 144, 255, 0.6);
            }
        """)
        
        if icon:
            self.setIcon(QIcon(icon))
            self.setIconSize(QSize(24, 24))

class GradientWidget(QWidget):
    """渐变背景组件"""
    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(10, 20, 35))
        gradient.setColorAt(1.0, QColor(25, 35, 60))
        painter.fillRect(self.rect(), gradient)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("数据科学工具")
        self.setGeometry(300, 100, 900, 600)
        
        # 设置主窗口图标（统一使用CASC-LOGO.png）
        if os.path.exists("CASC-LOGO.png"):
            self.setWindowIcon(QIcon("CASC-LOGO.png"))
        
        # 设置主窗口背景
        self.setStyleSheet("background-color: #0a1423;")
        
        # 创建主布局
        main_widget = GradientWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建侧边栏
        sidebar = QWidget()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("background-color: rgba(20, 30, 50, 0.8);")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(15)
        
        # 添加侧边栏标题
        title = QLabel("多模态数据治理工具箱")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #1e90ff; padding-bottom: 20px;")
        title.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(title)
        
        # 添加按钮
        self.btn_select = TechButton("数据选择", "icons/select.png")
        self.btn_select.clicked.connect(self.show_data_select)
        sidebar_layout.addWidget(self.btn_select)
        
        self.btn_refine = TechButton("数据精炼", "icons/refine.png")
        self.btn_refine.clicked.connect(self.show_data_refine)
        sidebar_layout.addWidget(self.btn_refine)
        
        # 添加伸缩空间
        sidebar_layout.addStretch()
        
        # 创建主内容区
        self.content = QStackedWidget()
        self.content.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 25, 40, 0.7);
                border-radius: 10px;
                border: 1px solid #1e3a5f;
            }
        """)
        
        # 添加初始页面
        self.init_page = QWidget()
        self.init_page.setStyleSheet("background: transparent;")
        init_layout = QVBoxLayout(self.init_page)
        init_layout.addStretch()
        welcome = QLabel("欢迎使用数据科学工具箱")
        welcome.setFont(QFont("Segoe UI", 24, QFont.Bold))
        welcome.setStyleSheet("color: #e0e0ff;")
        welcome.setAlignment(Qt.AlignCenter)
        init_layout.addWidget(welcome)
        
        hint = QLabel("请从侧边栏选择功能模块")
        hint.setFont(QFont("Segoe UI", 14))
        hint.setStyleSheet("color: #a0a0c0; padding-top: 20px;")
        hint.setAlignment(Qt.AlignCenter)
        init_layout.addWidget(hint)
        init_layout.addStretch()
        
        # 添加功能页面占位
        self.select_page = QWidget()
        self.refine_page = QWidget()
        
        # 添加到堆栈窗口
        self.content.addWidget(self.init_page)
        self.content.addWidget(self.select_page)
        self.content.addWidget(self.refine_page)
        
        # 将侧边栏和内容添加到主布局
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.content, 1)
        
        self.setCentralWidget(main_widget)
        
        # 初始化模块状态
        self.data_select_imported = False
        self.data_refine_imported = False
        self.data_select_window = None
        self.data_refine_window = None
    
    def show_data_select(self):
        """显示数据选择界面并导入模块"""
        # 导入模块
        if not self.data_select_imported:
            try:
                # 使用importlib动态导入模块
                import importlib
                data_select = importlib.import_module('data_select')
                self.data_select_imported = True
                
                # 创建数据选择窗口
                self.data_select_window = data_select.ImageDataCleaner()
                
                # 添加到内容页面
                layout = QVBoxLayout(self.select_page)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.data_select_window)
                
                print("数据选择模块导入成功")
            except Exception as e:
                error_label = QLabel(f"导入错误: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet("color: #ff5555; font-size: 16px;")
                layout = QVBoxLayout(self.select_page)
                layout.addWidget(error_label)
                print(f"导入data_select.py失败: {e}")
                return
        
        # 切换到数据选择页面
        self.content.setCurrentIndex(1)
        print("正在执行数据选择功能...")
    
    def show_data_refine(self):
        """显示数据精炼界面并导入模块"""
        # 导入模块
        if not self.data_refine_imported:
            try:
                # 使用importlib动态导入模块
                import importlib
                data_refine = importlib.import_module('data_refine')
                self.data_refine_imported = True
                
                # 创建数据精炼窗口
                self.data_refine_window = data_refine.ImageTextAnnotator()
                
                # 添加到内容页面
                layout = QVBoxLayout(self.refine_page)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.data_refine_window)
                
                print("数据精炼模块导入成功")
            except Exception as e:
                error_label = QLabel(f"导入错误: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet("color: #ff5555; font-size: 16px;")
                layout = QVBoxLayout(self.refine_page)
                layout.addWidget(error_label)
                print(f"导入data_refine.py失败: {e}")
                return
        
        # 切换到数据精炼页面
        self.content.setCurrentIndex(2)
        print("正在执行数据精炼功能...")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(10, 20, 35))
    palette.setColor(QPalette.WindowText, QColor(200, 200, 255))
    app.setPalette(palette)
    
    # 设置应用图标（统一使用icons/CASC-LOGO-transparency.png）
    if os.path.exists("./icons/CASC-LOGO-transparency.png"):
        app.setWindowIcon(QIcon("./icons/CASC-LOGO-transparency.png"))
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())