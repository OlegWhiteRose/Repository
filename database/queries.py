class Queries:
    # --- Users (for Login) ---
    GET_USER_BY_USERNAME = (
        "SELECT user_id, username, password_hash, role FROM users WHERE username = %s"
    )

    # --- Legal Entities ---
    GET_ALL_ENTITIES = """
        SELECT entity_id, entity_name, address, inn, phone_number, status
        FROM legal_entities
        WHERE (LOWER(entity_name) LIKE LOWER(%s) OR %s IS NULL)
          AND (inn LIKE %s OR %s IS NULL)
        ORDER BY entity_name
    """
    GET_ENTITY_BY_ID = "SELECT entity_id, entity_name, address, inn, phone_number, status FROM legal_entities WHERE entity_id = %s"
    ADD_ENTITY = """
        INSERT INTO legal_entities (entity_name, address, inn, phone_number, status)
        VALUES (%s, %s, %s, %s, %s) RETURNING entity_id
    """
    UPDATE_ENTITY = """
        UPDATE legal_entities
        SET entity_name = %s, address = %s, inn = %s, phone_number = %s, status = %s
        WHERE entity_id = %s
    """
    DELETE_ENTITY = "DELETE FROM legal_entities WHERE entity_id = %s"
    GET_ENTITY_LIST = "SELECT entity_id, entity_name FROM legal_entities WHERE status = TRUE ORDER BY entity_name"
    CHECK_ENTITY_INN_EXISTS = """
        SELECT 1 FROM legal_entities WHERE inn = %s AND (%s IS NULL OR entity_id != %s) LIMIT 1
    """
    CHECK_ENTITY_PHONE_EXISTS = """
        SELECT 1 FROM legal_entities WHERE phone_number = %s AND (%s IS NULL OR entity_id != %s) LIMIT 1
    """
    GET_AVAILABLE_ENTITIES_FOR_INVESTOR = """
        SELECT le.entity_id, le.entity_name
        FROM legal_entities le
        LEFT JOIN investors i ON le.entity_id = i.entity_id
        WHERE i.investor_id IS NULL AND le.status = TRUE
        ORDER BY le.entity_name
    """
    GET_AVAILABLE_ENTITIES_FOR_EMITTER = """
        SELECT le.entity_id, le.entity_name
        FROM legal_entities le
        LEFT JOIN emitters e ON le.entity_id = e.entity_id
        WHERE e.emitter_id IS NULL AND le.status = TRUE
        ORDER BY le.entity_name
    """
    GET_AVAILABLE_ENTITIES_FOR_REGISTRAR = """
        SELECT le.entity_id, le.entity_name
        FROM legal_entities le
        LEFT JOIN registrats r ON le.entity_id = r.entity_id
        WHERE r.registrat_id IS NULL AND le.status = TRUE
        ORDER BY le.entity_name
    """

    # --- Investors ---
    GET_INVESTORS = """
        SELECT i.investor_id, l.entity_name, l.inn
        FROM investors i
        JOIN legal_entities l ON i.entity_id = l.entity_id
        WHERE (LOWER(l.entity_name) LIKE LOWER(%s) OR %s IS NULL)
          AND (l.inn LIKE %s OR %s IS NULL)
        ORDER BY l.entity_name
    """
    GET_INVESTOR_BY_ENTITY = "SELECT investor_id FROM investors WHERE entity_id = %s"
    ADD_INVESTOR = "INSERT INTO investors (entity_id) VALUES (%s) RETURNING investor_id"
    DELETE_INVESTOR = "DELETE FROM investors WHERE investor_id = %s"
    GET_INVESTOR_SALES = """
        SELECT s.sell_id, st.ticket, s.sale_date, s.num, s.price
        FROM sells s
        JOIN stocks st ON s.stock_id = st.stock_id
        WHERE s.investor_id = %s
        ORDER BY s.sale_date DESC
    """
    GET_INVESTOR_LIST = """
        SELECT i.investor_id, le.entity_name
        FROM investors i
        JOIN legal_entities le ON i.entity_id = le.entity_id
        ORDER BY le.entity_name
    """

    # --- Emitters ---
    GET_EMITTERS = """
        SELECT e.emitter_id, l.entity_name, l.inn
        FROM emitters e
        JOIN legal_entities l ON e.entity_id = l.entity_id
        WHERE (LOWER(l.entity_name) LIKE LOWER(%s) OR %s IS NULL)
          AND (l.inn LIKE %s OR %s IS NULL)
        ORDER BY l.entity_name
    """
    GET_EMITTER_BY_ENTITY = "SELECT emitter_id FROM emitters WHERE entity_id = %s"
    ADD_EMITTER = "INSERT INTO emitters (entity_id) VALUES (%s) RETURNING emitter_id"
    DELETE_EMITTER = "DELETE FROM emitters WHERE emitter_id = %s"
    GET_EMITTER_LIST = """
        SELECT em.emitter_id, le.entity_name
        FROM emitters em
        JOIN legal_entities le ON em.entity_id = le.entity_id
        WHERE le.status = TRUE -- Только активные эмитенты? Уточнить.
        ORDER BY le.entity_name
    """

    # --- Registrars ---
    GET_REGISTRARS = """
        SELECT r.registrat_id, l.entity_name, l.inn, r.num_licence, r.license_expiry_date
        FROM registrats r
        JOIN legal_entities l ON r.entity_id = l.entity_id
        WHERE (LOWER(l.entity_name) LIKE LOWER(%s) OR %s IS NULL)
          AND (l.inn LIKE %s OR %s IS NULL)
          AND (LOWER(r.num_licence) LIKE LOWER(%s) OR %s IS NULL)
        ORDER BY l.entity_name
    """
    GET_REGISTRAR_BY_ID = "SELECT r.registrat_id, r.entity_id, r.num_licence, r.license_expiry_date FROM registrats r WHERE r.registrat_id = %s"
    ADD_REGISTRAR = """
        INSERT INTO registrats (entity_id, num_licence, license_expiry_date)
        VALUES (%s, %s, %s) RETURNING registrat_id
    """
    UPDATE_REGISTRAR = """
        UPDATE registrats SET entity_id = %s, num_licence = %s, license_expiry_date = %s
        WHERE registrat_id = %s
    """  # entity_id не должен меняться при UPDATE регистратора
    UPDATE_REGISTRAR_DETAILS = """
        UPDATE registrats SET num_licence = %s, license_expiry_date = %s
        WHERE registrat_id = %s
    """  # Используем этот для обновления деталей
    DELETE_REGISTRAR = "DELETE FROM registrats WHERE registrat_id = %s"
    GET_REGISTRAR_LIST = """
        SELECT rg.registrat_id, le.entity_name || ' (Лиц. ' || rg.num_licence || ')'
        FROM registrats rg
        JOIN legal_entities le ON rg.entity_id = le.entity_id
        WHERE le.status = TRUE AND (rg.license_expiry_date IS NULL OR rg.license_expiry_date >= CURRENT_DATE)
        ORDER BY le.entity_name
    """
    CHECK_REGISTRAR_LICENSE_EXISTS = """
        SELECT 1 FROM registrats WHERE num_licence = %s AND (%s IS NULL OR registrat_id != %s) LIMIT 1
    """

    # --- Emissions ---
    GET_EMISSIONS = """
        SELECT ems.emission_id, emt_le.entity_name as emitter_name, ems.value,
               CASE WHEN ems.status THEN 'Активна' ELSE 'Не активна' END as status_text,
               ems.date_register, reg_le.entity_name as registrar_name
        FROM emissions ems
        JOIN emitters emt ON ems.emitter_id = emt.emitter_id
        JOIN legal_entities emt_le ON emt.entity_id = emt_le.entity_id
        JOIN registrats reg ON ems.registrat_id = reg.registrat_id
        JOIN legal_entities reg_le ON reg.entity_id = reg_le.entity_id
        WHERE (LOWER(emt_le.entity_name) LIKE LOWER(%s) OR %s IS NULL)
          AND (LOWER(reg_le.entity_name) LIKE LOWER(%s) OR %s IS NULL)
          AND (ems.status = %s OR %s IS NULL)
          AND (ems.date_register >= %s OR %s IS NULL)
          AND (ems.date_register <= %s OR %s IS NULL)
        ORDER BY ems.date_register DESC
    """
    GET_EMISSION_BY_ID = "SELECT emission_id, value, status, date_register, emitter_id, registrat_id FROM emissions WHERE emission_id = %s"
    ADD_EMISSION = """
        INSERT INTO emissions (value, status, date_register, emitter_id, registrat_id)
        VALUES (%s, %s, %s, %s, %s) RETURNING emission_id
    """
    UPDATE_EMISSION = """
        UPDATE emissions SET value = %s, status = %s, date_register = %s, emitter_id = %s, registrat_id = %s
        WHERE emission_id = %s
    """
    DELETE_EMISSION = "DELETE FROM emissions WHERE emission_id = %s"
    GET_EMISSION_LIST = """
        SELECT e.emission_id, le.entity_name || ' (от ' || e.date_register::text || ' Объем:' || e.value::text || ')'
        FROM emissions e
        JOIN emitters em ON e.emitter_id = em.emitter_id
        JOIN legal_entities le ON em.entity_id = le.entity_id
        -- WHERE e.status = TRUE -- Возможно, стоит показывать все для выбора?
        ORDER BY e.date_register DESC
    """

    # --- Stocks ---
    GET_STOCKS = """
        SELECT s.stock_id, s.ticket, s.nominal_value, em_le.entity_name as emitter_name, e.date_register as emission_date
        FROM stocks s
        JOIN emissions e ON s.emission_id = e.emission_id
        JOIN emitters em ON e.emitter_id = em.emitter_id
        JOIN legal_entities em_le ON em.entity_id = em_le.entity_id
        WHERE (LOWER(s.ticket) LIKE LOWER(%s) OR %s IS NULL)
          AND (LOWER(em_le.entity_name) LIKE LOWER(%s) OR %s IS NULL)
          AND (e.emission_id = %s OR %s IS NULL)
        ORDER BY s.ticket
    """
    GET_STOCK_BY_ID = "SELECT stock_id, ticket, nominal_value, emission_id FROM stocks WHERE stock_id = %s"
    ADD_STOCK = """
        INSERT INTO stocks (ticket, nominal_value, emission_id)
        VALUES (%s, %s, %s) RETURNING stock_id
    """
    UPDATE_STOCK = """
        UPDATE stocks SET ticket = %s, nominal_value = %s, emission_id = %s
        WHERE stock_id = %s
    """
    DELETE_STOCK = "DELETE FROM stocks WHERE stock_id = %s"
    GET_STOCK_LIST = """
        SELECT st.stock_id, st.ticket || ' (' || le.entity_name || ')'
        FROM stocks st
        JOIN emissions em ON st.emission_id = em.emission_id
        JOIN emitters e ON em.emitter_id = e.emitter_id
        JOIN legal_entities le ON e.entity_id = le.entity_id
        ORDER BY st.ticket
    """
    CHECK_STOCK_TICKET_EXISTS = """
        SELECT 1 FROM stocks WHERE ticket = %s AND (%s IS NULL OR stock_id != %s) LIMIT 1
    """

    # --- Sells ---
    GET_SELLS = """
        SELECT sl.sell_id, inv_le.entity_name as investor_name, st.ticket as stock_ticket,
               sl.sale_date, sl.num, sl.price
        FROM sells sl
        JOIN investors inv ON sl.investor_id = inv.investor_id
        JOIN legal_entities inv_le ON inv.entity_id = inv_le.entity_id
        JOIN stocks st ON sl.stock_id = st.stock_id
        WHERE (LOWER(inv_le.entity_name) LIKE LOWER(%s) OR %s IS NULL)
          AND (LOWER(st.ticket) LIKE LOWER(%s) OR %s IS NULL)
          AND (sl.sale_date >= %s OR %s IS NULL)
          AND (sl.sale_date <= %s OR %s IS NULL)
        ORDER BY sl.sale_date DESC
    """
    GET_SELL_BY_ID = "SELECT sell_id, investor_id, stock_id, sale_date, num, price FROM sells WHERE sell_id = %s"
    ADD_SELL = """
        INSERT INTO sells (investor_id, stock_id, sale_date, num, price)
        VALUES (%s, %s, %s, %s, %s) RETURNING sell_id
    """
    UPDATE_SELL = """
        UPDATE sells SET investor_id = %s, stock_id = %s, sale_date = %s, num = %s, price = %s
        WHERE sell_id = %s
    """
    DELETE_SELL = "DELETE FROM sells WHERE sell_id = %s"

    # --- Analytics ---
    GET_EMISSIONS_BY_STATUS = """
        SELECT CASE WHEN status THEN 'Активна' ELSE 'Не активна' END,
               COUNT(*) as count, SUM(value) as total_value
        FROM emissions
        GROUP BY status
        ORDER BY status
    """
    GET_STOCKS_AVG_PRICE = """
        SELECT s.ticket, s.nominal_value, AVG(sl.price) as avg_sell_price, COALESCE(SUM(sl.num), 0) as total_sold
        FROM stocks s
        LEFT JOIN sells sl ON s.stock_id = sl.stock_id
        GROUP BY s.stock_id, s.ticket, s.nominal_value
        ORDER BY s.ticket
    """
    GET_TOP_EMISSIONS_BY_VALUE = """
        SELECT e.emission_id, le.entity_name, e.value, e.date_register
        FROM emissions e
        JOIN emitters em ON e.emitter_id = em.emitter_id
        JOIN legal_entities le ON em.entity_id = le.entity_id
        ORDER BY e.value DESC
        LIMIT %s
    """
    GET_REGISTRAR_EMISSIONS = """
        SELECT reg_le.entity_name as registrar_name, r.num_licence,
               ems.emission_id, emt_le.entity_name as emitter_name, ems.value, ems.date_register
        FROM registrats r
        JOIN legal_entities reg_le ON r.entity_id = reg_le.entity_id
        LEFT JOIN emissions ems ON r.registrat_id = ems.registrat_id
        LEFT JOIN emitters emt ON ems.emitter_id = emt.emitter_id
        LEFT JOIN legal_entities emt_le ON emt.entity_id = emt_le.entity_id
        WHERE r.registrat_id = %s OR %s IS NULL
        ORDER BY reg_le.entity_name, ems.date_register DESC
    """
    GET_INVESTOR_ACTIVITY = """
        SELECT inv_le.entity_name as investor_name, inv_le.inn,
               COUNT(sl.sell_id) as deals_count,
               COALESCE(SUM(sl.num), 0) as total_stocks_bought,
               COALESCE(SUM(sl.num * sl.price), 0) as total_spent
        FROM investors inv
        JOIN legal_entities inv_le ON inv.entity_id = inv_le.entity_id
        LEFT JOIN sells sl ON inv.investor_id = sl.investor_id
        GROUP BY inv.investor_id, inv_le.entity_name, inv_le.inn
        ORDER BY total_spent DESC NULLS LAST
    """
    GET_NEW_EMISSIONS_BY_PERIOD = """
        SELECT ems.emission_id, emt_le.entity_name as emitter_name, ems.value,
               CASE WHEN ems.status THEN 'Активна' ELSE 'Не активна' END as status_text,
               ems.date_register
        FROM emissions ems
        JOIN emitters emt ON ems.emitter_id = emt.emitter_id
        JOIN legal_entities emt_le ON emt.entity_id = emt_le.entity_id
        WHERE ems.date_register BETWEEN %s AND %s
        ORDER BY ems.date_register DESC
    """

    # --- Combined Search ---
    COMBINED_SEARCH = """
       SELECT DISTINCT
           'Сделка' AS result_type,
           sl.sell_id AS id,
           le_inv.entity_name AS investor_name,
           le_inv.inn AS investor_inn,
           s.ticket AS stock_ticker,
           sl.sale_date::text,
           le_em.entity_name AS emitter_name,
           le_reg.entity_name AS registrar_name,
           ems.date_register::text AS emission_date
       FROM sells sl
       LEFT JOIN investors inv ON sl.investor_id = inv.investor_id
       LEFT JOIN legal_entities le_inv ON inv.entity_id = le_inv.entity_id
       LEFT JOIN stocks s ON sl.stock_id = s.stock_id
       LEFT JOIN emissions ems ON s.emission_id = ems.emission_id
       LEFT JOIN emitters emt ON ems.emitter_id = emt.emitter_id
       LEFT JOIN legal_entities le_em ON emt.entity_id = le_em.entity_id
       LEFT JOIN registrats reg ON ems.registrat_id = reg.registrat_id
       LEFT JOIN legal_entities le_reg ON reg.entity_id = le_reg.entity_id
       WHERE
           (LOWER(le_inv.entity_name) LIKE LOWER(%s) OR %s IS NULL) AND
           (le_inv.inn LIKE %s OR %s IS NULL) AND
           (LOWER(le_reg.entity_name) LIKE LOWER(%s) OR %s IS NULL) AND
           (LOWER(le_em.entity_name) LIKE LOWER(%s) OR %s IS NULL) AND
           (LOWER(s.ticket) LIKE LOWER(%s) OR %s IS NULL) AND
           (sl.sale_date >= %s OR %s IS NULL) AND
           (sl.sale_date <= %s OR %s IS NULL)

       UNION ALL

       SELECT DISTINCT
           'Эмиссия' AS result_type,
           ems.emission_id AS id,
           NULL, NULL, NULL, NULL, -- Заглушки для полей сделки
           le_em.entity_name AS emitter_name,
           le_reg.entity_name AS registrar_name,
           ems.date_register::text AS emission_date
       FROM emissions ems
       LEFT JOIN emitters emt ON ems.emitter_id = emt.emitter_id
       LEFT JOIN legal_entities le_em ON emt.entity_id = le_em.entity_id
       LEFT JOIN registrats reg ON ems.registrat_id = reg.registrat_id
       LEFT JOIN legal_entities le_reg ON reg.entity_id = le_reg.entity_id
       WHERE
           (%s IS NULL) AND -- Placeholder для inv_name
           (%s IS NULL) AND -- Placeholder для inv_inn
           (LOWER(le_reg.entity_name) LIKE LOWER(%s) OR %s IS NULL) AND
           (LOWER(le_em.entity_name) LIKE LOWER(%s) OR %s IS NULL) AND
           (%s IS NULL) AND -- Placeholder для ticker
           (ems.date_register >= %s OR %s IS NULL) AND
           (ems.date_register <= %s OR %s IS NULL) AND
           NOT EXISTS (
               SELECT 1
               FROM sells sl_sub -- Используем другие алиасы внутри подзапроса
               JOIN stocks s_sub ON sl_sub.stock_id = s_sub.stock_id
               -- === ДОБАВЛЕННЫЕ JOIN ===
               JOIN investors inv_sub ON sl_sub.investor_id = inv_sub.investor_id
               JOIN legal_entities le_inv_sub ON inv_sub.entity_id = le_inv_sub.entity_id
               -- =======================
               WHERE s_sub.emission_id = ems.emission_id -- Связь с внешней эмиссией
               -- Используем алиасы подзапроса (inv_sub, le_inv_sub, s_sub, sl_sub)
               AND (LOWER(le_inv_sub.entity_name) LIKE LOWER(%s) OR %s IS NULL)
               AND (le_inv_sub.inn LIKE %s OR %s IS NULL)
               AND (LOWER(s_sub.ticket) LIKE LOWER(%s) OR %s IS NULL)
               AND (sl_sub.sale_date >= %s OR %s IS NULL)
               AND (sl_sub.sale_date <= %s OR %s IS NULL)
            )

       ORDER BY result_type, emission_date DESC NULLS LAST, sale_date DESC NULLS LAST
    """
