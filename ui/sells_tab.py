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
    QDateEdit,
)
from PyQt5.QtCore import Qt, QTimer, QDate
from PyQt5.QtGui import QIcon, QColor

# Используем КЛАССЫ
from database.db import Database
from database.queries import Queries

# Относительный импорт диалога
from .sell_dialog import SellDialog
import psycopg2
from decimal import Decimal
import datetime


class SellsTab(QWidget):
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
        """Инициализирует пользовательский интерфейс вкладки."""
        layout = QVBoxLayout(self)  # Родитель

        # Search/Filter Bar
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Фильтры:"))
        self.search_investor_input = QLineEdit()
        self.search_investor_input.setPlaceholderText("Инвестор...")
        self.search_investor_input.textChanged.connect(self.on_search_text_changed)
        self.search_stock_input = QLineEdit()
        self.search_stock_input.setPlaceholderText("Тикер ЦБ...")
        self.search_stock_input.textChanged.connect(self.on_search_text_changed)

        self.filter_date_start_edit = QDateEdit()
        self.filter_date_start_edit.setCalendarPopup(True)
        self.filter_date_start_edit.setDate(QDate())  # Пустая дата по умолчанию
        self.filter_date_start_edit.setSpecialValueText(" ")  # Текст для пустой даты
        self.filter_date_start_edit.setToolTip("Дата сделки С (дд.мм.гггг)")
        self.filter_date_start_edit.setDisplayFormat("dd.MM.yyyy")  # Российский формат
        self.filter_date_start_edit.setMaximumDate(QDate(9999, 12, 31))
        self.filter_date_start_edit.setMinimumDate(QDate(1990, 1, 1))
        self.filter_date_start_edit.dateChanged.connect(self.on_search_text_changed)

        self.filter_date_end_edit = QDateEdit()
        self.filter_date_end_edit.setCalendarPopup(True)
        self.filter_date_end_edit.setDate(QDate.currentDate())  # По умолчанию сегодня
        # self.filter_date_end_edit.setSpecialValueText(" ") # Не нужно, показываем дату
        self.filter_date_end_edit.setToolTip("Дата сделки ПО (дд.мм.гггг)")
        self.filter_date_end_edit.setDisplayFormat("dd.MM.yyyy")  # Российский формат
        self.filter_date_end_edit.setMaximumDate(QDate(9999, 12, 31))  # Макс. дата
        self.filter_date_end_edit.setMinimumDate(QDate(1990, 1, 1))
        self.filter_date_end_edit.dateChanged.connect(self.on_search_text_changed)

        self.clear_search_btn = QPushButton()
        # Используем стандартную иконку или запасную
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

        filter_layout.addWidget(self.search_investor_input)
        filter_layout.addWidget(self.search_stock_input)
        filter_layout.addWidget(QLabel("Дата с:"))
        filter_layout.addWidget(self.filter_date_start_edit)
        filter_layout.addWidget(QLabel("по:"))
        filter_layout.addWidget(self.filter_date_end_edit)
        filter_layout.addWidget(self.clear_search_btn)
        filter_layout.addStretch(1)

        # Toolbar
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton(QIcon.fromTheme("list-add"), " Добавить сделку")
        self.add_btn.clicked.connect(self.add_sell)  # Обычный вызов без предустановки
        self.edit_btn = QPushButton(QIcon.fromTheme("document-edit"), " Редактировать")
        self.edit_btn.clicked.connect(self.edit_sell)
        self.delete_btn = QPushButton(QIcon.fromTheme("edit-delete"), " Удалить")
        self.delete_btn.clicked.connect(self.delete_sell)

        # Начальное состояние кнопок
        self.add_btn.setEnabled(self.is_admin)  # Добавление только админу
        self.edit_btn.setEnabled(False)  # Зависит от выбора
        self.delete_btn.setEnabled(False)  # Зависит от выбора

        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addStretch(1)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        # Указываем заголовки столбцов
        self.table.setHorizontalHeaderLabels(
            ["ID", "Инвестор", "Тикер ЦБ", "Дата", "Кол-во (шт)", "Цена за шт (руб)"]
        )
        header = self.table.horizontalHeader()
        # Настройка ширины колонок
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Инвестор
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Тикер
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Дата
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Кол-во
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Цена
        # Настройки поведения таблицы
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)  # Выбор строк
        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )  # Только одна строка
        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )  # Запрет редактирования в ячейках
        self.table.setAlternatingRowColors(True)  # Чередование цветов строк
        self.table.verticalHeader().setVisible(False)  # Скрыть номера строк слева
        self.table.setSortingEnabled(True)  # Включаем сортировку по клику на заголовок

        # Сигналы таблицы
        self.table.itemSelectionChanged.connect(
            self.on_selection_changed
        )  # При изменении выбора
        self.table.doubleClicked.connect(
            self.edit_sell_on_double_click
        )  # При двойном клике

        # Добавление элементов в основной layout
        layout.addLayout(filter_layout)
        layout.addLayout(toolbar)
        layout.addWidget(self.table)

    def on_search_text_changed(self):
        """Запускает таймер для отложенного поиска/фильтрации."""
        self.search_timer.start()

    def _perform_search(self):
        """Выполняет загрузку данных (фильтрацию)."""
        self.load_data()

    def clear_search(self):
        """Сбрасывает все фильтры и перезагружает данные."""
        # Блокируем сигналы, чтобы избежать лишних срабатываний load_data
        self.search_investor_input.blockSignals(True)
        self.search_stock_input.blockSignals(True)
        self.filter_date_start_edit.blockSignals(True)
        self.filter_date_end_edit.blockSignals(True)
        # Очищаем/сбрасываем поля
        self.search_investor_input.clear()
        self.search_stock_input.clear()
        self.filter_date_start_edit.setDate(QDate())  # Сброс на пустую дату
        self.filter_date_end_edit.setDate(QDate.currentDate())  # Сброс на сегодня
        # Разблокируем сигналы
        self.search_investor_input.blockSignals(False)
        self.search_stock_input.blockSignals(False)
        self.filter_date_start_edit.blockSignals(False)
        self.filter_date_end_edit.blockSignals(False)
        # Запускаем загрузку данных с новыми (сброшенными) фильтрами
        self.load_data()

    def get_filter_params(self):
        """Собирает параметры из полей фильтрации для SQL запроса GET_SELLS."""
        investor_text = self.search_investor_input.text().strip()
        stock_text = (
            self.search_stock_input.text().strip().upper()
        )  # Тикеры в верхнем регистре

        # Получаем дату начала, используем только если она валидна (не пустая)
        date_start_qdate = self.filter_date_start_edit.date()
        date_start = date_start_qdate.toPyDate() if date_start_qdate.isValid() else None

        # Получаем дату конца, используем всегда (т.к. там дата по умолчанию)
        date_end_qdate = self.filter_date_end_edit.date()
        date_end = date_end_qdate.toPyDate()

        # Подготавливаем параметры для SQL LIKE (None если поле пустое)
        investor_param = f"%{investor_text}%" if investor_text else None
        stock_param = f"%{stock_text}%" if stock_text else None

        # Кортеж параметров в порядке, ожидаемом запросом Queries.GET_SELLS
        params = (
            investor_param,
            investor_param,  # Для имени инвестора
            stock_param,
            stock_param,  # Для тикера ЦБ
            date_start,
            date_start,  # Для даты С
            date_end,
            date_end,  # Для даты ПО
        )
        print(f"DEBUG [{self.__class__.__name__}]: Filter params: {params}")
        return params

    def load_data(self):
        """Загружает данные сделок в таблицу с учетом фильтров."""
        params = self.get_filter_params()
        # Выключаем сортировку перед манипуляциями с таблицей
        self.table.setSortingEnabled(False)
        # Блокируем сигналы таблицы, чтобы избежать лишних вызовов on_selection_changed
        self.table.blockSignals(True)

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Выполняем запрос к БД
                    cursor.execute(Queries.GET_SELLS, params)
                    sells = cursor.fetchall()  # Получаем все строки

                    # Очищаем таблицу и устанавливаем новое количество строк
                    self.table.setRowCount(0)
                    self.table.setRowCount(len(sells))

                    # Заполняем таблицу данными
                    for row, sell in enumerate(sells):
                        # Распаковываем данные строки
                        sell_id, investor_name, stock_ticket, sale_date, num, price = (
                            sell
                        )

                        # Создаем и настраиваем ячейку ID
                        id_item = QTableWidgetItem()
                        id_item.setData(
                            Qt.DisplayRole, sell_id
                        )  # Данные для отображения и сортировки
                        id_item.setData(
                            Qt.UserRole, sell_id
                        )  # Данные для get_selected_id (внутреннее использование)
                        id_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.table.setItem(row, 0, id_item)

                        # Создаем ячейки для остальных столбцов
                        self.table.setItem(row, 1, QTableWidgetItem(investor_name))
                        self.table.setItem(row, 2, QTableWidgetItem(stock_ticket))

                        # Форматируем и выравниваем дату
                        date_item = QTableWidgetItem(
                            sale_date.strftime("%d.%m.%Y")
                        )  # Российский формат
                        date_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                        self.table.setItem(row, 3, date_item)

                        # Форматируем и выравниваем количество
                        num_item = QTableWidgetItem()
                        num_item.setData(Qt.DisplayRole, num)  # Число для сортировки
                        num_item.setText(
                            f"{num:,}".replace(",", " ")
                        )  # Формат с разделителем
                        num_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.table.setItem(row, 4, num_item)

                        # Форматируем и выравниваем цену
                        price_item = QTableWidgetItem()
                        price_item.setData(
                            Qt.DisplayRole, float(price)
                        )  # Float для сортировки
                        price_item.setText(
                            f"{price:,.2f}".replace(",", " ")
                        )  # Формат с разделителем и 2 знаками
                        price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.table.setItem(row, 5, price_item)

            # Обновляем состояние кнопок после загрузки данных
            self.on_selection_changed()

        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось загрузить сделки:\n{db_err}"
            )
            self.table.setRowCount(0)  # Очищаем таблицу при ошибке
        except Exception as e:
            QMessageBox.critical(
                self, "Критическая Ошибка", f"Не удалось загрузить сделки:\n{str(e)}"
            )
            self.table.setRowCount(0)  # Очищаем таблицу при ошибке
            import traceback

            traceback.print_exc()  # Вывод полного стека ошибки в консоль
        finally:
            # Включаем сортировку и сигналы обратно
            self.table.setSortingEnabled(True)
            self.table.blockSignals(False)

    def on_selection_changed(self):
        """Обновляет состояние кнопок 'Редактировать', 'Удалить' при изменении выбора."""
        is_selected = bool(self.table.selectionModel().selectedRows())
        # Включаем Edit/Delete ТОЛЬКО если выбрана строка И пользователь админ
        can_manage = is_selected and self.is_admin

        if hasattr(self, "edit_btn"):
            self.edit_btn.setEnabled(can_manage)
        if hasattr(self, "delete_btn"):
            self.delete_btn.setEnabled(can_manage)

    def get_selected_id(self):
        """Возвращает ID выбранной сделки или None."""
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            # Получаем ID из UserRole первой ячейки (столбец 0) выбранной строки
            id_item = self.table.item(selected_rows[0].row(), 0)
            return id_item.data(Qt.UserRole) if id_item else None
        return None

    def add_sell_preselected(self, preselected_investor_info):
        """Открывает диалог добавления сделки с предустановленным инвестором."""
        if not self.is_admin:
            QMessageBox.warning(
                self, "Доступ запрещен", "Только администратор может добавлять сделки."
            )
            return

        print(
            f"DEBUG [{self.__class__.__name__}]: add_sell_preselected called with info: {preselected_investor_info}"
        )
        # Создаем диалог, передавая информацию об инвесторе
        dialog = SellDialog(self, preselected_investor=preselected_investor_info)
        # Если диалог закрыт через OK, сохраняем данные
        if dialog.exec_() == QDialog.Accepted:
            self.save_sell_data(dialog)
        else:
            print(
                f"DEBUG [{self.__class__.__name__}]: SellDialog (preselected) cancelled or rejected."
            )

    def add_sell(self):
        """Открывает диалог добавления сделки без предустановки инвестора."""
        if not self.is_admin:
            QMessageBox.warning(
                self, "Доступ запрещен", "Только администратор может добавлять сделки."
            )
            return

        print(f"DEBUG [{self.__class__.__name__}]: add_sell called (no preselection)")
        # Создаем диалог, не передавая информацию об инвесторе
        dialog = SellDialog(self, preselected_investor=None)
        # Если диалог закрыт через OK, сохраняем данные
        if dialog.exec_() == QDialog.Accepted:
            self.save_sell_data(dialog)
        else:
            print(
                f"DEBUG [{self.__class__.__name__}]: SellDialog (no preselection) cancelled or rejected."
            )

    def save_sell_data(self, dialog_instance):
        """Сохраняет данные сделки из диалогового окна в БД."""
        try:
            # Получаем данные из диалога
            investor_id, stock_id, sale_date, num, price = dialog_instance.get_data()
            # Выполняем запрос на добавление в БД
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        Queries.ADD_SELL,
                        (investor_id, stock_id, sale_date, num, price),
                    )
                    new_id = cursor.fetchone()[0]  # Получаем ID новой записи
                    conn.commit()  # Подтверждаем транзакцию
                    QMessageBox.information(
                        self, "Успех", f"Сделка успешно добавлена (ID: {new_id})."
                    )
                    self.load_data()  # Обновляем таблицу на текущей вкладке
        except psycopg2.OperationalError as db_err:
            # Ошибка подключения или выполнения на сервере
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось добавить сделку:\n{db_err}"
            )
        except psycopg2.IntegrityError as e:
            # Ошибка нарушения ограничений БД (например, внешние ключи)
            error_message = f"Ошибка целостности данных:\n{e}"
            # Пытаемся дать более конкретное сообщение
            if "sells_stock_id_fkey" in str(e):
                error_message = (
                    "Ошибка: Выбранная ценная бумага не существует или была удалена."
                )
            elif "sells_investor_id_fkey" in str(e):
                error_message = (
                    "Ошибка: Выбранный инвестор не существует или был удален."
                )
            QMessageBox.warning(self, "Ошибка данных", error_message)
        except Exception as e:
            # Другие непредвиденные ошибки
            QMessageBox.critical(
                self, "Критическая Ошибка", f"Не удалось добавить сделку:\n{str(e)}"
            )
            import traceback

            traceback.print_exc()  # Для подробной отладки в консоли

    def edit_sell_on_double_click(self, index):
        """Обрабатывает двойной клик по строке таблицы (если редактирование доступно)."""
        # Проверяем, активна ли кнопка редактирования (т.е. выбрана строка и есть права)
        if self.edit_btn.isEnabled():
            self.edit_sell()

    def edit_sell(self):
        """Открывает диалог для редактирования выбранной сделки."""
        if not self.is_admin:
            return  # Проверка прав

        sell_id = self.get_selected_id()  # Получаем ID выбранной сделки
        if sell_id is None:
            # Предупреждаем, только если строка действительно не выбрана
            if not self.table.selectionModel().selectedRows():
                QMessageBox.warning(
                    self, "Внимание", "Выберите сделку для редактирования."
                )
            return

        # Создаем диалог, передавая ID сделки для загрузки данных
        dialog = SellDialog(self, sell_id=sell_id)
        # Если диалог закрыт через OK
        if dialog.exec_() == QDialog.Accepted:
            try:
                # Получаем измененные данные из диалога
                investor_id, stock_id, sale_date, num, price = dialog.get_data()
                # Выполняем запрос на обновление в БД
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            Queries.UPDATE_SELL,
                            (
                                investor_id,
                                stock_id,
                                sale_date,
                                num,
                                price,
                                sell_id,
                            ),  # ID в конце для WHERE
                        )
                        conn.commit()  # Подтверждаем транзакцию
                        QMessageBox.information(
                            self, "Успех", f"Сделка (ID: {sell_id}) успешно обновлена."
                        )
                        self.load_data()  # Обновляем таблицу
            except psycopg2.OperationalError as db_err:
                QMessageBox.critical(
                    self, "Ошибка БД", f"Не удалось обновить сделку:\n{db_err}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Критическая Ошибка", f"Не удалось обновить сделку:\n{str(e)}"
                )
                import traceback

                traceback.print_exc()

    def delete_sell(self):
        """Удаляет выбранную сделку."""
        if not self.is_admin:
            return  # Проверка прав

        sell_id = self.get_selected_id()  # Получаем ID
        if sell_id is None:
            if not self.table.selectionModel().selectedRows():
                QMessageBox.warning(self, "Внимание", "Выберите сделку для удаления.")
            return

        # Получаем информацию о сделке для окна подтверждения
        current_row = self.table.currentRow()
        if current_row < 0:
            return  # На всякий случай

        investor = (
            self.table.item(current_row, 1).text()
            if self.table.item(current_row, 1)
            else "?"
        )
        stock = (
            self.table.item(current_row, 2).text()
            if self.table.item(current_row, 2)
            else "?"
        )
        date = (
            self.table.item(current_row, 3).text()
            if self.table.item(current_row, 3)
            else "?"
        )

        # Запрос подтверждения у пользователя
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить сделку:\nID: {sell_id} ({investor}, {stock}, {date})?",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,  # По умолчанию выбрана "Отмена"
        )

        # Если пользователь подтвердил удаление
        if reply == QMessageBox.Yes:
            try:
                # Выполняем запрос на удаление
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            Queries.DELETE_SELL, (sell_id,)
                        )  # Передаем ID в кортеже
                        conn.commit()  # Подтверждаем транзакцию
                        QMessageBox.information(
                            self, "Успех", f"Сделка (ID: {sell_id}) удалена."
                        )
                        self.load_data()  # Обновляем таблицу
            except psycopg2.OperationalError as db_err:
                QMessageBox.critical(
                    self, "Ошибка БД", f"Не удалось удалить сделку:\n{db_err}"
                )
            except psycopg2.Error as db_err:  # Ловим специфичные ошибки БД
                QMessageBox.critical(
                    self,
                    "Ошибка при удалении",
                    f"Ошибка базы данных:\n{db_err.pgcode} - {db_err.pgerror}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Критическая Ошибка", f"Не удалось удалить сделку:\n{str(e)}"
                )
                import traceback

                traceback.print_exc()
