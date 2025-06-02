from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QAbstractItemView,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QHeaderView,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from database.db import Database
from database.queries import Queries
from .document_dialog import DocumentDialog
import psycopg2
from datetime import datetime


class DocumentsDialog(QDialog):
    def __init__(self, parent=None, client_id=None, client_name=None):
        super().__init__(parent)
        self.client_id = client_id
        self.client_name = client_name
        self.db = Database()

        self.setWindowTitle(f"Документы клиента: {client_name}")
        self.setModal(True)
        self.setMinimumSize(800, 400)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header with client info
        header_layout = QHBoxLayout()
        header_label = QLabel(f"Документы клиента: {self.client_name}")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #21A038;
            }
        """)
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        # Toolbar
        toolbar = QHBoxLayout()
        
        self.add_btn = QPushButton(QIcon.fromTheme("list-add"), " Добавить")
        self.add_btn.clicked.connect(self.add_document)
        
        self.edit_btn = QPushButton(QIcon.fromTheme("document-edit"), " Изменить")
        self.edit_btn.clicked.connect(self.edit_document)
        self.edit_btn.setEnabled(False)
        
        self.delete_btn = QPushButton(QIcon.fromTheme("edit-delete"), " Удалить")
        self.delete_btn.clicked.connect(self.delete_document)
        self.delete_btn.setEnabled(False)

        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addStretch()

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "ID", "Тип", "Номер", "Дата выдачи"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        # Close button
        button_box = QHBoxLayout()
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.reject)
        button_box.addStretch()
        button_box.addWidget(close_btn)

        layout.addLayout(header_layout)
        layout.addLayout(toolbar)
        layout.addWidget(self.table)
        layout.addLayout(button_box)

    def load_data(self):
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        Queries.GET_CLIENT_DOCUMENTS,
                        {"client_id": self.client_id}
                    )
                    documents = cursor.fetchall()
                    
                    self.table.setRowCount(len(documents))
                    for row, doc in enumerate(documents):
                        # ID
                        id_item = QTableWidgetItem(str(doc[0]))
                        id_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 0, id_item)
                        
                        # Type
                        self.table.setItem(row, 1, QTableWidgetItem(doc[1]))
                        
                        # Number
                        number_item = QTableWidgetItem(doc[2])
                        number_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 2, number_item)
                        
                        # Issue Date
                        date_item = QTableWidgetItem(doc[3].strftime("%d.%m.%Y"))
                        date_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, 3, date_item)
                        
        except psycopg2.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка БД",
                f"Не удалось загрузить документы:\n{str(e)}"
            )
            self.table.setRowCount(0)

    def on_selection_changed(self):
        has_selection = bool(self.table.selectedItems())
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def get_selected_document_id(self):
        selected_rows = self.table.selectedItems()
        if selected_rows:
            return int(self.table.item(selected_rows[0].row(), 0).text())
        return None

    def add_document(self):
        dialog = DocumentDialog(self, client_id=self.client_id)
        if dialog.exec_() == QDialog.Accepted:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            Queries.ADD_DOCUMENT,
                            dialog.get_data()
                        )
                        conn.commit()
                        QMessageBox.information(self, "Успех", "Документ успешно добавлен")
                        self.load_data()
            except psycopg2.Error as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось добавить документ:\n{str(e)}"
                )

    def edit_document(self):
        document_id = self.get_selected_document_id()
        if document_id is None:
            QMessageBox.warning(self, "Внимание", "Выберите документ для редактирования")
            return
            
        dialog = DocumentDialog(self, document_id=document_id)
        if dialog.exec_() == QDialog.Accepted:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        data = dialog.get_data()
                        data["id"] = document_id
                        cursor.execute(
                            Queries.UPDATE_DOCUMENT,
                            data
                        )
                        conn.commit()
                        QMessageBox.information(self, "Успех", "Данные документа обновлены")
                        self.load_data()
            except psycopg2.Error as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось обновить данные документа:\n{str(e)}"
                )

    def delete_document(self):
        document_id = self.get_selected_document_id()
        if document_id is None:
            QMessageBox.warning(self, "Внимание", "Выберите документ для удаления")
            return
            
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить этот документ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            Queries.DELETE_DOCUMENT,
                            {"id": document_id}
                        )
                        conn.commit()
                        QMessageBox.information(self, "Успех", "Документ успешно удален")
                        self.load_data()
            except psycopg2.Error as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось удалить документ:\n{str(e)}"
                ) 