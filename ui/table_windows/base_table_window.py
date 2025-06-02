from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QLabel,
    QMessageBox,
    QMenu,
    QHeaderView,
    QGroupBox,
    QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QColor, QPalette

class BaseTableWindow(QMainWindow):
    """Базовый класс для окон с таблицами"""
    
    # Сигнал для обновления связанных окон
    data_changed = pyqtSignal()
    
    def __init__(self, parent=None, title="Table Window", user_role="user"):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle(title)
        self.user_role = user_role
        self.setGeometry(150, 150, 1000, 600)
        
        # Создаем центральный виджет и главный layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Создаем навбар
        self.create_navbar(title)
        
        # Создаем контейнер для основного содержимого
        content_container = QWidget()
        content_container.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)  # Отступ между всеми элементами
        self.main_layout.addWidget(content_container)
        
        # Верхняя панель с кнопкой "Назад" и поиском
        self.create_top_panel()
        
        # Создаем таблицу
        self.create_table()
        
        # Нижняя панель с кнопками действий
        self.create_bottom_panel()
        
        # Панель навигации
        self.create_navigation_panel()
        
        # Применяем стили
        self.apply_sberbank_style()
        
    def create_navbar(self, title):
        """Создает навбар в стиле Сбербанка"""
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
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        navbar_layout.addWidget(title_label)
        navbar_layout.addStretch()
        
        self.main_layout.addWidget(navbar)
        
    def create_top_panel(self):
        """Создает верхнюю панель с кнопкой назад и поиском"""
        top_panel = QHBoxLayout()
        top_panel.setSpacing(20)  # Отступ между кнопкой назад и поиском
        
        # Кнопка "Назад"
        back_button = QPushButton("← Назад")
        back_button.setFixedWidth(100)
        back_button.clicked.connect(self.close)
        back_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #21A038;
                border: 2px solid #21A038;
                padding: 6px;
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
        """)
        top_panel.addWidget(back_button)
        
        # Поиск
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        self.search_label = QLabel("Поиск:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите текст для поиска...")
        self.search_input.textChanged.connect(self.search_in_table)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid #21A038;
            }
        """)
        
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_input)
        
        top_panel.addLayout(search_layout)
        self.main_layout.addLayout(top_panel)
        
    def create_table(self):
        """Создает таблицу"""
        self.table = QTableWidget()
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Стилизация таблицы
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #E7F5E9;
                color: black;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 5px;
                border: none;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
            }
            QHeaderView::section:hover {
                background-color: #E7F5E9;
            }
        """)
        
        self.main_layout.addWidget(self.table)
        
    def create_bottom_panel(self):
        """Создает нижнюю панель с кнопками действий"""
        bottom_panel = QHBoxLayout()
        bottom_panel.setSpacing(10)  # Отступ между кнопками
        
        button_style = """
            QPushButton {
                background-color: white;
                color: #21A038;
                border: 2px solid #21A038;
                padding: 6px 12px;
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
            QPushButton:disabled {
                background-color: #F5F5F5;
                color: #999;
                border-color: #999;
            }
        """
        
        # Кнопки действий только для админа
        if self.user_role == "admin":
            self.add_button = QPushButton("Добавить")
            self.add_button.clicked.connect(self.add_record)
            self.add_button.setStyleSheet(button_style)
            bottom_panel.addWidget(self.add_button)
            
            self.edit_button = QPushButton("Изменить")
            self.edit_button.clicked.connect(self.edit_record)
            self.edit_button.setEnabled(False)
            self.edit_button.setStyleSheet(button_style)
            bottom_panel.addWidget(self.edit_button)
            
            self.delete_button = QPushButton("Удалить")
            self.delete_button.clicked.connect(self.delete_record)
            self.delete_button.setEnabled(False)
            self.delete_button.setStyleSheet(button_style)
            bottom_panel.addWidget(self.delete_button)
        
        bottom_panel.addStretch()
        self.main_layout.addLayout(bottom_panel)
        
    def create_navigation_panel(self):
        """Создает панель навигации со связанными таблицами"""
        self.nav_group = QGroupBox("Навигация")
        self.nav_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #21A038;
                font-weight: bold;
            }
        """)
        
        self.nav_layout = QHBoxLayout()
        nav_label = QLabel("Перейти к:")
        nav_label.setStyleSheet("color: #666;")
        self.nav_layout.addWidget(nav_label)
        self.nav_layout.addStretch()
        self.nav_group.setLayout(self.nav_layout)
        self.nav_group.hide()  # По умолчанию скрыта
        self.main_layout.addWidget(self.nav_group)
        
    def add_navigation_button(self, text, callback):
        """Добавляет кнопку навигации"""
        button = QPushButton(text)
        button.clicked.connect(callback)
        button.setEnabled(False)
        button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #21A038;
                border: 2px solid #21A038;
                padding: 6px 12px;
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
            QPushButton:disabled {
                background-color: #F5F5F5;
                color: #999;
                border-color: #999;
            }
        """)
        self.nav_layout.insertWidget(self.nav_layout.count() - 1, button)
        self.nav_group.show()
        return button
        
    def apply_sberbank_style(self):
        """Применяет общие стили Сбербанка"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
            QLabel {
                color: #333;
            }
            QGroupBox {
                font-weight: bold;
                color: #21A038;
            }
        """)
        
    def on_selection_changed(self):
        """Обработчик изменения выделения в таблице"""
        has_selection = len(self.table.selectedItems()) > 0
        
        if self.user_role == "admin":
            self.edit_button.setEnabled(has_selection)
            self.delete_button.setEnabled(has_selection)
            
        # Активируем навигационные кнопки
        for i in range(self.nav_layout.count()):
            widget = self.nav_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setEnabled(has_selection)
                
        if has_selection:
            self.show_related_records(self.table.currentRow())
        
    def show_context_menu(self, position):
        """Показывает контекстное меню для строки таблицы"""
        menu = QMenu()
        
        # Получаем выбранную строку
        row = self.table.rowAt(position.y())
        if row >= 0:
            view_related = menu.addAction("Просмотр связанных записей")
            edit_action = menu.addAction("Изменить")
            delete_action = menu.addAction("Удалить")
            
            action = menu.exec_(self.table.viewport().mapToGlobal(position))
            
            if action == view_related:
                self.show_related_records(row)
            elif action == edit_action:
                self.edit_record()
            elif action == delete_action:
                self.delete_record()
                
    def search_in_table(self):
        """Поиск по таблице"""
        search_text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            row_hidden = True
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    row_hidden = False
                    break
            self.table.setRowHidden(row, row_hidden)
            
    def add_record(self):
        """Добавление новой записи"""
        raise NotImplementedError("Метод add_record должен быть переопределен")
        
    def edit_record(self):
        """Редактирование записи"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите запись для редактирования")
            return
        raise NotImplementedError("Метод edit_record должен быть переопределен")
        
    def delete_record(self):
        """Удаление записи"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите запись для удаления")
            return
        raise NotImplementedError("Метод delete_record должен быть переопределен")
        
    def show_related_records(self, row):
        """Показ связанных записей"""
        if row < 0:
            return
        raise NotImplementedError("Метод show_related_records должен быть переопределен")
        
    def refresh_table(self):
        """Обновление данных в таблице"""
        raise NotImplementedError("Метод refresh_table должен быть переопределен") 