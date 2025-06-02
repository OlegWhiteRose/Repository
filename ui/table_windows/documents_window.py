from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QTableWidgetItem,
    QDateEdit,
    QComboBox,
    QGroupBox
)
from PyQt5.QtCore import Qt, QDate
from datetime import datetime

from .base_table_window import BaseTableWindow
from database.db import Database

class DocumentDialog(QDialog):
    """Диалог для добавления/редактирования документа"""
    def __init__(self, parent=None, document_data=None):
        super().__init__(parent)
        self.document_data = document_data
        self.setWindowTitle("Добавить документ" if not document_data else "Редактировать документ")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Создаем поля ввода
        self.passport_edit = QLineEdit()
        self.passport_edit.setPlaceholderText("XXXX XXXXXX")
        
        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setDate(QDate.currentDate().addYears(-18))
        
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["М", "Ж"])
        
        self.agreement_date_edit = QDateEdit()
        self.agreement_date_edit.setCalendarPopup(True)
        self.agreement_date_edit.setDate(QDate.currentDate())
        
        self.security_word_edit = QLineEdit()
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["active", "expired", "suspended"])
        
        # Добавляем поля в форму
        form_layout.addRow("Номер паспорта*:", self.passport_edit)
        form_layout.addRow("Дата рождения*:", self.birth_date_edit)
        form_layout.addRow("Пол*:", self.gender_combo)
        form_layout.addRow("Дата договора*:", self.agreement_date_edit)
        form_layout.addRow("Кодовое слово*:", self.security_word_edit)
        form_layout.addRow("Статус*:", self.status_combo)
        
        # Если редактируем существующий документ
        if self.document_data:
            self.passport_edit.setText(self.document_data["passport_number"])
            self.birth_date_edit.setDate(QDate.fromString(self.document_data["birth_date"], Qt.ISODate))
            self.gender_combo.setCurrentText(self.document_data["gender"])
            self.agreement_date_edit.setDate(QDate.fromString(self.document_data["agreement_date"], Qt.ISODate))
            self.security_word_edit.setText(self.document_data["security_word"])
            self.status_combo.setCurrentText(self.document_data["agreement_status"])
            
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
            "passport_number": self.passport_edit.text(),
            "birth_date": self.birth_date_edit.date().toString(Qt.ISODate),
            "gender": self.gender_combo.currentText(),
            "agreement_date": self.agreement_date_edit.date().toString(Qt.ISODate),
            "security_word": self.security_word_edit.text(),
            "agreement_status": self.status_combo.currentText()
        }

