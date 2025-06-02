from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDialogButtonBox,
    QMessageBox,
    QDoubleSpinBox,
)
from PyQt5.QtCore import Qt

# Используем КЛАССЫ
from database.db import Database
from database.queries import Queries
import psycopg2
from decimal import Decimal  # Для работы с NUMERIC


class StockDialog(QDialog):
    def __init__(self, parent=None, stock_id=None):
        super().__init__(parent)
        self.stock_id = stock_id
        self.db = Database()  # Экземпляр
        self.original_ticket = None

        self.setWindowTitle(
            "Добавить ценную бумагу" if not stock_id else "Редактировать ценную бумагу"
        )
        self.setMinimumWidth(400)
        self.init_ui()
        # Загружаем комбобоксы сразу
        self.load_combos()

        if stock_id:
            self.load_data()
        else:
            # Фокус на первом поле
            self.emission_combo.setFocus()

    def init_ui(self):
        layout = QFormLayout(self)  # Родитель

        self.emission_combo = QComboBox()
        self.emission_combo.setToolTip("Выберите эмиссию, к которой относится ЦБ")
        self.ticket_input = QLineEdit()
        self.ticket_input.setToolTip("Уникальный тикер ценной бумаги (например, GAZP)")
        self.nominal_value_spinbox = QDoubleSpinBox()
        self.nominal_value_spinbox.setDecimals(2)
        self.nominal_value_spinbox.setRange(0.01, 9999999999.99)  # Увеличил диапазон
        self.nominal_value_spinbox.setSuffix(" руб.")
        self.nominal_value_spinbox.setGroupSeparatorShown(True)
        self.nominal_value_spinbox.setMaximumWidth(180)  # Чуть шире
        self.nominal_value_spinbox.setAlignment(Qt.AlignRight)

        layout.addRow("Эмиссия*:", self.emission_combo)
        layout.addRow("Тикер*:", self.ticket_input)
        layout.addRow("Номинальная стоимость*:", self.nominal_value_spinbox)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_data)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def load_combos(self):
        """Загружает список эмиссий."""
        self.emission_combo.clear()
        self.emission_combo.addItem("--- Выберите эмиссию ---", None)
        ok_button = self.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok)
        emission_ok = False
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Используем запрос для списка эмиссий (возможно, только активных?)
                    # Пока используем GET_EMISSION_LIST как есть
                    cursor.execute(Queries.GET_EMISSION_LIST)
                    emissions = cursor.fetchall()
                    if emissions:
                        emission_ok = True
                        for em_id, name in emissions:
                            self.emission_combo.addItem(name, em_id)
                    else:
                        self.emission_combo.addItem("Нет доступных эмиссий", None)
                        self.emission_combo.setEnabled(False)

        except Exception as e:
            QMessageBox.warning(
                self, "Ошибка БД", f"Не удалось загрузить список эмиссий:\n{str(e)}"
            )
            self.emission_combo.setEnabled(False)
        finally:
            # Блокируем кнопку OK, если нет эмиссий для выбора
            if ok_button:
                ok_button.setEnabled(emission_ok)

    def load_data(self):
        """Загружает данные существующей ЦБ."""
        ok_button = self.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok)
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_STOCK_BY_ID, (self.stock_id,))
                    stock_data = cursor.fetchone()
                    if not stock_data:
                        QMessageBox.critical(
                            self, "Ошибка", "Ценная бумага не найдена."
                        )
                        if ok_button:
                            ok_button.setEnabled(False)
                        return

                    _, ticket, nominal_value, emission_id = stock_data
                    self.original_ticket = ticket

                    emission_index = self.emission_combo.findData(emission_id)
                    if emission_index != -1:
                        self.emission_combo.setCurrentIndex(emission_index)
                    else:
                        # Эмиссия не найдена в списке (стала неактивной?)
                        # Добавляем ее временно для отображения
                        cursor.execute(Queries.GET_EMISSION_BY_ID, (emission_id,))
                        em_data = cursor.fetchone()
                        if em_data:
                            # Получаем имя эмитента для отображения
                            cursor.execute(Queries.GET_EMITTER_LIST)  # Нужно имя ЮЛ
                            # Тут сложнее получить имя, нужна доп. логика или запрос имени эмиссии
                            # Пока просто ID
                            em_name = f"Эмиссия ID {emission_id} (Неактивна?)"
                            self.emission_combo.insertItem(1, em_name, emission_id)
                            self.emission_combo.setCurrentIndex(1)
                            QMessageBox.warning(
                                self,
                                "Внимание",
                                f"Связанная эмиссия ID {emission_id} не найдена в активном списке.",
                            )
                        else:
                            self.emission_combo.insertItem(
                                1, f"Эмиссия ID {emission_id} (Удалена?)", emission_id
                            )
                            self.emission_combo.setCurrentIndex(1)
                            QMessageBox.warning(
                                self,
                                "Внимание",
                                f"Связанная эмиссия ID {emission_id} не найдена.",
                            )

                    self.ticket_input.setText(ticket)
                    self.nominal_value_spinbox.setValue(
                        float(nominal_value) if nominal_value else 0.01
                    )

                    if ok_button:
                        ok_button.setEnabled(True)  # Активируем ОК

        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось загрузить данные ЦБ:\n{db_err}"
            )
            if ok_button:
                ok_button.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка загрузки", f"Не удалось загрузить данные ЦБ:\n{str(e)}"
            )
            if ok_button:
                ok_button.setEnabled(False)

    def get_data(self):
        emission_id = self.emission_combo.currentData()
        ticket = self.ticket_input.text().strip().upper()
        # Преобразуем в Decimal для точности
        nominal_value = Decimal(str(self.nominal_value_spinbox.value())).quantize(
            Decimal("0.01")
        )

        return emission_id, ticket, nominal_value

    def accept_data(self):
        emission_id, ticket, nominal_value = self.get_data()

        errors = []
        if emission_id is None:
            errors.append("Необходимо выбрать эмиссию.")
        if not ticket:
            errors.append("Тикер не может быть пустым.")
        # Валидация формата тикера (например, только латиница и цифры)?
        if nominal_value <= 0:
            errors.append("Номинальная стоимость должна быть положительной.")

        if errors:
            QMessageBox.warning(self, "Ошибка ввода", "\n".join(errors))
            if emission_id is None:
                self.emission_combo.setFocus()
            elif not ticket:
                self.ticket_input.setFocus()
            elif nominal_value <= 0:
                self.nominal_value_spinbox.setFocus()
            return

        # Проверка уникальности тикера
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Проверяем только если тикер изменился или это новая запись
                    if ticket != self.original_ticket:
                        cursor.execute(
                            Queries.CHECK_STOCK_TICKET_EXISTS,
                            (ticket, self.stock_id, self.stock_id),
                        )
                        if cursor.fetchone():
                            QMessageBox.warning(
                                self,
                                "Ошибка ввода",
                                f"Ценная бумага с тикером '{ticket}' уже существует.",
                            )
                            self.ticket_input.setFocus()
                            return
        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self,
                "Ошибка проверки",
                f"Ошибка БД при проверке уникальности тикера:\n{db_err}",
            )
            return
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка проверки",
                f"Не удалось проверить уникальность тикера:\n{str(e)}",
            )
            return

        super().accept()
