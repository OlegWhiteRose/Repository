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
    QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

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
        
        # Верхняя панель с кнопкой "Назад" и поиском
        self.create_top_panel()
        
        # Создаем таблицу
        self.create_table()
        
        # Нижняя панель с кнопками действий
        self.create_bottom_panel()
        
        # Панель навигации
        self.create_navigation_panel()
        
    def create_top_panel(self):
        """Создает верхнюю панель с кнопкой назад и поиском"""
        top_panel = QHBoxLayout()
        
        # Кнопка "Назад"
        back_button = QPushButton("← Назад")
        back_button.setFixedWidth(100)
        back_button.clicked.connect(self.close)
        top_panel.addWidget(back_button)
        
        # Поиск
        search_layout = QHBoxLayout()
        self.search_label = QLabel("Поиск:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите текст для поиска...")
        self.search_input.textChanged.connect(self.search_in_table)
        
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
        self.main_layout.addWidget(self.table)
        
    def create_bottom_panel(self):
        """Создает нижнюю панель с кнопками действий"""
        bottom_panel = QHBoxLayout()
        
        # Кнопки действий только для админа
        if self.user_role == "admin":
            self.add_button = QPushButton("Добавить")
            self.add_button.clicked.connect(self.add_record)
            bottom_panel.addWidget(self.add_button)
            
            self.edit_button = QPushButton("Изменить")
            self.edit_button.clicked.connect(self.edit_record)
            self.edit_button.setEnabled(False)
            bottom_panel.addWidget(self.edit_button)
            
            self.delete_button = QPushButton("Удалить")
            self.delete_button.clicked.connect(self.delete_record)
            self.delete_button.setEnabled(False)
            bottom_panel.addWidget(self.delete_button)
        
        bottom_panel.addStretch()
        
        self.main_layout.addLayout(bottom_panel)
        
    def create_navigation_panel(self):
        """Создает панель навигации со связанными таблицами"""
        self.nav_group = QGroupBox("Навигация")
        self.nav_layout = QHBoxLayout()
        self.nav_layout.addWidget(QLabel("Перейти к:"))
        self.nav_layout.addStretch()
        self.nav_group.setLayout(self.nav_layout)
        self.nav_group.hide()  # По умолчанию скрыта
        self.main_layout.addWidget(self.nav_group)
        
    def add_navigation_button(self, text, callback):
        """Добавляет кнопку навигации"""
        button = QPushButton(text)
        button.clicked.connect(callback)
        button.setEnabled(False)  # По умолчанию кнопки неактивны
        self.nav_layout.insertWidget(self.nav_layout.count() - 1, button)
        self.nav_group.show()
        return button
        
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