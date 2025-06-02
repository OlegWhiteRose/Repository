from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QCheckBox,
    QDialogButtonBox,
    QMessageBox,
    QTextEdit,
)
from PyQt5.QtCore import Qt

# Используем КЛАССЫ
from database.db import Database
from database.queries import Queries
import psycopg2


class EntityDialog(QDialog):
    def __init__(self, parent=None, entity_id=None):
        super().__init__(parent)
        self.entity_id = entity_id
        self.db = Database()  # Создаем экземпляр
        self.original_inn = None
        self.original_phone = None

        self.setWindowTitle(
            "Добавить юридическое лицо"
            if not entity_id
            else "Редактировать юридическое лицо"
        )
        self.setModal(True)
        self.setMinimumWidth(450)
        self.init_ui()
        if entity_id:
            self.load_data()

    def init_ui(self):
        layout = QFormLayout(self)  # Родитель

        self.name_input = QLineEdit()
        self.address_input = QTextEdit()
        self.address_input.setAcceptRichText(False)
        self.address_input.setFixedHeight(60)
        self.inn_input = QLineEdit()
        # Маска для ИНН (10 или 12 цифр). Пробелы в маске игнорируются при вводе.
        # Но валидацию длины все равно делаем.
        # self.inn_input.setInputMask("9999999999;_") # _ позволяет вводить меньше цифр, но нам нужно точно 10 или 12
        self.phone_input = QLineEdit()
        # Пример маски для телефона РФ
        # self.phone_input.setInputMask("+7 (999) 999-99-99;_")
        self.status_check = QCheckBox("Активно")
        self.status_check.setChecked(True)

        layout.addRow("Название*:", self.name_input)
        layout.addRow("Адрес*:", self.address_input)
        layout.addRow("ИНН*:", self.inn_input)
        layout.addRow("Телефон:", self.phone_input)
        layout.addRow("Статус:", self.status_check)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(
            self.accept_data
        )  # Используем accept_data для валидации
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)
        self.name_input.setFocus()  # Фокус на первом поле

    def load_data(self):
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_ENTITY_BY_ID, (self.entity_id,))
                    entity = cursor.fetchone()
                    if not entity:
                        QMessageBox.critical(
                            self, "Ошибка", "Юридическое лицо не найдено."
                        )
                        # Нужно корректно закрыть диалог в случае ошибки
                        # self.reject() не сработает до показа окна, используем done()
                        # Лучше просто вернуть управление, кнопка OK не сработает без данных
                        self.findChild(QDialogButtonBox).button(
                            QDialogButtonBox.Ok
                        ).setEnabled(False)
                        return

                    # entity_id, entity_name, address, inn, phone_number, status
                    self.name_input.setText(entity[1])
                    self.address_input.setPlainText(entity[2])
                    self.inn_input.setText(entity[3])
                    self.phone_input.setText(entity[4] if entity[4] else "")
                    self.status_check.setChecked(entity[5])

                    self.original_inn = entity[3]
                    self.original_phone = entity[4]

        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось загрузить данные:\n{db_err}"
            )
            # Блокируем кнопку OK
            self.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok).setEnabled(
                False
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка загрузки", f"Не удалось загрузить данные:\n{str(e)}"
            )
            self.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok).setEnabled(
                False
            )

    def get_data(self):
        name = self.name_input.text().strip()
        address = self.address_input.toPlainText().strip()
        inn = self.inn_input.text().strip()
        phone = self.phone_input.text().strip() or None
        status = self.status_check.isChecked()
        return name, address, inn, phone, status

    def accept_data(self):
        name, address, inn, phone, status = self.get_data()

        # Валидация
        errors = []
        if not name:
            errors.append("Название не может быть пустым.")
        if not address:
            errors.append("Адрес не может быть пустым.")
        if not inn:
            errors.append("ИНН не может быть пустым.")
        elif not (len(inn) == 10 or len(inn) == 12) or not inn.isdigit():
            errors.append("ИНН должен состоять из 10 или 12 цифр.")
        # Добавить валидацию формата телефона, если нужно

        if errors:
            QMessageBox.warning(self, "Ошибка ввода", "\n".join(errors))
            # Установка фокуса на первое ошибочное поле (упрощенно)
            if not name:
                self.name_input.setFocus()
            elif not address:
                self.address_input.setFocus()
            elif not inn:
                self.inn_input.setFocus()
            return

        # Проверка уникальности ИНН и телефона
        unique_errors = []
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Проверка ИНН (если изменился или новая запись)
                    if inn != self.original_inn:
                        cursor.execute(
                            Queries.CHECK_ENTITY_INN_EXISTS,
                            (inn, self.entity_id, self.entity_id),
                        )
                        if cursor.fetchone():
                            unique_errors.append(
                                f"Юридическое лицо с ИНН '{inn}' уже существует."
                            )
                    # Проверка телефона (если введен и изменился или новая запись)
                    if phone and phone != self.original_phone:
                        cursor.execute(
                            Queries.CHECK_ENTITY_PHONE_EXISTS,
                            (phone, self.entity_id, self.entity_id),
                        )
                        if cursor.fetchone():
                            unique_errors.append(
                                f"Юридическое лицо с телефоном '{phone}' уже существует."
                            )

            if unique_errors:
                QMessageBox.warning(self, "Ошибка ввода", "\n".join(unique_errors))
                if f"ИНН '{inn}'" in unique_errors[0]:
                    self.inn_input.setFocus()
                elif f"телефоном '{phone}'" in unique_errors[0]:
                    self.phone_input.setFocus()
                return

        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self,
                "Ошибка проверки",
                f"Ошибка БД при проверке уникальности:\n{db_err}",
            )
            return
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка проверки",
                f"Не удалось проверить уникальность данных:\n{str(e)}",
            )
            return

        # Если все проверки пройдены
        super().accept()  # Вызываем родной accept, который закроет диалог
