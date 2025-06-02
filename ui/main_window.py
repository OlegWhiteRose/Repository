from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QMessageBox,
    QLabel
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt

from .table_windows.clients_window import ClientsWindow
from .table_windows.documents_window import DocumentsWindow
from .table_windows.deposits_window import DepositsWindow
from .table_windows.transactions_window import TransactionsWindow
from .table_windows.employees_window import EmployeesWindow
from .table_windows.reports_window import ReportsWindow
from .statistics_window import StatisticsWindow

from database.db import Database
from .clients_tab import ClientsTab
from .documents_dialog import DocumentsDialog
from .deposits_dialog import DepositsDialog
from .transactions_dialog import TransactionsDialog
from .employees_dialog import EmployeesDialog
from .reports_dialog import ReportsDialog

import logging
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, username, user_role):
        super().__init__()
        self.username = username
        self.user_role = user_role
        self.db = Database()
        
        # Проверяем подключение к БД
        try:
            self.db.test_connection()
            logger.debug("Database connection successful.")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка подключения",
                f"Не удалось подключиться к базе данных: {str(e)}"
            )
            raise
            
        self.init_ui()
        
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        logger.debug("Started")
        
        self.setWindowTitle("Банковская система управления вкладами")
        self.setGeometry(100, 100, 800, 600)
        
        # Создаем центральный виджет и главный layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Верхняя панель с информацией о пользователе и кнопкой выхода
        header_layout = QHBoxLayout()
        
        # Информация о пользователе
        user_info = QLabel(f"Пользователь: {self.username} ({self.user_role})")
        user_info.setFont(QFont("Arial", 10, QFont.Bold))
        header_layout.addWidget(user_info)
        
        # Кнопка выхода
        logout_button = QPushButton("Выйти")
        logout_button.setFixedWidth(100)
        logout_button.clicked.connect(self.logout)
        header_layout.addWidget(logout_button)
        
        main_layout.addLayout(header_layout)
        
        # Создаем кнопки для разных разделов
        buttons_layout = QVBoxLayout()
        
        # Кнопка "Клиенты"
        clients_button = QPushButton("Клиенты")
        clients_button.setMinimumHeight(50)
        clients_button.clicked.connect(self.open_clients_window)
        buttons_layout.addWidget(clients_button)
        
        # Кнопка "Документы"
        documents_button = QPushButton("Документы")
        documents_button.setMinimumHeight(50)
        documents_button.clicked.connect(self.open_documents_window)
        buttons_layout.addWidget(documents_button)
        
        # Кнопка "Вклады"
        deposits_button = QPushButton("Вклады")
        deposits_button.setMinimumHeight(50)
        deposits_button.clicked.connect(self.open_deposits_window)
        buttons_layout.addWidget(deposits_button)
        
        # Кнопка "Транзакции"
        transactions_button = QPushButton("Транзакции")
        transactions_button.setMinimumHeight(50)
        transactions_button.clicked.connect(self.open_transactions_window)
        buttons_layout.addWidget(transactions_button)
        
        # Кнопки доступные только администраторам
        if self.user_role == "admin":
            # Кнопка "Сотрудники"
            employees_button = QPushButton("Сотрудники")
            employees_button.setMinimumHeight(50)
            employees_button.clicked.connect(self.open_employees_window)
            buttons_layout.addWidget(employees_button)
            
            # Кнопка "Отчеты"
            reports_button = QPushButton("Отчеты")
            reports_button.setMinimumHeight(50)
            reports_button.clicked.connect(self.open_reports_window)
            buttons_layout.addWidget(reports_button)
            
        # Кнопка "Статистика"
        statistics_button = QPushButton("Статистика")
        statistics_button.setMinimumHeight(50)
        statistics_button.clicked.connect(self.open_statistics_window)
        buttons_layout.addWidget(statistics_button)
        
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)
        
        # Добавляем информацию о версии
        version_label = QLabel("Версия 1.0")
        version_label.setAlignment(Qt.AlignRight)
        main_layout.addWidget(version_label)
        
        logger.debug("UI initialization completed")
        
    def open_clients_window(self):
        """Открывает окно работы с клиентами"""
        window = ClientsWindow(self, user_role=self.user_role)
        window.show()
        
    def open_documents_window(self):
        """Открывает окно работы с документами"""
        window = DocumentsWindow(self, user_role=self.user_role)
        window.show()
        
    def open_deposits_window(self):
        """Открывает окно работы с вкладами"""
        window = DepositsWindow(self, user_role=self.user_role)
        window.show()
        
    def open_transactions_window(self):
        """Открывает окно работы с транзакциями"""
        window = TransactionsWindow(self, user_role=self.user_role)
        window.show()
        
    def open_employees_window(self):
        """Открывает окно работы с сотрудниками"""
        window = EmployeesWindow(self, user_role=self.user_role)
        window.show()
        
    def open_reports_window(self):
        """Открывает окно работы с отчетами"""
        window = ReportsWindow(self, user_role=self.user_role)
        window.show()
        
    def open_statistics_window(self):
        """Открывает окно статистики"""
        window = StatisticsWindow(self)
        window.show()
        
    def logout(self):
        """Выход из системы"""
        reply = QMessageBox.question(
            self,
            'Подтверждение',
            'Вы действительно хотите выйти?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            from .login_window import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()
            self.close()
