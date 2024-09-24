-- MySQL Script generated by MySQL Workbench
-- Tue Sep 24 18:57:33 2024
-- Model: New Model    Version: 1.0
-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema minutia
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema minutia
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `minutia` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
USE `minutia` ;

-- -----------------------------------------------------
-- Table `minutia`.`apirest_alimento`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `minutia`.`apirest_alimento` ;

CREATE TABLE IF NOT EXISTS `minutia`.`apirest_alimento` (
  `id_alimento` INT NOT NULL AUTO_INCREMENT,
  `name_alimento` VARCHAR(255) NOT NULL,
  `unit_measurement` VARCHAR(255) NOT NULL,
  `load_alimento` INT NOT NULL,
  PRIMARY KEY (`id_alimento`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `minutia`.`apirest_dispensa`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `minutia`.`apirest_dispensa` ;

CREATE TABLE IF NOT EXISTS `minutia`.`apirest_dispensa` (
  `id_dispensa` INT NOT NULL AUTO_INCREMENT,
  `alimento_id` INT NOT NULL,
  PRIMARY KEY (`id_dispensa`),
  INDEX `apirest_dispensa_alimento_id_06e4965b_fk_apirest_a` (`alimento_id` ASC) VISIBLE,
  CONSTRAINT `apirest_dispensa_alimento_id_06e4965b_fk_apirest_a`
    FOREIGN KEY (`alimento_id`)
    REFERENCES `minutia`.`apirest_alimento` (`id_alimento`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `minutia`.`apirest_users`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `minutia`.`apirest_users` ;

CREATE TABLE IF NOT EXISTS `minutia`.`apirest_users` (
  `id_user` INT NOT NULL AUTO_INCREMENT,
  `name_user` VARCHAR(255) NOT NULL,
  `last_name_user` VARCHAR(255) NOT NULL,
  `year_user` INT NOT NULL,
  `type_user` VARCHAR(255) NOT NULL,
  `dispensa_id` INT NULL DEFAULT NULL,
  PRIMARY KEY (`id_user`),
  UNIQUE INDEX `dispensa_id` (`dispensa_id` ASC) VISIBLE,
  CONSTRAINT `apirest_users_dispensa_id_13fc7b44_fk_apirest_d`
    FOREIGN KEY (`dispensa_id`)
    REFERENCES `minutia`.`apirest_dispensa` (`id_dispensa`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `minutia`.`apirest_historialalimentos`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `minutia`.`apirest_historialalimentos` ;

CREATE TABLE IF NOT EXISTS `minutia`.`apirest_historialalimentos` (
  `id_historial` INT NOT NULL AUTO_INCREMENT,
  `name_alimento` VARCHAR(255) NOT NULL,
  `unit_measurement` VARCHAR(255) NOT NULL,
  `load_alimento` INT NOT NULL,
  `date_join` DATETIME(6) NOT NULL,
  `alimento_id` INT NULL DEFAULT NULL,
  `dispensa_id` INT NULL DEFAULT NULL,
  `user_id` INT NOT NULL,
  PRIMARY KEY (`id_historial`),
  INDEX `apirest_historialali_alimento_id_8adf9cfe_fk_apirest_a` (`alimento_id` ASC) VISIBLE,
  INDEX `apirest_historialali_dispensa_id_2eece1a9_fk_apirest_d` (`dispensa_id` ASC) VISIBLE,
  INDEX `apirest_historialali_user_id_23e964d2_fk_apirest_u` (`user_id` ASC) VISIBLE,
  CONSTRAINT `apirest_historialali_alimento_id_8adf9cfe_fk_apirest_a`
    FOREIGN KEY (`alimento_id`)
    REFERENCES `minutia`.`apirest_alimento` (`id_alimento`),
  CONSTRAINT `apirest_historialali_dispensa_id_2eece1a9_fk_apirest_d`
    FOREIGN KEY (`dispensa_id`)
    REFERENCES `minutia`.`apirest_dispensa` (`id_dispensa`),
  CONSTRAINT `apirest_historialali_user_id_23e964d2_fk_apirest_u`
    FOREIGN KEY (`user_id`)
    REFERENCES `minutia`.`apirest_users` (`id_user`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `minutia`.`apirest_minuta`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `minutia`.`apirest_minuta` ;

CREATE TABLE IF NOT EXISTS `minutia`.`apirest_minuta` (
  `id_minuta` INT NOT NULL AUTO_INCREMENT,
  `fecha` DATE NULL DEFAULT NULL,
  `type_food` VARCHAR(255) NOT NULL,
  `name_food` VARCHAR(255) NOT NULL,
  `state_minuta` TINYINT(1) NOT NULL,
  `user_id` INT NOT NULL,
  PRIMARY KEY (`id_minuta`),
  INDEX `apirest_minuta_user_id_aceaea8d_fk_apirest_users_id_user` (`user_id` ASC) VISIBLE,
  CONSTRAINT `apirest_minuta_user_id_aceaea8d_fk_apirest_users_id_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `minutia`.`apirest_users` (`id_user`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `minutia`.`auth_group`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `minutia`.`auth_group` ;

CREATE TABLE IF NOT EXISTS `minutia`.`auth_group` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `name` (`name` ASC) VISIBLE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `minutia`.`django_content_type`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `minutia`.`django_content_type` ;

CREATE TABLE IF NOT EXISTS `minutia`.`django_content_type` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `app_label` VARCHAR(100) NOT NULL,
  `model` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label` ASC, `model` ASC) VISIBLE)
ENGINE = InnoDB
AUTO_INCREMENT = 12
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `minutia`.`auth_permission`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `minutia`.`auth_permission` ;

CREATE TABLE IF NOT EXISTS `minutia`.`auth_permission` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `content_type_id` INT NOT NULL,
  `codename` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id` ASC, `codename` ASC) VISIBLE,
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co`
    FOREIGN KEY (`content_type_id`)
    REFERENCES `minutia`.`django_content_type` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 45
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `minutia`.`auth_group_permissions`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `minutia`.`auth_group_permissions` ;

CREATE TABLE IF NOT EXISTS `minutia`.`auth_group_permissions` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `group_id` INT NOT NULL,
  `permission_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id` ASC, `permission_id` ASC) VISIBLE,
  INDEX `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id` ASC) VISIBLE,
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm`
    FOREIGN KEY (`permission_id`)
    REFERENCES `minutia`.`auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id`
    FOREIGN KEY (`group_id`)
    REFERENCES `minutia`.`auth_group` (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `minutia`.`auth_user`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `minutia`.`auth_user` ;

CREATE TABLE IF NOT EXISTS `minutia`.`auth_user` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `password` VARCHAR(128) NOT NULL,
  `last_login` DATETIME(6) NULL DEFAULT NULL,
  `is_superuser` TINYINT(1) NOT NULL,
  `username` VARCHAR(150) NOT NULL,
  `first_name` VARCHAR(150) NOT NULL,
  `last_name` VARCHAR(150) NOT NULL,
  `email` VARCHAR(254) NOT NULL,
  `is_staff` TINYINT(1) NOT NULL,
  `is_active` TINYINT(1) NOT NULL,
  `date_joined` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `username` (`username` ASC) VISIBLE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `minutia`.`auth_user_groups`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `minutia`.`auth_user_groups` ;

CREATE TABLE IF NOT EXISTS `minutia`.`auth_user_groups` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `group_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id` ASC, `group_id` ASC) VISIBLE,
  INDEX `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id` ASC) VISIBLE,
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id`
    FOREIGN KEY (`group_id`)
    REFERENCES `minutia`.`auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `minutia`.`auth_user` (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `minutia`.`auth_user_user_permissions`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `minutia`.`auth_user_user_permissions` ;

CREATE TABLE IF NOT EXISTS `minutia`.`auth_user_user_permissions` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `permission_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id` ASC, `permission_id` ASC) VISIBLE,
  INDEX `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id` ASC) VISIBLE,
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm`
    FOREIGN KEY (`permission_id`)
    REFERENCES `minutia`.`auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `minutia`.`auth_user` (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `minutia`.`django_admin_log`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `minutia`.`django_admin_log` ;

CREATE TABLE IF NOT EXISTS `minutia`.`django_admin_log` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `action_time` DATETIME(6) NOT NULL,
  `object_id` LONGTEXT NULL DEFAULT NULL,
  `object_repr` VARCHAR(200) NOT NULL,
  `action_flag` SMALLINT UNSIGNED NOT NULL,
  `change_message` LONGTEXT NOT NULL,
  `content_type_id` INT NULL DEFAULT NULL,
  `user_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id` ASC) VISIBLE,
  INDEX `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id` ASC) VISIBLE,
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co`
    FOREIGN KEY (`content_type_id`)
    REFERENCES `minutia`.`django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `minutia`.`auth_user` (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `minutia`.`django_migrations`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `minutia`.`django_migrations` ;

CREATE TABLE IF NOT EXISTS `minutia`.`django_migrations` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `app` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `applied` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 21
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `minutia`.`django_session`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `minutia`.`django_session` ;

CREATE TABLE IF NOT EXISTS `minutia`.`django_session` (
  `session_key` VARCHAR(40) NOT NULL,
  `session_data` LONGTEXT NOT NULL,
  `expire_date` DATETIME(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  INDEX `django_session_expire_date_a5c62663` (`expire_date` ASC) VISIBLE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
