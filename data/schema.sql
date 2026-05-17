-- Pixel Asset Manager Database Schema

CREATE TABLE IF NOT EXISTS asset_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    folder_path TEXT DEFAULT '',
    sort_order INTEGER DEFAULT 0,
    note TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(parent_id) REFERENCES asset_nodes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS asset_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    role TEXT DEFAULT '',
    thumbnail_path TEXT DEFAULT '',
    file_hash TEXT DEFAULT '',
    width INTEGER DEFAULT 0,
    height INTEGER DEFAULT 0,
    frame_count INTEGER DEFAULT 0,
    file_size INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(node_id) REFERENCES asset_nodes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#888888',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS asset_node_tags (
    node_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY(node_id, tag_id),
    FOREIGN KEY(node_id) REFERENCES asset_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
