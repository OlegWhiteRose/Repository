from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor

from database.db import Database
from .main_window import MainWindow

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.setup_ui()
        self.apply_sberbank_style()
        
    def setup_ui(self):
        """Настраивает пользовательский интерфейс"""
        self.setWindowTitle("Вход в систему")
        self.setGeometry(100, 100, 400, 200)
        
        # Создаем центральный виджет и главный layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Заголовок
        title_label = QLabel("АС Учета вкладов в Сбербанке")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #1E4620; margin: 10px;")  # Темно-зеленый цвет Сбербанка
        main_layout.addWidget(title_label)
        
        # Форма входа
        form_layout = QFormLayout()
        
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        
        # Стилизация полей ввода
        input_style = """
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid #21A038;
            }
        """
        self.username_edit.setStyleSheet(input_style)
        self.password_edit.setStyleSheet(input_style)
        
        form_layout.addRow("Логин:", self.username_edit)
        form_layout.addRow("Пароль:", self.password_edit)
        
        main_layout.addLayout(form_layout)
        
        # Кнопка входа
        login_button = QPushButton("Войти")
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #21A038;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1E4620;
            }
            QPushButton:pressed {
                background-color: #167025;
            }
        """)
        login_button.clicked.connect(self.login)
        main_layout.addWidget(login_button)
        
        # Добавляем отступы
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
    def apply_sberbank_style(self):
        """Применяет стиль Сбербанка к окну"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
            QLabel {
                color: #1E4620;
            }
            QFormLayout {
                spacing: 10px;
            }
        """)
        
    def login(self):
        """Обработка входа в систему"""
        username = self.username_edit.text()
        password = self.password_edit.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return
            
        try:
            # В реальной системе здесь должна быть проверка пароля
            # Сейчас для демонстрации используем простую логику:
            # admin/admin для администратора
            # user/user для обычного пользователя
            
            if username == "admin" and password == "admin":
                role = "admin"
            elif username == "user" and password == "user":
                role = "user"
            else:
                QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
                return
                
            # Открываем главное окно
            self.main_window = MainWindow(username, role)
            self.main_window.show()
            self.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка входа в систему: {str(e)}") 