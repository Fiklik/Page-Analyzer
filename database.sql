DROP TABLE IF EXISTS urls CASCADE;
CREATE TABLE urls (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(255) UNIQUE,
    created_at DATE
);

DROP TABLE IF EXISTS url_checks;
CREATE TABLE url_checks (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    url_id BIGINT REFERENCES urls(id),
    status_code INTEGER,
    h1 TEXT NOT NULL DEFAULT '',
    title TEXT,
    description TEXT,
    created_at DATE
);
