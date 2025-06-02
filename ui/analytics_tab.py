import sys
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QAbstractItemView,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QHeaderView,
    QFileDialog,  # Заменили QTextEdit на QStackedWidget
    QTableWidgetItem,
    QMessageBox,
    QLabel,
    QDateEdit,
    QSpinBox,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon

import matplotlib

matplotlib.use("Qt5Agg")  # Указываем бэкенд для PyQt5
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot as plt  # Для доступа к стилям и функциям форматирования

from database.db import Database
from database.queries import Queries
import psycopg2
import datetime
import csv
from decimal import Decimal
import random  # Для цветов в графиках (можно заменить на палитру)


# --- Виджет для отображения графика ---
class PlotCanvasWidget(QWidget):
    """Виджет для отображения Matplotlib графика с панелью навигации."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(5, 4), dpi=100)  # Создаем фигуру Matplotlib
        self.canvas = FigureCanvasQTAgg(self.figure)  # Создаем холст Qt для фигуры
        self.toolbar = NavigationToolbar2QT(self.canvas, self)  # Панель навигации

        layout = QVBoxLayout(self)
        layout.addWidget(self.toolbar)  # Добавляем панель
        layout.addWidget(self.canvas)  # Добавляем холст

    def plot_pie(self, sizes, labels, title=""):
        """Строит круговую диаграмму."""
        self.figure.clear()  # Очищаем предыдущий график
        ax = self.figure.add_subplot(111)
        # Используем цвета по умолчанию или задаем свои
        # colors = plt.cm.Paired(range(len(sizes))) # Пример палитры
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",  # Формат процентов
            startangle=90,
            # colors=colors, # Можно задать цвета
            pctdistance=0.85,  # Расстояние текста процентов от центра
        )
        # Улучшаем читаемость текста
        plt.setp(autotexts, size=8, weight="bold", color="white")
        # Добавляем легенду, если много секторов
        # if len(labels) > 5:
        #     ax.legend(wedges, labels, title="Категории", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        ax.set_title(title)
        # ax.axis('equal') # Делает диаграмму круглой (может обрезать текст)
        self.figure.tight_layout()  # Подгоняем размер
        self.canvas.draw()  # Перерисовываем холст

    def plot_bar(self, x_labels, y_values, title="", xlabel="", ylabel=""):
        """Строит гистограмму."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        # Генерируем цвета (можно использовать палитру Matplotlib)
        colors = [
            plt.cm.viridis(i / float(len(x_labels))) for i in range(len(x_labels))
        ]
        bars = ax.bar(x_labels, y_values, color=colors)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        # Поворот меток по оси X, если их много или они длинные
        if len(x_labels) > 5 or any(len(str(lbl)) > 10 for lbl in x_labels):
            plt.setp(
                ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
            )

        # Добавляем значения над столбцами (опционально)
        # ax.bar_label(bars, fmt='{:,.0f}', padding=3) # Форматирование по желанию

        # Убедимся, что метки не обрезаются
        self.figure.tight_layout()
        self.canvas.draw()


# --- Конец виджета для графика ---


class AnalyticsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.current_headers = []
        self.current_data = []
        # Определяем, какие отчеты могут быть графиками
        self.plot_reports = [
            "run_emissions_by_status",
            "run_top_emissions",
            "run_investor_activity",
        ]
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        controls_layout = QHBoxLayout()

        self.report_combo = QComboBox()
        self.report_combo.addItem("--- Выберите отчет ---", None)
        self.report_combo.addItem(
            "Распределение эмиссий по статусам", "run_emissions_by_status"
        )
        self.report_combo.addItem(
            "Ценные бумаги (средняя цена продажи)", "run_stocks_avg_price"
        )
        self.report_combo.addItem("Топ N эмиссий по объему", "run_top_emissions")
        self.report_combo.addItem("Эмиссии по регистраторам", "run_registrar_emissions")
        self.report_combo.addItem("Активность инвесторов", "run_investor_activity")
        self.report_combo.addItem("Новые эмиссии за период", "run_new_emissions_period")
        self.report_combo.currentIndexChanged.connect(self.on_report_selected)

        # Панель параметров (без изменений)
        self.param_widget = QWidget()
        self.param_layout = QHBoxLayout(self.param_widget)
        self.param_layout.setContentsMargins(5, 0, 5, 0)
        # ... (код для top_n, registrar_combo, date_edit - как в предыдущем шаге) ...
        self.top_n_label = QLabel("N:")
        self.top_n_spinbox = QSpinBox()
        self.top_n_spinbox.setRange(1, 1000)
        self.top_n_spinbox.setValue(10)
        self.param_layout.addWidget(self.top_n_label)
        self.param_layout.addWidget(self.top_n_spinbox)
        self.registrar_label = QLabel("Регистратор:")
        self.registrar_combo = QComboBox()
        self.registrar_combo.setMinimumWidth(250)
        self.param_layout.addWidget(self.registrar_label)
        self.param_layout.addWidget(self.registrar_combo)
        self.date_label = QLabel("Период с:")
        self.date_start_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.date_start_edit.setCalendarPopup(True)
        self.date_start_edit.setMaximumDate(QDate(9999, 12, 31))
        self.date_start_edit.setMinimumDate(QDate(1990, 1, 1))
        self.date_label_to = QLabel("по:")
        self.date_end_edit = QDateEdit(QDate.currentDate())
        self.date_end_edit.setCalendarPopup(True)
        self.date_end_edit.setMaximumDate(QDate(9999, 12, 31))
        self.date_end_edit.setMinimumDate(QDate(1990, 1, 1))
        self.param_layout.addWidget(self.date_label)
        self.param_layout.addWidget(self.date_start_edit)
        self.param_layout.addWidget(self.date_label_to)
        self.param_layout.addWidget(self.date_end_edit)
        self.param_layout.addStretch(1)
        self.set_param_visibility(False, False, False)  # Скрываем все по умолчанию

        self.run_report_btn = QPushButton(
            QIcon.fromTheme("view-refresh"), " Сформировать"
        )
        self.run_report_btn.clicked.connect(self.run_report)
        self.run_report_btn.setEnabled(False)

        self.export_btn = QPushButton(
            QIcon.fromTheme("document-save-as"), " Экспорт в CSV"
        )
        self.export_btn.setToolTip("Экспортировать табличные данные")
        self.export_btn.clicked.connect(self.export_to_csv)
        self.export_btn.setEnabled(False)

        controls_layout.addWidget(QLabel("Отчет:"))
        controls_layout.addWidget(self.report_combo)
        controls_layout.addWidget(self.param_widget)
        controls_layout.addWidget(self.run_report_btn)
        controls_layout.addWidget(self.export_btn)  # Экспорт остается для таблиц
        controls_layout.addStretch(1)

        # --- Используем QStackedWidget для отображения ---
        self.result_display_widget = QStackedWidget()

        # Страница 0: Таблица
        self.result_table = QTableWidget()
        self.result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.verticalHeader().setVisible(False)
        self.result_display_widget.addWidget(self.result_table)

        # Страница 1: График
        self.plot_widget = PlotCanvasWidget(self)  # Наш виджет с графиком
        self.result_display_widget.addWidget(self.plot_widget)
        # -------------------------------------------------

        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.result_display_widget)  # Добавляем QStackedWidget

    # load_registrars_combo, set_param_visibility (без изменений)
    def load_registrars_combo(self):
        """Загружает список активных регистраторов для фильтра."""
        self.registrar_combo.clear()
        self.registrar_combo.addItem("Все регистраторы", None)
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        Queries.GET_REGISTRAR_LIST
                    )  # Запрос выбирает активных
                    for reg_id, name in cursor.fetchall():
                        self.registrar_combo.addItem(name, reg_id)
        except Exception as e:
            QMessageBox.warning(
                self, "Ошибка БД", f"Не удалось загрузить регистраторов:\n{str(e)}"
            )

    def set_param_visibility(self, top_n=False, registrar=False, period=False):
        """Управляет видимостью виджетов параметров."""
        self.top_n_label.setVisible(top_n)
        self.top_n_spinbox.setVisible(top_n)
        self.registrar_label.setVisible(registrar)
        self.registrar_combo.setVisible(registrar)
        self.date_label.setVisible(period)
        self.date_start_edit.setVisible(period)
        self.date_label_to.setVisible(period)
        self.date_end_edit.setVisible(period)
        self.param_widget.setVisible(top_n or registrar or period)

    def on_report_selected(self, index):
        report_method_name = self.report_combo.currentData()
        is_report_selected = report_method_name is not None
        self.run_report_btn.setEnabled(is_report_selected)
        self.export_btn.setEnabled(False)  # Сбрасываем экспорт

        # Очищаем предыдущий результат (и таблицу, и график)
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        self.plot_widget.figure.clear()
        self.plot_widget.canvas.draw()
        self.current_headers = []
        self.current_data = []

        # Показываем нужный виджет (таблицу или пустой график)
        if report_method_name in self.plot_reports:
            self.result_display_widget.setCurrentIndex(1)  # Показать виджет с графиком
        else:
            self.result_display_widget.setCurrentIndex(0)  # Показать таблицу

        # Настройка видимости параметров (без изменений)
        self.set_param_visibility(
            top_n=(report_method_name == "run_top_emissions"),
            registrar=(report_method_name == "run_registrar_emissions"),
            period=(report_method_name == "run_new_emissions_period"),
        )
        if report_method_name == "run_registrar_emissions":
            self.load_registrars_combo()

    def run_report(self):
        report_method_name = self.report_combo.currentData()
        if not report_method_name:
            return

        report_method = getattr(self, report_method_name, None)
        if report_method and callable(report_method):
            try:
                # --- Переключаем виджет перед выполнением ---
                if report_method_name in self.plot_reports:
                    self.result_display_widget.setCurrentIndex(1)  # График
                    self.export_btn.setEnabled(False)  # Экспорт недоступен для графиков
                else:
                    self.result_display_widget.setCurrentIndex(0)  # Таблица
                    self.export_btn.setEnabled(
                        False
                    )  # Деактивируем перед заполнением таблицы

                # Вызываем метод
                report_method()

            except psycopg2.OperationalError as db_err:
                QMessageBox.critical(
                    self, "Ошибка БД", f"Ошибка при выполнении отчета:\n{db_err}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка выполнения отчета",
                    f"Не удалось сформировать отчет:\n{str(e)}",
                )
                import traceback

                traceback.print_exc()
        else:
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Метод для отчета '{self.report_combo.currentText()}' не найден.",
            )

    # --- Методы для выполнения КОНКРЕТНЫХ отчетов ---

    def _execute_and_get_data(self, query, params):
        """Вспомогательный метод для выполнения запроса и получения данных."""
        print(
            f"DEBUG [Analytics]: Executing query: {query[:100]}... with params: {params}"
        )  # Отладка
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                data = cursor.fetchall()
                print(f"DEBUG [Analytics]: Fetched {len(data)} rows.")  # Отладка
                return data

    # --- Отчеты с ГРАФИКАМИ ---
    def run_emissions_by_status(self):
        headers = ["Статус", "Количество", "Общий объем"]
        query = Queries.GET_EMISSIONS_BY_STATUS
        raw_data = self._execute_and_get_data(query, ())
        if not raw_data:
            QMessageBox.information(
                self, "Информация", "Нет данных для построения графика."
            )
            self.plot_widget.figure.clear()
            self.plot_widget.canvas.draw()
            return
        labels = [row[0] for row in raw_data]
        sizes = [row[1] for row in raw_data]
        self.plot_widget.plot_pie(
            sizes, labels, title="Распределение эмиссий по статусам (по количеству)"
        )
        self.current_headers = headers
        self.current_data = raw_data

    def run_top_emissions(self):
        n_limit = self.top_n_spinbox.value()
        headers = [
            "ID эмиссии",
            "Эмитент",
            "Объем",
            "Дата регистрации",
        ]  # Полные заголовки
        query = Queries.GET_TOP_EMISSIONS_BY_VALUE
        raw_data = self._execute_and_get_data(query, (n_limit,))
        if not raw_data:
            QMessageBox.information(
                self, "Информация", "Нет данных для построения графика."
            )
            self.plot_widget.figure.clear()
            self.plot_widget.canvas.draw()
            return
        labels = [f"{row[1]}\n(ID:{row[0]})" for row in raw_data]
        values = [float(row[2]) for row in raw_data]
        self.plot_widget.plot_bar(
            labels, values, title=f"Топ-{n_limit} эмиссий по объему", ylabel="Объем"
        )
        self.current_headers = headers
        self.current_data = raw_data

    def run_investor_activity(self):
        headers = [
            "Инвестор",
            "ИНН",
            "Кол-во сделок",
            "Куплено ЦБ (шт.)",
            "Потрачено всего",
        ]
        query = Queries.GET_INVESTOR_ACTIVITY
        raw_data = self._execute_and_get_data(query, ())
        if not raw_data:
            QMessageBox.information(
                self, "Информация", "Нет данных для построения графика."
            )
            self.plot_widget.figure.clear()
            self.plot_widget.canvas.draw()
            return
        top_n = 15
        plot_data = raw_data[:top_n]
        labels = [row[0] for row in plot_data]
        values = [float(row[4]) if row[4] else 0.0 for row in plot_data]
        self.plot_widget.plot_bar(
            labels,
            values,
            title=f"Активность инвесторов (Топ-{top_n} по затратам)",
            ylabel="Потрачено всего",
        )
        self.current_headers = headers
        self.current_data = raw_data

    # --- Отчеты ТАБЛИЧНЫЕ ---
    def run_stocks_avg_price(self):
        headers = ["Тикер", "Номинал", "Средняя цена продажи", "Всего продано (шт.)"]
        query = Queries.GET_STOCKS_AVG_PRICE
        raw_data = self._execute_and_get_data(query, ())  # <<< Получаем данные
        # --- Отображаем в таблице ---
        if raw_data:
            self.display_results(headers, raw_data)
            self.current_headers = headers
            self.current_data = raw_data
            self.export_btn.setEnabled(True)
        else:
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)
            self.export_btn.setEnabled(False)
            QMessageBox.information(self, "Информация", "Нет данных для отображения.")
        # ---------------------------

    def run_registrar_emissions(self):
        registrar_id = self.registrar_combo.currentData()
        headers = [
            "Регистратор",
            "Лицензия",
            "ID эмиссии",
            "Эмитент",
            "Объем",
            "Дата регистрации",
        ]
        query = Queries.GET_REGISTRAR_EMISSIONS
        raw_data = self._execute_and_get_data(
            query, (registrar_id, registrar_id)
        )  # <<< Получаем данные
        # --- Отображаем в таблице ---
        if raw_data:
            self.display_results(headers, raw_data)
            self.current_headers = headers
            self.current_data = raw_data
            self.export_btn.setEnabled(True)
        else:
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)
            self.export_btn.setEnabled(False)
            QMessageBox.information(
                self, "Информация", "Нет данных для отображения по выбранным критериям."
            )

    def run_new_emissions_period(self):
        date_start = self.date_start_edit.date().toPyDate()
        date_end = self.date_end_edit.date().toPyDate()
        if date_start > date_end:
            QMessageBox.warning(
                self, "Ошибка", "Дата начала не может быть позже даты окончания."
            )
            return
        headers = ["ID эмиссии", "Эмитент", "Объем", "Статус", "Дата регистрации"]
        query = Queries.GET_NEW_EMISSIONS_BY_PERIOD
        raw_data = self._execute_and_get_data(
            query, (date_start, date_end)
        )  # <<< Получаем данные
        # --- Отображаем в таблице ---
        if raw_data:
            self.display_results(headers, raw_data)
            self.current_headers = headers
            self.current_data = raw_data
            self.export_btn.setEnabled(True)
        else:
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)
            self.export_btn.setEnabled(False)
            QMessageBox.information(
                self, "Информация", "Нет данных для отображения за выбранный период."
            )
        # ---------------------------

    # --- Отображение таблицы и экспорт (без изменений) ---
    def display_results(self, headers, data):
        """Отображает данные в таблице с форматированием."""
        self.result_table.setColumnCount(len(headers))
        self.result_table.setHorizontalHeaderLabels(headers)
        self.result_table.setRowCount(len(data))
        # ... (код форматирования ячеек как в предыдущем шаге) ...
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_value in enumerate(row_data):
                align = Qt.AlignLeft | Qt.AlignVCenter
                if isinstance(cell_value, (Decimal, float)):
                    text_value = "{:,.2f}".format(cell_value)
                    align = Qt.AlignRight | Qt.AlignVCenter
                elif isinstance(cell_value, int):
                    header_lower = headers[col_idx].lower()
                    if (
                        "id" in header_lower
                        or "количество" in header_lower
                        or "кол-во" in header_lower
                        or "шт" in header_lower
                    ):
                        text_value = str(cell_value)
                    else:
                        text_value = "{:,}".format(cell_value).replace(",", " ")
                    align = Qt.AlignRight | Qt.AlignVCenter
                elif isinstance(cell_value, datetime.date):
                    text_value = cell_value.strftime("%Y-%m-%d")
                    align = Qt.AlignCenter | Qt.AlignVCenter
                else:
                    text_value = str(cell_value) if cell_value is not None else ""
                    if headers[col_idx].lower() == "статус":
                        align = Qt.AlignCenter | Qt.AlignVCenter
                item = QTableWidgetItem(text_value)
                item.setTextAlignment(align)
                self.result_table.setItem(row_idx, col_idx, item)

        self.result_table.resizeColumnsToContents()
        if self.result_table.columnCount() > 0:
            last_col = self.result_table.columnCount() - 1
            # Только если больше 1 колонки, иначе растягивать нечего
            if last_col > 0:
                self.result_table.horizontalHeader().setSectionResizeMode(
                    last_col, QHeaderView.Stretch
                )

    def export_to_csv(self):
        # (код без изменений)
        if not self.current_data:
            QMessageBox.information(self, "Экспорт", "Нет данных для экспорта.")
            return
        report_name = (
            self.report_combo.currentText()
            .replace(" ", "_")
            .replace("(", "")
            .replace(")", "")
        )
        default_filename = f"report_{report_name}_{datetime.date.today()}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчет как CSV",
            default_filename,
            "CSV Files (*.csv);;All Files (*)",
        )
        if path:
            try:
                with open(path, "w", newline="", encoding="utf-8-sig") as csvfile:
                    writer = csv.writer(csvfile, delimiter=";")
                    writer.writerow(self.current_headers)
                    for row_data in self.current_data:
                        formatted_row = []
                        for val in row_data:
                            if isinstance(val, (Decimal, float)):
                                formatted_row.append(str(val).replace(".", ","))
                            else:
                                formatted_row.append(
                                    str(val) if val is not None else ""
                                )
                        writer.writerow(formatted_row)
                QMessageBox.information(
                    self, "Экспорт завершен", f"Отчет успешно сохранен в файл:\n{path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Ошибка экспорта", f"Не удалось сохранить файл:\n{str(e)}"
                )
