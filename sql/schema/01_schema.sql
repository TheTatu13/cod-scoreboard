
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game` (
  `game_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) DEFAULT NULL,
  `release_year` year DEFAULT NULL,
  `studio` enum('Infinity Ward','Treyarch','Sledgehammer') DEFAULT NULL,
  PRIMARY KEY (`game_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kill_table` (
  `kill_id` int NOT NULL AUTO_INCREMENT,
  `match_id` int DEFAULT NULL,
  `killer_id` int DEFAULT NULL,
  `victim_id` int NOT NULL,
  `assister_id` int DEFAULT NULL,
  `weapon_id` int DEFAULT NULL,
  `is_headshot` tinyint(1) DEFAULT NULL,
  `timestamp_in_match` smallint DEFAULT NULL,
  PRIMARY KEY (`kill_id`),
  KEY `match_id` (`match_id`),
  KEY `killer_id` (`killer_id`),
  KEY `victim_id` (`victim_id`),
  KEY `assister_id` (`assister_id`),
  KEY `weapon_id` (`weapon_id`),
  CONSTRAINT `kill_table_ibfk_1` FOREIGN KEY (`match_id`) REFERENCES `match` (`match_id`),
  CONSTRAINT `kill_table_ibfk_2` FOREIGN KEY (`killer_id`) REFERENCES `player` (`player_id`),
  CONSTRAINT `kill_table_ibfk_3` FOREIGN KEY (`victim_id`) REFERENCES `player` (`player_id`),
  CONSTRAINT `kill_table_ibfk_4` FOREIGN KEY (`assister_id`) REFERENCES `player` (`player_id`),
  CONSTRAINT `kill_table_ibfk_5` FOREIGN KEY (`weapon_id`) REFERENCES `weapon` (`weapon_id`)
) ENGINE=InnoDB AUTO_INCREMENT=90671 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `map` (
  `map_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) DEFAULT NULL,
  `game_id` int DEFAULT NULL,
  `size_category` enum('Very Small','Small','Medium','Large') DEFAULT NULL,
  `design_style` enum('3-lane','CQC','Open-Sniper','Mixed') DEFAULT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`map_id`),
  KEY `game_id` (`game_id`),
  CONSTRAINT `map_ibfk_1` FOREIGN KEY (`game_id`) REFERENCES `game` (`game_id`)
) ENGINE=InnoDB AUTO_INCREMENT=90 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `match` (
  `match_id` int NOT NULL AUTO_INCREMENT,
  `map_id` int DEFAULT NULL,
  `mode` enum('Team Deathmatch','Domination','Kill Confirmed','Hardpoint') DEFAULT NULL,
  `started_at` datetime DEFAULT NULL,
  `duration_sec` smallint DEFAULT NULL,
  `winner_team_id` int DEFAULT NULL,
  PRIMARY KEY (`match_id`),
  KEY `map_id` (`map_id`),
  KEY `winner_team_id` (`winner_team_id`),
  CONSTRAINT `match_ibfk_1` FOREIGN KEY (`map_id`) REFERENCES `map` (`map_id`),
  CONSTRAINT `match_ibfk_2` FOREIGN KEY (`winner_team_id`) REFERENCES `team` (`team_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1501 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `match_player` (
  `match_id` int NOT NULL,
  `player_id` int NOT NULL,
  `team_id` int DEFAULT NULL,
  `kills` tinyint DEFAULT NULL,
  `deaths` tinyint DEFAULT NULL,
  `assists` tinyint DEFAULT NULL,
  `score` smallint DEFAULT NULL,
  PRIMARY KEY (`match_id`,`player_id`),
  KEY `player_id` (`player_id`),
  KEY `team_id` (`team_id`),
  CONSTRAINT `match_player_ibfk_1` FOREIGN KEY (`match_id`) REFERENCES `match` (`match_id`),
  CONSTRAINT `match_player_ibfk_2` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`),
  CONSTRAINT `match_player_ibfk_3` FOREIGN KEY (`team_id`) REFERENCES `team` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `player` (
  `player_id` int NOT NULL AUTO_INCREMENT,
  `gamertag` varchar(25) DEFAULT NULL,
  `platform` enum('PC','Xbox','PS') DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `archetype` enum('Recrut','Ghost','Smoker','Mohawk','Number','Insanity','Ramirez','Demon','Menendez','No Russian') NOT NULL DEFAULT 'Recrut',
  PRIMARY KEY (`player_id`),
  UNIQUE KEY `gamertag` (`gamertag`)
) ENGINE=InnoDB AUTO_INCREMENT=15001 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team` (
  `team_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(25) DEFAULT NULL,
  PRIMARY KEY (`team_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_player_leaderboard` AS SELECT 
 1 AS `player_id`,
 1 AS `gamertag`,
 1 AS `total_kills`,
 1 AS `rank_poz`*/;
SET character_set_client = @saved_cs_client;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `weapon` (
  `weapon_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) DEFAULT NULL,
  `category` enum('AR','SMG','Sniper','Shotgun','LMG','Pistol') DEFAULT NULL,
  PRIMARY KEY (`weapon_id`)
) ENGINE=InnoDB AUTO_INCREMENT=66 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `weapon_game` (
  `weapon_id` int NOT NULL,
  `game_id` int NOT NULL,
  PRIMARY KEY (`weapon_id`,`game_id`),
  KEY `game_id` (`game_id`),
  CONSTRAINT `weapon_game_ibfk_1` FOREIGN KEY (`weapon_id`) REFERENCES `weapon` (`weapon_id`),
  CONSTRAINT `weapon_game_ibfk_2` FOREIGN KEY (`game_id`) REFERENCES `game` (`game_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!50001 DROP VIEW IF EXISTS `v_player_leaderboard`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_player_leaderboard` AS select `mp`.`player_id` AS `player_id`,`p`.`gamertag` AS `gamertag`,sum(`mp`.`kills`) AS `total_kills`,dense_rank() OVER (ORDER BY sum(`mp`.`kills`) desc )  AS `rank_poz` from (`match_player` `mp` join `player` `p` on((`mp`.`player_id` = `p`.`player_id`))) group by `mp`.`player_id`,`p`.`gamertag` order by `total_kills` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

