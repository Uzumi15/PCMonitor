-- Создаем таблицу для хранения системных метрик
CREATE TABLE IF NOT EXISTS system_metrics (

    -- Уникальный идентификатор каждой записи
    id BIGSERIAL PRIMARY KEY,

    -- Имя компьютера, с которого пришли данные
    hostname VARCHAR(255) NOT NULL,

    -- Загрузка процессора в процентах
    cpu_percent DOUBLE PRECISION NOT NULL
        CHECK (cpu_percent BETWEEN 0 AND 100),

    -- Использование оперативной памяти в процентах
    ram_percent DOUBLE PRECISION NOT NULL
        CHECK (ram_percent BETWEEN 0 AND 100),

    -- Свободное место на системном диске в ГБ
    disk_free_gb DOUBLE PRECISION NOT NULL
        CHECK (disk_free_gb >= 0),

    -- Время работы компьютера в секундах
    uptime_seconds DOUBLE PRECISION NOT NULL
        CHECK (uptime_seconds >= 0),

    -- Дата и время получения данных сервером
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Создаем индекс для быстрого поиска
-- метрик определенного компьютера по времени
CREATE INDEX IF NOT EXISTS idx_metrics_hostname_timestamp
ON system_metrics (hostname, timestamp DESC);
