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
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer, QDate
from PyQt5.QtGui import QIcon, QColor

# Используем КЛАССЫ
from database.db import Database
from database.queries import Queries

# Относительный импорт диалога
from .registrar_dialog import RegistrarDialog
import psycopg2
import datetime  # Для сравнения дат


class RegistrarsTab(QWidget):
    def __init__(self, user_role):
        super().__init__()
        self.user_role = user_role
        self.is_admin = self.user_role == "admin"
        print(
            f"DEBUG [{self.__class__.__name__}]: Initialized with role '{self.user_role}', is_admin={self.is_admin}"
        )
        self.db = Database()  # Экземпляр
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(500)
        self.search_timer.timeout.connect(self._perform_search)

        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)  # Родитель

        # Search Bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_name_input = QLineEdit()
        self.search_name_input.setPlaceholderText("По названию юр. лица...")
        self.search_name_input.textChanged.connect(self.on_search_text_changed)
        self.search_inn_input = QLineEdit()
        self.search_inn_input.setPlaceholderText("По ИНН...")
        self.search_inn_input.textChanged.connect(self.on_search_text_changed)
        self.search_license_input = QLineEdit()
        self.search_license_input.setPlaceholderText("По номеру лицензии...")
        self.search_license_input.textChanged.connect(self.on_search_text_changed)
        self.clear_search_btn = QPushButton()
        self.clear_search_btn.setIcon(
            QIcon.fromTheme(
                "edit-clear",
                QIcon(
                    ":/qt-project.org/styles/commonstyle/images/standardbutton-cancel-16.png"
                ),
            )
        )
        self.clear_search_btn.setToolTip("Очистить поиск")
        self.clear_search_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(self.search_name_input)
        search_layout.addWidget(self.search_inn_input)
        search_layout.addWidget(self.search_license_input)
        search_layout.addWidget(self.clear_search_btn)
        # search_layout.addStretch(1)

        # Toolbar
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton(QIcon.fromTheme("list-add"), " Добавить")
        self.add_btn.setToolTip("Добавить нового регистратора")
        self.add_btn.clicked.connect(self.add_registrar)

        self.edit_btn = QPushButton(QIcon.fromTheme("document-edit"), " Редактировать")
        self.edit_btn.setToolTip("Редактировать выбранного регистратора")
        self.edit_btn.clicked.connect(self.edit_registrar)
        self.edit_btn.setEnabled(False)

        self.delete_btn = QPushButton(QIcon.fromTheme("edit-delete"), " Удалить")
        self.delete_btn.setToolTip("Удалить выбранного регистратора")
        self.delete_btn.clicked.connect(self.delete_registrar)
        self.delete_btn.setEnabled(False)

        if hasattr(self, "add_btn"):
            self.add_btn.setEnabled(self.is_admin)  # Активна только для админа

        # Кнопки, зависящие от выбора (Edit, Delete, Sales) - всегда неактивны при старте
        if hasattr(self, "edit_btn"):
            self.edit_btn.setEnabled(False)
        if hasattr(self, "delete_btn"):
            self.delete_btn.setEnabled(False)
        if hasattr(self, "sales_btn"):  # Для инвесторов
            self.sales_btn.setEnabled(False)

        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addStretch(1)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Название юр. лица", "ИНН", "Лицензия", "Срок действия"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Название ЮЛ
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # ИНН
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Лицензия
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Срок

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.edit_registrar_on_double_click)

        layout.addLayout(search_layout)
        layout.addLayout(toolbar)
        layout.addWidget(self.table)

    def on_search_text_changed(self):
        self.search_timer.start()

    def _perform_search(self):
        self.load_data()

    def clear_search(self):
        self.search_name_input.blockSignals(True)
        self.search_inn_input.blockSignals(True)
        self.search_license_input.blockSignals(True)
        self.search_name_input.clear()
        self.search_inn_input.clear()
        self.search_license_input.clear()
        self.search_name_input.blockSignals(False)
        self.search_inn_input.blockSignals(False)
        self.search_license_input.blockSignals(False)
        self.load_data()

    def load_data(self):
        self.table.blockSignals(True)

        search_name_text = self.search_name_input.text().strip()
        search_inn_text = self.search_inn_input.text().strip()
        search_license_text = self.search_license_input.text().strip()

        name_param = f"%{search_name_text}%" if search_name_text else None
        inn_param = f"%{search_inn_text}%" if search_inn_text else None
        license_param = f"%{search_license_text}%" if search_license_text else None

        params = (
            name_param,
            name_param,
            inn_param,
            inn_param,
            license_param,
            license_param,
        )

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_REGISTRARS, params)
                    registrars = cursor.fetchall()

                    self.table.setRowCount(0)
                    self.table.setRowCount(len(registrars))
                    today = datetime.date.today()  # Текущая дата для сравнения

                    for row, registrar in enumerate(registrars):
                        reg_id = registrar[0]
                        entity_name = registrar[1]
                        inn = registrar[2]
                        license_num = registrar[3]
                        expiry_date = registrar[4]  # Это datetime.date или None

                        # ID
                        id_item = QTableWidgetItem(str(reg_id))
                        id_item.setData(Qt.UserRole, reg_id)
                        id_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.table.setItem(row, 0, id_item)
                        # Name
                        self.table.setItem(row, 1, QTableWidgetItem(entity_name))
                        # INN
                        self.table.setItem(row, 2, QTableWidgetItem(inn))
                        # License Num
                        self.table.setItem(row, 3, QTableWidgetItem(license_num))
                        # Expiry Date
                        expiry_text = (
                            expiry_date.strftime("%Y-%m-%d")
                            if expiry_date
                            else "Бессрочно"
                        )
                        expiry_item = QTableWidgetItem(expiry_text)
                        expiry_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                        self.table.setItem(row, 4, expiry_item)

                        # Подсветка просроченных лицензий
                        is_expired = expiry_date is not None and expiry_date < today
                        if is_expired:
                            expiry_item.setForeground(QColor("white"))
                            expiry_item.setBackground(QColor("red"))  # Красный фон
                            # Можно подсветить всю строку
                            # for col in range(self.table.columnCount()):
                            #     item = self.table.item(row, col)
                            #     if item: item.setForeground(QColor('red'))

            self.on_selection_changed()

        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось загрузить регистраторов:\n{db_err}"
            )
            self.table.setRowCount(0)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка загрузки",
                f"Не удалось загрузить регистраторов:\n{str(e)}",
            )
            self.table.setRowCount(0)
        finally:
            self.table.blockSignals(False)

    def on_selection_changed(self):
        selected_rows = self.table.selectionModel().selectedRows()
        is_selected = bool(selected_rows)

        # Включаем Edit/Delete ТОЛЬКО если выбрана строка И пользователь админ
        can_edit_delete = is_selected and self.is_admin

        if hasattr(self, "edit_btn"):
            self.edit_btn.setEnabled(can_edit_delete)
        if hasattr(self, "delete_btn"):
            self.delete_btn.setEnabled(can_edit_delete)
        if hasattr(self, "sales_btn"):
            self.sales_btn.setEnabled(is_selected)  # Зависит только от выбора

    def get_selected_id(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            id_item = self.table.item(selected_rows[0].row(), 0)
            return id_item.data(Qt.UserRole) if id_item else None
        return None

    def add_registrar(self):
        # Диалог сам загрузит доступные ЮЛ
        dialog = RegistrarDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            entity_id, license_num, expiry_date = dialog.get_data()
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            Queries.ADD_REGISTRAR, (entity_id, license_num, expiry_date)
                        )
                        new_id = cursor.fetchone()[0]
                        conn.commit()
                        QMessageBox.information(
                            self,
                            "Успех",
                            f"Регистратор успешно добавлен (ID: {new_id}).",
                        )
                        self.load_data()
            except psycopg2.OperationalError as db_err:
                QMessageBox.critical(
                    self, "Ошибка БД", f"Не удалось добавить запись:\n{db_err}"
                )
            except psycopg2.IntegrityError as e:
                QMessageBox.warning(
                    self,
                    "Ошибка БД",
                    f"Ошибка целостности данных (возможно, дубликат лицензии или ЮЛ уже регистратор?):\n{e}",
                )
                # conn.rollback() не нужен, with сам откатит
            except Exception as e:
                QMessageBox.critical(
                    self, "Ошибка добавления", f"Не удалось добавить запись:\n{str(e)}"
                )

    def edit_registrar_on_double_click(self, index):
        if self.edit_btn.isEnabled():
            self.edit_registrar()

    def edit_registrar(self):
        registrar_id = self.get_selected_id()
        if registrar_id is None:
            if not self.table.selectionModel().selectedRows():
                QMessageBox.warning(
                    self, "Внимание", "Выберите регистратора для редактирования."
                )
            return

        # Диалог сам загрузит данные по ID
        dialog = RegistrarDialog(self, registrar_id=registrar_id)
        if dialog.exec_() == QDialog.Accepted:
            # При редактировании мы НЕ МЕНЯЕМ entity_id.
            # get_data() в диалоге вернет ID, но мы его игнорируем для UPDATE.
            _, license_num, expiry_date = dialog.get_data()
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        # Используем специальный запрос без entity_id
                        cursor.execute(
                            Queries.UPDATE_REGISTRAR_DETAILS,
                            (license_num, expiry_date, registrar_id),
                        )
                        conn.commit()
                        QMessageBox.information(
                            self,
                            "Успех",
                            f"Данные регистратора (ID: {registrar_id}) успешно обновлены.",
                        )
                        self.load_data()
            except psycopg2.OperationalError as db_err:
                QMessageBox.critical(
                    self, "Ошибка БД", f"Не удалось обновить запись:\n{db_err}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Ошибка обновления", f"Не удалось обновить запись:\n{str(e)}"
                )

    def delete_registrar(self):
        registrar_id = self.get_selected_id()
        if registrar_id is None:
            if not self.table.selectionModel().selectedRows():
                QMessageBox.warning(
                    self, "Внимание", "Выберите регистратора для удаления."
                )
            return

        # Получаем имя и лицензию для сообщения
        current_row = self.table.currentRow()
        reg_name = (
            self.table.item(current_row, 1).text()
            if self.table.item(current_row, 1)
            else f"ID {registrar_id}"
        )
        license_num = (
            self.table.item(current_row, 3).text()
            if self.table.item(current_row, 3)
            else "??"
        )

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить регистратора:\n'{reg_name}' (Лиц.: {license_num}, ID: {registrar_id})?\n\n"
            f"ВНИМАНИЕ: Будут удалены все эмиссии, зарегистрированные им!",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )

        if reply == QMessageBox.Yes:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(Queries.DELETE_REGISTRAR, (registrar_id,))
                        conn.commit()
                        QMessageBox.information(
                            self, "Успех", f"Регистратор '{reg_name}' удален."
                        )
                        self.load_data()
            except psycopg2.OperationalError as db_err:
                QMessageBox.critical(
                    self, "Ошибка БД", f"Не удалось удалить регистратора:\n{db_err}"
                )
            except psycopg2.Error as db_err:
                QMessageBox.critical(
                    self,
                    "Ошибка при удалении",
                    f"Ошибка базы данных:\n{db_err.pgcode} - {db_err.pgerror}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка при удалении",
                    f"Не удалось удалить регистратора:\n{str(e)}",
                )
