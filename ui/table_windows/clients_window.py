from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QTableWidgetItem,
    QGroupBox,
    QHBoxLayout
)
from PyQt5.QtCore import Qt

from .base_table_window import BaseTableWindow
from database.db import Database
from .documents_window import DocumentsWindow
from .deposits_window import DepositsWindow

class ClientDialog(QDialog):
    """Диалог для добавления/редактирования клиента"""
    def __init__(self, parent=None, client_data=None):
        super().__init__(parent)
        self.client_data = client_data
        self.setWindowTitle("Добавить клиента" if not client_data else "Редактировать клиента")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Создаем поля ввода
        self.first_name_edit = QLineEdit()
        self.last_name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.phone_edit.setInputMask("+7 (999) 999-99-99")
        self.phone_edit.setPlaceholderText("+7 (___) ___-__-__")
        
        # Добавляем поля в форму
        form_layout.addRow("Имя*:", self.first_name_edit)
        form_layout.addRow("Фамилия*:", self.last_name_edit)
        form_layout.addRow("Телефон*:", self.phone_edit)
        
        # Если редактируем существующего клиента
        if self.client_data:
            self.first_name_edit.setText(self.client_data["first_name"])
            self.last_name_edit.setText(self.client_data["last_name"])
            self.phone_edit.setText(self.client_data["phone"])
            
        # Кнопки
        buttons_layout = QVBoxLayout()
        save_button = QPushButton("Сохранить")
        cancel_button = QPushButton("Отмена")
        
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        
        # Собираем layout
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        
    def get_data(self):
        """Возвращает введенные данные"""
        return {
            "first_name": self.first_name_edit.text(),
            "last_name": self.last_name_edit.text(),
            "phone": self.phone_edit.text()
        }

class ClientsWindow(BaseTableWindow):
    def __init__(self, parent=None, user_role="user", specific_client_id=None):
        super().__init__(parent, title="Клиенты", user_role=user_role)
        self.db = Database()
        self.specific_client_id = specific_client_id
        self.setup_search_panel()
        self.setup_table()
        self.setup_navigation()
        self.refresh_table()
        
    def setup_search_panel(self):
        """Настраивает панель поиска"""
        # Если указан конкретный клиент, не показываем панель поиска
        if self.specific_client_id:
            return

        search_group = QGroupBox("Поиск")
        search_layout = QFormLayout()
        
        self.search_last_name = QLineEdit()
        self.search_last_name.setPlaceholderText("Введите фамилию...")
        self.search_last_name.textChanged.connect(self.refresh_table)
        
        self.search_phone = QLineEdit()
        self.search_phone.setInputMask("+7 (999) 999-99-99;_")
        self.search_phone.setPlaceholderText("+7 (___) ___-__-__")
        self.initial_phone_mask = self.search_phone.text()
        self.search_phone.textChanged.connect(self.refresh_table)
        
        search_layout.addRow("Фамилия:", self.search_last_name)
        search_layout.addRow("Телефон:", self.search_phone)
        
        search_group.setLayout(search_layout)
        self.main_layout.insertWidget(1, search_group)
        
    def setup_table(self):
        """Настраивает структуру таблицы"""
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Имя", "Фамилия", "Телефон"])
        
    def setup_navigation(self):
        """Настраивает кнопки навигации"""
        self.add_navigation_button("Вклады клиента", self.show_deposits)
        self.add_navigation_button("Документы клиента", self.show_documents)
        
    def show_deposits(self):
        """Открывает окно вкладов для выбранного клиента"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            client_id = self.table.item(current_row, 0).text()
            client_name = f"{self.table.item(current_row, 1).text()} {self.table.item(current_row, 2).text()}"
            deposits_window = DepositsWindow(self, client_id, client_name)
            deposits_window.show()
            
    def show_documents(self):
        """Открывает окно документов для выбранного клиента"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            client_id = self.table.item(current_row, 0).text()
            client_name = f"{self.table.item(current_row, 1).text()} {self.table.item(current_row, 2).text()}"
            documents_window = DocumentsWindow(self, client_id, client_name)
            documents_window.show()
        
    def refresh_table(self):
        """Обновляет данные в таблице"""
        try:
            # Базовый запрос
            query = """
                SELECT id, first_name, last_name, phone
                FROM Client
                WHERE 1=1
            """
            params = []

            # Если указан конкретный клиент, показываем только его
            if self.specific_client_id:
                query += " AND id = %s"
                params.append(self.specific_client_id)
            else:
                # Иначе применяем фильтры поиска
                if self.search_last_name.text():
                    query += " AND LOWER(last_name) LIKE LOWER(%s)"
                    params.append(f"%{self.search_last_name.text()}%")

                if self.search_phone.text() != self.initial_phone_mask:
                    current_phone = ''.join(c for c in self.search_phone.text() if c.isdigit())
                    if current_phone:
                        query += " AND phone ~ %s"
                        search_pattern = '%'
                        for digit in current_phone:
                            search_pattern += f'[^0-9]*{digit}'
                        search_pattern += '%'
                        params.append(search_pattern)

            query += " ORDER BY last_name, first_name"
            
            results = self.db.execute_query(query, params=params, fetch_all=True)
            
            self.table.setRowCount(0)
            for row_num, row_data in enumerate(results):
                self.table.insertRow(row_num)
                for col_num, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_data) if cell_data is not None else "")
                    if col_num == 0:  # ID column
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row_num, col_num, item)
                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")
            
    def add_record(self):
        """Добавление нового клиента"""
        dialog = ClientDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    INSERT INTO Client (first_name, last_name, phone)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """
                self.db.execute_query(
                    query,
                    params=(data["first_name"], data["last_name"], data["phone"]),
                    commit=True
                )
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Клиент успешно добавлен")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить клиента: {str(e)}")
                
    def edit_record(self):
        """Редактирование выбранного клиента"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите клиента для редактирования")
            return
            
        client_data = {
            "id": self.table.item(current_row, 0).text(),
            "first_name": self.table.item(current_row, 1).text(),
            "last_name": self.table.item(current_row, 2).text(),
            "phone": self.table.item(current_row, 3).text()
        }
        
        dialog = ClientDialog(self, client_data)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    UPDATE Client
                    SET first_name = %s,
                        last_name = %s,
                        phone = %s
                    WHERE id = %s
                """
                self.db.execute_query(
                    query,
                    params=(
                        data["first_name"],
                        data["last_name"],
                        data["phone"],
                        client_data["id"]
                    ),
                    commit=True
                )
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Данные клиента обновлены")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить данные: {str(e)}")
                
    def delete_record(self):
        """Удаление выбранного клиента"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите клиента для удаления")
            return
            
        client_id = self.table.item(current_row, 0).text()
        client_name = f"{self.table.item(current_row, 1).text()} {self.table.item(current_row, 2).text()}"
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите удалить клиента {client_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM Client WHERE id = %s"
                self.db.execute_query(query, params=(client_id,), commit=True)
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Клиент успешно удален")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить клиента: {str(e)}")
                
    def show_related_records(self, row):
        """Показывает связанные записи для выбранного клиента"""
        # При выделении записи ничего не открываем автоматически
        pass 