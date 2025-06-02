from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QDialogButtonBox,
    QMessageBox,
    QCheckBox,
)
from PyQt5.QtCore import QDate, Qt, QVariant  # QVariant нужен? Вроде нет

# Используем КЛАССЫ
from database.db import Database
from database.queries import Queries
import psycopg2


class RegistrarDialog(QDialog):
    # Убрали entity_tab_ref, т.к. он не используется
    def __init__(self, parent=None, registrar_id=None):
        super().__init__(parent)
        self.registrar_id = registrar_id
        self.db = Database()  # Экземпляр
        self.original_license_num = None
        self.original_entity_id = None  # Запомним ЮЛ для режима редактирования

        self.setWindowTitle(
            "Добавить регистратора"
            if not registrar_id
            else "Редактировать регистратора"
        )
        self.setMinimumWidth(400)
        self.init_ui()
        # Загружаем комбо ЮЛ только при ДОБАВЛЕНИИ
        if not registrar_id:
            self.load_available_entities_combo()
        # Загружаем данные, если РЕДАКТИРОВАНИЕ
        if registrar_id:
            self.load_data()

    def init_ui(self):
        layout = QFormLayout(self)  # Родитель

        self.entity_combo = QComboBox()
        self.entity_combo.setToolTip("Выберите юр. лицо")
        # Блокируем комбо по умолчанию (разблокируется при добавлении или если есть выбор)
        self.entity_combo.setEnabled(False)

        self.license_num_input = QLineEdit()
        self.license_num_input.setToolTip("Уникальный номер лицензии")
        self.license_expiry_date_edit = QDateEdit()  # Без даты по умолчанию
        self.license_expiry_date_edit.setCalendarPopup(True)
        self.license_expiry_date_edit.setSpecialValueText(" ")  # Пустая строка для NULL
        self.license_expiry_date_edit.setDate(QDate())  # Ставим пустую дату
        self.license_expiry_date_edit.setMinimumDate(QDate(1990, 1, 1))
        self.license_expiry_date_edit.setEnabled(
            False
        )  # Включится, если убрать галку "бессрочно"

        self.no_expiry_check = QCheckBox("Лицензия бессрочная")
        self.no_expiry_check.setChecked(
            True
        )  # По умолчанию бессрочная = дата не активна
        self.no_expiry_check.stateChanged.connect(self.toggle_expiry_date)

        layout.addRow("Юридическое лицо*:", self.entity_combo)
        layout.addRow("Номер лицензии*:", self.license_num_input)
        layout.addRow("", self.no_expiry_check)  # Чекбокс сразу под лицензией
        layout.addRow("Срок действия до:", self.license_expiry_date_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_data)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def toggle_expiry_date(self, state):
        is_enabled = not (state == Qt.Checked)
        self.license_expiry_date_edit.setEnabled(is_enabled)
        if not is_enabled:
            # При установке галки "бессрочно", сбрасываем дату
            self.license_expiry_date_edit.setDate(QDate())

    def load_available_entities_combo(self):
        """Загружает список ДОСТУПНЫХ юр. лиц для *нового* регистратора"""
        self.entity_combo.clear()
        ok_button = self.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok)
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_AVAILABLE_ENTITIES_FOR_REGISTRAR)
                    entities = cursor.fetchall()
                    if not entities:
                        self.entity_combo.addItem("Нет доступных юр. лиц", None)
                        self.entity_combo.setEnabled(False)
                        if ok_button:
                            ok_button.setEnabled(False)  # Блокируем ОК
                    else:
                        self.entity_combo.setEnabled(True)
                        self.entity_combo.addItem("--- Выберите юр. лицо ---", None)
                        for entity_id, name in entities:
                            self.entity_combo.addItem(name, entity_id)
                        if ok_button:
                            ok_button.setEnabled(True)  # Разблокируем ОК

        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось загрузить список юр. лиц:\n{db_err}"
            )
            if ok_button:
                ok_button.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка", f"Не удалось загрузить список юр. лиц:\n{str(e)}"
            )
            if ok_button:
                ok_button.setEnabled(False)

    def load_data(self):
        """Загружает данные существующего регистратора для редактирования"""
        ok_button = self.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok)
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_REGISTRAR_BY_ID, (self.registrar_id,))
                    registrar_data = cursor.fetchone()
                    if not registrar_data:
                        QMessageBox.critical(self, "Ошибка", "Регистратор не найден.")
                        if ok_button:
                            ok_button.setEnabled(False)
                        return

                    _, entity_id, license_num, expiry_date = registrar_data
                    self.original_license_num = license_num
                    self.original_entity_id = entity_id  # Запоминаем ID ЮЛ

                    # Получаем имя связанного ЮЛ
                    cursor.execute(Queries.GET_ENTITY_BY_ID, (entity_id,))
                    entity_data = cursor.fetchone()
                    entity_name = (
                        entity_data[1] if entity_data else f"ЮЛ ID {entity_id}"
                    )

                    # Загружаем только одно ЮЛ в комбо и блокируем его
                    self.entity_combo.clear()
                    self.entity_combo.addItem(entity_name, entity_id)
                    self.entity_combo.setEnabled(
                        False
                    )  # Блокируем выбор ЮЛ при редактировании

                    self.license_num_input.setText(license_num)

                    if expiry_date:
                        self.no_expiry_check.setChecked(
                            False
                        )  # Убираем галку "бессрочно"
                        self.license_expiry_date_edit.setEnabled(
                            True
                        )  # Активируем поле даты
                        self.license_expiry_date_edit.setDate(QDate(expiry_date))
                    else:
                        self.no_expiry_check.setChecked(
                            True
                        )  # Ставим галку "бессрочно"
                        self.license_expiry_date_edit.setEnabled(
                            False
                        )  # Деактивируем поле даты
                        self.license_expiry_date_edit.setDate(
                            QDate()
                        )  # Сбрасываем дату

                    if ok_button:
                        ok_button.setEnabled(True)  # Разблокируем кнопку ОК

        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось загрузить данные:\n{db_err}"
            )
            if ok_button:
                ok_button.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка загрузки",
                f"Не удалось загрузить данные регистратора:\n{str(e)}",
            )
            if ok_button:
                ok_button.setEnabled(False)

    def get_data(self):
        # При редактировании entity_id берем из сохраненного, т.к. комбо заблокирован
        entity_id = (
            self.original_entity_id
            if self.registrar_id
            else self.entity_combo.currentData()
        )
        license_num = self.license_num_input.text().strip()
        expiry_date = None
        if not self.no_expiry_check.isChecked():
            qdate = self.license_expiry_date_edit.date()
            # Проверяем, что дата валидна и не пустая (не QDate())
            if qdate.isValid() and not qdate.isNull():
                expiry_date = qdate.toPyDate()

        return entity_id, license_num, expiry_date

    def accept_data(self):
        entity_id, license_num, expiry_date = self.get_data()

        errors = []
        # 1. Проверка выбора ЮЛ (только при добавлении)
        if not self.registrar_id and entity_id is None:
            errors.append("Необходимо выбрать юридическое лицо.")
        # 2. Проверка номера лицензии
        if not license_num:
            errors.append("Необходимо указать номер лицензии.")
        # 3. Проверка даты (если чекбокс снят, дата должна быть выбрана)
        if not self.no_expiry_check.isChecked() and expiry_date is None:
            errors.append("Необходимо указать дату окончания срока действия лицензии.")

        if errors:
            QMessageBox.warning(self, "Ошибка ввода", "\n".join(errors))
            # Фокус на первое ошибочное поле (упрощенно)
            if not self.registrar_id and entity_id is None:
                self.entity_combo.setFocus()
            elif not license_num:
                self.license_num_input.setFocus()
            elif not self.no_expiry_check.isChecked() and expiry_date is None:
                self.license_expiry_date_edit.setFocus()
            return

        # 4. Проверка уникальности номера лицензии
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    if license_num != self.original_license_num:
                        cursor.execute(
                            Queries.CHECK_REGISTRAR_LICENSE_EXISTS,
                            (license_num, self.registrar_id, self.registrar_id),
                        )
                        if cursor.fetchone():
                            QMessageBox.warning(
                                self,
                                "Ошибка ввода",
                                f"Регистратор с номером лицензии '{license_num}' уже существует.",
                            )
                            self.license_num_input.setFocus()
                            return
        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self,
                "Ошибка проверки",
                f"Ошибка БД при проверке уникальности лицензии:\n{db_err}",
            )
            return
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка проверки",
                f"Не удалось проверить уникальность лицензии:\n{str(e)}",
            )
            return

        super().accept()
