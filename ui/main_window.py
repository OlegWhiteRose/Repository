from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QMessageBox,
    QLabel,
    QFrame
)
from PyQt5.QtGui import QIcon, QFont, QColor
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
        self.apply_sberbank_style()
        
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        logger.debug("Started")
        
        self.setWindowTitle("АС Учета вкладов в Сбербанке")
        self.setGeometry(100, 100, 1200, 800)
        
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Создаем навбар
        navbar = QFrame()
        navbar.setStyleSheet("""
            QFrame {
                background-color: #21A038;
                min-height: 40px;
                max-height: 40px;
            }
        """)
        navbar_layout = QHBoxLayout(navbar)
        navbar_layout.setContentsMargins(20, 0, 20, 0)
        navbar_layout.setSpacing(10)
        
        # Заголовок в навбаре
        title_label = QLabel("АС Учета вкладов в Сбербанке")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        navbar_layout.addWidget(title_label)
        
        # Добавляем растягивающийся элемент
        navbar_layout.addStretch()
        
        # Информация о пользователе
        user_label = QLabel(f"Пользователь: {self.username}")
        user_label.setStyleSheet("""
            QLabel {
                color: white;
                margin-right: 15px;
            }
        """)
        navbar_layout.addWidget(user_label)
        
        # Кнопка выхода
        logout_button = QPushButton("Выйти")
        logout_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 1px solid white;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1E4620;
            }
            QPushButton:pressed {
                background-color: #167025;
            }
        """)
        logout_button.clicked.connect(self.logout)
        navbar_layout.addWidget(logout_button)
        
        main_layout.addWidget(navbar)
        
        # Контейнер для основного содержимого
        content_container = QWidget()
        content_container.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Создаем кнопки для разных разделов
        buttons_layout = QVBoxLayout()
        
        # Стиль для кнопок
        button_style = """
            QPushButton {
                background-color: white;
                color: #21A038;
                border: 2px solid #21A038;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #21A038;
                color: white;
            }
            QPushButton:pressed {
                background-color: #1E4620;
                color: white;
            }
        """
        
        # Кнопка "Клиенты"
        clients_button = QPushButton("Клиенты")
        clients_button.setStyleSheet(button_style)
        clients_button.clicked.connect(self.open_clients_window)
        buttons_layout.addWidget(clients_button)
        
        # Кнопка "Документы"
        documents_button = QPushButton("Документы")
        documents_button.setStyleSheet(button_style)
        documents_button.clicked.connect(self.open_documents_window)
        buttons_layout.addWidget(documents_button)
        
        # Кнопка "Вклады"
        deposits_button = QPushButton("Вклады")
        deposits_button.setStyleSheet(button_style)
        deposits_button.clicked.connect(self.open_deposits_window)
        buttons_layout.addWidget(deposits_button)
        
        # Кнопка "Транзакции"
        transactions_button = QPushButton("Транзакции")
        transactions_button.setStyleSheet(button_style)
        transactions_button.clicked.connect(self.open_transactions_window)
        buttons_layout.addWidget(transactions_button)
        
        # Кнопка "Сотрудники"
        employees_button = QPushButton("Сотрудники")
        employees_button.setStyleSheet(button_style)
        employees_button.clicked.connect(self.open_employees_window)
        buttons_layout.addWidget(employees_button)
        
        # Кнопка "Отчеты"
        reports_button = QPushButton("Отчеты")
        reports_button.setStyleSheet(button_style)
        reports_button.clicked.connect(self.open_reports_window)
        buttons_layout.addWidget(reports_button)

        # Кнопка "Статистика"
        statistics_button = QPushButton("Статистика")
        statistics_button.setStyleSheet(button_style)
        statistics_button.clicked.connect(self.open_statistics_window)
        buttons_layout.addWidget(statistics_button)
            
        content_layout.addLayout(buttons_layout)
        main_layout.addWidget(content_container)
        
        logger.debug("UI initialization completed")
        
    def apply_sberbank_style(self):
        """Применяет стиль Сбербанка к окну"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
        """)
        
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
            "Подтверждение",
            "Вы уверены, что хотите выйти из системы?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            from .login_window import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()
            self.close()