class DocumentsWindow(BaseTableWindow):
    def __init__(self, parent=None, client_id=None, client_name=None, user_role="user"):
        title = f"Документы - {client_name}" if client_name else "Документы"
        super().__init__(parent, title=title, user_role=user_role)
        self.db = Database()
        self.client_id = client_id
        self.client_name = client_name
        self.setup_search_panel()
        self.setup_table()
        self.setup_navigation()
        self.refresh_table()
        
    def setup_navigation(self):
        """Настраивает кнопки навигации"""
        if not self.client_id:  # Если окно открыто не из окна клиента
            self.add_navigation_button("Клиент", self.show_client)
        else:  # Если окно открыто из окна клиента
            self.add_navigation_button("Вклады", self.show_deposits)
            
    def show_client(self):
        """Открывает окно клиента для выбранного документа"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            try:
                query = """
                    SELECT c.id, c.first_name, c.last_name, c.phone
                    FROM Document d
                    JOIN Client c ON d.client_id = c.id
                    WHERE d.id = %s
                """
                client = self.db.execute_query(
                    query,
                    params=(self.table.item(current_row, 0).text(),),
                    fetch_one=True
                )
                
                if client:
                    from .clients_window import ClientsWindow
                    clients_window = ClientsWindow(self)
                    clients_window.show()
                    
                    # Устанавливаем фильтр для отображения только нужного клиента
                    clients_window.specific_client_id = client[0]
                    clients_window.refresh_table()
                    
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно клиента: {str(e)}")
        
    def show_deposits(self):
        """Открывает окно вкладов для текущего клиента"""
        deposits_window = DepositsWindow(self, self.client_id, self.client_name, self.user_role)
        deposits_window.show()
        
    def setup_search_panel(self):
        """Настраивает панель поиска"""
        search_group = QGroupBox("Поиск")
        search_layout = QFormLayout()
        
        self.search_passport = QLineEdit()
        self.search_passport.setPlaceholderText("XXXX XXXXXX")
        self.search_passport.textChanged.connect(self.refresh_table)
        
        self.search_status = QComboBox()
        self.search_status.addItems([
            "Все статусы",
            "active",
            "inactive"
        ])
        self.search_status.currentTextChanged.connect(self.refresh_table)
        
        search_layout.addRow("Номер паспорта:", self.search_passport)
        search_layout.addRow("Статус:", self.search_status)
        
        search_group.setLayout(search_layout)
        self.main_layout.insertWidget(0, search_group)
        
    def setup_table(self):
        """Настраивает структуру таблицы"""
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Номер паспорта", "Дата рождения", "Пол",
            "Клиент", "Дата договора", "Кодовое слово", "Статус"
        ])
        
    def refresh_table(self):
        """Обновляет данные в таблице"""
        try:
            base_query = """
                SELECT d.id, d.passport_number, d.birth_date, d.gender,
                       c.last_name || ' ' || c.first_name as client_name,
                       d.agreement_date, d.security_word, d.agreement_status
                FROM Document d
                JOIN Client c ON d.client_id = c.id
                WHERE (d.passport_number LIKE %s OR %s = '')
                  AND (d.agreement_status = %s OR %s = 'Все статусы')
            """
            
            if self.client_id:
                base_query += " AND d.client_id = %s"
                
            base_query += " ORDER BY d.agreement_date DESC"
            
            search_passport = f"%{self.search_passport.text()}%" if self.search_passport.text() else ""
            status = self.search_status.currentText()
            
            params = [search_passport, search_passport, status, status]
            if self.client_id:
                params.append(self.client_id)
                
            results = self.db.execute_query(base_query, params=params, fetch_all=True)
            
            self.table.setRowCount(0)
            for row_num, row_data in enumerate(results):
                self.table.insertRow(row_num)
                for col_num, cell_data in enumerate(row_data):
                    if isinstance(cell_data, datetime):
                        cell_data = cell_data.strftime("%Y-%m-%d")
                    item = QTableWidgetItem(str(cell_data))
                    if col_num in [0]:  # ID column
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row_num, col_num, item)
                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")
            
    def add_record(self):
        """Добавление нового документа"""
        dialog = DocumentDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    INSERT INTO Document (
                        passport_number, birth_date, gender,
                        client_id, agreement_date,
                        security_word, agreement_status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                self.db.execute_query(
                    query,
                    params=(
                        data["passport_number"],
                        data["birth_date"],
                        data["gender"],
                        self.client_id,
                        data["agreement_date"],
                        data["security_word"],
                        data["agreement_status"]
                    ),
                    commit=True
                )
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Документ успешно добавлен")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить документ: {str(e)}")
                
    def edit_record(self):
        """Редактирование выбранного документа"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите документ для редактирования")
            return
            
        document_data = {
            "id": self.table.item(current_row, 0).text(),
            "passport_number": self.table.item(current_row, 1).text(),
            "birth_date": self.table.item(current_row, 2).text(),
            "gender": self.table.item(current_row, 3).text(),
            "client_id": self.table.item(current_row, 4).text(),
            "agreement_date": self.table.item(current_row, 5).text(),
            "security_word": self.table.item(current_row, 6).text(),
            "agreement_status": self.table.item(current_row, 7).text()
        }
        
        dialog = DocumentDialog(self, document_data)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    UPDATE Document
                    SET passport_number = %s,
                        birth_date = %s,
                        gender = %s,
                        agreement_date = %s,
                        security_word = %s,
                        agreement_status = %s
                    WHERE id = %s
                """
                self.db.execute_query(
                    query,
                    params=(
                        data["passport_number"],
                        data["birth_date"],
                        data["gender"],
                        data["agreement_date"],
                        data["security_word"],
                        data["agreement_status"],
                        document_data["id"]
                    ),
                    commit=True
                )
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Документ успешно обновлен")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить документ: {str(e)}")
                
    def delete_record(self):
        """Удаление выбранного документа"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите документ для удаления")
            return
            
        document_id = self.table.item(current_row, 0).text()
        passport_number = self.table.item(current_row, 1).text()
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите удалить документ {passport_number}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM Document WHERE id = %s"
                self.db.execute_query(query, params=(document_id,), commit=True)
                self.refresh_table()
                QMessageBox.information(self, "Успех", "Документ успешно удален")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить документ: {str(e)}")
                
    def show_related_records(self, row):
        """У документов нет прямых связей с другими таблицами"""
        pass 