import os
import json
import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QLabel, QTextEdit, QFileDialog, QProgressBar,
                             QShortcut, QGroupBox, QSizePolicy, QFrame, QMenu, QAction, QMessageBox,
                             QGraphicsDropShadowEffect)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QKeySequence, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QThread, pyqtSignal

# ========================================================
# 多进程处理工作线程
# ========================================================
class SearchWorker(QThread):
    """后台工作线程，用于在搜索时处理JSON文件"""
    search_finished = pyqtSignal(list, str)  # 搜索完成信号
    progress_updated = pyqtSignal(int, int)  # 进度更新信号
    error_occurred = pyqtSignal(str)  # 错误信号
    
    def __init__(self, labels_path, search_term):
        super().__init__()
        self.labels_path = labels_path
        self.search_term = search_term
        self.running = True
    
    def run(self):
        """线程主执行函数"""
        try:
            if not os.path.exists(self.labels_path):
                self.error_occurred.emit(f"目录 {self.labels_path} 不存在！")
                return
                
            search_results = []
            json_files = [f for f in os.listdir(self.labels_path) if f.endswith(".json")]
            total_files = len(json_files)
            
            for idx, filename in enumerate(json_files):
                if not self.running:  # 检查是否已请求停止
                    return
                    
                filepath = os.path.join(self.labels_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # 检查annotations中是否包含搜索词
                        if self.contains_search_term(data, self.search_term):
                            search_results.append(filename.replace(".json", ""))
                except Exception as e:
                    self.error_occurred.emit(f"读取文件 {filename} 出错: {str(e)}")
                    continue
                
                # 每处理5个文件更新一次进度，减少UI更新频率
                if idx % 5 == 0:
                    self.progress_updated.emit(idx + 1, total_files)
            
            # 确保最后100%更新
            self.progress_updated.emit(total_files, total_files)
            self.search_finished.emit(search_results, self.search_term)
            
        except Exception as e:
            self.error_occurred.emit(f"搜索过程中发生错误: {str(e)}")
    
    def contains_search_term(self, data, search_term):
        """检查JSON数据中是否包含搜索词（修改：空搜索词返回所有文件）"""
        # 如果搜索词为空，返回所有文件
        if not search_term.strip():
            return True
            
        if "annotations" in data:
            for annotation in data["annotations"]:
                if ("class" in annotation and search_term in annotation["class"]) or \
                   ("label" in annotation and search_term in annotation["label"]):
                    return True
        return False
    
    def stop(self):
        """请求停止线程"""
        self.running = False
 
# ========================================================
# 主窗口类（已添加多进程支持）
# ========================================================
class ImageDataCleaner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多模态大模型训练数据（图像-文本）筛选工具v1.9 (多进程版)")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon("./CASC-LOGO.png"))
        
        # 初始化变量
        self.images_path = ""
        self.labels_path = ""
        self.search_results = []
        self.current_index = 0
        self.show_bbox = False
        self.current_image_with_bbox = None
        self.search_term = ""  # 存储当前的搜索关键词
        self.saved_count = 0   # 记录已保存的图片数量
        self.state_file = "data_cleaner_state.json"  # 状态保存文件
        self.search_worker = None  # 用于存储搜索工作线程
        
        # 创建主界面
        self.init_ui()
        
        # 添加快捷键
        self.setup_shortcuts()
        
        # 加载上次的工作状态
        self.load_state()
    
    def setup_shortcuts(self):
        """设置所有快捷键"""
        # 保存: Ctrl+S
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_current_image)
        
        # 上一张: 左键或上键
        prev_shortcut1 = QShortcut(QKeySequence(Qt.Key_Left), self)
        prev_shortcut1.activated.connect(self.show_previous)
        prev_shortcut2 = QShortcut(QKeySequence(Qt.Key_Up), self)
        prev_shortcut2.activated.connect(self.show_previous)
        
        # 下一张: 右键或下键
        next_shortcut1 = QShortcut(QKeySequence(Qt.Key_Right), self)
        next_shortcut1.activated.connect(self.show_next)
        next_shortcut2 = QShortcut(QKeySequence(Qt.Key_Down), self)
        next_shortcut2.activated.connect(self.show_next)
        
        # 删除(不保存): Backspace或Delete
        discard_shortcut1 = QShortcut(QKeySequence(Qt.Key_Backspace), self)
        discard_shortcut1.activated.connect(self.discard_current_image)
        discard_shortcut2 = QShortcut(QKeySequence(Qt.Key_Delete), self)
        discard_shortcut2.activated.connect(self.discard_current_image)
    
    def init_ui(self):
        # 主窗口布局
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        
        # 创建顶部布局（包含路径和搜索区域）
        top_layout = QVBoxLayout()
        top_layout.setSpacing(10)
        
        # ========================================================
        # 路径选择区域 - 使用网格布局更好
        # ========================================================
        path_layout = QHBoxLayout()
        
        # 图像路径选择按钮 (修改为下拉菜单)
        images_group = QGroupBox("图像路径")
        images_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        images_layout = QVBoxLayout()
        self.images_path_label = QLabel("未选择")
        images_layout.addWidget(self.images_path_label)
        
        # 创建带下拉菜单的按钮
        images_path_menu_button = QPushButton("选择...")
        images_path_menu_button.setFixedWidth(100)
        images_path_menu = QMenu()
        
        # 添加菜单项
        select_folder_action = QAction("选择图像文件夹", self)
        select_folder_action.triggered.connect(self.select_images_path)
        images_path_menu.addAction(select_folder_action)
        
        select_file_action = QAction("选择图像文件", self)
        select_file_action.triggered.connect(self.select_images_file)
        images_path_menu.addAction(select_file_action)
        
        images_path_menu_button.setMenu(images_path_menu)
        images_layout.addWidget(images_path_menu_button)
        
        images_group.setLayout(images_layout)
        
        # 标签路径选择按钮 (修改为下拉菜单)
        labels_group = QGroupBox("标签路径")
        labels_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        labels_layout = QVBoxLayout()
        self.labels_path_label = QLabel("未选择")
        labels_layout.addWidget(self.labels_path_label)
        
        # 创建带下拉菜单的按钮
        labels_path_menu_button = QPushButton("选择...")
        labels_path_menu_button.setFixedWidth(100)
        labels_path_menu = QMenu()
        
        # 添加菜单项
        select_folder_action = QAction("选择标签文件夹", self)
        select_folder_action.triggered.connect(self.select_labels_path)
        labels_path_menu.addAction(select_folder_action)
        
        select_file_action = QAction("选择标签文件", self)
        select_file_action.triggered.connect(self.select_labels_file)
        labels_path_menu.addAction(select_file_action)
        
        labels_path_menu_button.setMenu(labels_path_menu)
        labels_layout.addWidget(labels_path_menu_button)
        
        labels_group.setLayout(labels_layout)
        
        # 已保存图片计数
        saved_group = QGroupBox("已保存数量")
        saved_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        saved_layout = QVBoxLayout()
        self.saved_count_label = QLabel("0")
        self.saved_count_label.setAlignment(Qt.AlignCenter)
        self.saved_count_label.setFont(QFont("Arial", 16))
        saved_layout.addWidget(self.saved_count_label)
        saved_group.setLayout(saved_layout)
        
        path_layout.addWidget(images_group, 40)
        path_layout.addWidget(labels_group, 40)
        path_layout.addWidget(saved_group, 20)
        
        # 搜索区域
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索关键词（如'商业客机'），留空则提取所有文件")
        self.search_button = QPushButton("搜索")
        self.search_button.clicked.connect(self.start_search_thread)
        
        # 添加算法去重按钮
        self.dedup_button = QPushButton("算法去重")
        self.dedup_button.clicked.connect(self.dedup_images)
        self.dedup_button.setToolTip("使用算法去除重复图像")
        
        # 添加读取算法去重结果按钮
        self.load_dedup_button = QPushButton("读取算法去重结果")
        self.load_dedup_button.clicked.connect(self.load_dedup_results)
        self.load_dedup_button.setToolTip("读取算法去重结果的JSON文件")
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.dedup_button)
        search_layout.addWidget(self.load_dedup_button)
        
        # 将路径和搜索区域添加到顶部布局
        top_layout.addLayout(path_layout)
        top_layout.addLayout(search_layout)
        
        # ========================================================
        # 主显示区域（占据80%高度）
        # ========================================================
        display_layout = QVBoxLayout()
        display_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建包含图像和JSON的整体结果布局
        result_layout = QHBoxLayout()
        
        # 创建图像显示区域组
        image_group = QGroupBox("图像预览")
        image_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        image_group_layout = QVBoxLayout(image_group)
        image_group_layout.setContentsMargins(5, 10, 5, 5)
        
        # 图像显示容器
        self.image_container = QWidget()
        self.image_container_layout = QVBoxLayout()
        self.image_container_layout.setContentsMargins(5, 5, 5, 5)
        self.image_container_layout.setSpacing(5)
        
        # 图像显示标签
        self.image_display = QLabel()
        self.image_display.setAlignment(Qt.AlignCenter)
        # 修改背景色为暗色
        self.image_display.setStyleSheet("border: 1px solid #ccc; background-color: #0a1423;")
        self.image_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 图像文件名显示
        self.image_filename_label = QLabel("图像文件名: ")
        self.image_filename_label.setAlignment(Qt.AlignCenter)
        self.image_filename_label.setStyleSheet("font-weight: bold;")
        
        self.image_container_layout.addWidget(self.image_display, 9)
        self.image_container_layout.addWidget(self.image_filename_label, 1)
        self.image_container.setLayout(self.image_container_layout)
        image_group_layout.addWidget(self.image_container)
        
        # 创建JSON显示区域组
        json_group = QGroupBox("标签详情")
        json_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        json_group_layout = QVBoxLayout(json_group)
        json_group_layout.setContentsMargins(5, 10, 5, 5)
        
        # JSON显示区域
        self.json_display = QTextEdit()
        self.json_display.setReadOnly(True)
        self.json_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # JSON文件名显示
        self.json_filename_label = QLabel("标签文件名: ")
        self.json_filename_label.setAlignment(Qt.AlignCenter)
        self.json_filename_label.setStyleSheet("font-weight: bold;")
        
        json_group_layout.addWidget(self.json_display, 9)
        json_group_layout.addWidget(self.json_filename_label, 1)
        
        # 添加图像组和JSON组到结果布局
        result_layout.addWidget(image_group, 60)
        result_layout.addWidget(json_group, 40)
        display_layout.addLayout(result_layout)
        
        # ========================================================
        # 底部控制区域（占据剩余20%高度）
        # ========================================================
        bottom_layout = QVBoxLayout()
        
        # 进度条区域
        progress_layout = QHBoxLayout()
        self.progress_label = QLabel("0/0")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setMinimumWidth(80)
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("0/0")
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        
        # 导航按钮
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("上一张 (←/↑)")
        self.prev_button.clicked.connect(self.show_previous)
        self.prev_button.setEnabled(False)
        self.next_button = QPushButton("下一张 (→/↓)")
        self.next_button.clicked.connect(self.show_next)
        self.next_button.setEnabled(False)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        
        # 显示检测框按钮
        bbox_layout = QHBoxLayout()
        self.show_bbox_button = QPushButton("显示检测框")
        self.show_bbox_button.clicked.connect(self.toggle_bbox_display)
        self.hide_bbox_button = QPushButton("不显示检测框")
        self.hide_bbox_button.clicked.connect(self.toggle_bbox_display)
        bbox_layout.addWidget(self.show_bbox_button)
        bbox_layout.addWidget(self.hide_bbox_button)
        
        # 保存/不保存按钮
        save_layout = QHBoxLayout()
        self.save_button = QPushButton("保存 (Ctrl+S)")
        self.save_button.clicked.connect(self.save_current_image)
        self.save_button.setEnabled(False)
        self.discard_button = QPushButton("不保存并剔除 (Del/Backs)")
        self.discard_button.clicked.connect(self.discard_current_image)
        self.discard_button.setEnabled(False)
        save_layout.addWidget(self.save_button)
        save_layout.addWidget(self.discard_button)
        
        # 状态栏
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("font-size: 12px; padding: 5px; border-top: 1px solid #c0c0c0;")
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # 将控制元素添加到底部布局
        bottom_layout.addLayout(progress_layout)
        bottom_layout.addLayout(nav_layout)
        bottom_layout.addLayout(save_layout)
        bottom_layout.addLayout(bbox_layout)
        bottom_layout.addWidget(self.status_label, 1)
        
        # ========================================================
        # 组合所有布局
        # ========================================================
        # 创建拉伸项来控制高度比例
        main_layout.addLayout(top_layout, 20)  # 顶部区域占20%
        main_layout.addLayout(display_layout, 80)  # 显示区域占80%
        main_layout.addLayout(bottom_layout)  # 底部区域自动调整
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        self.setMinimumSize(800, 600)
        
        # ========================================================
        # 添加荧光效果
        # ========================================================
        self.add_glow_effect(self.search_button)
        self.add_glow_effect(self.dedup_button)
        self.add_glow_effect(self.load_dedup_button)
        self.add_glow_effect(self.prev_button)
        self.add_glow_effect(self.next_button)
        self.add_glow_effect(self.show_bbox_button)
        self.add_glow_effect(self.hide_bbox_button)
        self.add_glow_effect(self.save_button)
        self.add_glow_effect(self.discard_button)
    
    def add_glow_effect(self, button):
        """为按钮添加荧光效果"""
        effect = QGraphicsDropShadowEffect(button)
        effect.setColor(QColor(0, 255, 255))  # 青色发光
        effect.setBlurRadius(15)  # 发光半径
        effect.setOffset(0, 0)
        button.setGraphicsEffect(effect)
    
    def resizeEvent(self, event):
        """当窗口大小改变时重新缩放图像"""
        super().resizeEvent(event)
        # 重新加载当前图像以适应当前窗口大小
        if hasattr(self, 'current_image_path') and self.current_image_path:
            self.show_current_image()
    
    def show_current_image(self):
        """显示当前图像（根据窗口大小保持宽高比调整）"""
        if self.images_path and self.current_image_path:
            image = QImage(self.current_image_path)
            if not image.isNull():
                # 检查是否为单通道灰度图（Format_Grayscale8）
                if image.format() in (QImage.Format_Alpha8, QImage.Format_Grayscale8, 28):
                    # 更可靠的转换方式
                    rgb_image = QImage(image.width(), image.height(), QImage.Format_RGB888)
                    
                    # 方法1：使用QPainter绘制转换（推荐）
                    painter = QPainter(rgb_image)
                    painter.drawImage(0, 0, image)  # 自动处理格式转换
                    painter.end()
                    image = rgb_image
                
                # 如果需要显示检测框，则绘制检测框
                if self.show_bbox:
                    self.current_image_with_bbox = self.draw_bounding_boxes(image.copy(), self.current_basename)
                    display_image = self.current_image_with_bbox
                else:
                    display_image = image.copy()
                
                # 获取容器大小（减去边距以保持间距）
                container_size = self.image_display.size()
                
                # 计算保持宽高比的缩放尺寸
                img_width = image.width()
                img_height = image.height()
                
                # 计算缩放比例（保持宽高比）
                scale_factor = min(
                    container_size.width() / img_width,
                    container_size.height() / img_height
                )
                
                # 应用缩放比例
                scaled_width = int(img_width * scale_factor)
                scaled_height = int(img_height * scale_factor)
                
                # 缩放图像
                scaled_image = display_image.scaled(
                    scaled_width,
                    scaled_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                # 直接设置图像到标签
                self.image_display.setPixmap(QPixmap.fromImage(scaled_image))
    
    # ========================================================
    # 多进程处理方法
    # ========================================================
    def start_search_thread(self):
        """启动搜索线程（多进程处理）"""
        if not self.labels_path:
            self.status_label.setText("请先选择标签目录！")
            return
            
        search_term = self.search_input.text().strip()
        # 修改：允许空搜索词，提取整个文件夹
            
        # 存储搜索关键词，用于后续绘制检测框
        self.search_term = search_term
            
        # 重置状态
        self.search_results = []
        self.output_file = f"{search_term}.json" if search_term else "all_files.json"
        self.update_progress_bar(0, 0)
        
        # 禁用搜索按钮
        self.search_button.setEnabled(False)
        self.search_button.setText("搜索中...")
        
        # 创建并启动新线程
        self.search_worker = SearchWorker(self.labels_path, search_term)
        
        # 连接信号
        self.search_worker.search_finished.connect(self.handle_search_results)
        self.search_worker.progress_updated.connect(self.update_search_progress)
        self.search_worker.error_occurred.connect(self.handle_search_error)
        
        # 启动线程
        self.search_worker.start()
    
    def update_search_progress(self, processed, total):
        """更新搜索进度（来自工作线程）"""
        self.status_label.setText(f"正在搜索... 已完成 {processed}/{total}")
        self.update_progress_bar(processed, total)
    
    def handle_search_results(self, results, term):
        """处理搜索结果（来自工作线程）"""
        self.search_results = results
        self.search_term = term
        self.search_button.setEnabled(True)
        self.search_button.setText("搜索")
        
        # 读取已保存的数量
        self.update_saved_count()
        
        if not self.search_results:
            self.status_label.setText(f"未找到包含 '{term}' 的文件" if term else "标签文件夹中没有找到任何JSON文件")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            
            # 重置进度条
            self.update_progress_bar(0, 0)
            return
            
        # 保存结果到文件
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(self.search_results, f, ensure_ascii=False, indent=2)
            self.status_label.setText(f"找到 {len(self.search_results)} 个结果，已保存到 {self.output_file}")
            
            # 显示第一个结果
            self.current_index = 0
            self.show_current_result()
            
            # 启用导航按钮
            self.prev_button.setEnabled(len(self.search_results) > 1)
            self.next_button.setEnabled(len(self.search_results) > 1)
            
            # 保存状态
            self.save_state()
        except Exception as e:
            self.status_label.setText(f"保存结果文件出错: {str(e)}")
    
    def handle_search_error(self, error_msg):
        """处理搜索错误（来自工作线程）"""
        self.status_label.setText(error_msg)
        self.search_button.setEnabled(True)
        self.search_button.setText("搜索")
    
    # ========================================================
    # 新增方法：加载算法去重结果
    # ========================================================
    def load_dedup_results(self):
        """加载算法去重结果的JSON文件"""
        # 打开文件对话框让用户选择JSON文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择去重结果文件", 
            "", 
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return  # 用户取消选择
            
        try:
            # 读取JSON文件
            with open(file_path, 'r', encoding='utf-8') as f:
                dedup_results = json.load(f)
                
            # 验证数据格式
            if not isinstance(dedup_results, list) or not all(isinstance(item, str) for item in dedup_results):
                raise ValueError("JSON文件格式错误: 应包含字符串列表")
                
            # 更新搜索结果为去重结果
            self.search_results = dedup_results
            self.search_term = "算法去重结果"  # 设置搜索关键词
            self.output_file = file_path
            
            # 更新UI状态
            self.status_label.setText(f"已加载去重结果: {len(self.search_results)} 个文件")
            
            if self.search_results:
                self.current_index = 0
                self.show_current_result()
                
                # 启用导航按钮
                self.prev_button.setEnabled(len(self.search_results) > 1)
                self.next_button.setEnabled(len(self.search_results) > 1)
                
                # 保存状态
                self.save_state()
            else:
                self.status_label.setText("去重结果为空")
                self.prev_button.setEnabled(False)
                self.next_button.setEnabled(False)
                self.update_progress_bar(0, 0)
                
        except Exception as e:
            QMessageBox.critical(self, "加载错误", f"加载去重结果时出错: {str(e)}")
    
    # ========================================================
    # 新增方法：算法去重
    # ========================================================
    def dedup_images(self):
        """算法去重功能（保留接口）"""
        # 这里只实现基本提示，实际去重算法需要根据具体需求实现
        QMessageBox.information(self, "算法去重", "去重功能已预留接口，后续可在此处实现图像去重算法。")
        self.status_label.setText("去重功能接口已预留，待实现具体算法")
    
    # ========================================================
    # 修改后的路径选择方法
    # ========================================================
    def select_images_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择图像文件夹")
        if path:
            self.images_path = path
            self.images_path_label.setText(path)
            self.images_path_label.setToolTip(path)
            self.status_label.setText(f"已选择图像路径: {path}")
            self.save_state()  # 保存状态
    
    def select_images_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "选择图像文件", "", "Images (*.png *.jpg *.jpeg *.bmp *.tif)")
        if file:
            self.images_path = os.path.dirname(file)
            self.images_path_label.setText(self.images_path)
            self.images_path_label.setToolTip(self.images_path)
            self.status_label.setText(f"已选择图像文件: {os.path.basename(file)}")
            self.save_state()  # 保存状态
    
    def select_labels_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择标签文件夹")
        if path:
            self.labels_path = path
            self.labels_path_label.setText(path)
            self.labels_path_label.setToolTip(path)
            self.status_label.setText(f"已选择标签路径: {path}")
            self.save_state()  # 保存状态
    
    def select_labels_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "选择标签文件", "", "JSON Files (*.json)")
        if file:
            self.labels_path = os.path.dirname(file)
            self.labels_path_label.setText(self.labels_path)
            self.labels_path_label.setToolTip(self.labels_path)
            self.status_label.setText(f"已选择标签文件: {os.path.basename(file)}")
            self.save_state()  # 保存状态
    
    # ========================================================
    # 其他方法（与原代码相同）
    # ========================================================
    def update_saved_count(self):
        """更新已保存的图片数量"""
        if hasattr(self, 'output_file') and hasattr(self, 'search_term') and self.search_term:
            try:
                filter_file = f"{self.search_term}(筛选).json" if self.search_term else "all_files(筛选).json"
                if os.path.exists(filter_file):
                    with open(filter_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.saved_count = len(data)
                    self.saved_count_label.setText(f"{self.saved_count}")
                else:
                    self.saved_count = 0
                    self.saved_count_label.setText("0")
            except Exception as e:
                print(f"更新保存数量出错: {str(e)}")
    
    def show_current_result(self):
        if not self.search_results or self.current_index < 0 or self.current_index >= len(self.search_results):
            return
            
        # 更新进度条
        self.update_progress_bar(self.current_index + 1, len(self.search_results))
        
        basename = self.search_results[self.current_index]
        self.current_basename = basename
        
        # 显示图像文件名
        self.image_filename = ""
        found_ext = ""
        
        # 显示图像
        image_found = False
        image_path = ""
        
        if self.images_path:
            # 尝试常见图像格式
            for ext in ['.jpg', '.png', '.tif', '.bmp', '.jpeg', '.JPG', '.PNG']:
                test_path = os.path.join(self.images_path, f"{basename}{ext}")
                if os.path.exists(test_path):
                    image_found = True
                    image_path = test_path
                    self.image_filename = f"{basename}{ext}"
                    found_ext = ext
                    break
        
        if image_found:
            self.current_image_path = image_path
            self.show_current_image()
            self.image_filename_label.setText(f"图像文件名: {self.image_filename}")
        else:
            if self.images_path:
                self.image_filename_label.setText(f"图像文件不存在: {basename}.*")
            else:
                self.image_filename_label.setText("请先选择图像文件夹")
        
        # 显示JSON内容
        json_path = os.path.join(self.labels_path, f"{basename}.json")
        json_filename = f"{basename}.json"
        self.json_filename_label.setText(f"标签文件名: {json_filename}")
        
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    formatted_json = json.dumps(json_data, ensure_ascii=False, indent=2)
                    self.json_display.setPlainText(formatted_json)
            except Exception as e:
                self.json_display.setPlainText(f"读取JSON文件出错:\n{str(e)}")
        else:
            self.json_display.setPlainText(f"JSON文件不存在: {json_path}")
        
        # 启用保存按钮
        self.save_button.setEnabled(True)
        self.discard_button.setEnabled(True)
    
    def update_progress_bar(self, current, total):
        """更新进度条显示"""
        if total > 0:
            # 计算百分比
            percentage = int((current / total) * 100)
            
            # 更新进度文本
            self.progress_label.setText(f"{current}/{total}")
            
            # 更新进度条
            self.progress_bar.setValue(percentage)
            self.progress_bar.setFormat(f"{current}/{total} ({percentage}%)")
        else:
            self.progress_label.setText("0/0")
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("0/0 (0%)")
    
    def draw_bounding_boxes(self, image, basename):
        """绘制仅包含搜索关键词的检测框"""
        json_path = os.path.join(self.labels_path, f"{basename}.json")
        if not os.path.exists(json_path):
            return image
            
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                
            painter = QPainter(image)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)  # 确保颜色覆盖
            pen = QPen(QColor(255, 0, 0), 2)  # 红色，2像素宽
            painter.setPen(pen)
            
            # 只绘制包含搜索关键词的检测框
            if "annotations" in json_data:
                for annotation in json_data["annotations"]:
                    # 检查标注是否包含搜索关键词
                    if "coordinates of the corner point(Col,Row)" in annotation:
                        if ("class" in annotation and self.search_term in annotation["class"]) or \
                           ("label" in annotation and self.search_term in annotation["label"]):
                            
                            points = []
                            for coord in annotation["coordinates of the corner point(Col,Row)"]:
                                col, row = map(int, coord.split(','))
                                points.append(QPoint(col, row))
                            
                            # 绘制多边形
                            for i in range(len(points)):
                                painter.drawLine(points[i], points[(i+1)%len(points)])
                            
                            # 标注类别和ID
                            if "class" in annotation and "label" in annotation and "id" in annotation:
                                label = f"{annotation['class']} {annotation['label']} {annotation['id']}"
                                painter.drawText(points[0], label)
            
            painter.end()
            return image
            
        except Exception as e:
            print(f"绘制检测框出错: {str(e)}")
            return image
    
    def toggle_bbox_display(self):
        sender = self.sender()
        if sender == self.show_bbox_button:
            self.show_bbox = True
        else:
            self.show_bbox = False
        self.show_current_image()  # 刷新显示
        self.save_state()  # 保存状态
    
    def save_current_image(self):
        if not self.search_results or self.current_index < 0 or self.current_index >= len(self.search_results):
            return
            
        search_term = self.search_input.text().strip()
        if not search_term:
            self.status_label.setText("请先输入搜索关键词！")
            return
            
        basename = self.search_results[self.current_index]
        output_file = f"{search_term}(筛选).json"
        
        try:
            # 读取或创建筛选文件
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = []
            
            # 添加当前文件名（如果不存在）
            if basename not in data:
                data.append(basename)
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.status_label.setText(f"已保存 {basename} 到 {output_file}")
                self.saved_count += 1
                self.saved_count_label.setText(f"{self.saved_count}")
            else:
                self.status_label.setText(f"{basename} 已在 {output_file} 中")
                
            # 移动到下一张
            if self.current_index < len(self.search_results) - 1:
                self.current_index += 1
                self.show_current_result()
            else:
                self.next_button.setEnabled(False)
                self.status_label.setText(f"所有{len(self.search_results)}张图片已处理完成！")
            
            # 保存状态
            self.save_state()
                
        except Exception as e:
            self.status_label.setText(f"保存失败: {str(e)}")
    
    def discard_current_image(self):
        if not self.search_results or self.current_index < 0 or self.current_index >= len(self.search_results):
            return
            
        search_term = self.search_input.text().strip()
        if not search_term:
            self.status_label.setText("请先输入搜索关键词！")
            return
            
        basename = self.search_results[self.current_index]
        output_file = f"{search_term}(筛选).json"
        
        try:
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 移除当前文件名（如果存在）
                if basename in data:
                    data.remove(basename)
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    self.status_label.setText(f"已从 {output_file} 中移除 {basename}")
                    # 如果文件在筛选列表中，更新保存数量
                    self.update_saved_count()
                else:
                    self.status_label.setText(f"{basename} 不在 {output_file} 中")
            else:
                self.status_label.setText(f"{output_file} 不存在")
                
            # 移动到下一张
            if self.current_index < len(self.search_results) - 1:
                self.current_index += 1
                self.show_current_result()
            else:
                self.next_button.setEnabled(False)
                self.status_label.setText(f"所有{len(self.search_results)}张图片已处理完成！")
            
            # 保存状态
            self.save_state()
                
        except Exception as e:
            self.status_label.setText(f"剔除失败: {str(e)}")
    
    def show_previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_result()
            self.next_button.setEnabled(True)
            if self.current_index == 0:
                self.prev_button.setEnabled(False)
            
            # 保存状态
            self.save_state()
    
    def show_next(self):
        if self.current_index < len(self.search_results) - 1:
            self.current_index += 1
            self.show_current_result()
            self.prev_button.setEnabled(True)
            if self.current_index == len(self.search_results) - 1:
                self.next_button.setEnabled(False)
            
            # 保存状态
            self.save_state()
    
    def load_state(self):
        """加载上次的工作状态"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                
                # 恢复路径
                if 'images_path' in state_data:
                    self.images_path = state_data['images_path']
                    self.images_path_label.setText(self.images_path)
                
                if 'labels_path' in state_data:
                    self.labels_path = state_data['labels_path']
                    self.labels_path_label.setText(self.labels_path)
                
                # 恢复搜索状态
                if 'search_term' in state_data and state_data['search_term']:
                    self.search_term = state_data['search_term']
                    self.search_input.setText(self.search_term)
                    
                    # 恢复搜索结果
                    if 'search_results' in state_data:
                        self.search_results = state_data['search_results']
                    
                    # 恢复当前索引
                    if 'current_index' in state_data and self.search_results:
                        self.current_index = state_data['current_index']
                        if self.current_index >= len(self.search_results):
                            self.current_index = 0
                    
                    # 恢复保存数量
                    if 'saved_count' in state_data:
                        self.saved_count = state_data['saved_count']
                        self.saved_count_label.setText(str(self.saved_count))
                    
                    # 恢复检测框状态
                    if 'show_bbox' in state_data:
                        self.show_bbox = state_data['show_bbox']
                    
                    # 更新UI状态
                    if self.search_results:
                        self.status_label.setText(f"已恢复上次的搜索: {self.search_term} ({len(self.search_results)} 张图片)")
                        
                        # 启用按钮
                        self.prev_button.setEnabled(self.current_index > 0)
                        self.next_button.setEnabled(self.current_index < len(self.search_results) - 1)
                        self.save_button.setEnabled(True)
                        self.discard_button.setEnabled(True)
                        
                        # 显示当前结果
                        self.show_current_result()
        except Exception as e:
            print(f"加载状态出错: {str(e)}")
    
    def save_state(self):
        """保存当前工作状态"""
        try:
            state_data = {
                'images_path': self.images_path,
                'labels_path': self.labels_path,
                'search_term': self.search_term,
                'search_results': self.search_results,
                'current_index': self.current_index,
                'saved_count': self.saved_count,
                'show_bbox': self.show_bbox,
                'last_saved': str(datetime.datetime.now())
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存状态出错: {str(e)}")
    
    def closeEvent(self, event):
        """窗口关闭时保存状态，并确保停止任何运行的线程"""
        # 停止正在运行的搜索线程
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.stop()
            self.search_worker.quit()
            self.search_worker.wait()
        
        # 保存状态
        self.save_state()
        event.accept()


if __name__ == "__main__":
    # 设置环境变量解决OpenGL问题
    os.environ["QT_XCB_FORCE_SOFTWARE_OPENGL"] = "1"

    # 高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication([])

    
    window = ImageDataCleaner()
    window.show()
    app.exec_()
