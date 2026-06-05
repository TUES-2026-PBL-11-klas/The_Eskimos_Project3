-- events_fixture.sql
-- LOCAL / TEST-ONLY — this is NOT the production source of truth.
-- Used by integration tests (testcontainers throwaway postgres) and local ad-hoc runs to give
-- the API a readable events database without needing the ingestion service running.
--
-- Mirrors the ingestion schema after migration 0002 (trimmed shape):
--   sources, venues, categories, events  (no tags, no end_at, no price columns)
-- Also creates the events_reader role + grants exactly as migration 0001 does, so integration
-- tests that verify SELECT-only enforcement work against this fixture too.

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ─── Sources ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sources (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    type        VARCHAR(16)  NOT NULL CHECK (type IN ('api', 'scraper')),
    base_url    VARCHAR(500),
    last_run_at TIMESTAMPTZ,
    CONSTRAINT uq_sources_name UNIQUE (name)
);

-- ─── Venues ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS venues (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(120)
);

-- ─── Categories ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS categories (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    CONSTRAINT uq_categories_slug UNIQUE (slug)
);

-- ─── Events ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS events (
    id          SERIAL PRIMARY KEY,
    source_id   INT          NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    external_id VARCHAR(255) NOT NULL,
    title       VARCHAR(500) NOT NULL,
    description TEXT,
    start_at    TIMESTAMPTZ  NOT NULL,
    venue_id    INT          REFERENCES venues(id),
    category_id INT          REFERENCES categories(id),
    url         VARCHAR(1000) NOT NULL,
    dedup_key   VARCHAR(500) NOT NULL,
    raw_payload JSONB        NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT uq_events_source_external UNIQUE (source_id, external_id)
);

CREATE INDEX IF NOT EXISTS ix_events_start_at          ON events (start_at);
CREATE INDEX IF NOT EXISTS ix_events_category_start_at ON events (category_id, start_at);
CREATE INDEX IF NOT EXISTS ix_events_dedup_key         ON events (dedup_key);
CREATE INDEX IF NOT EXISTS ix_events_title_trgm        ON events USING GIN (title gin_trgm_ops);

-- ─── Read-only role (mirrors migration 0001) ────────────────────────────────
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'events_reader') THEN
    CREATE ROLE events_reader NOLOGIN;
  END IF;
END $$;
GRANT USAGE ON SCHEMA public TO events_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO events_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO events_reader;

-- ─── API login role — inherits SELECT-only from events_reader ────────────────
-- In production this is a LOGIN role; here it is NOLOGIN because the enforcement test
-- adopts it via SET ROLE from the superuser connection, avoiding host auth complexity.
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'events_api') THEN
    CREATE ROLE events_api NOLOGIN INHERIT;
  END IF;
END $$;
GRANT events_reader TO events_api;

-- ─── Reference data ─────────────────────────────────────────────────────────
INSERT INTO sources (name, type, base_url) VALUES
    ('fixture_scraper', 'scraper', 'https://example.com'),
    ('fixture_api',     'api',     'https://api.example.com')
ON CONFLICT (name) DO NOTHING;

INSERT INTO venues (name, city) VALUES
    ('National Palace of Culture', 'Sofia'),
    ('Sofia Opera and Ballet',     'Sofia'),
    ('Arena Sofia',                'Sofia'),
    ('City Art Gallery',           'Sofia'),
    ('Sofia Tech Park',            'Sofia')
ON CONFLICT DO NOTHING;

INSERT INTO categories (name, slug) VALUES
    ('Music',      'music'),
    ('Sport',      'sport'),
    ('Literature', 'literature'),
    ('Education',  'education'),
    ('Cinema',     'cinema'),
    ('Theatre',    'theatre'),
    ('Art',        'art')
ON CONFLICT (slug) DO NOTHING;

