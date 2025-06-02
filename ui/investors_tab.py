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

# Относительный импорт диалога
from .investor_sales_dialog import InvestorSalesDialog
import psycopg2


class InvestorsTab(QWidget):
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

        # Инициализируем переменные для зависимостей как None
        self.main_tabs = None
        self.sells_tab_ref = None
        self.entities_tab = None  # Оставляем, если entities_tab все еще нужен здесь

        self.init_ui()
        self.load_data()  # Загрузка данных и комбо-бокса при инициализации

    def set_dependencies(
        self, main_tabs_widget, sells_tab_widget, entities_tab_widget=None
    ):
        """Устанавливает ссылки на главный виджет вкладок и вкладку сделок."""
        self.main_tabs = main_tabs_widget
        self.sells_tab_ref = sells_tab_widget
        self.entities_tab = entities_tab_widget  # Сохраняем, если нужно
        print(
            f"DEBUG [{self.__class__.__name__}]: Dependencies received (main_tabs: {bool(self.main_tabs)}, sells_tab: {bool(self.sells_tab_ref)})"
        )

    def init_ui(self):
        """Инициализирует пользовательский интерфейс вкладки."""
        layout = QVBoxLayout(self)  # Родитель

        # --- Search Bar ---
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_name_input = QLineEdit()
        self.search_name_input.setPlaceholderText("По названию юр. лица...")
        self.search_name_input.textChanged.connect(self.on_search_text_changed)
        self.search_inn_input = QLineEdit()
        self.search_inn_input.setPlaceholderText("По ИНН...")
        self.search_inn_input.textChanged.connect(self.on_search_text_changed)
        self.clear_search_btn = QPushButton()
        # Используем стандартную иконку или запасную
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

        # --- Toolbar ---
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Добавить инвестора:"))
        self.entity_combo = QComboBox()
        self.entity_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.entity_combo.setToolTip("Юр. лица, еще не являющиеся инвесторами")
        self.entity_combo.currentIndexChanged.connect(self.on_combo_selection_changed)

        self.add_btn = QPushButton(QIcon.fromTheme("list-add"), " Добавить")
        self.add_btn.setToolTip("Сделать выбранное юр. лицо инвестором")
        self.add_btn.clicked.connect(self.add_investor)
        self.add_btn.setEnabled(False)  # Активируется выбором в комбо

        self.delete_btn = QPushButton(QIcon.fromTheme("edit-delete"), " Удалить")
        self.delete_btn.setToolTip("Удалить выбранного инвестора (и его сделки)")
        self.delete_btn.clicked.connect(self.delete_investor)
        self.delete_btn.setEnabled(False)  # Активируется выбором в таблице

        self.sales_btn = QPushButton(
            QIcon.fromTheme(
                "view-list-details",
                QIcon(":/qt-project.org/styles/commonstyle/images/file-open-16.png"),
            ),
            " Сделки",
        )
        self.sales_btn.setToolTip("Показать сделки выбранного инвестора")
        self.sales_btn.clicked.connect(self.show_investor_sales)
        self.sales_btn.setEnabled(False)  # Активируется выбором в таблице

        # Новая кнопка для перехода к добавлению сделки
        self.add_sell_btn = QPushButton(QIcon.fromTheme("list-add"), " Доб. сделку")
        self.add_sell_btn.setToolTip(
            "Открыть добавление сделки для выбранного инвестора"
        )
        self.add_sell_btn.clicked.connect(self.go_to_add_sell)
        self.add_sell_btn.setEnabled(
            False
        )  # Активируется выбором в таблице + роль админа

        # Начальное состояние кнопок с учетом роли
        self.add_btn.setEnabled(
            self.is_admin and self.entity_combo.currentData() is not None
        )
        self.delete_btn.setEnabled(False)
        self.sales_btn.setEnabled(False)
        self.add_sell_btn.setEnabled(False)

        toolbar.addWidget(self.entity_combo)
        toolbar.addWidget(self.add_btn)
        toolbar.addStretch(1)  # Отодвигаем кнопки
        toolbar.addWidget(self.delete_btn)
        toolbar.addWidget(self.sales_btn)
        toolbar.addWidget(self.add_sell_btn)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(
            ["ID инвестора", "Название юр. лица", "ИНН"]
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

        # Сигналы таблицы
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.show_investor_sales_on_double_click)

        layout.addLayout(search_layout)
        layout.addLayout(toolbar)
        layout.addWidget(self.table)

        self.load_entities_combo()  # Загружаем комбо при создании UI

    def on_search_text_changed(self):
        """Запускает таймер для отложенного поиска."""
        self.search_timer.start()

    def _perform_search(self):
        """Выполняет загрузку данных (поиск)."""
        self.load_data()

    def clear_search(self):
        """Очищает поля поиска и перезагружает данные."""
        # Блокируем сигналы, чтобы избежать лишних срабатываний load_data
        self.search_name_input.blockSignals(True)
        self.search_inn_input.blockSignals(True)
        self.search_name_input.clear()
        self.search_inn_input.clear()
        self.search_name_input.blockSignals(False)
        self.search_inn_input.blockSignals(False)
        self.load_data()  # Перезагружаем полный список

    def load_entities_combo(self):
        """Загружает список юр. лиц, не являющихся инвесторами, в комбобокс."""
        current_selection_id = self.entity_combo.currentData()
        self.entity_combo.blockSignals(True)
        self.entity_combo.clear()
        self.entity_combo.setEnabled(False)  # По умолчанию недоступен
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_AVAILABLE_ENTITIES_FOR_INVESTOR)
                    entities = cursor.fetchall()
                    if not entities:
                        self.entity_combo.addItem("Нет доступных юр. лиц", None)
                    else:
                        self.entity_combo.setEnabled(
                            self.is_admin
                        )  # Доступен только админу
                        self.entity_combo.addItem("--- Выберите юр. лицо ---", None)
                        for entity_id, name in entities:
                            self.entity_combo.addItem(name, entity_id)
                        # Восстанавливаем выбор, если он был и если комбо доступен
                        if self.is_admin:
                            index = self.entity_combo.findData(current_selection_id)
                            if index != -1:
                                self.entity_combo.setCurrentIndex(index)

        except psycopg2.OperationalError as db_err:
            QMessageBox.warning(
                self, "Ошибка БД", f"Не удалось загрузить список юр. лиц:\n{db_err}"
            )
            self.entity_combo.addItem("Ошибка загрузки", None)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Критическая Ошибка",
                f"Не удалось загрузить список юр. лиц:\n{str(e)}",
            )
            self.entity_combo.addItem("Ошибка загрузки", None)
        finally:
            self.entity_combo.blockSignals(False)
            self.on_combo_selection_changed()  # Обновляем состояние кнопки Добавить

    def on_combo_selection_changed(self):
        """Обновляет состояние кнопки 'Добавить' при изменении выбора в комбобоксе."""
        selected_data = self.entity_combo.currentData()
        can_add = selected_data is not None and self.is_admin
        self.add_btn.setEnabled(can_add)

    def load_data(self):
        """Загружает данные инвесторов в таблицу с учетом фильтров поиска."""
        self.table.blockSignals(True)

        search_name_text = self.search_name_input.text().strip()
        search_inn_text = self.search_inn_input.text().strip()
        name_param = f"%{search_name_text}%" if search_name_text else None
        inn_param = f"%{search_inn_text}%" if search_inn_text else None
        params = (name_param, name_param, inn_param, inn_param)

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.GET_INVESTORS, params)
                    investors = cursor.fetchall()

                    self.table.setRowCount(0)
                    self.table.setRowCount(len(investors))
                    for row, investor in enumerate(investors):
                        investor_id, entity_name, inn = investor

                        # ID (числовой, сохраняем ID и имя в UserRole)
                        id_item = QTableWidgetItem(str(investor_id))
                        id_item.setData(
                            Qt.UserRole, {"id": investor_id, "name": entity_name}
                        )
                        id_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.table.setItem(row, 0, id_item)
                        # Название (строка)
                        name_item = QTableWidgetItem(entity_name)
                        self.table.setItem(row, 1, name_item)
                        # ИНН (строка)
                        inn_item = QTableWidgetItem(inn if inn else "")
                        self.table.setItem(row, 2, inn_item)

            self.on_selection_changed()  # Обновляем состояние кнопок после загрузки

        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось загрузить инвесторов:\n{db_err}"
            )
            self.table.setRowCount(0)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Критическая Ошибка",
                f"Не удалось загрузить инвесторов:\n{str(e)}",
            )
            self.table.setRowCount(0)
        finally:
            self.table.blockSignals(False)
            # Обновляем комбобокс после загрузки данных (чтобы убрать добавленных)
            self.load_entities_combo()

    def on_selection_changed(self):
        """Обновляет состояние кнопок ('Удалить', 'Сделки', 'Доб. сделку') при изменении выбора в таблице."""
        selected_info = self.get_selected_investor_info()
        is_selected = selected_info is not None

        # Включаем Edit/Delete/AddSell ТОЛЬКО если выбрана строка И пользователь админ
        can_manage = is_selected and self.is_admin

        if hasattr(self, "delete_btn"):
            self.delete_btn.setEnabled(can_manage)
        if hasattr(self, "add_sell_btn"):
            self.add_sell_btn.setEnabled(can_manage)
        if hasattr(self, "sales_btn"):
            self.sales_btn.setEnabled(
                is_selected
            )  # Просмотр доступен всем, если выбрано

    def get_selected_investor_info(self):
        """Возвращает словарь {'id': ..., 'name': ...} для выбранного инвестора или None."""
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            id_item = self.table.item(selected_rows[0].row(), 0)
            return id_item.data(Qt.UserRole) if id_item else None
        return None

    def show_investor_sales_on_double_click(self, index):
        """Обрабатывает двойной клик по строке таблицы (если доступно)."""
        if self.sales_btn.isEnabled():
            self.show_investor_sales()

    def show_investor_sales(self):
        """Открывает диалог для просмотра сделок выбранного инвестора."""
        selected_info = self.get_selected_investor_info()
        if not selected_info:
            QMessageBox.warning(
                self, "Внимание", "Сначала выберите инвестора в таблице."
            )
            return

        investor_id = selected_info.get("id")
        investor_name = selected_info.get("name", f"ID: {investor_id}")

        # Передаем ID и имя в диалог сделок
        dialog = InvestorSalesDialog(investor_id, investor_name, self)
        dialog.exec_()

    def go_to_add_sell(self):
        """Переключает на вкладку Сделки и вызывает добавление для выбранного инвестора."""
        selected_info = (
            self.get_selected_investor_info()
        )  # Получаем {'id': ..., 'name': ...}
        if selected_info is None:
            QMessageBox.warning(
                self, "Внимание", "Сначала выберите инвестора в таблице."
            )
            return

        # Проверка наличия зависимостей
        if not self.main_tabs or not self.sells_tab_ref:
            QMessageBox.critical(
                self,
                "Ошибка конфигурации",
                "Зависимости между вкладками не установлены.\n"
                "Обратитесь к разработчику (MainWindow.init_ui).",
            )
            return

        # Проверка наличия метода на целевой вкладке
        if not hasattr(self.sells_tab_ref, "add_sell_preselected"):
            QMessageBox.critical(
                self,
                "Ошибка конфигурации",
                "Метод 'add_sell_preselected' не найден во вкладке 'Сделки'.",
            )
            return

        investor_id = selected_info.get("id")
        investor_name = selected_info.get("name", f"Инвестор ID {investor_id}")
        print(
            f"DEBUG [{self.__class__.__name__}]: go_to_add_sell triggered for Investor ID: {investor_id}, Name: {investor_name}"
        )

        # 1. Переключаемся на вкладку "Сделки"
        self.main_tabs.setCurrentWidget(self.sells_tab_ref)
        print(f"DEBUG [{self.__class__.__name__}]: Switched to SellsTab")

        # 2. Вызываем метод добавления на вкладке Сделки, передавая словарь
        self.sells_tab_ref.add_sell_preselected(selected_info)
        print(
            f"DEBUG [{self.__class__.__name__}]: Called add_sell_preselected on SellsTab"
        )

    def add_investor(self):
        """Добавляет выбранное в комбобоксе юр. лицо в инвесторы."""
        if not self.is_admin:
            return  # Дополнительная проверка

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
            f"Сделать юр. лицо '{entity_name}' инвестором?",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Cancel:
            return

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(Queries.ADD_INVESTOR, (entity_id,))
                    new_investor_id = cursor.fetchone()[0]
                    conn.commit()
                    QMessageBox.information(
                        self,
                        "Успех",
                        f"Инвестор '{entity_name}' (ID: {new_investor_id}) успешно добавлен.",
                    )
                    self.load_data()  # Перезагружаем все
        except psycopg2.OperationalError as db_err:
            QMessageBox.critical(
                self, "Ошибка БД", f"Не удалось добавить инвестора:\n{db_err}"
            )
        except psycopg2.IntegrityError:
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Юридическое лицо '{entity_name}' уже является инвестором.",
            )
            self.load_entities_combo()  # Обновить комбо
        except Exception as e:
            QMessageBox.critical(
                self, "Критическая Ошибка", f"Не удалось добавить инвестора:\n{str(e)}"
            )

    def delete_investor(self):
        """Удаляет выбранного инвестора и связанные с ним сделки."""
        if not self.is_admin:
            return

        selected_info = self.get_selected_investor_info()
        if not selected_info:
            QMessageBox.warning(
                self, "Внимание", "Сначала выберите инвестора для удаления."
            )
            return

        investor_id = selected_info.get("id")
        investor_name = selected_info.get("name", f"ID: {investor_id}")

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить инвестора:\n'{investor_name}' (ID: {investor_id})?\n\n"
            f"ВНИМАНИЕ: Будут удалены все сделки этого инвестора (CASCADE)!".upper(),
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )

        if reply == QMessageBox.Yes:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(Queries.DELETE_INVESTOR, (investor_id,))
                        conn.commit()
                        QMessageBox.information(
                            self, "Успех", f"Инвестор '{investor_name}' удален."
                        )
                        self.load_data()  # Перезагружаем все
            except psycopg2.OperationalError as db_err:
                QMessageBox.critical(
                    self, "Ошибка БД", f"Не удалось удалить инвестора:\n{db_err}"
                )
            except psycopg2.Error as db_err:  # Ловим другие ошибки psycopg2
                QMessageBox.critical(
                    self,
                    "Ошибка при удалении",
                    f"Ошибка базы данных:\n{db_err.pgcode} - {db_err.pgerror}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Критическая Ошибка",
                    f"Не удалось удалить инвестора:\n{str(e)}",
                )
