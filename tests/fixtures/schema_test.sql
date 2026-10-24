-- SCHEMĂ DE TEST, reconstruită din scripturile și planul proiectului.
-- NU e exportul real din baza ta. Folosește-o doar pentru teste/CI.
-- Schema reală: exportă-o în sql/schema/01_schema.sql (vezi sql/schema/README.md).

CREATE TABLE player (
  player_id INT AUTO_INCREMENT PRIMARY KEY,
  gamertag VARCHAR(60) NOT NULL UNIQUE,
  platform ENUM('PC','Xbox','PS') NOT NULL,
  archetype ENUM('Recrut','Ghost','Smoker','Mohawk','Number','Insanity','Ramirez',
                 'Demon','Menendez','No Russian') NOT NULL DEFAULT 'Recrut',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE team (
  team_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL
);

CREATE TABLE game (
  game_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(60) NOT NULL UNIQUE,
  release_year YEAR NOT NULL,
  studio ENUM('Treyarch','Infinity Ward','Sledgehammer') NOT NULL
);

CREATE TABLE map (
  map_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(60) NOT NULL,
  game_id INT NOT NULL,
  size_category ENUM('Very Small','Small','Medium','Large') NOT NULL,
  design_style ENUM('CQC','3-lane','Mixed','Open-Sniper') NOT NULL,
  image_url VARCHAR(255) NULL,
  FOREIGN KEY (game_id) REFERENCES game (game_id)
);

CREATE TABLE weapon (
  weapon_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(60) NOT NULL,
  category ENUM('AR','SMG','Sniper','Shotgun','LMG','Pistol') NOT NULL
);

CREATE TABLE weapon_game (
  weapon_id INT NOT NULL,
  game_id INT NOT NULL,
  PRIMARY KEY (weapon_id, game_id),
  FOREIGN KEY (weapon_id) REFERENCES weapon (weapon_id),
  FOREIGN KEY (game_id) REFERENCES game (game_id)
);

CREATE TABLE `match` (
  match_id INT AUTO_INCREMENT PRIMARY KEY,
  map_id INT NOT NULL,
  mode ENUM('Team Deathmatch','Domination','Kill Confirmed','Hardpoint') NOT NULL,
  started_at DATETIME NOT NULL,
  duration_sec SMALLINT UNSIGNED NOT NULL,
  winner_team_id INT NOT NULL,
  FOREIGN KEY (map_id) REFERENCES map (map_id),
  FOREIGN KEY (winner_team_id) REFERENCES team (team_id)
);

CREATE TABLE match_player (
  match_id INT NOT NULL,
  player_id INT NOT NULL,
  team_id INT NOT NULL,
  kills TINYINT UNSIGNED NOT NULL,
  deaths TINYINT UNSIGNED NOT NULL,
  assists TINYINT UNSIGNED NOT NULL,
  score SMALLINT NOT NULL,
  PRIMARY KEY (match_id, player_id),
  FOREIGN KEY (match_id) REFERENCES `match` (match_id),
  FOREIGN KEY (player_id) REFERENCES player (player_id),
  FOREIGN KEY (team_id) REFERENCES team (team_id)
);

CREATE TABLE kill_table (
  kill_id INT AUTO_INCREMENT PRIMARY KEY,
  match_id INT NOT NULL,
  killer_id INT NULL,
  victim_id INT NOT NULL,
  assister_id INT NULL,
  weapon_id INT NOT NULL,
  is_headshot BOOLEAN NOT NULL,
  timestamp_in_match SMALLINT UNSIGNED NOT NULL,
  FOREIGN KEY (match_id) REFERENCES `match` (match_id),
  FOREIGN KEY (killer_id) REFERENCES player (player_id),
  FOREIGN KEY (victim_id) REFERENCES player (player_id),
  FOREIGN KEY (assister_id) REFERENCES player (player_id),
  FOREIGN KEY (weapon_id) REFERENCES weapon (weapon_id)
);
