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
)  # Добавили QSizePolicy
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QColor  # Добавили QColor

# Используем КЛАССЫ
from database.db import Database
from database.queries import Queries

# Относительный импорт диалога из той же папки ui
from .entity_dialog import EntityDialog
import psycopg2


class EntitiesTab(QWidget):
    def __init__(self, user_role):
        super().__init__()
        self.user_role = user_role
        self.is_admin = self.user_role == "admin"
        print(
            f"DEBUG [{self.__class__.__name__}]: Initialized with role '{self.user_role}', is_admin={self.is_admin}"
        )
        self.db = Database()  # Экземпляр для вкладки
        # Таймер для отложенного поиска
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(500)  # 500 мс задержка
        self.search_timer.timeout.connect(self._perform_search)

        self.init_ui()
        self.load_data()  # Первоначальная загрузка данных

    def init_ui(self):
        layout = QVBoxLayout(self)  # Указываем родителя

        # --- Search Bar ---
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_name_input = QLineEdit()
        self.search_name_input.setPlaceholderText("По названию...")
        self.search_name_input.textChanged.connect(self.on_search_text_changed)
        self.search_inn_input = QLineEdit()
        self.search_inn_input.setPlaceholderText("По ИНН...")
        self.search_inn_input.textChanged.connect(self.on_search_text_changed)

        search_layout.addWidget(self.search_name_input)
        search_layout.addWidget(self.search_inn_input)
        self.clear_search_btn = QPushButton()
        # Иконка из стандартных тем Qt (может не везде работать) или fallback
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
        search_layout.addWidget(self.clear_search_btn)
        # search_layout.addStretch(1) # Растягиваем поля поиска

        # --- Toolbar ---
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton(
            QIcon.fromTheme(
                "list-add",
                QIcon(":/qt-project.org/styles/commonstyle/images/file-new-16.png"),
            ),
            " Добавить",
        )
        self.add_btn.setToolTip("Добавить новое юридическое лицо")
        self.add_btn.clicked.connect(self.add_entity)

        self.edit_btn = QPushButton(
            QIcon.fromTheme(
                "document-edit",
                QIcon(":/qt-project.org/styles/commonstyle/images/file-open-16.png"),
            ),
            " Редактировать",
        )
        self.edit_btn.setToolTip("Редактировать выбранное юридическое лицо")
        self.edit_btn.clicked.connect(self.edit_entity)
        self.edit_btn.setEnabled(False)

        self.delete_btn = QPushButton(
            QIcon.fromTheme(
                "edit-delete",
                QIcon(":/qt-project.org/styles/commonstyle/images/edit-delete-16.png"),
            ),
            " Удалить",
        )
        self.delete_btn.setToolTip("Удалить выбранное юридическое лицо")
        self.delete_btn.clicked.connect(self.delete_entity)
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

        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addStretch(1)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Название", "Адрес", "ИНН", "Телефон", "Статус"]
        )
        # Настройка таблицы
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Название растягиваем
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Адрес растягиваем
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # ИНН
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Телефон
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Статус

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(True)

        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        # Добавим реакцию на двойной клик для редактирования
        self.table.doubleClicked.connect(self.edit_entity_on_double_click)

        layout.addLayout(search_layout)
        layout.addLayout(toolbar)
        layout.addWidget(self.table)

    def on_search_text_changed(self):
        self.search_timer.start()

    def _perform_search(self):
        self.load_data()

    def clear_search(self):
        # Блокируем сигналы на время очистки
        self.search_name_input.blockSignals(True)
        self.search_inn_input.blockSignals(True)
        self.search_name_input.clear()
        self.search_inn_input.clear()
        self.search_name_input.blockSignals(False)
        self.search_inn_input.blockSignals(False)
        # Запускаем поиск после очистки
        self.load_data()

    def load_data(self):
        search_name_text = self.search_name_input.text().strip()
        search_inn_text = self.search_inn_input.text().strip()

        name_param = f"%{search_name_text}%" if search_name_text else None
        inn_param = f"%{search_inn_text}%" if search_inn_text else None

        params = (name_param, name_param, inn_param, inn_param)

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_ALL_ENTITIES, params)
                    entities = cursor.fetchall()

                    self.table.setRowCount(0)
                    self.table.setRowCount(len(entities))
                    for row, entity in enumerate(entities):
                        entity_id = entity[0]
                        status = entity[5]

                        # ID (сохраняем в UserRole)
                        id_item = QTableWidgetItem(str(entity_id))
                        id_item.setData(Qt.UserRole, entity_id)
                        self.table.setItem(row, 0, id_item)

                        # Остальные поля
                        self.table.setItem(row, 1, QTableWidgetItem(entity[1]))
                        self.table.setItem(row, 2, QTableWidgetItem(entity[2]))
                        self.table.setItem(row, 3, QTableWidgetItem(entity[3]))
                        self.table.setItem(
                            row, 4, QTableWidgetItem(entity[4] if entity[4] else "-")
                        )

                        # Статус (чекбокс для отображения)
                        status_item = QTableWidgetItem()
                        status_item.setCheckState(
                            Qt.Checked if status else Qt.Unchecked
                        )
                        status_item.setFlags(
                            Qt.ItemIsEnabled
                        )  # Не редактируемый в таблице
                        self.table.setItem(row, 5, status_item)

                        # Подсветка неактивных
                        if not status:
                            for col in range(self.table.columnCount()):
                                item = self.table.item(row, col)
                                if item:
                                    item.setForeground(QColor("gray"))

            self.on_selection_changed()  # Обновляем состояние кнопок

        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось загрузить данные:\n{db_err}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка загрузки", f"Не удалось загрузить юр. лица:\n{str(e)}"
            )
            self.table.setRowCount(0)

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

    def get_selected_id(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            # Получаем ID из UserRole первого столбца
            id_item = self.table.item(selected_rows[0].row(), 0)
            return id_item.data(Qt.UserRole) if id_item else None
        return None

    def add_entity(self):
        dialog = EntityDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            name, address, inn, phone, status = dialog.get_data()
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            Queries.ADD_ENTITY, (name, address, inn, phone, status)
                        )
                        new_id = cursor.fetchone()[0]
                        conn.commit()
                        QMessageBox.information(
                            self,
                            "Успех",
                            f"Юридическое лицо '{name}' успешно добавлено (ID: {new_id}).",
                        )
                        self.load_data()  # Перезагружаем данные
            except psycopg2.OperationalError as db_err:
                QMessageBox.critical(
                    self, "Ошибка БД", f"Не удалось добавить запись:\n{db_err}"
                )
                # Транзакция откатывается автоматически при выходе из 'with' при ошибке
            except Exception as e:
                QMessageBox.critical(
                    self, "Ошибка добавления", f"Не удалось добавить запись:\n{str(e)}"
                )

    def edit_entity_on_double_click(self, index):
        """Вызывает редактирование по двойному клику."""
        # Проверяем, активна ли кнопка редактирования (значит, есть выбор)
        if self.edit_btn.isEnabled():
            self.edit_entity()

    def edit_entity(self):
        entity_id = self.get_selected_id()
        if entity_id is None:
            # Дополнительно проверяем, если вызвано не через двойной клик
            if not self.table.selectionModel().selectedRows():
                QMessageBox.warning(
                    self, "Внимание", "Выберите запись для редактирования."
                )
            return  # Ничего не делаем, если ID не получен

        dialog = EntityDialog(self, entity_id=entity_id)
        if dialog.exec_() == QDialog.Accepted:
            name, address, inn, phone, status = dialog.get_data()
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            Queries.UPDATE_ENTITY,
                            (name, address, inn, phone, status, entity_id),
                        )
                        conn.commit()
                        QMessageBox.information(
                            self,
                            "Успех",
                            f"Данные юр. лица '{name}' (ID: {entity_id}) обновлены.",
                        )
                        self.load_data()
            except psycopg2.OperationalError as db_err:
                QMessageBox.critical(
                    self, "Ошибка БД", f"Не удалось обновить запись:\n{db_err}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Ошибка обновления", f"Не удалось обновить запись:\n{str(e)}"
                )

    def delete_entity(self):
        entity_id = self.get_selected_id()
        if entity_id is None:
            if not self.table.selectionModel().selectedRows():
                QMessageBox.warning(self, "Внимание", "Выберите запись для удаления.")
            return

        # Получаем имя для сообщения
        current_row = self.table.currentRow()
        entity_name_item = self.table.item(current_row, 1)
        entity_name = (
            entity_name_item.text() if entity_name_item else f"ID: {entity_id}"
        )

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить юридическое лицо:\n'{entity_name}' (ID: {entity_id})?\n\n"
            f"ВНИМАНИЕ: Будут удалены ВСЕ связанные данные\n"
            f"(инвесторы, эмитенты, регистраторы, их эмиссии, ЦБ, сделки)\n"
            f"из-за каскадного удаления в БД!",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )

        if reply == QMessageBox.Yes:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(Queries.DELETE_ENTITY, (entity_id,))
                        conn.commit()
                        QMessageBox.information(
                            self, "Успех", f"Юридическое лицо '{entity_name}' удалено."
                        )
                        self.load_data()
            except psycopg2.OperationalError as db_err:
                QMessageBox.critical(
                    self, "Ошибка БД", f"Не удалось удалить запись:\n{db_err}"
                )
            except psycopg2.Error as db_err:  # Ловим другие ошибки БД (например, ограничения внешних ключей, если нет каскада)
                QMessageBox.critical(
                    self,
                    "Ошибка при удалении",
                    f"Ошибка базы данных (возможно, есть связанные записи?):\n{db_err.pgcode} - {db_err.pgerror}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Ошибка при удалении", f"Произошла ошибка:\n{str(e)}"
                )
