from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QGridLayout
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
        
        # Создаем верхнюю панель с графиком и статистикой
        top_panel = QHBoxLayout()
        
        # График сумм по вкладам
        deposits_chart = QGroupBox("Сумма по вкладам")
        deposits_layout = QVBoxLayout()
        self.deposits_canvas = self.create_deposits_chart()
        deposits_layout.addWidget(self.deposits_canvas)
        deposits_chart.setLayout(deposits_layout)
        
        # Статистика справа
        stats_group = QGroupBox("Общая статистика")
        stats_layout = QVBoxLayout()
        
        self.avg_deposits_label = QLabel()
        self.avg_lifetime_label = QLabel()
        self.avg_transaction_label = QLabel()
        
        stats_layout.addWidget(self.avg_deposits_label)
        stats_layout.addWidget(self.avg_lifetime_label)
        stats_layout.addWidget(self.avg_transaction_label)
        
        stats_group.setLayout(stats_layout)
        
        top_panel.addWidget(deposits_chart, stretch=2)
        top_panel.addWidget(stats_group, stretch=1)
        
        # Создаем нижнюю панель со списком вкладов и топами
        bottom_panel = QHBoxLayout()
        
        # Список вкладов и суммы
        deposits_list = QGroupBox("Список вкладов и суммы всех транзакций по ним")
        deposits_list_layout = QVBoxLayout()
        self.deposits_list_label = QLabel()
        self.deposits_list_label.setAlignment(Qt.AlignTop)
        deposits_list_layout.addWidget(self.deposits_list_label)
        deposits_list.setLayout(deposits_list_layout)
        
        # Топы сотрудников и клиентов
        tops_panel = QVBoxLayout()
        
        # Топ сотрудников
        employees_top = QGroupBox("Топ 3 сотрудника по составлению отчетов")
        employees_layout = QGridLayout()
        self.employees_labels = []
        for i in range(3):
            row_labels = []
            for j in range(4):  # ФИО + кол-во
                label = QLabel()
                employees_layout.addWidget(label, i, j)
                row_labels.append(label)
            self.employees_labels.append(row_labels)
        employees_top.setLayout(employees_layout)
        
        # Топ клиентов
        clients_top = QGroupBox("Топ 3 клиента по количеству транзакций")
        clients_layout = QGridLayout()
        self.clients_labels = []
        for i in range(3):
            row_labels = []
            for j in range(4):  # ФИО + кол-во
                label = QLabel()
                clients_layout.addWidget(label, i, j)
                row_labels.append(label)
            self.clients_labels.append(row_labels)
        clients_top.setLayout(clients_layout)
        
        tops_panel.addWidget(employees_top)
        tops_panel.addWidget(clients_top)
        
        bottom_panel.addWidget(deposits_list, stretch=2)
        bottom_panel.addLayout(tops_panel, stretch=1)
        
        # Добавляем панели в главный layout
        main_layout.addLayout(top_panel)
        main_layout.addLayout(bottom_panel)
        
        # Обновляем данные
        self.refresh_data()
        
    def create_deposits_chart(self):
        """Создает график сумм по вкладам"""
        figure = Figure(figsize=(10, 6))  # Увеличиваем размер с 8,4 до 10,6
        canvas = FigureCanvas(figure)
        self.deposits_ax = figure.add_subplot(111)
        
        # Добавляем отступы, чтобы график не обрезался
        figure.subplots_adjust(bottom=0.2, left=0.1)
        
        # Настраиваем стиль графика
        self.deposits_ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        self.deposits_ax.set_title('Распределение сумм по типам вкладов', pad=20)
        
        return canvas
        
    def refresh_data(self):
        """Обновляет все данные на форме"""
        try:
            # 1. Обновляем график сумм по вкладам
            query = """
                SELECT d.type, SUM(t.amount)
                FROM Deposit d
                JOIN Transaction t ON d.id = t.deposit_id
                GROUP BY d.type
                ORDER BY d.type
            """
            results = self.db.execute_query(query, fetch_all=True)
            
            types = [r[0] for r in results]
            amounts = [float(r[1]) for r in results]
            
            self.deposits_ax.clear()
            bars = self.deposits_ax.bar(range(len(types)), amounts)
            self.deposits_ax.set_xticks(range(len(types)))
            self.deposits_ax.set_xticklabels(types, rotation=45, ha='right')
            self.deposits_ax.set_ylabel('Сумма (руб.)')
            
            # Добавляем подписи значений над столбцами
            for bar in bars:
                height = bar.get_height()
                self.deposits_ax.text(bar.get_x() + bar.get_width()/2., height,
                                   f'{int(height):,}',
                                   ha='center', va='bottom')
            
            self.deposits_canvas.draw()
            
            # 2. Обновляем статистику
            # Среднее кол-во вкладов на клиента
            query = """
                SELECT AVG(deposit_count)
                FROM (
                    SELECT client_id, COUNT(*) as deposit_count
                    FROM Deposit
                    GROUP BY client_id
                ) subquery
            """
            avg_deposits = self.db.execute_query(query, fetch_one=True)[0]
            self.avg_deposits_label.setText(f"Среднее кол-во вкладов, открываемое 1 клиентом: {avg_deposits:.2f}")
            
            # Средняя продолжительность существования вклада
            query = """
                SELECT AVG(EXTRACT(DAY FROM (close_date - open_date)))
                FROM Deposit
                WHERE close_date IS NOT NULL
            """
            avg_lifetime = self.db.execute_query(query, fetch_one=True)[0]
            self.avg_lifetime_label.setText(f"Средняя продолжительность существования вклада: {avg_lifetime:.1f} дней")
            
            # Средняя сумма транзакции
            query = """
                SELECT AVG(amount)
                FROM Transaction
            """
            avg_transaction = self.db.execute_query(query, fetch_one=True)[0]
            self.avg_transaction_label.setText(f"Средняя сумма по одной транзакции: {avg_transaction:.2f} руб.")
            
            # 3. Обновляем список вкладов и сумм
            query = """
                SELECT d.type, SUM(t.amount)
                FROM Deposit d
                JOIN Transaction t ON d.id = t.deposit_id
                GROUP BY d.type
                ORDER BY SUM(t.amount) DESC
            """
            results = self.db.execute_query(query, fetch_all=True)
            
            deposits_text = ""
            total_amount = 0
            for deposit_type, amount in results:
                deposits_text += f"{deposit_type:<20} {float(amount):.2f}\n"
                total_amount += float(amount)
            deposits_text += f"\nСреднее: {total_amount / len(results):.2f}"
            
            self.deposits_list_label.setText(deposits_text)
            
            # 4. Обновляем топ сотрудников
            query = """
                SELECT e.first_name, e.last_name, COUNT(*) as report_count
                FROM Employee e
                JOIN Report r ON e.id = r.employee_id
                GROUP BY e.id, e.first_name, e.last_name
                ORDER BY report_count DESC
                LIMIT 3
            """
            results = self.db.execute_query(query, fetch_all=True)
            
            for i, (first_name, last_name, count) in enumerate(results):
                self.employees_labels[i][0].setText("ФИ")
                self.employees_labels[i][1].setText(first_name)
                self.employees_labels[i][2].setText(last_name)
                self.employees_labels[i][3].setText(f"Кол-во отчетов: {count}")
            
            # 5. Обновляем топ клиентов
            query = """
                SELECT c.first_name, c.last_name, COUNT(*) as transaction_count
                FROM Client c
                JOIN Deposit d ON c.id = d.client_id
                JOIN Transaction t ON d.id = t.deposit_id
                GROUP BY c.id, c.first_name, c.last_name
                ORDER BY transaction_count DESC
                LIMIT 3
            """
            results = self.db.execute_query(query, fetch_all=True)
            
            for i, (first_name, last_name, count) in enumerate(results):
                self.clients_labels[i][0].setText("ФИ")
                self.clients_labels[i][1].setText(first_name)
                self.clients_labels[i][2].setText(last_name)
                self.clients_labels[i][3].setText(f"кол-во: {count}")
                
        except Exception as e:
            print(f"Ошибка при обновлении данных: {str(e)}") 