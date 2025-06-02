from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QDialogButtonBox,
    QMessageBox,
    QCheckBox,
    QSpinBox,
)
from PyQt5.QtCore import QDate, Qt

# Используем КЛАССЫ
from database.db import Database
from database.queries import Queries
import psycopg2


class EmissionDialog(QDialog):
    def __init__(self, parent=None, emission_id=None):
        super().__init__(parent)
        self.emission_id = emission_id
        self.db = Database()  # Экземпляр

        self.setWindowTitle(
            "Добавить эмиссию" if not emission_id else "Редактировать эмиссию"
        )
        self.setMinimumWidth(450)
        self.init_ui()
        # Загружаем комбобоксы сразу
        self.load_combos()

        if emission_id:
            self.load_data()
        else:
            # Устанавливаем фокус на первое поле для удобства
            self.emitter_combo.setFocus()

    def init_ui(self):
        layout = QFormLayout(self)  # Родитель

        self.emitter_combo = QComboBox()
        self.emitter_combo.setToolTip("Выберите эмитента данной эмиссии")
        self.registrar_combo = QComboBox()
        self.registrar_combo.setToolTip(
            "Выберите активного регистратора для этой эмиссии"
        )
        self.value_spinbox = QSpinBox()
        self.value_spinbox.setRange(1, 2147483647)
        self.value_spinbox.setSuffix(" шт.")  # Убрал "у.е." - обычно объем в штуках ЦБ
        self.value_spinbox.setGroupSeparatorShown(True)
        self.value_spinbox.setMaximumWidth(150)
        self.value_spinbox.setAlignment(Qt.AlignRight)  # Выравнивание
        self.register_date_edit = QDateEdit(QDate.currentDate())
        self.register_date_edit.setCalendarPopup(True)
        self.register_date_edit.setMaximumDate(QDate.currentDate())  # Максимум сегодня
        self.register_date_edit.setDisplayFormat("yyyy-MM-dd")  # Явный формат
        self.status_check = QCheckBox("Активна")
        self.status_check.setChecked(True)
        self.status_check.setToolTip("Отметьте, если эмиссия является активной")

        layout.addRow("Эмитент*:", self.emitter_combo)
        layout.addRow("Регистратор*:", self.registrar_combo)
        layout.addRow("Объем эмиссии (шт)*:", self.value_spinbox)
        layout.addRow("Дата регистрации*:", self.register_date_edit)
        layout.addRow("Статус:", self.status_check)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_data)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def load_combos(self):
        """Загружает списки активных эмитентов и регистраторов."""
        ok_button = self.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok)
        emitter_ok = False
        registrar_ok = False

        # --- Эмитенты ---
        self.emitter_combo.clear()
        self.emitter_combo.addItem("--- Выберите эмитента ---", None)
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        Queries.GET_EMITTER_LIST
                    )  # Запрос должен выбирать активных
                    emitters = cursor.fetchall()
                    if emitters:
                        emitter_ok = True
                        for em_id, name in emitters:
                            self.emitter_combo.addItem(name, em_id)
                    else:
                        self.emitter_combo.addItem("Нет активных эмитентов", None)
                        self.emitter_combo.setEnabled(False)

        except Exception as e:
            QMessageBox.warning(
                self, "Ошибка БД", f"Не удалось загрузить эмитентов:\n{str(e)}"
            )
            self.emitter_combo.setEnabled(False)

        # --- Регистраторы ---
        self.registrar_combo.clear()
        self.registrar_combo.addItem("--- Выберите регистратора ---", None)
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Запрос должен выбирать активных с действующей лицензией
                    cursor.execute(Queries.GET_REGISTRAR_LIST)
                    registrars = cursor.fetchall()
                    if registrars:
                        registrar_ok = True
                        for reg_id, name in registrars:
                            self.registrar_combo.addItem(name, reg_id)
                    else:
                        self.registrar_combo.addItem("Нет активных регистраторов", None)
                        self.registrar_combo.setEnabled(False)

        except Exception as e:
            QMessageBox.warning(
                self, "Ошибка БД", f"Не удалось загрузить регистраторов:\n{str(e)}"
            )
            self.registrar_combo.setEnabled(False)

        # Блокируем кнопку OK, если нет эмитентов или регистраторов
        if ok_button:
            ok_button.setEnabled(emitter_ok and registrar_ok)

    def load_data(self):
        """Загружает данные существующей эмиссии."""
        ok_button = self.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok)
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_EMISSION_BY_ID, (self.emission_id,))
                    emission_data = cursor.fetchone()
                    if not emission_data:
                        QMessageBox.critical(self, "Ошибка", "Эмиссия не найдена.")
                        if ok_button:
                            ok_button.setEnabled(False)
                        return

                    _, value, status, date_reg, emitter_id, registrat_id = emission_data

                    # Устанавливаем значения в комбо-боксах
                    emitter_index = self.emitter_combo.findData(emitter_id)
                    if emitter_index != -1:
                        self.emitter_combo.setCurrentIndex(emitter_index)
                    else:  # Если эмитент стал неактивным
                        # Нужно получить его имя по ID и временно добавить в список
                        cursor.execute(
                            Queries.GET_ENTITY_BY_ID, (emitter_id,)
                        )  # Имя эмитента = имя ЮЛ
                        entity_data = cursor.fetchone()
                        emitter_name = (
                            entity_data[1]
                            if entity_data
                            else f"Эмитент ID {emitter_id}"
                        )
                        self.emitter_combo.insertItem(
                            1, f"{emitter_name} (ЮЛ неактивно?)", emitter_id
                        )
                        self.emitter_combo.setCurrentIndex(1)
                        QMessageBox.warning(
                            self,
                            "Внимание",
                            f"Выбранный эмитент '{emitter_name}' может быть неактивен.",
                        )

                    registrar_index = self.registrar_combo.findData(registrat_id)
                    if registrar_index != -1:
                        self.registrar_combo.setCurrentIndex(registrar_index)
                    else:  # Если регистратор стал неактивным/просрочен
                        cursor.execute(Queries.GET_REGISTRAR_BY_ID, (registrat_id,))
                        reg_data = cursor.fetchone()
                        if reg_data:
                            cursor.execute(Queries.GET_ENTITY_BY_ID, (reg_data[1],))
                            entity_data = cursor.fetchone()
                            reg_name = (
                                entity_data[1]
                                if entity_data
                                else f"Регистратор ID {registrat_id}"
                            )
                            license_num = reg_data[2]
                            self.registrar_combo.insertItem(
                                1,
                                f"{reg_name} (Лиц. {license_num} - Неактивен?)",
                                registrat_id,
                            )
                            self.registrar_combo.setCurrentIndex(1)
                            QMessageBox.warning(
                                self,
                                "Внимание",
                                f"Выбранный регистратор '{reg_name}' может быть неактивен или его лицензия просрочена.",
                            )

                    self.value_spinbox.setValue(value)
                    self.register_date_edit.setDate(QDate(date_reg))
                    self.status_check.setChecked(status)

                    if ok_button:
                        ok_button.setEnabled(
                            True
                        )  # Разблокируем, если данные загружены

        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось загрузить данные эмиссии:\n{db_err}"
            )
            if ok_button:
                ok_button.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка загрузки",
                f"Не удалось загрузить данные эмиссии:\n{str(e)}",
            )
            if ok_button:
                ok_button.setEnabled(False)

    def get_data(self):
        emitter_id = self.emitter_combo.currentData()
        registrar_id = self.registrar_combo.currentData()
        value = self.value_spinbox.value()
        date_reg = self.register_date_edit.date().toPyDate()
        status = self.status_check.isChecked()
        return emitter_id, registrar_id, value, date_reg, status

    def accept_data(self):
        emitter_id, registrar_id, value, date_reg, status = self.get_data()

        errors = []
        if emitter_id is None:
            errors.append("Необходимо выбрать эмитента.")
        if registrar_id is None:
            errors.append("Необходимо выбрать регистратора.")
        if value <= 0:
            errors.append("Объем эмиссии должен быть положительным.")
        # Проверка даты не нужна, т.к. QDateEdit всегда валидна

        if errors:
            QMessageBox.warning(self, "Ошибка ввода", "\n".join(errors))
            if emitter_id is None:
                self.emitter_combo.setFocus()
            elif registrar_id is None:
                self.registrar_combo.setFocus()
            elif value <= 0:
                self.value_spinbox.setFocus()
            return

        # Можно добавить проверку на уникальность эмиссии (Эмитент + Регистратор + Дата)?
        # Зависит от требований. В вашей схеме такой уникальности нет.

        super().accept()
