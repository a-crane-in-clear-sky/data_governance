import sys
import random
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class TechDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TechVision - 系统监控仪表盘")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)
        
        # 设置主窗口背景为深色科技感
        self.setStyleSheet("background-color: #0f1620;")
        
        # 创建中心部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        
        # 创建标题栏
        self.create_title_bar()
        
        # 创建状态卡片
        self.create_status_cards()
        
        # 创建仪表盘区域
        self.create_dashboard()
        
        # 创建数据表格
        self.create_data_table()
        
        # 启动数据更新定时器
        self.data_update_timer = QTimer(self)
        self.data_update_timer.timeout.connect(self.update_data)
        self.data_update_timer.start(1500)
        
        # 粒子系统动画
        self.particle_timer = QTimer(self)
        self.particle_timer.timeout.connect(self.update_particles)
        self.particle_timer.start(50)
        self.particles = []
        
    def create_title_bar(self):
        # 标题栏容器
        title_container = QWidget()
        title_container.setStyleSheet("background-color: rgba(20, 30, 50, 150); border-radius: 10px;")
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(20, 10, 20, 10)
        
        # 标题
        title_label = QLabel("TECHVISION")
        title_label.setStyleSheet("""
            color: #00f3ff;
            font-size: 28px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        title_layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel("系统监控仪表盘")
        subtitle_label.setStyleSheet("""
            color: #6a7c94;
            font-size: 18px;
            font-weight: medium;
        """)
        title_layout.addWidget(subtitle_label)
        
        # 添加弹簧
        title_layout.addStretch()
        
        # 状态指示器
        status_indicator = QLabel("● 运行中")
        status_indicator.setStyleSheet("""
            color: #00ff9d;
            font-size: 16px;
            font-weight: medium;
        """)
        title_layout.addWidget(status_indicator)
        
        self.main_layout.addWidget(title_container)
    
    def create_status_cards(self):
        # 卡片容器
        cards_container = QWidget()
        cards_layout = QHBoxLayout(cards_container)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(20)
        
        # 卡片样式
        card_style = """
            QWidget {
                background-color: rgba(25, 35, 60, 180);
                border-radius: 12px;
                border: 1px solid rgba(0, 243, 255, 60);
            }
            QLabel {
                color: #c0d0e8;
            }
        """
        
        # 创建4个状态卡片
        card_titles = ["CPU使用率", "内存占用", "网络流量", "存储空间"]
        card_values = ["42%", "5.8/16GB", "↑1.2 ↓0.8 Gb/s", "1.2/2.0 TB"]
        card_icons = ["⚙️", "🧠", "🌐", "💾"]
        card_colors = ["#ff6b6b", "#4ecdc4", "#ffd166", "#6a0572"]
        
        self.cards = []
        
        for i in range(4):
            card = QWidget()
            card.setStyleSheet(card_style)
            card.setMinimumHeight(120)
            
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 15, 20, 15)
            
            # 图标和标题
            top_layout = QHBoxLayout()
            
            icon_label = QLabel(card_icons[i])
            icon_label.setStyleSheet(f"font-size: 24px; color: {card_colors[i]};")
            top_layout.addWidget(icon_label)
            
            title_label = QLabel(card_titles[i])
            title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
            top_layout.addWidget(title_label)
            top_layout.addStretch()
            
            card_layout.addLayout(top_layout)
            
            # 值
            value_label = QLabel(card_values[i])
            value_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #ffffff;")
            card_layout.addWidget(value_label)
            
            # 进度条
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(random.randint(30, 80))
            progress.setTextVisible(False)
            progress.setStyleSheet(f"""
                QProgressBar {{
                    background-color: rgba(40, 50, 80, 150);
                    border-radius: 6px;
                    height: 10px;
                }}
                QProgressBar::chunk {{
                    background-color: {card_colors[i]};
                    border-radius: 6px;
                }}
            """)
            card_layout.addWidget(progress)
            
            cards_layout.addWidget(card)
            self.cards.append((value_label, progress))
        
        self.main_layout.addWidget(cards_container)
    
    def create_dashboard(self):
        # 仪表盘容器
        dashboard_container = QWidget()
        dashboard_layout = QHBoxLayout(dashboard_container)
        dashboard_layout.setContentsMargins(0, 0, 0, 0)
        dashboard_layout.setSpacing(20)
        
        # 左侧仪表盘
        left_dashboard = QWidget()
        left_dashboard.setStyleSheet("""
            background-color: rgba(25, 35, 60, 180);
            border-radius: 12px;
            border: 1px solid rgba(0, 243, 255, 60);
        """)
        left_layout = QVBoxLayout(left_dashboard)
        left_layout.setContentsMargins(20, 20, 20, 20)
        
        left_title = QLabel("系统性能指标")
        left_title.setStyleSheet("""
            color: #00f3ff;
            font-size: 18px;
            font-weight: bold;
            border-bottom: 1px solid rgba(0, 243, 255, 60);
            padding-bottom: 10px;
        """)
        left_layout.addWidget(left_title)
        
        # 仪表盘可视化区域
        self.dashboard_widget = QWidget()
        self.dashboard_widget.setMinimumHeight(250)
        left_layout.addWidget(self.dashboard_widget)
        
        dashboard_layout.addWidget(left_dashboard, 2)
        
        # 右侧日志
        right_log = QWidget()
        right_log.setStyleSheet("""
            background-color: rgba(25, 35, 60, 180);
            border-radius: 12px;
            border: 1px solid rgba(0, 243, 255, 60);
        """)
        log_layout = QVBoxLayout(right_log)
        log_layout.setContentsMargins(20, 20, 20, 20)
        
        log_title = QLabel("实时日志")
        log_title.setStyleSheet("""
            color: #00f3ff;
            font-size: 18px;
            font-weight: bold;
            border-bottom: 1px solid rgba(0, 243, 255, 60);
            padding-bottom: 10px;
        """)
        log_layout.addWidget(log_title)
        
        self.log_text = QTextEdit()
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(20, 30, 50, 120);
                color: #a0c0e0;
                border: none;
                border-radius: 8px;
                font-family: 'Consolas', monospace;
                font-size: 14px;
            }
        """)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        # 添加示例日志
        log_messages = [
            "系统启动成功，所有服务运行正常",
            "检测到安全更新可用，建议安装",
            "网络连接稳定，延迟: 24ms",
            "自动备份任务已开始执行",
            "存储空间使用率超过60%，建议清理",
            "CPU温度正常，当前: 45°C",
            "内存优化完成，释放 320MB 空间"
        ]
        for msg in log_messages:
            self.log_text.append(f"> [{QTime.currentTime().toString()}] {msg}")
        
        dashboard_layout.addWidget(right_log, 1)
        
        self.main_layout.addWidget(dashboard_container)
    
    def create_data_table(self):
        # 数据表格容器
        table_container = QWidget()
        table_container.setStyleSheet("""
            background-color: rgba(25, 35, 60, 180);
            border-radius: 12px;
            border: 1px solid rgba(0, 243, 255, 60);
        """)
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(20, 20, 20, 20)
        
        table_title = QLabel("运行进程监控")
        table_title.setStyleSheet("""
            color: #00f3ff;
            font-size: 18px;
            font-weight: bold;
            border-bottom: 1px solid rgba(0, 243, 255, 60);
            padding-bottom: 10px;
        """)
        table_layout.addWidget(table_title)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(20, 30, 50, 120);
                color: #c0d0e8;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                gridline-color: rgba(0, 243, 255, 30);
            }
            QHeaderView::section {
                background-color: rgba(30, 45, 70, 200);
                color: #00f3ff;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 8px;
            }
        """)
        
        # 设置表格属性
        self.table.setColumnCount(5)
        self.table.setRowCount(8)
        self.table.setHorizontalHeaderLabels(["进程ID", "进程名称", "CPU占用", "内存占用", "状态"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # 填充示例数据
        processes = [
            ["1012", "systemd", "2.1%", "120MB", "运行中"],
            ["2456", "NetworkManager", "1.8%", "85MB", "运行中"],
            ["3124", "gnome-shell", "8.5%", "420MB", "运行中"],
            ["4587", "chrome", "15.2%", "1.2GB", "运行中"],
            ["5213", "code", "12.8%", "980MB", "运行中"],
            ["6321", "spotify", "5.3%", "320MB", "运行中"],
            ["7125", "docker", "3.2%", "210MB", "运行中"],
            ["8012", "python3", "1.2%", "85MB", "运行中"]
        ]
        
        for row, process in enumerate(processes):
            for col, data in enumerate(process):
                item = QTableWidgetItem(data)
                if col == 4:  # 状态列
                    item.setForeground(QColor("#00ff9d") if data == "运行中" else item.setForeground(QColor("#ff6b6b")))
                self.table.setItem(row, col, item)
        
        table_layout.addWidget(self.table)
        self.main_layout.addWidget(table_container)
    
    def update_data(self):
        # 更新卡片数据
        for i, (value_label, progress) in enumerate(self.cards):
            if i == 0:  # CPU
                new_value = random.randint(30, 85)
                value_label.setText(f"{new_value}%")
                progress.setValue(new_value)
            elif i == 1:  # 内存
                used = random.uniform(5.0, 14.0)
                value_label.setText(f"{used:.1f}/16.0 GB")
                progress.setValue(int(used / 16.0 * 100))
            elif i == 2:  # 网络
                up = random.uniform(0.5, 2.5)
                down = random.uniform(0.3, 2.0)
                value_label.setText(f"↑{up:.1f} ↓{down:.1f} Gb/s")
                progress.setValue(random.randint(40, 90))
            elif i == 3:  # 存储
                used = random.uniform(1.0, 1.8)
                value_label.setText(f"{used:.1f}/2.0 TB")
                progress.setValue(int(used / 2.0 * 100))
        
        # 添加新日志
        new_logs = [
            "系统运行正常，无异常事件",
            "网络流量波动在正常范围内",
            "CPU负载均衡，无过载情况",
            "内存缓存使用效率提升",
            "磁盘读写速度正常",
            "安全扫描未发现威胁",
            "系统温度监测正常"
        ]
        self.log_text.append(f"> [{QTime.currentTime().toString()}] {random.choice(new_logs)}")
        
        # 滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        
        # 更新表格数据
        for row in range(self.table.rowCount()):
            cpu_item = self.table.item(row, 2)
            if cpu_item:
                current = float(cpu_item.text().replace('%', ''))
                new_cpu = max(0.1, min(99.9, current + random.uniform(-3.0, 5.0)))
                cpu_item.setText(f"{new_cpu:.1f}%")
                
            mem_item = self.table.item(row, 3)
            if mem_item:
                mem = mem_item.text().replace('MB', '').replace('GB', '')
                unit = 'MB' if 'MB' in mem_item.text() else 'GB'
                current = float(mem)
                new_mem = max(1, min(5000 if unit == 'MB' else 16, current + random.uniform(-10, 30)))
                mem_item.setText(f"{new_mem:.0f}{unit}")
        
        # 触发重绘
        self.dashboard_widget.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制网格背景
        painter.setPen(QPen(QColor(30, 45, 70, 60), 1, Qt.DotLine))
        grid_size = 30
        for x in range(0, self.width(), grid_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), grid_size):
            painter.drawLine(0, y, self.width(), y)
        
        # 绘制装饰性线条
        painter.setPen(QPen(QColor(0, 243, 255, 30), 2))
        painter.drawLine(0, 100, self.width(), 100)
        
        # 绘制粒子
        for particle in self.particles:
            x, y, size, speed, life = particle
            alpha = min(255, int(255 * life / 100))
            color = QColor(0, 243, 255, alpha)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(int(x), int(y), size, size)
    
    def update_particles(self):
        # 添加新粒子
        if len(self.particles) < 100 and random.random() < 0.3:
            x = random.randint(0, self.width())
            y = self.height()
            size = random.randint(2, 5)
            speed = random.uniform(1.0, 3.0)
            self.particles.append([x, y, size, speed, 100])
        
        # 更新粒子位置
        for particle in self.particles[:]:
            particle[1] -= particle[3]  # 向上移动
            particle[4] -= 1  # 减少生命周期
            
            # 移除生命周期结束的粒子
            if particle[4] <= 0:
                self.particles.remove(particle)
    
    def resizeEvent(self, event):
        # 窗口大小改变时清除粒子
        self.particles.clear()
        super().resizeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用字体
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    dashboard = TechDashboard()
    dashboard.show()
    
    sys.exit(app.exec_())
