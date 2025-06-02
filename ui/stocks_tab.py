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
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QColor

# Используем КЛАССЫ
from database.db import Database
from database.queries import Queries

# Относительный импорт
from .stock_dialog import StockDialog
import psycopg2
from decimal import Decimal  # Для форматирования


class StocksTab(QWidget):
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
        self.load_data()  # Загрузка данных и комбо фильтра

    def init_ui(self):
        layout = QVBoxLayout(self)  # Родитель

        # Search/Filter Bar
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Фильтры:"))
        self.search_ticket_input = QLineEdit()
        self.search_ticket_input.setPlaceholderText("Тикер...")
        self.search_ticket_input.textChanged.connect(self.on_search_text_changed)
        self.search_emitter_input = QLineEdit()
        self.search_emitter_input.setPlaceholderText("Эмитент...")
        self.search_emitter_input.textChanged.connect(self.on_search_text_changed)

        self.filter_emission_combo = QComboBox()
        self.filter_emission_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.filter_emission_combo.setMinimumWidth(250)  # Пошире для имен эмиссий
        self.filter_emission_combo.setToolTip("Фильтр по эмиссии")
        self.filter_emission_combo.currentIndexChanged.connect(
            self.on_search_text_changed
        )

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

        filter_layout.addWidget(self.search_ticket_input)
        filter_layout.addWidget(self.search_emitter_input)
        filter_layout.addWidget(QLabel("Эмиссия:"))
        filter_layout.addWidget(self.filter_emission_combo)
        filter_layout.addWidget(self.clear_search_btn)
        filter_layout.addStretch(1)

        # Toolbar
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton(QIcon.fromTheme("list-add"), " Добавить")
        self.add_btn.clicked.connect(self.add_stock)
        self.edit_btn = QPushButton(QIcon.fromTheme("document-edit"), " Редактировать")
        self.edit_btn.clicked.connect(self.edit_stock)
        self.edit_btn.setEnabled(False)
        self.delete_btn = QPushButton(QIcon.fromTheme("edit-delete"), " Удалить")
        self.delete_btn.clicked.connect(self.delete_stock)
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
            ["ID", "Тикер", "Номинал (руб.)", "Эмитент", "Дата эмиссии"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Эмитент
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Тикер
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Номинал
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Дата эмиссии

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.edit_stock_on_double_click)

        layout.addLayout(filter_layout)
        layout.addLayout(toolbar)
        layout.addWidget(self.table)

        # Загрузка комбо фильтра при создании
        self.load_emission_filter_combo()

    def on_search_text_changed(self):
        self.search_timer.start()

    def _perform_search(self):
        self.load_data()

    def clear_search(self):
        self.search_ticket_input.blockSignals(True)
        self.search_emitter_input.blockSignals(True)
        self.filter_emission_combo.blockSignals(True)

        self.search_ticket_input.clear()
        self.search_emitter_input.clear()
        self.filter_emission_combo.setCurrentIndex(0)  # "Все эмиссии"

        self.search_ticket_input.blockSignals(False)
        self.search_emitter_input.blockSignals(False)
        self.filter_emission_combo.blockSignals(False)

        self._perform_search()  # Явный вызов поиска

    def load_emission_filter_combo(self):
        """Загружает список эмиссий для фильтра."""
        current_selection = self.filter_emission_combo.currentData()
        self.filter_emission_combo.blockSignals(True)
        self.filter_emission_combo.clear()
        self.filter_emission_combo.addItem(
            "Все эмиссии", None
        )  # Опция для отсутствия фильтра
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        Queries.GET_EMISSION_LIST
                    )  # Используем тот же список
                    for em_id, name in cursor.fetchall():
                        self.filter_emission_combo.addItem(name, em_id)
            # Восстанавливаем выбор
            index = self.filter_emission_combo.findData(current_selection)
            if index != -1:
                self.filter_emission_combo.setCurrentIndex(index)
        except Exception as e:
            print(f"Ошибка загрузки комбо эмиссий для фильтра: {e}")
            # Не показываем QMessageBox, чтобы не мешать
        finally:
            self.filter_emission_combo.blockSignals(False)

    def get_filter_params(self):
        ticket_text = (
            self.search_ticket_input.text().strip().upper()
        )  # Сразу в верхний регистр
        emitter_text = self.search_emitter_input.text().strip()
        emission_id = self.filter_emission_combo.currentData()  # ID или None

        ticket_param = f"%{ticket_text}%" if ticket_text else None
        emitter_param = f"%{emitter_text}%" if emitter_text else None
        emission_id_param = emission_id

        params = (
            ticket_param,
            ticket_param,
            emitter_param,
            emitter_param,
            emission_id_param,
            emission_id_param,
        )
        return params

    def load_data(self):
        params = self.get_filter_params()
        self.table.blockSignals(True)

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_STOCKS, params)
                    stocks = cursor.fetchall()

                    self.table.setRowCount(0)
                    self.table.setRowCount(len(stocks))

                    for row, stock in enumerate(stocks):
                        stock_id = stock[0]
                        ticket = stock[1]
                        nominal_value = stock[2]  # Decimal
                        emitter_name = stock[3]
                        emission_date = stock[4]  # date

                        # ID
                        id_item = QTableWidgetItem(str(stock_id))
                        id_item.setData(Qt.UserRole, stock_id)
                        id_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.table.setItem(row, 0, id_item)
                        # Ticket
                        self.table.setItem(row, 1, QTableWidgetItem(ticket))
                        # Nominal
                        nominal_item = QTableWidgetItem(f"{nominal_value:,.2f}")
                        nominal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.table.setItem(row, 2, nominal_item)
                        # Emitter
                        self.table.setItem(row, 3, QTableWidgetItem(emitter_name))
                        # Emission Date
                        date_item = QTableWidgetItem(emission_date.strftime("%Y-%m-%d"))
                        date_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                        self.table.setItem(row, 4, date_item)

            # Обновляем комбо фильтра эмиссий после загрузки данных
            # Это нужно, если эмиссии могли быть добавлены/удалены
            self.load_emission_filter_combo()
            self.on_selection_changed()

        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось загрузить ЦБ:\n{db_err}"
            )
            self.table.setRowCount(0)
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка загрузки", f"Не удалось загрузить ЦБ:\n{str(e)}"
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

    def add_stock(self):
        # Диалог сам загрузит эмиссии
        dialog = StockDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            emission_id, ticket, nominal_value = dialog.get_data()
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            Queries.ADD_STOCK, (ticket, nominal_value, emission_id)
                        )
                        new_id = cursor.fetchone()[0]
                        conn.commit()
                        QMessageBox.information(
                            self,
                            "Успех",
                            f"Ценная бумага '{ticket}' успешно добавлена (ID: {new_id}).",
                        )
                        self.load_data()
            except psycopg2.OperationalError as db_err:
                QMessageBox.critical(
                    self, "Ошибка БД", f"Не удалось добавить ЦБ:\n{db_err}"
                )
            except psycopg2.IntegrityError as e:
                QMessageBox.warning(
                    self,
                    "Ошибка БД",
                    f"Ошибка целостности (возможно, дубликат тикера?):\n{e}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Ошибка добавления", f"Не удалось добавить ЦБ:\n{str(e)}"
                )

    def edit_stock_on_double_click(self, index):
        if self.edit_btn.isEnabled():
            self.edit_stock()

    def edit_stock(self):
        stock_id = self.get_selected_id()
        if stock_id is None:
            if not self.table.selectionModel().selectedRows():
                QMessageBox.warning(self, "Внимание", "Выберите ЦБ для редактирования.")
            return

        dialog = StockDialog(self, stock_id=stock_id)
        if dialog.exec_() == QDialog.Accepted:
            emission_id, ticket, nominal_value = dialog.get_data()
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            Queries.UPDATE_STOCK,
                            (ticket, nominal_value, emission_id, stock_id),
                        )
                        conn.commit()
                        QMessageBox.information(
                            self,
                            "Успех",
                            f"Данные ЦБ '{ticket}' (ID: {stock_id}) успешно обновлены.",
                        )
                        self.load_data()
            except psycopg2.OperationalError as db_err:
                QMessageBox.critical(
                    self, "Ошибка БД", f"Не удалось обновить ЦБ:\n{db_err}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Ошибка обновления", f"Не удалось обновить ЦБ:\n{str(e)}"
                )

    def delete_stock(self):
        stock_id = self.get_selected_id()
        if stock_id is None:
            if not self.table.selectionModel().selectedRows():
                QMessageBox.warning(self, "Внимание", "Выберите ЦБ для удаления.")
            return

        ticket = (
            self.table.item(self.table.currentRow(), 1).text()
            if self.table.item(self.table.currentRow(), 1)
            else f"ID {stock_id}"
        )

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить ЦБ:\n'{ticket}' (ID: {stock_id})?\n\n"
            f"ВНИМАНИЕ: Будут удалены все сделки с этой ЦБ!",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )

        if reply == QMessageBox.Yes:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(Queries.DELETE_STOCK, (stock_id,))
                        conn.commit()
                        QMessageBox.information(
                            self, "Успех", f"Ценная бумага '{ticket}' удалена."
                        )
                        self.load_data()
            except psycopg2.OperationalError as db_err:
                QMessageBox.critical(
                    self, "Ошибка БД", f"Не удалось удалить ЦБ:\n{db_err}"
                )
            except psycopg2.Error as db_err:
                QMessageBox.critical(
                    self,
                    "Ошибка при удалении",
                    f"Ошибка базы данных:\n{db_err.pgcode} - {db_err.pgerror}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Ошибка при удалении", f"Не удалось удалить ЦБ:\n{str(e)}"
                )
