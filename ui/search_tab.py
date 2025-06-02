from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QAbstractItemView,
    QPushButton,
    QTableWidget,
    QHeaderView,
    QLabel,
    QDateEdit,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QTableWidgetItem,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon

# Используем КЛАССЫ
from database.db import Database
from database.queries import Queries
import psycopg2
import datetime
from decimal import Decimal


class SearchTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()  # Экземпляр
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)  # Родитель

        # Панель критериев поиска
        criteria_group = QGroupBox("Комбинированный поиск сделок и эмиссий")
        form_layout = QFormLayout()  # Удобно для пар "Метка: Поле"

        self.investor_name_input = QLineEdit()
        self.investor_inn_input = QLineEdit()
        self.registrar_name_input = QLineEdit()
        self.emitter_name_input = QLineEdit()
        self.stock_ticker_input = QLineEdit()
        self.date_start_edit = QDateEdit()
        self.date_start_edit.setCalendarPopup(True)
        self.date_start_edit.setSpecialValueText(" ")
        self.date_start_edit.setDate(QDate())
        self.date_start_edit.setMaximumDate(QDate(9999, 12, 31))
        self.date_start_edit.setMinimumDate(QDate(1990, 1, 1))
        self.date_end_edit = QDateEdit()
        self.date_end_edit.setCalendarPopup(True)
        self.date_end_edit.setSpecialValueText(" ")
        self.date_end_edit.setDate(QDate())
        self.date_end_edit.setMaximumDate(QDate(9999, 12, 31))
        self.date_end_edit.setMinimumDate(QDate(1990, 1, 1))

        form_layout.addRow("Имя инвестора (часть):", self.investor_name_input)
        form_layout.addRow("ИНН инвестора:", self.investor_inn_input)
        form_layout.addRow("Имя регистратора (часть):", self.registrar_name_input)
        form_layout.addRow("Имя эмитента (часть):", self.emitter_name_input)
        form_layout.addRow("Тикер ЦБ:", self.stock_ticker_input)
        # Для дат используем QHBoxLayout внутри QFormLayout
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("с:"))
        date_layout.addWidget(self.date_start_edit)
        date_layout.addWidget(QLabel("по:"))
        date_layout.addWidget(self.date_end_edit)
        date_layout.addStretch(1)
        form_layout.addRow("Период (сделки/эмиссии):", date_layout)

        criteria_group.setLayout(form_layout)

        # Кнопки поиска и сброса
        btn_layout = QHBoxLayout()
        self.clear_button = QPushButton(QIcon.fromTheme("edit-clear"), " Сбросить")
        self.clear_button.clicked.connect(self.clear_criteria)
        self.search_button = QPushButton(QIcon.fromTheme("system-search"), " Найти")
        self.search_button.clicked.connect(self.perform_search)
        btn_layout.addWidget(self.clear_button)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.search_button)

        # Таблица результатов
        self.results_table = QTableWidget()
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.verticalHeader().setVisible(False)
        # Сортировку здесь пока не добавляем, чтобы не усложнять

        main_layout.addWidget(criteria_group)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(QLabel("Результаты поиска:"))
        main_layout.addWidget(self.results_table)

    def clear_criteria(self):
        # Очистка всех полей ввода
        self.investor_name_input.clear()
        self.investor_inn_input.clear()
        self.registrar_name_input.clear()
        self.emitter_name_input.clear()
        self.stock_ticker_input.clear()
        self.date_start_edit.setDate(QDate())
        self.date_end_edit.setDate(QDate())
        # Очистка таблицы результатов
        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(0)

    def get_search_params(self):
        """Собирает параметры из полей ввода для SQL запроса."""
        inv_name = (
            f"%{self.investor_name_input.text().strip()}%"
            if self.investor_name_input.text().strip()
            else None
        )
        inv_inn = (
            f"%{self.investor_inn_input.text().strip()}%"
            if self.investor_inn_input.text().strip()
            else None
        )
        reg_name = (
            f"%{self.registrar_name_input.text().strip()}%"
            if self.registrar_name_input.text().strip()
            else None
        )
        em_name = (
            f"%{self.emitter_name_input.text().strip()}%"
            if self.emitter_name_input.text().strip()
            else None
        )
        ticker = (
            f"%{self.stock_ticker_input.text().strip().upper()}%"
            if self.stock_ticker_input.text().strip()
            else None
        )

        date_start_q = self.date_start_edit.date()
        date_start = (
            date_start_q.toPyDate()
            if date_start_q.isValid() and not date_start_q.isNull()
            else None
        )
        date_end_q = self.date_end_edit.date()
        date_end = (
            date_end_q.toPyDate()
            if date_end_q.isValid() and not date_end_q.isNull()
            else None
        )

        # Формируем кортеж из 35 параметров
        params = (
            # --- Параметры для секции Сделок (WHERE) --- (14 штук)
            inv_name,
            inv_name,  # investor_name
            inv_inn,
            inv_inn,  # investor_inn
            reg_name,
            reg_name,  # registrar_name
            em_name,
            em_name,  # emitter_name
            ticker,
            ticker,  # stock_ticker
            date_start,
            date_start,  # date_start
            date_end,
            date_end,  # date_end
            # --- Параметры для секции Эмиссий (WHERE) --- (11 штук)
            # Вместо инвестора передаем сами значения (которые будут None если не заданы)
            inv_name,  # %s IS NULL для имени инвестора
            inv_inn,  # %s IS NULL для ИНН инвестора
            reg_name,
            reg_name,  # registrar_name
            em_name,
            em_name,  # emitter_name
            # Вместо тикера передаем само значение
            ticker,  # %s IS NULL для тикера
            date_start,
            date_start,  # date_start
            date_end,
            date_end,  # date_end
            # --- Параметры для подзапроса NOT EXISTS в секции Эмиссий --- (10 штук)
            # Повторяем параметры, относящиеся к сделке
            inv_name,
            inv_name,  # investor_name
            inv_inn,
            inv_inn,  # investor_inn
            ticker,
            ticker,  # stock_ticker
            date_start,
            date_start,  # date_start
            date_end,
            date_end,  # date_end
        )

        # Проверка длины кортежа
        if len(params) != 35:
            raise ValueError(
                f"Ошибка формирования параметров для поиска: ожидалось 35, получено {len(params)}"
            )

        return params

    def perform_search(self):
        try:  # Добавим try..except вокруг get_search_params на случай ошибки там
            params = self.get_search_params()
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка параметров", str(e))
            return

        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(0)

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    print(
                        f"DEBUG [SearchTab]: Executing COMBINED_SEARCH with {len(params)} params."
                    )
                    cursor.execute(Queries.COMBINED_SEARCH, params)
                    results = cursor.fetchall()

                    if not results:
                        QMessageBox.information(
                            self, "Поиск", "По вашему запросу ничего не найдено."
                        )
                        return

                    # --- ИЗМЕНЕНИЕ ЗДЕСЬ: Задаем русские заголовки ---
                    # Словарь соответствия: 'алиас_из_sql' : 'Русский заголовок'
                    # Ключи должны ТОЧНО совпадать с алиасами в вашем COMBINED_SEARCH
                    header_map = {
                        "result_type": "Тип",
                        "id": "ID",
                        "investor_name": "Инвестор",
                        "investor_inn": "ИНН Инвестора",
                        "stock_ticker": "Тикер ЦБ",
                        "sale_date": "Дата сделки",  # Будет пустым для эмиссий
                        "emitter_name": "Эмитент",
                        "registrar_name": "Регистратор",
                        "emission_date": "Дата эмиссии",  # Будет пустым для сделок? Нет, ваш запрос возвращает и там и там.
                        # Возможно, лучше назвать 'Дата'? Или оставить так. Оставим пока так.
                    }

                    # Получаем оригинальные имена столбцов (алиасы) из курсора
                    original_headers = [desc[0] for desc in cursor.description]

                    # Проверка: Выведем алиасы, которые вернул запрос (для отладки)
                    print(
                        f"DEBUG [SearchTab]: Original headers from DB: {original_headers}"
                    )

                    # Формируем список русских заголовков, используя карту
                    # Если алиас не найден в карте, используем его как есть (запасной вариант)
                    display_headers = [
                        header_map.get(h, h.replace("_", " ").title())
                        for h in original_headers
                    ]

                    self.results_table.setColumnCount(len(display_headers))
                    self.results_table.setHorizontalHeaderLabels(
                        display_headers
                    )  # Используем новые заголовки

                    try:
                        id_column_index = display_headers.index("ID")
                        self.results_table.setColumnHidden(id_column_index, True)
                    except ValueError:
                        print("Warning: 'ID' header not found, cannot hide column.")

                    self.results_table.setRowCount(len(results))
                    for row_idx, row_data in enumerate(results):
                        for col_idx, cell_value in enumerate(row_data):
                            # Преобразование в строку и форматирование
                            if isinstance(cell_value, datetime.date):
                                formatted_value = cell_value.strftime(
                                    "%d.%m.%Y"
                                )  # Формат даты
                            elif isinstance(cell_value, (Decimal, float)):
                                # Форматирование с пробелом как разделителем тысяч
                                try:
                                    formatted_value = "{:,.2f}".format(
                                        cell_value
                                    ).replace(",", " ")
                                except (ValueError, TypeError):
                                    formatted_value = str(
                                        cell_value
                                    )  # Запасной вариант
                            elif (
                                isinstance(cell_value, int)
                                and display_headers[col_idx] == "Количество"
                            ):  # Пример для целых
                                formatted_value = "{:,}".format(cell_value).replace(
                                    ",", " "
                                )
                            else:
                                formatted_value = (
                                    str(cell_value) if cell_value is not None else ""
                                )

                            item = QTableWidgetItem(formatted_value)

                            # Выравнивание (можно улучшить, проверяя тип данных или конкретные заголовки)
                            if display_headers[col_idx] in [
                                "ID",
                                "ИНН Инвестора",
                                "Количество",
                                "Цена/Объем",
                            ]:
                                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                            elif display_headers[col_idx] in [
                                "Дата сделки",
                                "Дата эмиссии",
                            ]:
                                item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)

                            self.results_table.setItem(row_idx, col_idx, item)

                    # Настройка ширины колонок
                    # self.results_table.resizeColumnsToContents() # Вариант 1: Автоматически по содержимому
                    # Вариант 2: Растянуть некоторые, остальные по содержимому
                    header = self.results_table.horizontalHeader()
                    for i in range(len(display_headers)):
                        if display_headers[i] in ["Инвестор", "Эмитент", "Регистратор"]:
                            header.setSectionResizeMode(i, QHeaderView.Stretch)
                        else:
                            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        except psycopg2.Error as db_err:  # Ловим специфичные ошибки БД
            QMessageBox.critical(
                self, "Ошибка БД", f"Ошибка при выполнении поиска:\n{db_err}"
            )
            print(f"DB ERROR in perform_search: {db_err}")  # Для консоли
        except ValueError as val_err:  # Ловим ошибку из get_search_params
            QMessageBox.critical(self, "Ошибка параметров", str(val_err))
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка поиска", f"Произошла непредвиденная ошибка:\n{str(e)}"
            )
            print(f"ERROR in perform_search: {e}")
            import traceback

            traceback.print_exc()