-- ─── Sample events (~50 rows across all categories and cities) ───────────────
-- start_at values are set relative to 2026-06-04 (today) so "upcoming" queries return results.
INSERT INTO events (source_id, external_id, title, description, start_at, venue_id, category_id, url, dedup_key) VALUES
-- Music (category 1, venue 1)
(1,'fix-1', 'Music Event #1',      'Sample music event.',      '2026-06-10 19:00+00', 1, 1, 'https://example.com/events/1',  'music-event-1|2026-06-10|sofia'),
(1,'fix-2', 'Music Event #2',      'Sample music event.',      '2026-06-11 19:00+00', 1, 1, 'https://example.com/events/2',  'music-event-2|2026-06-11|sofia'),
(1,'fix-3', 'Music Event #3',      'Sample music event.',      '2026-06-12 19:00+00', 2, 1, 'https://example.com/events/3',  'music-event-3|2026-06-12|sofia'),
(1,'fix-4', 'Classical Concert',   'An evening of Beethoven.', '2026-06-20 20:00+00', 2, 1, 'https://example.com/events/4',  'classical-concert|2026-06-20|sofia'),
(1,'fix-5', 'Jazz Night',          'Live jazz at the park.',   '2026-07-01 21:00+00', 3, 1, 'https://example.com/events/5',  'jazz-night|2026-07-01|sofia'),
-- Sport (category 2, venue 3)
(1,'fix-6', 'Sport Event #1',      'Sample sport event.',      '2026-06-10 18:00+00', 3, 2, 'https://example.com/events/6',  'sport-event-1|2026-06-10|sofia'),
(1,'fix-7', 'Sport Event #2',      'Sample sport event.',      '2026-06-15 18:00+00', 3, 2, 'https://example.com/events/7',  'sport-event-2|2026-06-15|sofia'),
(1,'fix-8', 'Football Match',      'Sofia Cup final.',         '2026-06-22 17:00+00', 3, 2, 'https://example.com/events/8',  'football-match|2026-06-22|sofia'),
-- Literature (category 3, venue 4)
(1,'fix-9', 'Literature Event #1', 'Sample literature event.', '2026-06-11 17:00+00', 4, 3, 'https://example.com/events/9',  'literature-event-1|2026-06-11|sofia'),
(1,'fix-10','Book Fair 2026',      'Annual book fair.',        '2026-06-25 10:00+00', 4, 3, 'https://example.com/events/10', 'book-fair-2026|2026-06-25|sofia'),
(1,'fix-11','Poetry Night',        'Local poets reading.',     '2026-07-05 19:00+00', 4, 3, 'https://example.com/events/11', 'poetry-night|2026-07-05|sofia'),
-- Education (category 4, venue 5)
(2,'fix-12','Education Event #1',  'Sample education event.',  '2026-06-12 16:00+00', 5, 4, 'https://example.com/events/12', 'education-event-1|2026-06-12|sofia'),
(2,'fix-13','Education Event #2',  'Sample education event.',  '2026-06-13 16:00+00', 5, 4, 'https://example.com/events/13', 'education-event-2|2026-06-13|sofia'),
(2,'fix-14','Tech Conference',     'Annual tech meetup.',      '2026-06-28 09:00+00', 5, 4, 'https://example.com/events/14', 'tech-conference|2026-06-28|sofia'),
(2,'fix-15','AI Workshop',         'Hands-on AI session.',     '2026-07-10 10:00+00', 5, 4, 'https://example.com/events/15', 'ai-workshop|2026-07-10|sofia'),
-- Cinema (category 5, venue 1)
(1,'fix-16','Cinema Event #1',     'Sample cinema event.',     '2026-06-13 20:00+00', 1, 5, 'https://example.com/events/16', 'cinema-event-1|2026-06-13|sofia'),
(1,'fix-17','Film Festival',       'Independent films week.',  '2026-06-30 19:00+00', 1, 5, 'https://example.com/events/17', 'film-festival|2026-06-30|sofia'),
(1,'fix-18','Documentary Night',   'Nature documentaries.',    '2026-07-08 20:00+00', 1, 5, 'https://example.com/events/18', 'documentary-night|2026-07-08|sofia'),
-- Theatre (category 6, venue 2)
(1,'fix-19','Theatre Event #1',    'Sample theatre event.',    '2026-06-14 19:30+00', 2, 6, 'https://example.com/events/19', 'theatre-event-1|2026-06-14|sofia'),
(1,'fix-20','Theatre Event #2',    'Sample theatre event.',    '2026-06-15 19:30+00', 2, 6, 'https://example.com/events//20','theatre-event-2|2026-06-15|sofia'),
(1,'fix-21','Swan Lake',           'National Ballet.',         '2026-07-03 19:30+00', 2, 6, 'https://example.com/events/21', 'swan-lake|2026-07-03|sofia'),
-- Art (category 7, venue 4)
(1,'fix-22','Art Event #1',        'Sample art event.',        '2026-06-16 11:00+00', 4, 7, 'https://example.com/events/22', 'art-event-1|2026-06-16|sofia'),
(1,'fix-23','Art Event #2',        'Sample art event.',        '2026-06-17 11:00+00', 4, 7, 'https://example.com/events/23', 'art-event-2|2026-06-17|sofia'),
(1,'fix-24','Photography Expo',    'Contemporary photography.','2026-06-29 10:00+00', 4, 7, 'https://example.com/events/24', 'photography-expo|2026-06-29|sofia'),
(1,'fix-25','Sculpture Garden',    'Open-air sculpture show.', '2026-07-12 12:00+00', 4, 7, 'https://example.com/events/25', 'sculpture-garden|2026-07-12|sofia'),
-- Mixed — more events to reach ~50, spread across categories and future dates
(2,'fix-26','Music Event #4',      'Sample music event.',      '2026-06-18 19:00+00', 3, 1, 'https://example.com/events/26', 'music-event-4|2026-06-18|sofia'),
(2,'fix-27','Sport Event #3',      'Sample sport event.',      '2026-06-19 18:00+00', 3, 2, 'https://example.com/events/27', 'sport-event-3|2026-06-19|sofia'),
(2,'fix-28','Literature Event #2', 'Sample literature event.', '2026-06-20 17:00+00', 4, 3, 'https://example.com/events/28', 'literature-event-2|2026-06-20|sofia'),
(2,'fix-29','Education Event #3',  'Sample education event.',  '2026-06-21 16:00+00', 5, 4, 'https://example.com/events/29', 'education-event-3|2026-06-21|sofia'),
(2,'fix-30','Cinema Event #2',     'Sample cinema event.',     '2026-06-22 20:00+00', 1, 5, 'https://example.com/events/30', 'cinema-event-2|2026-06-22|sofia'),
(2,'fix-31','Theatre Event #3',    'Sample theatre event.',    '2026-06-23 19:30+00', 2, 6, 'https://example.com/events/31', 'theatre-event-3|2026-06-23|sofia'),
(2,'fix-32','Art Event #3',        'Sample art event.',        '2026-06-24 11:00+00', 4, 7, 'https://example.com/events/32', 'art-event-3|2026-06-24|sofia'),
(2,'fix-33','Music Event #5',      'Sample music event.',      '2026-07-01 19:00+00', 1, 1, 'https://example.com/events/33', 'music-event-5|2026-07-01|sofia'),
(2,'fix-34','Sport Event #4',      'Sample sport event.',      '2026-07-02 18:00+00', 3, 2, 'https://example.com/events/34', 'sport-event-4|2026-07-02|sofia'),
(2,'fix-35','Literature Event #3', 'Sample literature event.', '2026-07-04 17:00+00', 4, 3, 'https://example.com/events/35', 'literature-event-3|2026-07-04|sofia'),
(2,'fix-36','Education Event #4',  'Sample education event.',  '2026-07-06 16:00+00', 5, 4, 'https://example.com/events/36', 'education-event-4|2026-07-06|sofia'),
(2,'fix-37','Cinema Event #3',     'Sample cinema event.',     '2026-07-07 20:00+00', 1, 5, 'https://example.com/events/37', 'cinema-event-3|2026-07-07|sofia'),
(2,'fix-38','Theatre Event #4',    'Sample theatre event.',    '2026-07-09 19:30+00', 2, 6, 'https://example.com/events/38', 'theatre-event-4|2026-07-09|sofia'),
(2,'fix-39','Art Event #4',        'Sample art event.',        '2026-07-11 11:00+00', 4, 7, 'https://example.com/events/39', 'art-event-4|2026-07-11|sofia'),
(2,'fix-40','Music Event #6',      'Sample music event.',      '2026-07-13 19:00+00', 2, 1, 'https://example.com/events/40', 'music-event-6|2026-07-13|sofia'),
(2,'fix-41','Sport Event #5',      'Sample sport event.',      '2026-07-14 18:00+00', 3, 2, 'https://example.com/events/41', 'sport-event-5|2026-07-14|sofia'),
(2,'fix-42','Literature Event #4', 'Sample literature event.', '2026-07-15 17:00+00', 4, 3, 'https://example.com/events/42', 'literature-event-4|2026-07-15|sofia'),
(2,'fix-43','Education Event #5',  'Sample education event.',  '2026-07-16 16:00+00', 5, 4, 'https://example.com/events/43', 'education-event-5|2026-07-16|sofia'),
(2,'fix-44','Cinema Event #4',     'Sample cinema event.',     '2026-07-17 20:00+00', 1, 5, 'https://example.com/events/44', 'cinema-event-4|2026-07-17|sofia'),
(2,'fix-45','Theatre Event #5',    'Sample theatre event.',    '2026-07-18 19:30+00', 2, 6, 'https://example.com/events/45', 'theatre-event-5|2026-07-18|sofia'),
(2,'fix-46','Art Event #5',        'Sample art event.',        '2026-07-19 11:00+00', 4, 7, 'https://example.com/events/46', 'art-event-5|2026-07-19|sofia'),
(2,'fix-47','Summer Music Fest',   'Three-day festival.',      '2026-08-01 17:00+00', 3, 1, 'https://example.com/events/47', 'summer-music-fest|2026-08-01|sofia'),
(2,'fix-48','Marathon 2026',       'City marathon.',           '2026-08-10 07:00+00', 3, 2, 'https://example.com/events/48', 'marathon-2026|2026-08-10|sofia'),
(2,'fix-49','Winter Book Fair',    'November book fair.',      '2026-11-20 10:00+00', 4, 3, 'https://example.com/events/49', 'winter-book-fair|2026-11-20|sofia'),
(2,'fix-50','New Year Concert',    'Philharmonic NYE.',        '2026-12-31 21:00+00', 2, 1, 'https://example.com/events/50', 'new-year-concert|2026-12-31|sofia');
