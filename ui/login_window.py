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
from PyQt5.QtGui import QFont

from database.db import Database
from .main_window import MainWindow

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.setup_ui()
        
    def setup_ui(self):
        """Настраивает пользовательский интерфейс"""
        self.setWindowTitle("Вход в систему")
        self.setGeometry(100, 100, 400, 200)
        
        # Создаем центральный виджет и главный layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Заголовок
        title_label = QLabel("Банковская система управления вкладами")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Форма входа
        form_layout = QFormLayout()
        
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("Логин:", self.username_edit)
        form_layout.addRow("Пароль:", self.password_edit)
        
        main_layout.addLayout(form_layout)
        
        # Кнопка входа
        login_button = QPushButton("Войти")
        login_button.clicked.connect(self.login)
        main_layout.addWidget(login_button)
        
        # Версия
        version_label = QLabel("Версия 1.0")
        version_label.setAlignment(Qt.AlignRight)
        main_layout.addWidget(version_label)
        
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