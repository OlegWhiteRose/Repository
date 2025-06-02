from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTableWidget,
    QHeaderView,
    QAbstractItemView,
    QTableWidgetItem,
    QMessageBox,
    QLabel,
    QDialogButtonBox,
)
from PyQt5.QtCore import Qt

# Импортируем КЛАССЫ
from database.db import Database
from database.queries import Queries
import psycopg2
from decimal import Decimal


class InvestorSalesDialog(QDialog):
    def __init__(self, investor_id, investor_name, parent=None):
        super().__init__(parent)
        self.investor_id = investor_id
        self.db = Database()  # Экземпляр
        self.setWindowTitle(f"Сделки инвестора: {investor_name} (ID: {investor_id})")
        self.setModal(True)
        self.setMinimumSize(650, 400)
        self.init_ui()
        self.load_sales_data()

    def init_ui(self):
        layout = QVBoxLayout(self)  # Родитель

        # Таблица сделок
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(5)
        self.sales_table.setHorizontalHeaderLabels(
            ["ID сделки", "Тикер ЦБ", "Дата", "Количество", "Цена за шт."]
        )
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        header = self.sales_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Дата
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Кол-во
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Цена
        self.sales_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sales_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sales_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.sales_table.setAlternatingRowColors(True)
        self.sales_table.verticalHeader().setVisible(False)  # Скрываем номера строк

        # Кнопка закрытия
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)  # Close -> reject

        layout.addWidget(
            QLabel(f"Список сделок для инвестора: {self.windowTitle()}")
        )  # Используем заголовок окна
        layout.addWidget(self.sales_table)
        layout.addWidget(buttons)

    def load_sales_data(self):
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_INVESTOR_SALES, (self.investor_id,))
                    sales = cursor.fetchall()

                    self.sales_table.setRowCount(0)  # Очистка
                    self.sales_table.setRowCount(len(sales))
                    for row, sale in enumerate(sales):
                        # sell_id, stock_ticket, sale_date, num, price
                        sell_id = sale[0]
                        ticket = sale[1]
                        sale_date = sale[2]
                        num = sale[3]
                        price = sale[4]  # Decimal

                        # ID
                        id_item = QTableWidgetItem(str(sell_id))
                        id_item.setData(
                            Qt.UserRole, sell_id
                        )  # Сохраняем ID, если нужно
                        self.sales_table.setItem(row, 0, id_item)
                        # Тикер
                        self.sales_table.setItem(row, 1, QTableWidgetItem(ticket))
                        # Дата
                        date_item = QTableWidgetItem(sale_date.strftime("%Y-%m-%d"))
                        date_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                        self.sales_table.setItem(row, 2, date_item)
                        # Количество
                        num_item = QTableWidgetItem(str(num))
                        num_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.sales_table.setItem(row, 3, num_item)
                        # Цена
                        price_item = QTableWidgetItem(f"{price:,.2f}")
                        price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.sales_table.setItem(row, 4, price_item)

            # self.sales_table.resizeColumnsToContents() # Убрали, используем ResizeMode

        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось загрузить сделки:\n{db_err}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка загрузки", f"Не удалось загрузить сделки:\n{str(e)}"
            )
            self.sales_table.setRowCount(0)
