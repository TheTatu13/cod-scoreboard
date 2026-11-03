-- Stratul RAW din PostgreSQL: copie fidelă a sursei, fără curățare.
-- Reguli: nicio transformare, niciun FK, duplicatele din feed se păstrează (le tratează dbt mai târziu).
-- Fișierul e idempotent (IF NOT EXISTS). Îl rulează `cod.ingest`, cu search_path pe schema țintă.

-- ---------- copii ale tabelelor din MySQL (upsert pe cheia primară) ----------
CREATE TABLE IF NOT EXISTS game (
    game_id integer PRIMARY KEY,
    name text, release_year smallint, studio text,
    _ingested_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS map (
    map_id integer PRIMARY KEY,
    name text, game_id integer, size_category text, design_style text, image_url text,
    _ingested_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS weapon (
    weapon_id integer PRIMARY KEY,
    name text, category text,
    _ingested_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS weapon_game (
    weapon_id integer, game_id integer,
    _ingested_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (weapon_id, game_id)
);
CREATE TABLE IF NOT EXISTS team (
    team_id integer PRIMARY KEY,
    name text,
    _ingested_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS player (
    player_id integer PRIMARY KEY,
    gamertag text, platform text, created_at timestamp, archetype text,
    _ingested_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS match (
    match_id integer PRIMARY KEY,
    map_id integer, mode text, started_at timestamp, duration_sec integer,
    winner_team_id integer,
    _ingested_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_match_started_at ON match (started_at);
CREATE TABLE IF NOT EXISTS match_player (
    match_id integer, player_id integer,
    team_id integer, kills integer, deaths integer, assists integer, score integer,
    _ingested_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (match_id, player_id)
);

-- ---------- feed-ul de evenimente (JSON, partiționat pe ziua de LIVRARE) ----------
-- payload = linia JSON exact cum a venit (jsonb), deci schimbările de schemă nu strică încărcarea.
-- (dt, line_no) identifică un rând: o rulare repetată pe aceeași zi dă exact aceleași rânduri.
CREATE TABLE IF NOT EXISTS kill_event (
    dt date NOT NULL,
    line_no integer NOT NULL,
    event_id text,
    payload jsonb NOT NULL,
    source_file text NOT NULL,
    run_id bigint NOT NULL,
    _ingested_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (dt, line_no)
);
CREATE INDEX IF NOT EXISTS idx_kill_event_event_id ON kill_event (event_id);

-- Liniile care nu sunt JSON valid nu se pierd și nu opresc rularea: merg aici.
CREATE TABLE IF NOT EXISTS kill_event_rejected (
    dt date NOT NULL,
    line_no integer NOT NULL,
    line text,
    error text,
    source_file text NOT NULL,
    run_id bigint NOT NULL,
    _ingested_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (dt, line_no)
);

-- ---------- evidența rulărilor și watermark ----------
CREATE TABLE IF NOT EXISTS ingest_run (
    run_id bigserial PRIMARY KEY,
    source text NOT NULL,           -- 'feed.kills' sau 'mysql.match'
    day date NOT NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    rows_read integer,
    rows_loaded integer,
    rows_rejected integer,
    status text NOT NULL DEFAULT 'running'   -- running | ok | failed
);
-- Ultima zi încărcată cu succes, per sursă. Nu se mișcă niciodată înapoi.
CREATE TABLE IF NOT EXISTS ingest_watermark (
    source text PRIMARY KEY,
    last_day date NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);
