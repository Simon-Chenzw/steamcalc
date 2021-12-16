CREATE TABLE IF NOT EXISTS buff(
  item_id INTEGER PRIMARY KEY,
  url TEXT,
  lowest_sell DECIMAL,
  highest_buy DECIMAL,
  update_time INTEGER
);
--
CREATE TABLE IF NOT EXISTS market(
  item_id INTEGER PRIMARY KEY,
  lowest_sell DECIMAL,
  highest_buy DECIMAL,
  update_time INTEGER
);
--
CREATE TABLE IF NOT EXISTS idmap(
  appid INTEGER,
  hash_name TEXT,
  item_id INTEGER,
  primary key (appid, hash_name)
);
--
CREATE TABLE IF NOT EXISTS locale(
  item_id INTEGER PRIMARY KEY,
  name TEXT
);
-- use for `insert or ignore`
create unique index if not exists locale_index on locale (item_id, name);
