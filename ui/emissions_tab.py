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
    QComboBox,
    QDateEdit,
    QCheckBox,
)
from PyQt5.QtCore import Qt, QTimer, QDate
from PyQt5.QtGui import QIcon, QColor

# Используем КЛАССЫ
from database.db import Database
from database.queries import Queries

# Относительный импорт диалога
from .emission_dialog import EmissionDialog
import psycopg2
from decimal import Decimal  # Для форматирования
import datetime  # Для дат


class EmissionsTab(QWidget):
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

        # Search/Filter Bar
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Фильтры:"))
        self.search_emitter_input = QLineEdit()
        self.search_emitter_input.setPlaceholderText("Эмитент...")
        self.search_emitter_input.textChanged.connect(self.on_search_text_changed)
        self.search_registrar_input = QLineEdit()
        self.search_registrar_input.setPlaceholderText("Регистратор...")
        self.search_registrar_input.textChanged.connect(self.on_search_text_changed)

        self.filter_status_combo = QComboBox()
        self.filter_status_combo.addItem("Все статусы", None)
        self.filter_status_combo.addItem("Активные", True)
        self.filter_status_combo.addItem("Не активные", False)
        self.filter_status_combo.currentIndexChanged.connect(
            self.on_search_text_changed
        )

        self.filter_date_start_edit = QDateEdit()
        self.filter_date_start_edit.setCalendarPopup(True)
        # Используем пустую строку как текст для NULL-даты
        self.filter_date_start_edit.setSpecialValueText(" ")
        self.filter_date_start_edit.setDate(QDate())  # <<< УСТАНАВЛИВАЕМ ПУСТУЮ ДАТУ
        self.filter_date_start_edit.setToolTip("Дата регистрации С")
        # Устанавливаем максимально возможную дату, чтобы не ограничивать будущее
        self.filter_date_start_edit.setMaximumDate(QDate(9999, 12, 31))
        self.filter_date_start_edit.setMinimumDate(
            QDate(1990, 1, 1)
        )  # Минимальная дата
        self.filter_date_start_edit.dateChanged.connect(self.on_search_text_changed)

        self.filter_date_end_edit = QDateEdit()
        self.filter_date_end_edit.setCalendarPopup(True)
        self.filter_date_end_edit.setSpecialValueText(" ")
        self.filter_date_end_edit.setDate(
            QDate.currentDate()
        )  # <<< УСТАНАВЛИВАЕМ ПУСТУЮ ДАТУ
        self.filter_date_end_edit.setToolTip("Дата регистрации ПО")
        self.filter_date_end_edit.setMaximumDate(QDate(9999, 12, 31))
        self.filter_date_end_edit.setMinimumDate(QDate(1990, 1, 1))
        self.filter_date_end_edit.dateChanged.connect(self.on_search_text_changed)

        self.clear_search_btn = QPushButton()
        self.clear_search_btn.setIcon(
            QIcon.fromTheme(
                "edit-clear",
                QIcon(
                    ":/qt-project.org/styles/commonstyle/images/standardbutton-cancel-16.png"
                ),
            )
        )
        self.clear_search_btn.setToolTip("Сбросить фильтры")
        self.clear_search_btn.clicked.connect(self.clear_search)

        filter_layout.addWidget(self.search_emitter_input)
        filter_layout.addWidget(self.search_registrar_input)
        filter_layout.addWidget(self.filter_status_combo)
        filter_layout.addWidget(QLabel("Дата рег. с:"))
        filter_layout.addWidget(self.filter_date_start_edit)
        filter_layout.addWidget(QLabel("по:"))
        filter_layout.addWidget(self.filter_date_end_edit)
        filter_layout.addWidget(self.clear_search_btn)
        filter_layout.addStretch(1)

        # Toolbar (без изменений)
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton(QIcon.fromTheme("list-add"), " Добавить")
        self.add_btn.clicked.connect(self.add_emission)
        self.edit_btn = QPushButton(QIcon.fromTheme("document-edit"), " Редактировать")
        self.edit_btn.clicked.connect(self.edit_emission)
        self.edit_btn.setEnabled(False)
        self.delete_btn = QPushButton(QIcon.fromTheme("edit-delete"), " Удалить")
        self.delete_btn.clicked.connect(self.delete_emission)
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

        # Table (без изменений)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Эмитент", "Объем (шт)", "Статус", "Дата рег.", "Регистратор"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.edit_emission_on_double_click)

        layout.addLayout(filter_layout)
        layout.addLayout(toolbar)
        layout.addWidget(self.table)

    def on_search_text_changed(self):
        self.search_timer.start()

    def _perform_search(self):
        self.load_data()

    def clear_search(self):
        # Блокируем сигналы
        self.search_emitter_input.blockSignals(True)
        self.search_registrar_input.blockSignals(True)
        self.filter_status_combo.blockSignals(True)
        self.filter_date_start_edit.blockSignals(True)
        self.filter_date_end_edit.blockSignals(True)

        self.search_emitter_input.clear()
        self.search_registrar_input.clear()
        self.filter_status_combo.setCurrentIndex(0)  # "Все статусы"
        self.filter_date_start_edit.setDate(QDate())  # <<< СБРОС НА ПУСТУЮ ДАТУ
        self.filter_date_end_edit.setDate(QDate())  # <<< СБРОС НА ПУСТУЮ ДАТУ

        # Разблокируем сигналы
        self.search_emitter_input.blockSignals(False)
        self.search_registrar_input.blockSignals(False)
        self.filter_status_combo.blockSignals(False)
        self.filter_date_start_edit.blockSignals(False)
        self.filter_date_end_edit.blockSignals(False)

        # Запускаем _perform_search, который вызовет load_data
        self._perform_search()  # Явно вызываем после сброса

    def get_filter_params(self):
        emitter_text = self.search_emitter_input.text().strip()
        registrar_text = self.search_registrar_input.text().strip()
        status_val = self.filter_status_combo.currentData()

        date_start_qdate = self.filter_date_start_edit.date()
        # Проверяем, что дата не является "пустой" QDate()
        date_start = (
            date_start_qdate.toPyDate()
            if date_start_qdate.isValid() and not date_start_qdate.isNull()
            else None
        )

        date_end_qdate = self.filter_date_end_edit.date()
        date_end = (
            date_end_qdate.toPyDate()
            if date_end_qdate.isValid() and not date_end_qdate.isNull()
            else None
        )

        emitter_param = f"%{emitter_text}%" if emitter_text else None
        registrar_param = f"%{registrar_text}%" if registrar_text else None
        status_param = status_val

        params = (
            emitter_param,
            emitter_param,
            registrar_param,
            registrar_param,
            status_param,
            status_param,
            date_start,
            date_start,
            date_end,
            date_end,
        )

        return params

    def load_data(self):
        params = self.get_filter_params()
        self.table.blockSignals(True)

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # --- ОТЛАДКА ---
                    # print(f"DEBUG [load_data] Executing GET_EMISSIONS with params: {params}")
                    # ---------------
                    cursor.execute(Queries.GET_EMISSIONS, params)
                    emissions = cursor.fetchall()
                    # --- ОТЛАДКА ---
                    # print(f"DEBUG [load_data] Fetched {len(emissions)} rows.")
                    # ---------------

                    self.table.setRowCount(0)  # Очистка перед заполнением
                    self.table.setRowCount(len(emissions))

                    for row, emission in enumerate(emissions):
                        # --- ОТЛАДКА ---
                        # print(f"DEBUG [load_data] Row {row}: {emission}")
                        # ---------------
                        emission_id = emission[0]
                        emitter_name = emission[1]
                        value = emission[2]
                        status_text = emission[3]
                        date_reg = emission[4]
                        registrar_name = emission[5]

                        # ID
                        id_item = QTableWidgetItem(str(emission_id))
                        id_item.setData(Qt.UserRole, emission_id)
                        id_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.table.setItem(row, 0, id_item)
                        # Emitter
                        self.table.setItem(row, 1, QTableWidgetItem(emitter_name))
                        # Value
                        value_item = QTableWidgetItem(f"{value:,}")
                        value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.table.setItem(row, 2, value_item)
                        # Status
                        status_item = QTableWidgetItem(status_text)
                        status_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                        self.table.setItem(row, 3, status_item)
                        # Date Reg
                        date_item = QTableWidgetItem(date_reg.strftime("%Y-%m-%d"))
                        date_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                        self.table.setItem(row, 4, date_item)
                        # Registrar
                        self.table.setItem(row, 5, QTableWidgetItem(registrar_name))

                        if status_text == "Не активна":
                            for col in range(self.table.columnCount()):
                                item = self.table.item(row, col)
                                if item:
                                    item.setForeground(QColor("gray"))

            self.on_selection_changed()

        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось загрузить эмиссии:\n{db_err}"
            )
            self.table.setRowCount(0)
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка загрузки", f"Не удалось загрузить эмиссии:\n{str(e)}"
            )
            self.table.setRowCount(0)
        finally:
            self.table.blockSignals(False)

    # --- Остальные методы (on_selection_changed, get_selected_id, add_emission, etc.) без изменений ---
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

    def add_emission(self):
        dialog = EmissionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            emitter_id, registrar_id, value, date_reg, status = dialog.get_data()
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            Queries.ADD_EMISSION,
                            (value, status, date_reg, emitter_id, registrar_id),
                        )
                        new_id = cursor.fetchone()[0]
                        conn.commit()
                        QMessageBox.information(
                            self, "Успех", f"Эмиссия успешно добавлена (ID: {new_id})."
                        )
                        self.load_data()
            except psycopg2.OperationalError as db_err:
                QMessageBox.critical(
                    self, "Ошибка БД", f"Не удалось добавить эмиссию:\n{db_err}"
                )
            except psycopg2.IntegrityError as e:
                QMessageBox.warning(
                    self, "Ошибка БД", f"Ошибка целостности данных:\n{e}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Ошибка добавления", f"Не удалось добавить эмиссию:\n{str(e)}"
                )

    def edit_emission_on_double_click(self, index):
        if self.edit_btn.isEnabled():
            self.edit_emission()

    def edit_emission(self):
        emission_id = self.get_selected_id()
        if emission_id is None:
            if not self.table.selectionModel().selectedRows():
                QMessageBox.warning(
                    self, "Внимание", "Выберите эмиссию для редактирования."
                )
            return

        dialog = EmissionDialog(self, emission_id=emission_id)
        if dialog.exec_() == QDialog.Accepted:
            emitter_id, registrar_id, value, date_reg, status = dialog.get_data()
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            Queries.UPDATE_EMISSION,
                            (
                                value,
                                status,
                                date_reg,
                                emitter_id,
                                registrar_id,
                                emission_id,
                            ),
                        )
                        conn.commit()
                        QMessageBox.information(
                            self,
                            "Успех",
                            f"Данные эмиссии (ID: {emission_id}) успешно обновлены.",
                        )
                        self.load_data()
            except psycopg2.OperationalError as db_err:
                QMessageBox.critical(
                    self, "Ошибка БД", f"Не удалось обновить эмиссию:\n{db_err}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Ошибка обновления", f"Не удалось обновить эмиссию:\n{str(e)}"
                )

    def delete_emission(self):
        emission_id = self.get_selected_id()
        if emission_id is None:
            if not self.table.selectionModel().selectedRows():
                QMessageBox.warning(self, "Внимание", "Выберите эмиссию для удаления.")
            return

        current_row = self.table.currentRow()
        emitter_name = (
            self.table.item(current_row, 1).text()
            if self.table.item(current_row, 1)
            else "??"
        )
        date_reg = (
            self.table.item(current_row, 4).text()
            if self.table.item(current_row, 4)
            else "??"
        )

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить эмиссию:\nID: {emission_id} (Эмитент: {emitter_name}, Дата: {date_reg})?\n\n"
            f"ВНИМАНИЕ: Будут удалены все ЦБ, связанные с этой эмиссией!",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )

        if reply == QMessageBox.Yes:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(Queries.DELETE_EMISSION, (emission_id,))
                        conn.commit()
                        QMessageBox.information(
                            self, "Успех", f"Эмиссия (ID: {emission_id}) удалена."
                        )
                        self.load_data()
            except psycopg2.OperationalError as db_err:
                QMessageBox.critical(
                    self, "Ошибка БД", f"Не удалось удалить эмиссию:\n{db_err}"
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
                    f"Не удалось удалить эмиссию:\n{str(e)}",
                )
