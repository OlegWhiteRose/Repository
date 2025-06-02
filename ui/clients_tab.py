from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QAbstractItemView,
    QTableWidgetItem,
    QPushButton,
    QLineEdit,
    QLabel,
    QHeaderView,
    QMessageBox,
    QDialog,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

from database.db import Database
from database.queries import Queries
from .client_dialog import ClientDialog
import psycopg2


class ClientsTab(QWidget):
    def __init__(self, user_role):
        super().__init__()
        self.user_role = user_role
        self.is_admin = self.user_role == "admin"
        self.db = Database()
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(500)
        self.search_timer.timeout.connect(self._perform_search)

        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Search
        search_layout = QHBoxLayout()
        
        search_fname_label = QLabel("Имя:")
        self.search_fname_input = QLineEdit()
        self.search_fname_input.setPlaceholderText("Введите имя...")
        self.search_fname_input.textChanged.connect(self.on_search_text_changed)
        
        search_lname_label = QLabel("Фамилия:")
        self.search_lname_input = QLineEdit()
        self.search_lname_input.setPlaceholderText("Введите фамилию...")
        self.search_lname_input.textChanged.connect(self.on_search_text_changed)
        
        search_phone_label = QLabel("Телефон:")
        self.search_phone_input = QLineEdit()
        self.search_phone_input.setPlaceholderText("Введите телефон...")
        self.search_phone_input.textChanged.connect(self.on_search_text_changed)
        
        clear_search_btn = QPushButton("Очистить")
        clear_search_btn.clicked.connect(self.clear_search)
        
        search_layout.addWidget(search_fname_label)
        search_layout.addWidget(self.search_fname_input)
        search_layout.addWidget(search_lname_label)
        search_layout.addWidget(self.search_lname_input)
        search_layout.addWidget(search_phone_label)
        search_layout.addWidget(self.search_phone_input)
        search_layout.addWidget(clear_search_btn)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.add_btn = QPushButton(QIcon.fromTheme("list-add"), " Добавить")
        self.add_btn.clicked.connect(self.add_client)
        self.add_btn.setEnabled(self.is_admin)
        
        self.edit_btn = QPushButton(QIcon.fromTheme("document-edit"), " Изменить")
        self.edit_btn.clicked.connect(self.edit_client)
        self.edit_btn.setEnabled(False)
        
        self.delete_btn = QPushButton(QIcon.fromTheme("edit-delete"), " Удалить")
        self.delete_btn.clicked.connect(self.delete_client)
        self.delete_btn.setEnabled(False)
        
        self.documents_btn = QPushButton(QIcon.fromTheme("document-properties"), " Документы")
        self.documents_btn.clicked.connect(self.show_client_documents)
        self.documents_btn.setEnabled(False)
        
        self.deposits_btn = QPushButton(QIcon.fromTheme("folder-open"), " Вклады")
        self.deposits_btn.clicked.connect(self.show_client_deposits)
        self.deposits_btn.setEnabled(False)

        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addWidget(self.documents_btn)
        toolbar.addWidget(self.deposits_btn)
        toolbar.addStretch(1)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Имя", "Фамилия", "Телефон"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        layout.addLayout(search_layout)
        layout.addLayout(toolbar)
        layout.addWidget(self.table)

    def on_search_text_changed(self):
        self.search_timer.start()

    def _perform_search(self):
        self.load_data()

    def clear_search(self):
        self.search_fname_input.clear()
        self.search_lname_input.clear()
        self.search_phone_input.clear()
        self.load_data()

    def load_data(self):
        fname = self.search_fname_input.text().strip()
        lname = self.search_lname_input.text().strip()
        phone = self.search_phone_input.text().strip()
        
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Базовый запрос
                    query = "SELECT id, first_name, last_name, phone FROM Client WHERE 1=1"
                    params = []
                    
                    # Добавляем условия поиска
                    if fname:
                        query += " AND LOWER(first_name) LIKE LOWER(%s)"
                        params.append(f"%{fname}%")
                    if lname:
                        query += " AND LOWER(last_name) LIKE LOWER(%s)"
                        params.append(f"%{lname}%")
                    if phone:
                        query += " AND phone LIKE %s"
                        params.append(f"%{phone}%")
                    
                    query += " ORDER BY last_name, first_name"
                    
                    cursor.execute(query, params)
                    clients = cursor.fetchall()
                    
                    self.table.setRowCount(len(clients))
                    for row, client in enumerate(clients):
                        # ID
                        id_item = QTableWidgetItem(str(client[0]))
                        id_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 0, id_item)
                        
                        # First Name
                        self.table.setItem(row, 1, QTableWidgetItem(client[1]))
                        
                        # Last Name
                        self.table.setItem(row, 2, QTableWidgetItem(client[2]))
                        
                        # Phone
                        phone_item = QTableWidgetItem(client[3])
                        phone_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 3, phone_item)
                        
        except psycopg2.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка БД",
                f"Не удалось загрузить список клиентов:\n{str(e)}"
            )
            self.table.setRowCount(0)

    def on_selection_changed(self):
        has_selection = bool(self.table.selectedItems())
        self.edit_btn.setEnabled(has_selection and self.is_admin)
        self.delete_btn.setEnabled(has_selection and self.is_admin)
        self.documents_btn.setEnabled(has_selection)
        self.deposits_btn.setEnabled(has_selection)

    def get_selected_client_id(self):
        selected_rows = self.table.selectedItems()
        if selected_rows:
            return int(self.table.item(selected_rows[0].row(), 0).text())
        return None

    def add_client(self):
        dialog = ClientDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            Queries.ADD_CLIENT,
                            dialog.get_data()
                        )
                        conn.commit()
                        QMessageBox.information(self, "Успех", "Клиент успешно добавлен")
                        self.load_data()
            except psycopg2.Error as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить клиента:\n{str(e)}")

    def edit_client(self):
        client_id = self.get_selected_client_id()
        if client_id is None:
            QMessageBox.warning(self, "Внимание", "Выберите клиента для редактирования")
            return
            
        dialog = ClientDialog(self, client_id=client_id)
        if dialog.exec_() == QDialog.Accepted:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        data = dialog.get_data()
                        data["id"] = client_id
                        cursor.execute(
                            Queries.UPDATE_CLIENT,
                            data
                        )
                        conn.commit()
                        QMessageBox.information(self, "Успех", "Данные клиента обновлены")
                        self.load_data()
            except psycopg2.Error as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось обновить данные клиента:\n{str(e)}"
                )

    def delete_client(self):
        client_id = self.get_selected_client_id()
        if client_id is None:
            QMessageBox.warning(self, "Внимание", "Выберите клиента для удаления")
            return
            
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить этого клиента?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(Queries.DELETE_CLIENT, {"id": client_id})
                        conn.commit()
                        QMessageBox.information(self, "Успех", "Клиент успешно удален")
                        self.load_data()
            except psycopg2.Error as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось удалить клиента:\n{str(e)}"
                )

    def show_client_documents(self):
        client_id = self.get_selected_client_id()
        if client_id is None:
            QMessageBox.warning(self, "Внимание", "Выберите клиента для просмотра документов")
            return
            
        selected_row = self.table.selectedItems()[0].row()
        client_name = f"{self.table.item(selected_row, 1).text()} {self.table.item(selected_row, 2).text()}"
        
        dialog = DocumentsDialog(self, client_id, client_name)
        dialog.exec_()

    def show_client_deposits(self):
        client_id = self.get_selected_client_id()
        if client_id is None:
            QMessageBox.warning(self, "Внимание", "Выберите клиента для просмотра вкладов")
            return
            
        selected_row = self.table.selectedItems()[0].row()
        client_name = f"{self.table.item(selected_row, 1).text()} {self.table.item(selected_row, 2).text()}"
        
        dialog = DepositsDialog(self, client_id, client_name)
        dialog.exec_() 