from PyQt5.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QLabel,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

# Импорт ВСЕХ вкладок
from .entities_tab import EntitiesTab
from .investors_tab import InvestorsTab
from .registrars_tab import RegistrarsTab
from .emitters_tab import EmittersTab
from .emissions_tab import EmissionsTab
from .stocks_tab import StocksTab
from .sells_tab import SellsTab
from .search_tab import SearchTab
from .analytics_tab import AnalyticsTab

from database.db import Database
import psycopg2


class MainWindow(QMainWindow):
    def __init__(self, username, user_role):
        super().__init__()
        self.username = username
        self.user_role = user_role.lower() if user_role else "user"
        self.setWindowTitle(
            f"АС Учета Эмиссии Ценных Бумаг [{self.username} - {self.user_role.upper()}]"
        )
        self.setWindowIcon(QIcon.fromTheme("office-address-book"))
        self.setGeometry(50, 50, 1350, 800)

        self._initialization_failed = False
        if not self.check_db_connection():
            QMessageBox.critical(
                self, "Ошибка соединения с БД", "Не удалось подключиться к базе данных."
            )
            self._initialization_failed = True
            # Создаем простой виджет для отображения ошибки
            self.central_widget = QWidget()
            layout = QVBoxLayout(self.central_widget)
            layout.addWidget(
                QLabel(
                    "Ошибка подключения к базе данных. Приложение не может работать."
                ),
                alignment=Qt.AlignCenter,
            )
            self.setCentralWidget(self.central_widget)
            return  # Прекращаем инициализацию, если нет соединения

        # Инициализация UI только если соединение успешно
        self.init_ui()
        # Можно применить ограничения ролей сразу или с задержкой
        # self.apply_role_restrictions()
        # QTimer.singleShot(100, self.apply_role_restrictions)

    def initialization_failed(self):
        """Проверяет, произошла ли ошибка при инициализации (например, нет БД)."""
        return hasattr(self, "_initialization_failed") and self._initialization_failed

    def check_db_connection(self):
        """Проверяет соединение с базой данных."""
        try:
            db = Database()
            with db.get_connection():
                print("DEBUG [MainWindow]: Database connection successful.")
                return True
        except psycopg2.OperationalError as e:
            print(f"DB Connection Error in MainWindow check: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during DB connection check: {e}")
            return False

    def init_ui(self):
        """Инициализирует пользовательский интерфейс главного окна."""
        print("DEBUG [init_ui]: Started")
        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)

        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(True)  # Позволяет прокручивать вкладки

        # --- Создаем все вкладки ---
        # Передаем роль пользователя в конструкторы вкладок
        print("DEBUG [init_ui]: Creating tab widgets...")
        self.entities_tab = EntitiesTab(self.user_role)
        self.investors_tab = InvestorsTab(self.user_role)
        self.registrars_tab = RegistrarsTab(self.user_role)
        self.emitters_tab = EmittersTab(self.user_role)
        self.emissions_tab = EmissionsTab(self.user_role)
        self.stocks_tab = StocksTab(self.user_role)
        self.sells_tab = SellsTab(self.user_role)
        self.search_tab = SearchTab()  # Передаем роль, если нужно
        self.analytics_tab = AnalyticsTab()  # Передаем роль, если нужно
        print("DEBUG [init_ui]: All tab widgets created")

        # --- Устанавливаем зависимости для InvestorsTab ---
        if hasattr(self.investors_tab, "set_dependencies"):
            self.investors_tab.set_dependencies(self.tabs, self.sells_tab)
            print("DEBUG [init_ui]: Dependencies set for InvestorsTab")
        else:
            print("WARN [init_ui]: Method set_dependencies not found in InvestorsTab")
        # ----------------------------------------------------

        # --- Добавляем все вкладки с иконками ---
        print("DEBUG [init_ui]: Adding tabs to QTabWidget...")
        self.tabs.addTab(
            self.entities_tab, QIcon.fromTheme("office-address-book"), "Юр. лица"
        )
        self.tabs.addTab(
            self.investors_tab, QIcon.fromTheme("system-users"), "Инвесторы"
        )
        self.tabs.addTab(
            self.registrars_tab,
            QIcon.fromTheme("preferences-system-windows"),
            "Регистраторы",
        )
        self.tabs.addTab(
            self.emitters_tab, QIcon.fromTheme("network-server"), "Эмитенты"
        )
        self.tabs.addTab(
            self.emissions_tab, QIcon.fromTheme("document-send"), "Эмиссии"
        )
        self.tabs.addTab(
            self.stocks_tab, QIcon.fromTheme("insert-chart"), "Ценные бумаги"
        )
        self.tabs.addTab(self.sells_tab, QIcon.fromTheme("cash-register"), "Сделки")
        self.tabs.addTab(self.search_tab, QIcon.fromTheme("system-search"), "Поиск")
        self.tabs.addTab(
            self.analytics_tab, QIcon.fromTheme("office-chart-pie"), "Аналитика"
        )
        print("DEBUG [init_ui]: All tabs added to QTabWidget")

        self.layout.addWidget(self.tabs)
        self.setCentralWidget(self.central_widget)

        # --- Применяем ограничения (пока не используется активно) ---
        self.apply_role_restrictions()
        print("DEBUG [init_ui]: Finished")

    def apply_role_restrictions(self):
        """Применяет ограничения интерфейса на основе роли пользователя."""
        # Этот метод можно будет расширить для скрытия/блокировки кнопок
        # на основе self.user_role != 'admin'
        print(
            f"DEBUG [apply_role_restrictions]: Applying restrictions for role: {self.user_role}"
        )
        # Пример:
        # if not self.is_admin:
        #     # Найти кнопки добавления/редактирования/удаления на всех вкладках
        #     # и сделать setEnabled(False)
        pass
