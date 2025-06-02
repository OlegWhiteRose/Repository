from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QGridLayout,
    QTabWidget,
    QPushButton,
    QFrame,
    QScrollArea
)
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from database.db import Database

class StatisticsWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Статистика")
        self.setGeometry(100, 100, 1200, 800)
        self.db = Database()
        
        # Создаем центральный виджет и главный layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Создаем навбар
        navbar = QFrame()
        navbar.setStyleSheet("""
            QFrame {
                background-color: #21A038;
                min-height: 40px;
                max-height: 40px;
            }
            QPushButton {
                background-color: transparent;
                color: white;
                border: 1px solid white;
                padding: 5px 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: white;
                color: #21A038;
            }
            QPushButton:pressed {
                background-color: #f0f0f0;
                color: #21A038;
            }
        """)
        
        navbar_layout = QHBoxLayout(navbar)
        navbar_layout.setContentsMargins(20, 0, 20, 0)
        navbar_layout.setSpacing(10)
        
        # Заголовок в навбаре
        title_label = QLabel("Статистика")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        navbar_layout.addWidget(title_label)
        navbar_layout.addStretch()
        
        # Кнопка "Назад" в навбаре
        back_button = QPushButton("← Назад")
        back_button.setFixedWidth(100)
        back_button.clicked.connect(self.close)
        navbar_layout.addWidget(back_button)
        
        main_layout.addWidget(navbar)
        
        # Создаем контейнер для содержимого
        content_container = QWidget()
        content_container.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        main_layout.addWidget(content_container)
        
        # Создаем вкладки
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QTabBar::tab {
                background: #f5f5f5;
                color: #666;
                padding: 8px 15px;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 150px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #21A038;
                color: white;
                border-color: #21A038;
            }
            QTabBar::tab:hover:!selected {
                background: #E7F5E9;
                color: #21A038;
            }
        """)
        
        # Вкладка "Общая статистика"
        general_tab = QWidget()
        general_scroll = QScrollArea()
        general_scroll.setWidget(general_tab)
        general_scroll.setWidgetResizable(True)
        general_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: white;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #21A038;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        general_layout = QVBoxLayout(general_tab)
        general_layout.setSpacing(15)  # Возвращаем прежний отступ
        general_layout.setContentsMargins(15, 15, 15, 15)  # Возвращаем прежние отступы
        
        # Группы статистики
        self.create_stats_group("Статистика по вкладам", general_layout)
        self.create_stats_group("Статистика по клиентам", general_layout)
        self.create_stats_group("Статистика по транзакциям", general_layout)
        
        # Вкладка "Графики"
        charts_tab = QWidget()
        charts_scroll = QScrollArea()
        charts_scroll.setWidget(charts_tab)
        charts_scroll.setWidgetResizable(True)
        charts_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: white;
            }
        """)
        
        charts_layout = QVBoxLayout(charts_tab)
        charts_layout.setSpacing(20)
        charts_layout.setContentsMargins(15, 15, 15, 15)
        
        # Добавляем только график вкладов
        self.create_deposits_chart(charts_layout)
        
        # Добавляем вкладки
        tab_widget.addTab(general_scroll, "Общая статистика")
        tab_widget.addTab(charts_scroll, "Графики")
        
        content_layout.addWidget(tab_widget)
        
        # Обновляем данные
        self.refresh_data()
        
    def create_stats_group(self, title, parent_layout):
        """Создает группу для статистики"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 10px;
                padding: 15px;
                background: white;
            }
            QGroupBox::title {
                color: #21A038;
                font-weight: bold;
                font-size: 13px;
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                background: white;
            }
            QLabel {
                color: #333;
                font-size: 12px;
            }
            QLabel[class="stat-value"] {
                color: #21A038;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Добавляем статистику в зависимости от типа группы
        if "вкладам" in title:
            self.add_deposit_stats(layout)
        elif "клиентам" in title:
            self.add_client_stats(layout)
        elif "транзакциям" in title:
            self.add_transaction_stats(layout)
            
        parent_layout.addWidget(group)
        
    def add_deposit_stats(self, layout):
        """Добавляет статистику по вкладам"""
        stats = [
            ("Всего вкладов:", "SELECT COUNT(*) FROM Deposit"),
            ("Активных вкладов:", "SELECT COUNT(*) FROM Deposit WHERE status = 'open'"),
            ("Общая сумма вкладов:", "SELECT SUM(amount) FROM Deposit"),
            ("Средняя процентная ставка:", "SELECT AVG(interest_rate) FROM Deposit")
        ]
        self.add_stats_to_layout(layout, stats)
        
    def add_client_stats(self, layout):
        """Добавляет статистику по клиентам"""
        stats = [
            ("Всего клиентов:", "SELECT COUNT(*) FROM Client"),
            ("Клиентов с вкладами:", "SELECT COUNT(DISTINCT client_id) FROM Deposit"),
            ("Среднее количество вкладов на клиента:", """
                SELECT CAST(COUNT(d.id) AS FLOAT) / COUNT(DISTINCT d.client_id)
                FROM Deposit d
            """)
        ]
        self.add_stats_to_layout(layout, stats)
        
    def add_transaction_stats(self, layout):
        """Добавляет статистику по транзакциям"""
        stats = [
            ("Всего транзакций:", "SELECT COUNT(*) FROM Transaction"),
            ("Общая сумма транзакций:", "SELECT SUM(ABS(amount)) FROM Transaction"),
            ("Средняя сумма транзакции:", "SELECT AVG(ABS(amount)) FROM Transaction")
        ]
        self.add_stats_to_layout(layout, stats)
        
    def add_stats_to_layout(self, layout, stats):
        """Добавляет статистику в layout"""
        for row, (label_text, query) in enumerate(stats):
            try:
                result = self.db.execute_query(query, fetch_one=True)[0]
                if isinstance(result, (int, float)):
                    if "сумма" in label_text.lower():
                        value_text = f"₽ {result:,.2f}"
                    elif "ставка" in label_text.lower():
                        value_text = f"{result:.2f}%"
                    else:
                        value_text = f"{result:,.0f}"
                else:
                    value_text = str(result) if result is not None else "Н/Д"
            except Exception:
                value_text = "Н/Д"
                
            # Добавляем метку
            label = QLabel(label_text)
            layout.addWidget(label, row, 0)
            
            # Добавляем значение
            value_label = QLabel(value_text)
            value_label.setProperty("class", "stat-value")
            layout.addWidget(value_label, row, 1)
        
    def create_deposits_chart(self, parent_layout):
        """Создает график по вкладам"""
        chart_group = QGroupBox("Распределение сумм по типам вкладов")
        chart_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 10px;
                padding: 15px;
                background: white;
            }
            QGroupBox::title {
                color: #21A038;
                font-weight: bold;
                font-size: 13px;
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                background: white;
            }
        """)
        
        layout = QVBoxLayout(chart_group)
        
        figure = Figure(figsize=(10, 5))
        canvas = FigureCanvas(figure)
        self.deposits_ax = figure.add_subplot(111)
        
        # Настраиваем стиль графика
        self.deposits_ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        figure.subplots_adjust(bottom=0.2, left=0.1)
        
        layout.addWidget(canvas)
        parent_layout.addWidget(chart_group)
        self.deposits_canvas = canvas
        
    def create_transactions_chart(self, parent_layout):
        """Создает график по транзакциям"""
        chart_group = QGroupBox("Динамика транзакций по месяцам")
        chart_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 10px;
                padding: 15px;
                background: white;
            }
            QGroupBox::title {
                color: #21A038;
                font-weight: bold;
                font-size: 13px;
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                background: white;
            }
        """)
        
        layout = QVBoxLayout(chart_group)
        
        figure = Figure(figsize=(10, 5))
        canvas = FigureCanvas(figure)
        self.transactions_ax = figure.add_subplot(111)
        
        # Настраиваем стиль графика
        self.transactions_ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        figure.subplots_adjust(bottom=0.2, left=0.1)
        
        layout.addWidget(canvas)
        parent_layout.addWidget(chart_group)
        self.transactions_canvas = canvas
        
    def refresh_data(self):
        """Обновляет данные на графиках"""
        try:
            # График сумм по вкладам
            query = """
                SELECT d.type, SUM(d.amount) as total_amount
                FROM Deposit d
                GROUP BY d.type
                ORDER BY total_amount DESC
            """
            results = self.db.execute_query(query, fetch_all=True)
            
            types = [r[0] for r in results]
            amounts = [float(r[1]) for r in results]
            
            self.deposits_ax.clear()
            bars = self.deposits_ax.bar(range(len(types)), amounts, color='#21A038')
            self.deposits_ax.set_xticks(range(len(types)))
            self.deposits_ax.set_xticklabels(types, rotation=45, ha='right')
            self.deposits_ax.set_ylabel('Сумма (₽)')
            
            # Добавляем подписи значений над столбцами
            for bar in bars:
                height = bar.get_height()
                self.deposits_ax.text(bar.get_x() + bar.get_width()/2., height,
                                   f'₽{int(height):,}',
                                   ha='center', va='bottom')
            
            self.deposits_canvas.draw()
            
        except Exception as e:
            print(f"Ошибка при обновлении графиков: {str(e)}") 