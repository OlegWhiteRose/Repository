from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QAbstractItemView,
    QTableWidgetItem,
    QPushButton,
    QComboBox,
    QHeaderView,
    QMessageBox,
    QLabel,
    QLineEdit,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

# Используем КЛАССЫ
from database.db import Database
from database.queries import Queries
import psycopg2


class EmittersTab(QWidget):
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
        self.load_data()  # Загрузка данных и комбо-бокса

    def init_ui(self):
        layout = QVBoxLayout(self)  # Родитель

        # Search Bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_name_input = QLineEdit()
        self.search_name_input.setPlaceholderText("По названию юр. лица...")
        self.search_name_input.textChanged.connect(self.on_search_text_changed)
        self.search_inn_input = QLineEdit()
        self.search_inn_input.setPlaceholderText("По ИНН...")
        self.search_inn_input.textChanged.connect(self.on_search_text_changed)
        self.clear_search_btn = QPushButton()
        self.clear_search_btn.setIcon(
            QIcon.fromTheme(
                "edit-clear",
                QIcon(
                    ":/qt-project.org/styles/commonstyle/images/standardbutton-cancel-16.png"
                ),
            )
        )
        self.clear_search_btn.setToolTip("Очистить поиск")
        self.clear_search_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(self.search_name_input)
        search_layout.addWidget(self.search_inn_input)
        search_layout.addWidget(self.clear_search_btn)
        # search_layout.addStretch(1)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Добавить эмитента:"))
        self.entity_combo = QComboBox()
        self.entity_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.entity_combo.setToolTip("Юр. лица, еще не являющиеся эмитентами")
        self.entity_combo.currentIndexChanged.connect(self.on_combo_selection_changed)

        self.add_btn = QPushButton(QIcon.fromTheme("list-add"), " Добавить")
        self.add_btn.setToolTip("Сделать выбранное юр. лицо эмитентом")
        self.add_btn.clicked.connect(self.add_emitter)
        self.add_btn.setEnabled(False)

        self.delete_btn = QPushButton(QIcon.fromTheme("edit-delete"), " Удалить")
        self.delete_btn.setToolTip("Удалить выбранного эмитента (и его эмиссии, ЦБ)")
        self.delete_btn.clicked.connect(self.delete_emitter)
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

        toolbar.addWidget(self.entity_combo)
        toolbar.addWidget(self.add_btn)
        toolbar.addStretch(1)  # Отодвигаем кнопку удаления
        toolbar.addWidget(self.delete_btn)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(
            ["ID эмитента", "Название юр. лица", "ИНН"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Название
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # ИНН
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        # Двойной клик здесь не нужен (нет доп. окна)

        layout.addLayout(search_layout)
        layout.addLayout(toolbar)
        layout.addWidget(self.table)

        self.load_entities_combo()  # Загрузка комбо при создании

    def on_search_text_changed(self):
        self.search_timer.start()

    def _perform_search(self):
        self.load_data()

    def clear_search(self):
        self.search_name_input.blockSignals(True)
        self.search_inn_input.blockSignals(True)
        self.search_name_input.clear()
        self.search_inn_input.clear()
        self.search_name_input.blockSignals(False)
        self.search_inn_input.blockSignals(False)
        self.load_data()

    def load_entities_combo(self):
        current_selection_id = self.entity_combo.currentData()
        self.entity_combo.blockSignals(True)
        self.entity_combo.clear()
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_AVAILABLE_ENTITIES_FOR_EMITTER)
                    entities = cursor.fetchall()
                    if not entities:
                        self.entity_combo.addItem("Нет доступных юр. лиц", None)
                        self.entity_combo.setEnabled(False)
                    else:
                        self.entity_combo.setEnabled(True)
                        self.entity_combo.addItem("--- Выберите юр. лицо ---", None)
                        for entity_id, name in entities:
                            self.entity_combo.addItem(name, entity_id)
                        index = self.entity_combo.findData(current_selection_id)
                        if index != -1:
                            self.entity_combo.setCurrentIndex(index)

        except psycopg2.OperationalError as db_err:
            QMessageBox.warning(
                self, "Ошибка БД", f"Не удалось загрузить список юр. лиц:\n{db_err}"
            )
            self.entity_combo.clear()
            self.entity_combo.addItem("Ошибка загрузки", None)
            self.entity_combo.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка", f"Не удалось загрузить список юр. лиц:\n{str(e)}"
            )
            self.entity_combo.clear()
            self.entity_combo.addItem("Ошибка загрузки", None)
            self.entity_combo.setEnabled(False)
        finally:
            self.entity_combo.blockSignals(False)
            self.on_combo_selection_changed()

    def on_combo_selection_changed(self):
        selected_data = self.entity_combo.currentData()
        # Включаем кнопку Добавить ТОЛЬКО если выбран элемент (не None) И пользователь админ
        can_add = selected_data is not None and self.is_admin
        self.add_btn.setEnabled(can_add)

    def load_data(self):
        self.table.blockSignals(True)

        search_name_text = self.search_name_input.text().strip()
        search_inn_text = self.search_inn_input.text().strip()
        name_param = f"%{search_name_text}%" if search_name_text else None
        inn_param = f"%{search_inn_text}%" if search_inn_text else None
        params = (name_param, name_param, inn_param, inn_param)

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_EMITTERS, params)
                    emitters = cursor.fetchall()

                    self.table.setRowCount(0)
                    self.table.setRowCount(len(emitters))
                    for row, emitter in enumerate(emitters):
                        emitter_id = emitter[0]
                        entity_name = emitter[1]
                        inn = emitter[2]

                        # ID (числовой, сохраняем ID и имя)
                        id_item = QTableWidgetItem(str(emitter_id))
                        id_item.setData(
                            Qt.UserRole, {"id": emitter_id, "name": entity_name}
                        )
                        id_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.table.setItem(row, 0, id_item)
                        # Название
                        self.table.setItem(row, 1, QTableWidgetItem(entity_name))
                        # ИНН
                        self.table.setItem(row, 2, QTableWidgetItem(inn))

            self.load_entities_combo()  # Обновляем комбо
            self.on_selection_changed()  # Обновляем кнопки

        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось загрузить эмитентов:\n{db_err}"
            )
            self.table.setRowCount(0)
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка загрузки", f"Не удалось загрузить эмитентов:\n{str(e)}"
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

    def get_selected_emitter_info(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            id_item = self.table.item(selected_rows[0].row(), 0)
            return id_item.data(Qt.UserRole) if id_item else None
        return None

    def add_emitter(self):
        entity_id = self.entity_combo.currentData()
        if not entity_id:
            QMessageBox.warning(
                self, "Внимание", "Выберите юридическое лицо из выпадающего списка."
            )
            return
        entity_name = self.entity_combo.currentText()

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Сделать юридическое лицо '{entity_name}' эмитентом?",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Cancel:
            return

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.ADD_EMITTER, (entity_id,))
                    new_emitter_id = cursor.fetchone()[0]
                    conn.commit()
                    QMessageBox.information(
                        self,
                        "Успех",
                        f"Эмитент '{entity_name}' (ID: {new_emitter_id}) успешно добавлен.",
                    )
                    self.load_data()
        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось добавить эмитента:\n{db_err}"
            )
        except psycopg2.IntegrityError:
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Юридическое лицо '{entity_name}' уже является эмитентом.",
            )
            self.load_entities_combo()
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка добавления", f"Не удалось добавить эмитента:\n{str(e)}"
            )

    def delete_emitter(self):
        selected_info = self.get_selected_emitter_info()
        if not selected_info:
            return

        emitter_id = selected_info.get("id")
        emitter_name = selected_info.get("name", f"ID: {emitter_id}")

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить эмитента:\n'{emitter_name}' (ID: {emitter_id})?\n\n"
            f"ВНИМАНИЕ: Будут удалены ВСЕ его эмиссии и связанные ЦБ!",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )

        if reply == QMessageBox.Yes:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(Queries.DELETE_EMITTER, (emitter_id,))
                        conn.commit()
                        QMessageBox.information(
                            self, "Успех", f"Эмитент '{emitter_name}' удален."
                        )
                        self.load_data()
            except psycopg2.OperationalError as db_err:
                QMessageBox.critical(
                    self, "Ошибка БД", f"Не удалось удалить эмитента:\n{db_err}"
                )
            except psycopg2.Error as db_err:
                QMessageBox.critical(
                    self,
                    "Ошибка при удалении",
                    f"Ошибка базы данных:\n{db_err.pgcode} - {db_err.pgerror}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка при удалении",
                    f"Не удалось удалить эмитента:\n{str(e)}",
                )
