from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QComboBox,
    QDateEdit,
    QDialogButtonBox,
    QMessageBox,
    QSpinBox,
    QDoubleSpinBox,
)
from PyQt5.QtCore import QDate, Qt

# Используем КЛАССЫ
from database.db import Database
from database.queries import Queries
import psycopg2
from decimal import Decimal  # Для работы с NUMERIC


class SellDialog(QDialog):
    def __init__(self, parent=None, sell_id=None, preselected_investor=None):
        super().__init__(parent)
        self.sell_id = sell_id
        self.preselected_investor_info = (
            preselected_investor  # Словарь {'id': ..., 'name': ...} или None
        )
        self.db = Database()  # Экземпляр

        # Определяем заголовок окна
        if sell_id:
            self.setWindowTitle(f"Редактировать сделку ID: {sell_id}")
        elif self.preselected_investor_info:
            # Получаем имя, если есть, иначе используем ID
            inv_name = self.preselected_investor_info.get(
                "name", f"ID {self.preselected_investor_info.get('id')}"
            )
            self.setWindowTitle(f"Новая сделка для: {inv_name}")
        else:
            self.setWindowTitle("Добавить новую сделку")

        self.setMinimumWidth(450)
        self.init_ui()
        # Загружаем комбобоксы
        self.load_combos()

        if sell_id:
            self.load_data()  # Загрузка данных для редактирования
        elif self.preselected_investor_info:
            # Устанавливаем инвестора ПОСЛЕ загрузки комбобокса
            self.set_preselected_investor()
        else:
            # Фокус на первом поле при обычном добавлении
            self.investor_combo.setFocus()

    def init_ui(self):
        """Инициализирует виджеты диалогового окна."""
        layout = QFormLayout(self)  # Родитель

        self.investor_combo = QComboBox()
        self.investor_combo.setToolTip("Выберите инвестора")
        self.stock_combo = QComboBox()
        self.stock_combo.setToolTip("Выберите ценную бумагу")
        self.sale_date_edit = QDateEdit(QDate.currentDate())
        self.sale_date_edit.setCalendarPopup(True)
        self.sale_date_edit.setMaximumDate(
            QDate.currentDate()
        )  # Нельзя выбрать будущую дату
        self.sale_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.num_spinbox = QSpinBox()
        self.num_spinbox.setRange(1, 2147483647)  # Макс. int4
        self.num_spinbox.setSuffix(" шт.")
        self.num_spinbox.setGroupSeparatorShown(True)
        self.num_spinbox.setMaximumWidth(180)
        self.num_spinbox.setAlignment(Qt.AlignRight)
        self.price_spinbox = QDoubleSpinBox()
        self.price_spinbox.setDecimals(2)
        self.price_spinbox.setRange(0.01, 9999999999.99)  # Примерный макс.
        self.price_spinbox.setSuffix(" руб.")
        self.price_spinbox.setGroupSeparatorShown(True)
        self.price_spinbox.setMaximumWidth(180)
        self.price_spinbox.setAlignment(Qt.AlignRight)

        layout.addRow("Инвестор*:", self.investor_combo)
        layout.addRow("Ценная бумага*:", self.stock_combo)
        layout.addRow("Дата сделки*:", self.sale_date_edit)
        layout.addRow("Количество (шт)*:", self.num_spinbox)
        layout.addRow("Цена за шт. (руб)*:", self.price_spinbox)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_data)  # Подключаем свою валидацию
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def load_combos(self):
        """Загружает списки инвесторов и ЦБ в комбобоксы."""
        ok_button = self.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok)
        investor_ok = False
        stock_ok = False

        # --- Инвесторы ---
        self.investor_combo.clear()
        self.investor_combo.addItem("--- Выберите инвестора ---", None)  # ID = None
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_INVESTOR_LIST)
                    investors = cursor.fetchall()
                    if investors:
                        investor_ok = True
                        for inv_id, name in investors:
                            self.investor_combo.addItem(
                                name, inv_id
                            )  # Сохраняем ID в данных
                    else:
                        self.investor_combo.addItem("Нет инвесторов в БД", None)
                        self.investor_combo.setEnabled(False)
        except Exception as e:
            print(f"ERROR loading investors: {e}")
            QMessageBox.warning(
                self, "Ошибка БД", f"Не удалось загрузить инвесторов:\n{str(e)}"
            )
            self.investor_combo.setEnabled(False)

        # --- Ценные бумаги ---
        self.stock_combo.clear()
        self.stock_combo.addItem("--- Выберите ЦБ ---", None)  # ID = None
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        Queries.GET_STOCK_LIST
                    )  # Запрос должен возвращать ID и Ticker/Name
                    stocks = cursor.fetchall()
                    if stocks:
                        stock_ok = True
                        for st_id, name in stocks:
                            self.stock_combo.addItem(
                                name, st_id
                            )  # Сохраняем ID в данных
                    else:
                        self.stock_combo.addItem("Нет ЦБ в БД", None)
                        self.stock_combo.setEnabled(False)
        except Exception as e:
            print(f"ERROR loading stocks: {e}")
            QMessageBox.warning(
                self, "Ошибка БД", f"Не удалось загрузить ЦБ:\n{str(e)}"
            )
            self.stock_combo.setEnabled(False)

        # Активируем кнопку OK только если есть и инвесторы и ЦБ
        if ok_button:
            ok_button.setEnabled(investor_ok and stock_ok)

    def set_preselected_investor(self):
        """Находит и устанавливает инвестора в комбобоксе, блокирует его."""
        if (
            not self.preselected_investor_info
            or "id" not in self.preselected_investor_info
        ):
            print(
                f"DEBUG [{self.__class__.__name__}]: No valid preselected_investor_info provided."
            )
            return

        investor_id_to_select = self.preselected_investor_info["id"]
        print(
            f"DEBUG [{self.__class__.__name__}]: Attempting to preselect investor ID: {investor_id_to_select}"
        )

        index = self.investor_combo.findData(investor_id_to_select)
        if index != -1:
            self.investor_combo.setCurrentIndex(index)
            self.investor_combo.setEnabled(False)  # Блокируем выбор
            print(
                f"DEBUG [{self.__class__.__name__}]: Investor set to index {index} and combo disabled."
            )
            self.stock_combo.setFocus()  # Переводим фокус на следующий элемент
        else:
            # Инвестор был передан, но не найден в списке (например, удален?)
            QMessageBox.warning(
                self,
                "Внимание",
                f"Предустановленный инвестор ID {investor_id_to_select} не найден в активном списке.\n"
                "Возможно, он был удален. Выберите другого инвестора.",
            )
            print(
                f"WARN [{self.__class__.__name__}]: Preselected investor ID {investor_id_to_select} not found in ComboBox."
            )
            # Оставляем комбобокс доступным для выбора
            self.investor_combo.setEnabled(True)
            self.investor_combo.setFocus()

    def load_data(self):
        """Загружает данные существующей сделки для редактирования."""
        ok_button = self.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok)
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_SELL_BY_ID, (self.sell_id,))
                    sell_data = cursor.fetchone()
                    if not sell_data:
                        QMessageBox.critical(
                            self, "Ошибка", f"Сделка с ID {self.sell_id} не найдена."
                        )
                        if ok_button:
                            ok_button.setEnabled(False)
                        # Возможно, стоит закрыть диалог self.reject()
                        return

                    _, investor_id, stock_id, sale_date, num, price = sell_data

                    # Установка инвестора
                    inv_index = self.investor_combo.findData(investor_id)
                    if inv_index != -1:
                        self.investor_combo.setCurrentIndex(inv_index)
                    else:  # Инвестор не найден
                        # Добавляем "Не найден" в начало списка (после плейсхолдера)
                        self.investor_combo.insertItem(
                            1, f"ID {investor_id} (Не найден)", investor_id
                        )
                        self.investor_combo.setCurrentIndex(1)
                        QMessageBox.warning(
                            self,
                            "Внимание",
                            f"Инвестор ID {investor_id} не найден в текущем списке.",
                        )

                    # Установка ЦБ
                    stock_index = self.stock_combo.findData(stock_id)
                    if stock_index != -1:
                        self.stock_combo.setCurrentIndex(stock_index)
                    else:  # ЦБ не найдена
                        self.stock_combo.insertItem(
                            1, f"ID {stock_id} (Не найдена)", stock_id
                        )
                        self.stock_combo.setCurrentIndex(1)
                        QMessageBox.warning(
                            self,
                            "Внимание",
                            f"ЦБ ID {stock_id} не найдена в текущем списке.",
                        )

                    # Установка остальных полей
                    self.sale_date_edit.setDate(QDate(sale_date))
                    self.num_spinbox.setValue(num)
                    # Преобразуем Decimal в float для QDoubleSpinBox
                    self.price_spinbox.setValue(
                        float(price) if price is not None else 0.01
                    )

                    # Блокируем инвестора при редактировании
                    self.investor_combo.setEnabled(False)

                    if ok_button:
                        ok_button.setEnabled(True)  # Убедимся, что кнопка ОК активна

        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self,
                "Ошибка БД",
                f"Не удалось загрузить данные сделки ID {self.sell_id}:\n{db_err}",
            )
            if ok_button:
                ok_button.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Критическая Ошибка",
                f"Не удалось загрузить данные сделки ID {self.sell_id}:\n{str(e)}",
            )
            if ok_button:
                ok_button.setEnabled(False)

    def get_data(self):
        """Собирает и возвращает данные из полей диалога."""
        investor_id = self.investor_combo.currentData()
        stock_id = self.stock_combo.currentData()
        sale_date = self.sale_date_edit.date().toPyDate()  # Возвращает datetime.date
        num = self.num_spinbox.value()
        # Получаем float из QDoubleSpinBox и преобразуем в Decimal для точности
        price_float = self.price_spinbox.value()
        price_decimal = Decimal(str(price_float)).quantize(Decimal("0.01"))

        return (
            investor_id,
            stock_id,
            sale_date,
            num,
            price_decimal,
        )  # Возвращаем Decimal

    def accept_data(self):
        """Выполняет валидацию данных перед закрытием диалога по кнопке OK."""
        investor_id = self.investor_combo.currentData()
        stock_id = self.stock_combo.currentData()
        num = self.num_spinbox.value()
        price_float = self.price_spinbox.value()

        errors = []
        if investor_id is None:
            errors.append("Необходимо выбрать инвестора.")
        if stock_id is None:
            errors.append("Необходимо выбрать ценную бумагу.")
        # Проверки на > 0 в SpinBox'ах обычно делаются через setMinimum, но подстрахуемся
        if num <= 0:
            errors.append("Количество должно быть больше нуля.")
        if price_float <= 0:
            errors.append("Цена должна быть больше нуля.")

        if errors:
            QMessageBox.warning(self, "Ошибка ввода", "\n".join(errors))
            # Устанавливаем фокус на первое ошибочное поле
            if investor_id is None:
                self.investor_combo.setFocus()
            elif stock_id is None:
                self.stock_combo.setFocus()
            elif num <= 0:
                self.num_spinbox.setFocus()
            elif price_float <= 0:
                self.price_spinbox.setFocus()
            return  # Не закрываем диалог

        # Если все проверки пройдены, вызываем стандартный accept
        super().accept()
