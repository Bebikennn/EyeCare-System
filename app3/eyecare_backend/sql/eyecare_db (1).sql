-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Dec 14, 2025 at 09:26 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `eyecare_db`
--

DELIMITER $$
--
-- Procedures
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `get_recent_activity` (IN `p_limit` INT)   BEGIN
    SELECT 
        al.id,
        al.action,
        al.entity_type,
        al.entity_id,
        al.details,
        al.ip_address,
        al.created_at,
        a.username,
        a.full_name
    FROM activity_logs al
    LEFT JOIN admins a ON al.admin_id = a.id
    ORDER BY al.created_at DESC
    LIMIT p_limit;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `log_admin_activity` (IN `p_admin_id` INT, IN `p_action` VARCHAR(100), IN `p_entity_type` VARCHAR(50), IN `p_entity_id` VARCHAR(100), IN `p_details` TEXT, IN `p_ip_address` VARCHAR(50))   BEGIN
    INSERT INTO activity_logs (admin_id, action, entity_type, entity_id, details, ip_address)
    VALUES (p_admin_id, p_action, p_entity_type, p_entity_id, p_details, p_ip_address);
END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `activity_logs`
--

CREATE TABLE `activity_logs` (
  `id` int(11) NOT NULL,
  `admin_id` int(11) DEFAULT NULL,
  `action` varchar(100) NOT NULL,
  `entity_type` varchar(50) DEFAULT NULL COMMENT 'user, assessment, healthtip, admin',
  `entity_id` varchar(100) DEFAULT NULL,
  `details` text DEFAULT NULL,
  `ip_address` varchar(50) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `activity_logs`
--

INSERT INTO `activity_logs` (`id`, `admin_id`, `action`, `entity_type`, `entity_id`, `details`, `ip_address`, `created_at`) VALUES
(1, 1, 'Login', 'auth', NULL, 'Admin admin logged in', '192.168.1.8', '2025-12-09 06:07:10'),
(2, 1, 'Login', 'auth', NULL, 'Admin admin logged in', '192.168.1.8', '2025-12-09 07:10:58'),
(3, 1, 'Create Admin', 'admin', '4', 'Created admin account: admin john', '192.168.1.8', '2025-12-09 21:40:45'),
(4, 1, 'Update Admin', 'admin', '4', 'Updated admin account: admin john', '192.168.1.8', '2025-12-09 21:41:00'),
(5, 1, 'Logout', 'auth', NULL, 'Admin logged out', '192.168.1.8', '2025-12-09 21:41:08'),
(6, 4, 'Login', 'auth', NULL, 'Admin admin john logged in', '192.168.1.8', '2025-12-09 21:41:15'),
(7, 1, 'Login', 'auth', NULL, 'Admin admin logged in', '192.168.1.8', '2025-12-11 12:46:19'),
(8, 1, 'Login', 'auth', NULL, 'Admin admin logged in', '192.168.100.12', '2025-12-12 05:25:17'),
(9, 1, 'Login', 'auth', NULL, 'Admin admin logged in', '192.168.1.8', '2025-12-12 09:23:39');

-- --------------------------------------------------------

--
-- Table structure for table `admins`
--

CREATE TABLE `admins` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `role` enum('super_admin','analyst','staff') DEFAULT 'staff',
  `status` enum('active','inactive') DEFAULT 'active',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `last_login` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `admins`
--

INSERT INTO `admins` (`id`, `username`, `email`, `password_hash`, `full_name`, `role`, `status`, `created_at`, `last_login`) VALUES
(1, 'admin', 'admin@eyecare.com', 'scrypt:32768:8:1$r2uy7o1ikx8W6sxr$3ee3d72924d2f7f667e43390c263cf7e428a430901435cb79305e54af22ebed9a9e11daab100aaf459509ad0e9cd02363426655709f2994c5b91092ede54d7aa', 'Super Administrator', 'super_admin', 'active', '2025-12-09 13:42:10', '2025-12-12 09:23:38'),
(2, 'analyst', 'analyst@eyecare.com', 'placeholder_will_be_set_by_flask', 'Data Analyst', 'analyst', 'active', '2025-12-09 13:42:10', NULL),
(3, 'staff', 'staff@eyecare.com', 'placeholder_will_be_set_by_flask', 'Staff Member', 'staff', 'active', '2025-12-09 13:42:10', NULL),
(4, 'admin john', 'johnvincentbilolo355@gmail.com', 'scrypt:32768:8:1$7brmOsJxkiQ4PhVL$43f874fe4d50c0eec387a36b39c739f62d11e9939ec9b94769c822c0a361f460027daa786320b1a0fcd871c264b91b644715d8e9c961f8b125a6be636defd24f', 'john vincent', 'analyst', 'active', '2025-12-09 21:40:44', '2025-12-09 21:41:15');

-- --------------------------------------------------------

--
-- Stand-in structure for view `admin_activity_summary`
-- (See below for the actual view)
--
CREATE TABLE `admin_activity_summary` (
`admin_id` int(11)
,`username` varchar(50)
,`full_name` varchar(100)
,`role` enum('super_admin','analyst','staff')
,`total_actions` bigint(21)
,`last_activity` timestamp
,`last_login` timestamp
);

-- --------------------------------------------------------

--
-- Table structure for table `admin_notifications`
--

CREATE TABLE `admin_notifications` (
  `id` int(11) NOT NULL,
  `admin_id` int(11) DEFAULT NULL,
  `title` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `type` enum('info','warning','error','success') DEFAULT 'info',
  `is_read` tinyint(1) DEFAULT 0,
  `link` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `admin_notifications`
--

INSERT INTO `admin_notifications` (`id`, `admin_id`, `title`, `message`, `type`, `is_read`, `link`, `created_at`) VALUES
(1, 1, 'Welcome to EyeCare Admin', 'Your admin dashboard has been successfully set up. Please change your default password.', 'info', 0, NULL, '2025-12-09 13:42:11'),
(2, 1, 'Database Merged', 'The mobile app and admin dashboard now share a unified database for better data access.', 'success', 0, NULL, '2025-12-09 13:42:11');

-- --------------------------------------------------------

--
-- Table structure for table `admin_settings`
--

CREATE TABLE `admin_settings` (
  `id` int(11) NOT NULL,
  `setting_key` varchar(100) NOT NULL,
  `setting_value` text DEFAULT NULL,
  `setting_type` enum('string','number','boolean','json') DEFAULT 'string',
  `description` text DEFAULT NULL,
  `updated_by` int(11) DEFAULT NULL,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `admin_settings`
--

INSERT INTO `admin_settings` (`id`, `setting_key`, `setting_value`, `setting_type`, `description`, `updated_by`, `updated_at`) VALUES
(1, 'system_name', 'EyeCare Admin Dashboard', 'string', 'System display name', NULL, '2025-12-09 13:42:11'),
(2, 'max_login_attempts', '5', 'number', 'Maximum login attempts before account lock', NULL, '2025-12-09 13:42:11'),
(3, 'session_timeout', '3600', 'number', 'Session timeout in seconds (1 hour)', NULL, '2025-12-09 13:42:11'),
(4, 'enable_notifications', 'true', 'boolean', 'Enable admin notifications', NULL, '2025-12-09 13:42:11'),
(5, 'records_per_page', '10', 'number', 'Default records per page in tables', NULL, '2025-12-09 13:42:11'),
(6, 'ml_model_version', 'LightGBM-v1.0', 'string', 'Current active ML model version', NULL, '2025-12-09 13:42:11'),
(7, 'backup_enabled', 'true', 'boolean', 'Enable automatic database backups', NULL, '2025-12-09 13:42:11'),
(8, 'backup_frequency', '86400', 'number', 'Backup frequency in seconds (24 hours)', NULL, '2025-12-09 13:42:11');

-- --------------------------------------------------------

--
-- Table structure for table `assessment_results`
--

CREATE TABLE `assessment_results` (
  `assessment_id` varchar(36) NOT NULL,
  `user_id` varchar(36) NOT NULL,
  `risk_level` enum('Low','Moderate','High','Critical') NOT NULL,
  `risk_score` decimal(5,2) NOT NULL,
  `confidence_score` decimal(5,2) DEFAULT NULL,
  `predicted_disease` varchar(100) DEFAULT NULL,
  `model_version` varchar(50) DEFAULT 'LightGBM_v1.0',
  `assessment_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT 'Stores input features used' CHECK (json_valid(`assessment_data`)),
  `per_disease_scores` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT 'Individual disease probabilities' CHECK (json_valid(`per_disease_scores`)),
  `assessed_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `assessment_results`
--

INSERT INTO `assessment_results` (`assessment_id`, `user_id`, `risk_level`, `risk_score`, `confidence_score`, `predicted_disease`, `model_version`, `assessment_data`, `per_disease_scores`, `assessed_at`) VALUES
('012f1019-05ce-4f06-a8c9-74120d9e31da', '571797fd-34b1-48c0-98db-9059edd8c762', 'Low', 16.00, 100.00, 'Blurred Vision', 'LightGBM_v1.0', '{\"Age\": 21, \"Gender\": \"Male\", \"BMI\": 27.29, \"Screen_Time_Hours\": 8.0, \"Sleep_Hours\": 8.0, \"Smoker\": 0, \"Alcohol_Use\": 0, \"Diabetes\": 0, \"Hypertension\": 0, \"Family_History_Eye_Disease\": 0, \"Eye_Pain_Frequency\": 0, \"Blurry_Vision_Score\": 1, \"Light_Sensitivity\": 0, \"Eye_Strains_Per_Day\": 0, \"Outdoor_Exposure_Hours\": 4.0, \"Diet_Score\": 10, \"Water_Intake_Liters\": 3.0, \"Glasses_Usage\": 0, \"Previous_Eye_Surgery\": 0, \"Physical_Activity_Level\": \"High\"}', '{\"Allergic Conjunctivitis\": 5.027800266210049e-08, \"Astigmatism\": 9.093597453128356e-08, \"Blurred Vision\": 0.9999983394594965, \"Cataract\": 4.717277616941696e-08, \"Dry Eye\": 5.6182315207481155e-08, \"Eye Strain / CVS\": 1.0849214797421117e-06, \"Hyperopia\": 8.879545201592131e-08, \"Light Sensitivity\": 4.803471267471945e-08, \"Myopia\": 6.728101352946975e-08, \"Presbyopia\": 1.269387770817773e-07}', '2025-12-12 09:50:38'),
('24e1f19d-7896-424d-8422-df1cd70b4ff5', '571797fd-34b1-48c0-98db-9059edd8c762', 'Low', 48.00, 100.00, 'Myopia', 'LightGBM_v1.0', '{\"Age\": 23, \"Gender\": \"Male\", \"BMI\": 23.34, \"Screen_Time_Hours\": 6.0, \"Sleep_Hours\": 5.0, \"Smoker\": 1, \"Alcohol_Use\": 0, \"Diabetes\": 0, \"Hypertension\": 1, \"Family_History_Eye_Disease\": 1, \"Eye_Pain_Frequency\": 0, \"Blurry_Vision_Score\": 5, \"Light_Sensitivity\": 1, \"Eye_Strains_Per_Day\": 0, \"Outdoor_Exposure_Hours\": 1.0, \"Diet_Score\": 10, \"Water_Intake_Liters\": 2.0, \"Glasses_Usage\": 0, \"Previous_Eye_Surgery\": 0, \"Physical_Activity_Level\": \"Moderate\"}', '{\"Allergic Conjunctivitis\": 2.976625350546437e-09, \"Astigmatism\": 1.2674106434365787e-08, \"Blurred Vision\": 7.171633565379704e-07, \"Cataract\": 4.630087732019422e-09, \"Dry Eye\": 4.49098960201703e-09, \"Eye Strain / CVS\": 1.2555129799098223e-08, \"Hyperopia\": 7.94645878886935e-09, \"Light Sensitivity\": 3.988811714154009e-09, \"Myopia\": 0.9999992240240454, \"Presbyopia\": 9.5503887253539e-09}', '2025-12-11 12:14:19'),
('a8cb526a-c1bf-49ff-8b4a-47876436ecc3', '571797fd-34b1-48c0-98db-9059edd8c762', 'Low', 12.00, 100.00, 'Blurred Vision', 'LightGBM_v1.0', '{\"Age\": 21, \"Gender\": \"Male\", \"BMI\": 27.29, \"Screen_Time_Hours\": 6.0, \"Sleep_Hours\": 7.0, \"Smoker\": 0, \"Alcohol_Use\": 0, \"Diabetes\": 0, \"Hypertension\": 0, \"Family_History_Eye_Disease\": 0, \"Eye_Pain_Frequency\": 0, \"Blurry_Vision_Score\": 1, \"Light_Sensitivity\": 0, \"Eye_Strains_Per_Day\": 1, \"Outdoor_Exposure_Hours\": 4.0, \"Diet_Score\": 5, \"Water_Intake_Liters\": 2.0, \"Glasses_Usage\": 0, \"Previous_Eye_Surgery\": 0, \"Physical_Activity_Level\": \"Moderate\"}', '{\"Allergic Conjunctivitis\": 4.6536043677485854e-08, \"Astigmatism\": 8.798241896264562e-08, \"Blurred Vision\": 0.9999987132158676, \"Cataract\": 4.56406261417071e-08, \"Dry Eye\": 5.623954326872972e-08, \"Eye Strain / CVS\": 7.270822415044115e-07, \"Hyperopia\": 8.591141956206419e-08, \"Light Sensitivity\": 4.647456891599682e-08, \"Myopia\": 6.810140216986826e-08, \"Presbyopia\": 1.228158682565467e-07}', '2025-12-11 08:09:26'),
('e2a6d76b-1e12-4a79-8797-c784ad88888e', '571797fd-34b1-48c0-98db-9059edd8c762', 'Moderate', 55.00, 100.00, 'Hyperopia', 'LightGBM_v1.0', '{\"Age\": 12, \"Gender\": \"Male\", \"BMI\": 23.0, \"Screen_Time_Hours\": 4.0, \"Sleep_Hours\": 4.0, \"Smoker\": 1, \"Alcohol_Use\": 1, \"Diabetes\": 1, \"Hypertension\": 0, \"Family_History_Eye_Disease\": 1, \"Eye_Pain_Frequency\": 21, \"Blurry_Vision_Score\": 1, \"Light_Sensitivity\": 1, \"Eye_Strains_Per_Day\": 12, \"Outdoor_Exposure_Hours\": 1.0, \"Diet_Score\": 1, \"Water_Intake_Liters\": 1.0, \"Glasses_Usage\": 1, \"Previous_Eye_Surgery\": 1, \"Physical_Activity_Level\": \"High\"}', '{\"Allergic Conjunctivitis\": 3.8418576574174624e-09, \"Astigmatism\": 6.507556316509648e-09, \"Blurred Vision\": 5.263739574744695e-08, \"Cataract\": 3.474165997193257e-09, \"Dry Eye\": 1.6494113045190893e-06, \"Eye Strain / CVS\": 3.692401574557604e-09, \"Hyperopia\": 0.9999982601487605, \"Light Sensitivity\": 2.8212650863172475e-09, \"Myopia\": 1.3001035564354451e-08, \"Presbyopia\": 4.464257267934695e-09}', '2025-12-09 06:17:57');

-- --------------------------------------------------------

--
-- Table structure for table `eye_symptoms`
--

CREATE TABLE `eye_symptoms` (
  `symptom_id` varchar(36) NOT NULL,
  `user_id` varchar(36) NOT NULL,
  `eye_pain_frequency` int(11) DEFAULT 0 COMMENT 'Times per week',
  `blurry_vision_score` int(11) DEFAULT 0 COMMENT '1-10 scale',
  `light_sensitivity` enum('Yes','No') DEFAULT 'No',
  `eye_strains_per_day` int(11) DEFAULT 0,
  `family_history_eye_disease` tinyint(1) DEFAULT 0,
  `recorded_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `eye_symptoms`
--

INSERT INTO `eye_symptoms` (`symptom_id`, `user_id`, `eye_pain_frequency`, `blurry_vision_score`, `light_sensitivity`, `eye_strains_per_day`, `family_history_eye_disease`, `recorded_at`) VALUES
('38b01916-8cb0-4d18-bdb3-0a4d10c6da26', '571797fd-34b1-48c0-98db-9059edd8c762', 0, 5, 'Yes', 0, 1, '2025-12-11 20:14:30'),
('47f17f3b-ecdd-47b4-acf4-d3e42bebbad3', '571797fd-34b1-48c0-98db-9059edd8c762', 0, 1, 'No', 0, 0, '2025-12-12 17:50:41'),
('5c8db285-2f1c-4530-88ba-3e0b95d36da4', '571797fd-34b1-48c0-98db-9059edd8c762', 0, 1, 'No', 1, 0, '2025-12-11 16:09:34'),
('c5e8d0e2-5e7b-45e1-83e8-1de4dc83fc5d', '571797fd-34b1-48c0-98db-9059edd8c762', 21, 1, 'Yes', 12, 1, '2025-12-09 14:17:58'),
('symptom-001', 'test-user-001', 2, 4, 'Yes', 3, 0, '2025-12-09 13:42:10');

-- --------------------------------------------------------

--
-- Table structure for table `feedback`
--

CREATE TABLE `feedback` (
  `feedback_id` int(11) NOT NULL,
  `user_id` varchar(36) NOT NULL,
  `username` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `rating` int(11) NOT NULL CHECK (`rating` >= 1 and `rating` <= 5),
  `category` varchar(100) NOT NULL,
  `comment` text NOT NULL,
  `submitted_at` datetime NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `feedback`
--

INSERT INTO `feedback` (`feedback_id`, `user_id`, `username`, `email`, `rating`, `category`, `comment`, `submitted_at`, `created_at`) VALUES
(1, '571797fd-34b1-48c0-98db-9059edd8c762', 'John', 'Johnvincentbilolo@gmail.com', 2, 'Assessment Accuracy', 'dsadsa', '2025-12-13 01:29:28', '2025-12-12 17:29:30');

-- --------------------------------------------------------

--
-- Table structure for table `habit_data`
--

CREATE TABLE `habit_data` (
  `habit_id` varchar(36) NOT NULL,
  `user_id` varchar(36) NOT NULL,
  `screen_time_hours` decimal(4,2) DEFAULT NULL,
  `sleep_hours` decimal(4,2) DEFAULT NULL,
  `diet_quality` int(11) DEFAULT NULL COMMENT '1-10 scale',
  `smoking_status` enum('Yes','No','Former') DEFAULT 'No',
  `alcohol_use` tinyint(1) DEFAULT 0,
  `outdoor_activity_hours` decimal(4,2) DEFAULT NULL,
  `water_intake_liters` decimal(4,2) DEFAULT NULL,
  `physical_activity_level` enum('Low','Moderate','High') DEFAULT 'Moderate',
  `glasses_usage` tinyint(1) DEFAULT 0,
  `recorded_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `habit_data`
--

INSERT INTO `habit_data` (`habit_id`, `user_id`, `screen_time_hours`, `sleep_hours`, `diet_quality`, `smoking_status`, `alcohol_use`, `outdoor_activity_hours`, `water_intake_liters`, `physical_activity_level`, `glasses_usage`, `recorded_at`) VALUES
('046da3ab-d782-11f0-a550-141333afcd02', '571797fd-34b1-48c0-98db-9059edd8c762', 6.00, 5.00, 5, 'Yes', 0, NULL, 2.00, 'Moderate', 0, '2025-12-12 17:42:46'),
('10893b62-d782-11f0-a550-141333afcd02', '571797fd-34b1-48c0-98db-9059edd8c762', 6.00, 5.00, 5, 'Yes', 0, NULL, 2.00, 'Moderate', 0, '2025-12-12 17:43:06'),
('1f8385ab-090e-4958-bd0a-5da300ab19f3', '571797fd-34b1-48c0-98db-9059edd8c762', 6.00, 5.00, 10, 'Yes', 0, 1.00, 2.00, 'Moderate', 0, '2025-12-11 20:14:30'),
('209423c7-d782-11f0-a550-141333afcd02', '571797fd-34b1-48c0-98db-9059edd8c762', 6.00, 5.00, 5, 'Yes', 0, NULL, 2.00, 'Moderate', 0, '2025-12-12 17:43:33'),
('25461241-d8c3-11f0-a550-141333afcd02', '571797fd-34b1-48c0-98db-9059edd8c762', 8.00, 8.00, 5, 'No', 0, NULL, 3.00, 'High', 0, '2025-12-14 08:01:01'),
('4de1d639-e4b9-48d5-8d57-562910c1a3cf', '571797fd-34b1-48c0-98db-9059edd8c762', 4.00, 4.00, 1, 'Yes', 1, 1.00, 1.00, 'High', 1, '2025-12-09 14:17:58'),
('83372c63-b58f-446d-a722-b2765447201e', '571797fd-34b1-48c0-98db-9059edd8c762', 8.00, 8.00, 10, 'No', 0, 4.00, 3.00, 'High', 0, '2025-12-12 17:50:41'),
('a1ac7cf7-d782-11f0-a550-141333afcd02', '571797fd-34b1-48c0-98db-9059edd8c762', 6.00, 5.00, 5, 'Yes', 0, NULL, 2.00, 'Moderate', 0, '2025-12-12 17:47:09'),
('b0d14c65-cbcb-44b8-a3a4-b27d20a972f1', '571797fd-34b1-48c0-98db-9059edd8c762', 6.00, 7.00, 5, 'No', 0, 4.00, 2.00, 'Moderate', 0, '2025-12-11 16:09:34'),
('e660f3b1-d780-11f0-a550-141333afcd02', '571797fd-34b1-48c0-98db-9059edd8c762', 6.00, 5.00, 5, 'Yes', 0, NULL, 2.00, 'Moderate', 0, '2025-12-12 17:34:46'),
('habit-001', 'test-user-001', 7.00, 6.00, 5, 'No', 0, 2.00, 2.50, 'Moderate', 0, '2025-12-09 13:42:10');

-- --------------------------------------------------------

--
-- Table structure for table `health_records`
--

CREATE TABLE `health_records` (
  `record_id` varchar(36) NOT NULL,
  `user_id` varchar(36) NOT NULL,
  `age` int(11) DEFAULT NULL,
  `gender` enum('Male','Female','Other') DEFAULT NULL,
  `bmi` decimal(5,2) DEFAULT NULL,
  `medical_history` text DEFAULT NULL,
  `blood_pressure` varchar(20) DEFAULT NULL,
  `blood_sugar` varchar(20) DEFAULT NULL,
  `diabetes` tinyint(1) DEFAULT 0,
  `hypertension` tinyint(1) DEFAULT 0,
  `previous_eye_surgery` tinyint(1) DEFAULT 0,
  `date_recorded` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `health_records`
--

INSERT INTO `health_records` (`record_id`, `user_id`, `age`, `gender`, `bmi`, `medical_history`, `blood_pressure`, `blood_sugar`, `diabetes`, `hypertension`, `previous_eye_surgery`, `date_recorded`) VALUES
('04670e73-d782-11f0-a550-141333afcd02', '571797fd-34b1-48c0-98db-9059edd8c762', 21, NULL, NULL, NULL, NULL, NULL, 0, 0, 0, '2025-12-12'),
('1082930b-d782-11f0-a550-141333afcd02', '571797fd-34b1-48c0-98db-9059edd8c762', 21, NULL, NULL, NULL, NULL, NULL, 0, 0, 0, '2025-12-12'),
('2088696d-d782-11f0-a550-141333afcd02', '571797fd-34b1-48c0-98db-9059edd8c762', 21, NULL, NULL, NULL, NULL, NULL, 0, 0, 0, '2025-12-12'),
('247a9c65-5f0d-476e-abd8-0bec61256bc0', '571797fd-34b1-48c0-98db-9059edd8c762', 21, 'Male', 27.29, NULL, NULL, NULL, 0, 0, 0, '2025-12-12'),
('25373925-d8c3-11f0-a550-141333afcd02', '571797fd-34b1-48c0-98db-9059edd8c762', 21, NULL, NULL, NULL, NULL, NULL, 0, 0, 0, '2025-12-14'),
('39bfd81f-f123-4de5-9bd3-d1547f70a7ac', '571797fd-34b1-48c0-98db-9059edd8c762', 23, 'Male', 23.34, NULL, NULL, NULL, 0, 1, 0, '2025-12-11'),
('855bbf22-1ce6-463a-b5b9-698d276b7d4d', '571797fd-34b1-48c0-98db-9059edd8c762', 21, 'Male', 27.29, NULL, NULL, NULL, 0, 0, 0, '2025-12-11'),
('85ac6e37-12ff-4972-89e5-67a9c9c7eaef', '571797fd-34b1-48c0-98db-9059edd8c762', 12, 'Male', 23.00, NULL, NULL, NULL, 1, 0, 1, '2025-12-09'),
('a1a4db88-d782-11f0-a550-141333afcd02', '571797fd-34b1-48c0-98db-9059edd8c762', 21, NULL, NULL, NULL, NULL, NULL, 0, 0, 0, '2025-12-12'),
('e628b5d5-d780-11f0-a550-141333afcd02', '571797fd-34b1-48c0-98db-9059edd8c762', 21, NULL, NULL, NULL, NULL, NULL, 0, 0, 0, '2025-12-12'),
('record-001', 'test-user-001', 28, 'Male', 24.50, NULL, NULL, NULL, 0, 0, 0, '2025-12-09');

-- --------------------------------------------------------

--
-- Table structure for table `health_tips`
--

CREATE TABLE `health_tips` (
  `tip_id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text NOT NULL,
  `category` varchar(100) DEFAULT NULL,
  `icon` varchar(50) DEFAULT NULL,
  `risk_level` enum('Low','Moderate','High','All') DEFAULT 'All',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `health_tips`
--

INSERT INTO `health_tips` (`tip_id`, `title`, `description`, `category`, `icon`, `risk_level`, `created_at`) VALUES
(1, 'Follow 20-20-20 Rule', 'Every 20 minutes, look at something 20 feet away for 20 seconds to reduce eye strain.', 'Screen Time', 'screen_time', 'All', '2025-12-09 13:42:10'),
(2, 'Get Adequate Sleep', 'Aim for 7-9 hours of quality sleep per night to allow your eyes to rest and recover.', 'Sleep', 'sleep', 'All', '2025-12-09 13:42:10'),
(3, 'Stay Hydrated', 'Drink 6-8 glasses of water daily to prevent dry eyes and maintain eye health.', 'Hydration', 'water_drop', 'All', '2025-12-09 13:42:10'),
(4, 'Eat Eye-Healthy Foods', 'Include leafy greens, fish rich in omega-3, and colorful vegetables in your diet.', 'Nutrition', 'restaurant', 'All', '2025-12-09 13:42:10'),
(5, 'Wear UV Protection', 'Use sunglasses with UV protection when outdoors to prevent long-term eye damage.', 'Protection', 'sunny', 'All', '2025-12-09 13:42:10'),
(6, 'Reduce Screen Time', 'Limit continuous screen exposure to 6 hours or less per day when possible.', 'Screen Time', 'screen_time', 'Moderate', '2025-12-09 13:42:10'),
(7, 'Regular Eye Checkups', 'Schedule comprehensive eye exams every 1-2 years, or more frequently if recommended.', 'Prevention', 'health_and_safety', 'High', '2025-12-09 13:42:10'),
(8, 'Quit Smoking', 'Smoking increases risk of cataracts, macular degeneration, and other eye diseases.', 'Lifestyle', 'smoke_free', 'High', '2025-12-09 13:42:10'),
(9, 'Exercise Regularly', 'Physical activity improves blood circulation and reduces risk of eye diseases.', 'Physical Activity', 'fitness_center', 'All', '2025-12-09 13:42:10'),
(10, 'Manage Chronic Conditions', 'Keep diabetes and hypertension under control to prevent eye complications.', 'Medical', 'medical_services', 'High', '2025-12-09 13:42:10');

-- --------------------------------------------------------

--
-- Table structure for table `ml_metrics`
--

CREATE TABLE `ml_metrics` (
  `id` int(11) NOT NULL,
  `model_version` varchar(50) NOT NULL,
  `accuracy` decimal(5,4) DEFAULT NULL,
  `precision` decimal(5,4) DEFAULT NULL,
  `recall` decimal(5,4) DEFAULT NULL,
  `f1_score` decimal(5,4) DEFAULT NULL,
  `confusion_matrix` text DEFAULT NULL COMMENT 'JSON format',
  `feature_importance` text DEFAULT NULL COMMENT 'JSON format',
  `training_date` timestamp NOT NULL DEFAULT current_timestamp(),
  `dataset_size` int(11) DEFAULT NULL,
  `notes` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `ml_metrics`
--

INSERT INTO `ml_metrics` (`id`, `model_version`, `accuracy`, `precision`, `recall`, `f1_score`, `confusion_matrix`, `feature_importance`, `training_date`, `dataset_size`, `notes`) VALUES
(2, 'LightGBM-20251209-230220', 1.0000, 1.0000, 1.0000, 1.0000, '[[70, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 785, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 194, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 883, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 80, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 156, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 442, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 31, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 111, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 248]]', '{\"Age\": 4346.0, \"Eye_Strains_Per_Day\": 2847.0, \"Light_Sensitivity\": 2395.0, \"Blurry_Vision_Score\": 2234.0, \"Eye_Pain_Frequency\": 1806.0, \"Outdoor_Exposure_Hours\": 1693.0, \"Water_Intake_Liters\": 1669.0, \"Screen_Time_Hours\": 1593.0, \"Risk Score\": 1510.0, \"Glasses_Usage\": 1442.0, \"BMI\": 460.0, \"Sleep_Hours\": 240.0, \"Previous_Eye_Surgery\": 167.0, \"Physical_Activity_Level\": 142.0, \"Diet_Score\": 139.0, \"Hypertension\": 91.0, \"Gender_Male\": 66.0, \"Alcohol_Use\": 63.0, \"Family_History_Eye_Disease\": 41.0, \"Smoker\": 40.0, \"Diabetes\": 22.0}', '2025-12-09 07:02:20', 15000, NULL),
(3, 'LightGBM-20251209-230503', 1.0000, 1.0000, 1.0000, 1.0000, '[[70, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 785, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 194, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 883, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 80, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 156, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 442, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 31, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 111, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 248]]', '{\"Age\": 4346.0, \"Eye_Strains_Per_Day\": 2847.0, \"Light_Sensitivity\": 2395.0, \"Blurry_Vision_Score\": 2234.0, \"Eye_Pain_Frequency\": 1806.0, \"Outdoor_Exposure_Hours\": 1693.0, \"Water_Intake_Liters\": 1669.0, \"Screen_Time_Hours\": 1593.0, \"Risk Score\": 1510.0, \"Glasses_Usage\": 1442.0, \"BMI\": 460.0, \"Sleep_Hours\": 240.0, \"Previous_Eye_Surgery\": 167.0, \"Physical_Activity_Level\": 142.0, \"Diet_Score\": 139.0, \"Hypertension\": 91.0, \"Gender_Male\": 66.0, \"Alcohol_Use\": 63.0, \"Family_History_Eye_Disease\": 41.0, \"Smoker\": 40.0, \"Diabetes\": 22.0}', '2025-12-09 07:05:04', 15000, '{\"algorithm\": \"LightGBM Classifier\", \"n_classes\": 10, \"classes\": [\"Allergic Conjunctivitis\", \"Astigmatism\", \"Blurred Vision\", \"Cataract\", \"Dry Eye\", \"Eye Strain / CVS\", \"Hyperopia\", \"Light Sensitivity\", \"Myopia\", \"Presbyopia\"], \"train_samples\": 12000, \"test_samples\": 3000, \"n_features\": 21, \"feature_names\": [\"Age\", \"BMI\", \"Screen_Time_Hours\", \"Sleep_Hours\", \"Smoker\", \"Alcohol_Use\", \"Diabetes\", \"Hypertension\", \"Family_History_Eye_Disease\", \"Eye_Pain_Frequency\", \"Blurry_Vision_Score\", \"Light_Sensitivity\", \"Eye_Strains_Per_Day\", \"Outdoor_Exposure_Hours\", \"Diet_Score\", \"Water_Intake_Liters\", \"Glasses_Usage\", \"Previous_Eye_Surgery\", \"Physical_Activity_Level\", \"Risk Score\", \"Gender_Male\"], \"classification_report\": {\"classes\": {\"Allergic Conjunctivitis\": {\"precision\": 1.0, \"recall\": 1.0, \"f1-score\": 1.0, \"support\": 70.0}, \"Astigmatism\": {\"precision\": 1.0, \"recall\": 1.0, \"f1-score\": 1.0, \"support\": 785.0}, \"Blurred Vision\": {\"precision\": 1.0, \"recall\": 1.0, \"f1-score\": 1.0, \"support\": 194.0}, \"Cataract\": {\"precision\": 1.0, \"recall\": 1.0, \"f1-score\": 1.0, \"support\": 883.0}, \"Dry Eye\": {\"precision\": 1.0, \"recall\": 1.0, \"f1-score\": 1.0, \"support\": 80.0}, \"Eye Strain / CVS\": {\"precision\": 1.0, \"recall\": 1.0, \"f1-score\": 1.0, \"support\": 156.0}, \"Hyperopia\": {\"precision\": 1.0, \"recall\": 1.0, \"f1-score\": 1.0, \"support\": 442.0}, \"Light Sensitivity\": {\"precision\": 1.0, \"recall\": 1.0, \"f1-score\": 1.0, \"support\": 31.0}, \"Myopia\": {\"precision\": 1.0, \"recall\": 1.0, \"f1-score\": 1.0, \"support\": 111.0}, \"Presbyopia\": {\"precision\": 1.0, \"recall\": 1.0, \"f1-score\": 1.0, \"support\": 248.0}}, \"weighted_avg\": {\"precision\": 1.0, \"recall\": 1.0, \"f1-score\": 1.0}, \"accuracy\": 1.0}, \"random_state\": 42}');

-- --------------------------------------------------------

--
-- Stand-in structure for view `ml_metrics_summary`
-- (See below for the actual view)
--
CREATE TABLE `ml_metrics_summary` (
`model_version` varchar(50)
,`accuracy` decimal(5,4)
,`precision` decimal(5,4)
,`recall` decimal(5,4)
,`f1_score` decimal(5,4)
,`dataset_size` int(11)
,`training_date` timestamp
,`accuracy_rank` bigint(21)
,`recency_rank` bigint(21)
);

-- --------------------------------------------------------

--
-- Table structure for table `recommendations`
--

CREATE TABLE `recommendations` (
  `recommendation_id` varchar(36) NOT NULL,
  `assessment_id` varchar(36) NOT NULL,
  `recommendation_text` text NOT NULL,
  `priority` enum('High','Medium','Low') DEFAULT 'Medium',
  `category` varchar(100) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `recommendations`
--

INSERT INTO `recommendations` (`recommendation_id`, `assessment_id`, `recommendation_text`, `priority`, `category`, `created_at`) VALUES
('07e31008-ea34-4c2b-ab37-b975a729b652', 'e2a6d76b-1e12-4a79-8797-c784ad88888e', 'Increase water intake to 6-8 glasses daily', 'Medium', 'Nutrition', '2025-12-09 14:17:58'),
('22fe638c-97bc-4174-bb93-a7788d62aa15', '012f1019-05ce-4f06-a8c9-74120d9e31da', 'Reduce screen time and follow 20-20-20 rule', 'High', 'Lifestyle', '2025-12-12 17:50:40'),
('40a304a4-00c7-41dc-a431-790c62833eff', '24e1f19d-7896-424d-8422-df1cd70b4ff5', 'Improve sleep to 7-9 hours per night', 'High', 'Lifestyle', '2025-12-11 20:14:29'),
('52e3fce9-5b46-4090-82c6-01727f52be1d', 'a8cb526a-c1bf-49ff-8b4a-47876436ecc3', 'Maintain regular eye check-ups every 12 months', 'Low', 'Prevention', '2025-12-11 16:09:34'),
('6c639c12-a2f0-4e8e-8fcc-8cdd2f7de50e', '012f1019-05ce-4f06-a8c9-74120d9e31da', 'Maintain regular eye check-ups every 12 months', 'Low', 'Prevention', '2025-12-12 17:50:40'),
('788b6b13-72ab-49c1-bfc7-ffa9a7311656', '24e1f19d-7896-424d-8422-df1cd70b4ff5', 'Quit smoking to reduce eye disease risk', 'High', 'Lifestyle', '2025-12-11 20:14:29'),
('ad99a1af-a7f8-40e9-b0e2-3e561ed60566', '24e1f19d-7896-424d-8422-df1cd70b4ff5', 'Maintain regular eye check-ups every 12 months', 'Low', 'Prevention', '2025-12-11 20:14:29'),
('dd5258f2-8c38-48f2-b8eb-ec649d652775', 'e2a6d76b-1e12-4a79-8797-c784ad88888e', 'Improve sleep to 7-9 hours per night', 'High', 'Lifestyle', '2025-12-09 14:17:58'),
('e96a3f6f-051e-4cc8-a3e2-54b63de99605', 'e2a6d76b-1e12-4a79-8797-c784ad88888e', 'Quit smoking to reduce eye disease risk', 'High', 'Lifestyle', '2025-12-09 14:17:58'),
('f53913c2-52ee-42cf-8772-a12c854748b5', 'e2a6d76b-1e12-4a79-8797-c784ad88888e', 'Schedule eye check-up within 3-6 months', 'Medium', 'Medical', '2025-12-09 14:17:57');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` varchar(36) NOT NULL,
  `username` varchar(100) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `full_name` varchar(255) DEFAULT NULL,
  `phone_number` varchar(20) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `profile_picture` longblob DEFAULT NULL,
  `profile_picture_url` varchar(500) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `username`, `email`, `password_hash`, `full_name`, `phone_number`, `address`, `profile_picture`, `profile_picture_url`, `created_at`, `updated_at`) VALUES
('2469dd69-12b6-4b16-b03c-e782259dce7a', 'asikenn94', 'asikenn94@gmail.com', '68ea8a3df2e267f6a25801ce2ff19ac9517ca1d5aa85d5f33241475325e749c3', 'Kenn Asi', '09568638220', NULL, NULL, NULL, '2025-12-12 15:06:58', '2025-12-12 15:06:58'),
('3cf710fc-afb1-41d1-b6e5-25f84929f219', 'ako1', 'minatosan0949@gmail.com', '62baf9a3c5c58afb77b0aed3b84a0309b80f24a95c00ebdae16394b48c2fc00f', NULL, NULL, NULL, NULL, NULL, '2025-12-11 17:38:48', '2025-12-11 17:52:19'),
('571797fd-34b1-48c0-98db-9059edd8c762', 'John', 'Johnvincentbilolo@gmail.com', 'e9c02dbdf58734b63c484d51c7ba27b03cd21d6e228c4730ad8406da4db45475', 'John', '09493557890', 'kupal', NULL, 'http://192.168.1.11:5000/static/uploads/profile_pictures/profile_571797fd-34b1-48c0-98db-9059edd8c762_1765697351.282205.jpg', '2025-12-09 14:12:50', '2025-12-14 08:01:00'),
('9a841faf-b67e-43b1-8fcc-c5b693927b18', 'mika', 'mikavillegas169@gmail.com', '3a5b919a9e949c2bea978b47ad7e57c2429f74ab60d901413f295264ed390167', 'VILLEGASMIKA', '09625516917', NULL, NULL, NULL, '2025-12-12 15:10:11', '2025-12-12 15:10:11'),
('ec1710bb-0ef3-456e-8fbb-3bfb3ac998aa', 'test1', 'johnvincentbilolo355@gmail.com', 'e9c02dbdf58734b63c484d51c7ba27b03cd21d6e228c4730ad8406da4db45475', NULL, NULL, NULL, NULL, NULL, '2025-12-11 17:33:12', '2025-12-11 17:33:12'),
('test_user_123', 'test_user', 'test@example.com', 'hashed_password_placeholder', 'Test User', '1234567890', NULL, NULL, NULL, '2025-12-13 17:22:19', '2025-12-13 17:22:19'),
('test-user-001', 'testuser', 'test@eyecare.com', '9b71d224bd62f3785d96d46ad3ea3d73319bfbc2890caadae2dff72519673ca7', 'Test User', '+63 912 345 6789', NULL, NULL, NULL, '2025-12-09 13:42:09', '2025-12-09 13:42:09');

-- --------------------------------------------------------

--
-- Table structure for table `user_notifications`
--

CREATE TABLE `user_notifications` (
  `notification_id` varchar(36) NOT NULL,
  `user_id` varchar(36) NOT NULL,
  `title` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `type` enum('info','success','warning','error') DEFAULT 'info',
  `is_read` tinyint(1) DEFAULT 0,
  `link` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `user_notifications`
--

INSERT INTO `user_notifications` (`notification_id`, `user_id`, `title`, `message`, `type`, `is_read`, `link`, `created_at`) VALUES
('1b1ff4ea-d823-4cd9-993c-cbea6b631162', 'test_user_123', 'Warning', 'Please review this', 'warning', 1, NULL, '2025-12-13 17:27:24'),
('24a9c5d8-c04e-44ae-b8a7-9e63919ffd74', 'test_user_123', 'Error', 'Something went wrong', 'error', 1, NULL, '2025-12-13 17:22:21'),
('3a6b4763-e4cc-4e64-bbf0-660ea5b84ffd', 'test_user_123', 'Test Notification', 'This is a test notification message', 'success', 1, '/dashboard', '2025-12-13 17:27:23'),
('40a77ad2-c867-4265-a76f-a31e56b9b8e8', 'test_user_123', 'Warning', 'Please review this', 'warning', 1, NULL, '2025-12-13 17:22:21'),
('53e6e225-9993-4723-88f4-a6fb74ff5513', 'test_user_123', 'Error', 'Something went wrong', 'error', 1, NULL, '2025-12-13 17:27:24'),
('7a5695ca-7b33-48d3-9ac4-23f2ad3cecd4', 'test_user_123', 'Test Notification', 'This is a test notification message', 'success', 1, '/dashboard', '2025-12-13 17:22:21'),
('7ecb3672-14b3-40ab-87c0-393894ee25aa', 'test_user_123', 'Info', 'New information available', 'info', 1, NULL, '2025-12-13 17:27:24'),
('88f96bf7-aa16-41d4-a5f8-8678ebf163ea', 'test_user_123', 'Success', 'Operation completed', 'success', 1, NULL, '2025-12-13 17:27:24'),
('990954ab-555b-4802-985d-6f0bf3357dd1', 'test_user_123', 'Success', 'Operation completed', 'success', 1, NULL, '2025-12-13 17:22:21'),
('c6237cc9-d209-4f7c-80f7-f8901147c181', 'test_user_123', 'Info', 'New information available', 'info', 1, NULL, '2025-12-13 17:22:21'),
('notif-001', '571797fd-34b1-48c0-98db-9059edd8c762', 'Assessment Complete', 'Your latest eye health assessment has been completed. View your results.', 'success', 0, '/assessment', '2025-12-13 16:51:46'),
('notif-002', '571797fd-34b1-48c0-98db-9059edd8c762', 'Health Tip', 'Remember to follow the 20-20-20 rule to reduce eye strain.', 'info', 0, '/health-tips', '2025-12-13 16:51:46');

-- --------------------------------------------------------

--
-- Stand-in structure for view `user_profile_view`
-- (See below for the actual view)
--
CREATE TABLE `user_profile_view` (
`user_id` varchar(36)
,`username` varchar(100)
,`full_name` varchar(255)
,`email` varchar(255)
,`phone_number` varchar(20)
,`address` text
,`age` int(11)
,`gender` enum('Male','Female','Other')
,`bmi` decimal(5,2)
,`diabetes` tinyint(1)
,`hypertension` tinyint(1)
,`previous_eye_surgery` tinyint(1)
,`screen_time_hours` decimal(4,2)
,`sleep_hours` decimal(4,2)
,`diet_quality` int(11)
,`smoking_status` enum('Yes','No','Former')
,`alcohol_use` tinyint(1)
,`outdoor_activity_hours` decimal(4,2)
,`water_intake_liters` decimal(4,2)
,`physical_activity_level` enum('Low','Moderate','High')
,`glasses_usage` tinyint(1)
,`eye_pain_frequency` int(11)
,`blurry_vision_score` int(11)
,`light_sensitivity` enum('Yes','No')
,`eye_strains_per_day` int(11)
,`family_history_eye_disease` tinyint(1)
,`latest_risk_level` enum('Low','Moderate','High','Critical')
,`latest_risk_score` decimal(5,2)
,`latest_predicted_disease` varchar(100)
,`last_assessment_date` timestamp
);

-- --------------------------------------------------------

--
-- Structure for view `admin_activity_summary`
--
DROP TABLE IF EXISTS `admin_activity_summary`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `admin_activity_summary`  AS SELECT `a`.`id` AS `admin_id`, `a`.`username` AS `username`, `a`.`full_name` AS `full_name`, `a`.`role` AS `role`, count(`al`.`id`) AS `total_actions`, max(`al`.`created_at`) AS `last_activity`, `a`.`last_login` AS `last_login` FROM (`admins` `a` left join `activity_logs` `al` on(`a`.`id` = `al`.`admin_id`)) GROUP BY `a`.`id`, `a`.`username`, `a`.`full_name`, `a`.`role`, `a`.`last_login` ;

-- --------------------------------------------------------

--
-- Structure for view `ml_metrics_summary`
--
DROP TABLE IF EXISTS `ml_metrics_summary`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `ml_metrics_summary`  AS SELECT `ml_metrics`.`model_version` AS `model_version`, `ml_metrics`.`accuracy` AS `accuracy`, `ml_metrics`.`precision` AS `precision`, `ml_metrics`.`recall` AS `recall`, `ml_metrics`.`f1_score` AS `f1_score`, `ml_metrics`.`dataset_size` AS `dataset_size`, `ml_metrics`.`training_date` AS `training_date`, rank() over ( order by `ml_metrics`.`accuracy` desc) AS `accuracy_rank`, rank() over ( order by `ml_metrics`.`training_date` desc) AS `recency_rank` FROM `ml_metrics` ORDER BY `ml_metrics`.`training_date` DESC ;

-- --------------------------------------------------------

--
-- Structure for view `user_profile_view`
--
DROP TABLE IF EXISTS `user_profile_view`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `user_profile_view`  AS SELECT `u`.`user_id` AS `user_id`, `u`.`username` AS `username`, `u`.`full_name` AS `full_name`, `u`.`email` AS `email`, `u`.`phone_number` AS `phone_number`, `u`.`address` AS `address`, `hr`.`age` AS `age`, `hr`.`gender` AS `gender`, `hr`.`bmi` AS `bmi`, `hr`.`diabetes` AS `diabetes`, `hr`.`hypertension` AS `hypertension`, `hr`.`previous_eye_surgery` AS `previous_eye_surgery`, `hd`.`screen_time_hours` AS `screen_time_hours`, `hd`.`sleep_hours` AS `sleep_hours`, `hd`.`diet_quality` AS `diet_quality`, `hd`.`smoking_status` AS `smoking_status`, `hd`.`alcohol_use` AS `alcohol_use`, `hd`.`outdoor_activity_hours` AS `outdoor_activity_hours`, `hd`.`water_intake_liters` AS `water_intake_liters`, `hd`.`physical_activity_level` AS `physical_activity_level`, `hd`.`glasses_usage` AS `glasses_usage`, `es`.`eye_pain_frequency` AS `eye_pain_frequency`, `es`.`blurry_vision_score` AS `blurry_vision_score`, `es`.`light_sensitivity` AS `light_sensitivity`, `es`.`eye_strains_per_day` AS `eye_strains_per_day`, `es`.`family_history_eye_disease` AS `family_history_eye_disease`, `ar`.`risk_level` AS `latest_risk_level`, `ar`.`risk_score` AS `latest_risk_score`, `ar`.`predicted_disease` AS `latest_predicted_disease`, `ar`.`assessed_at` AS `last_assessment_date` FROM ((((`users` `u` left join (select `hr1`.`record_id` AS `record_id`,`hr1`.`user_id` AS `user_id`,`hr1`.`age` AS `age`,`hr1`.`gender` AS `gender`,`hr1`.`bmi` AS `bmi`,`hr1`.`medical_history` AS `medical_history`,`hr1`.`blood_pressure` AS `blood_pressure`,`hr1`.`blood_sugar` AS `blood_sugar`,`hr1`.`diabetes` AS `diabetes`,`hr1`.`hypertension` AS `hypertension`,`hr1`.`previous_eye_surgery` AS `previous_eye_surgery`,`hr1`.`date_recorded` AS `date_recorded` from `health_records` `hr1` where (`hr1`.`user_id`,`hr1`.`date_recorded`) in (select `health_records`.`user_id`,max(`health_records`.`date_recorded`) from `health_records` group by `health_records`.`user_id`)) `hr` on(`u`.`user_id` = `hr`.`user_id`)) left join (select `hd1`.`habit_id` AS `habit_id`,`hd1`.`user_id` AS `user_id`,`hd1`.`screen_time_hours` AS `screen_time_hours`,`hd1`.`sleep_hours` AS `sleep_hours`,`hd1`.`diet_quality` AS `diet_quality`,`hd1`.`smoking_status` AS `smoking_status`,`hd1`.`alcohol_use` AS `alcohol_use`,`hd1`.`outdoor_activity_hours` AS `outdoor_activity_hours`,`hd1`.`water_intake_liters` AS `water_intake_liters`,`hd1`.`physical_activity_level` AS `physical_activity_level`,`hd1`.`glasses_usage` AS `glasses_usage`,`hd1`.`recorded_at` AS `recorded_at` from `habit_data` `hd1` where (`hd1`.`user_id`,`hd1`.`recorded_at`) in (select `habit_data`.`user_id`,max(`habit_data`.`recorded_at`) from `habit_data` group by `habit_data`.`user_id`)) `hd` on(`u`.`user_id` = `hd`.`user_id`)) left join (select `es1`.`symptom_id` AS `symptom_id`,`es1`.`user_id` AS `user_id`,`es1`.`eye_pain_frequency` AS `eye_pain_frequency`,`es1`.`blurry_vision_score` AS `blurry_vision_score`,`es1`.`light_sensitivity` AS `light_sensitivity`,`es1`.`eye_strains_per_day` AS `eye_strains_per_day`,`es1`.`family_history_eye_disease` AS `family_history_eye_disease`,`es1`.`recorded_at` AS `recorded_at` from `eye_symptoms` `es1` where (`es1`.`user_id`,`es1`.`recorded_at`) in (select `eye_symptoms`.`user_id`,max(`eye_symptoms`.`recorded_at`) from `eye_symptoms` group by `eye_symptoms`.`user_id`)) `es` on(`u`.`user_id` = `es`.`user_id`)) left join (select `ar1`.`assessment_id` AS `assessment_id`,`ar1`.`user_id` AS `user_id`,`ar1`.`risk_level` AS `risk_level`,`ar1`.`risk_score` AS `risk_score`,`ar1`.`confidence_score` AS `confidence_score`,`ar1`.`predicted_disease` AS `predicted_disease`,`ar1`.`model_version` AS `model_version`,`ar1`.`assessment_data` AS `assessment_data`,`ar1`.`per_disease_scores` AS `per_disease_scores`,`ar1`.`assessed_at` AS `assessed_at` from `assessment_results` `ar1` where (`ar1`.`user_id`,`ar1`.`assessed_at`) in (select `assessment_results`.`user_id`,max(`assessment_results`.`assessed_at`) from `assessment_results` group by `assessment_results`.`user_id`)) `ar` on(`u`.`user_id` = `ar`.`user_id`)) ;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `activity_logs`
--
ALTER TABLE `activity_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_admin` (`admin_id`),
  ADD KEY `idx_created` (`created_at`),
  ADD KEY `idx_entity` (`entity_type`,`entity_id`),
  ADD KEY `idx_action` (`action`);

--
-- Indexes for table `admins`
--
ALTER TABLE `admins`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `idx_username` (`username`),
  ADD KEY `idx_email` (`email`),
  ADD KEY `idx_status` (`status`);

--
-- Indexes for table `admin_notifications`
--
ALTER TABLE `admin_notifications`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_admin_read` (`admin_id`,`is_read`),
  ADD KEY `idx_created` (`created_at`);

--
-- Indexes for table `admin_settings`
--
ALTER TABLE `admin_settings`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `setting_key` (`setting_key`),
  ADD KEY `updated_by` (`updated_by`),
  ADD KEY `idx_key` (`setting_key`);

--
-- Indexes for table `assessment_results`
--
ALTER TABLE `assessment_results`
  ADD PRIMARY KEY (`assessment_id`),
  ADD KEY `idx_user_assessed` (`user_id`,`assessed_at`),
  ADD KEY `idx_risk_level` (`risk_level`),
  ADD KEY `idx_assessed_at` (`assessed_at`);

--
-- Indexes for table `eye_symptoms`
--
ALTER TABLE `eye_symptoms`
  ADD PRIMARY KEY (`symptom_id`),
  ADD KEY `idx_user_symptoms` (`user_id`,`recorded_at`);

--
-- Indexes for table `feedback`
--
ALTER TABLE `feedback`
  ADD PRIMARY KEY (`feedback_id`),
  ADD KEY `idx_user_id` (`user_id`),
  ADD KEY `idx_submitted_at` (`submitted_at`);

--
-- Indexes for table `habit_data`
--
ALTER TABLE `habit_data`
  ADD PRIMARY KEY (`habit_id`),
  ADD KEY `idx_user_recorded` (`user_id`,`recorded_at`);

--
-- Indexes for table `health_records`
--
ALTER TABLE `health_records`
  ADD PRIMARY KEY (`record_id`),
  ADD KEY `idx_user_date` (`user_id`,`date_recorded`);

--
-- Indexes for table `health_tips`
--
ALTER TABLE `health_tips`
  ADD PRIMARY KEY (`tip_id`),
  ADD KEY `idx_risk_level` (`risk_level`),
  ADD KEY `idx_category` (`category`);

--
-- Indexes for table `ml_metrics`
--
ALTER TABLE `ml_metrics`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_version` (`model_version`),
  ADD KEY `idx_training_date` (`training_date`);

--
-- Indexes for table `recommendations`
--
ALTER TABLE `recommendations`
  ADD PRIMARY KEY (`recommendation_id`),
  ADD KEY `idx_assessment` (`assessment_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `idx_username` (`username`),
  ADD KEY `idx_email` (`email`);

--
-- Indexes for table `user_notifications`
--
ALTER TABLE `user_notifications`
  ADD PRIMARY KEY (`notification_id`),
  ADD KEY `user_id_idx` (`user_id`),
  ADD KEY `is_read_idx` (`is_read`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `activity_logs`
--
ALTER TABLE `activity_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `admins`
--
ALTER TABLE `admins`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `admin_notifications`
--
ALTER TABLE `admin_notifications`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `admin_settings`
--
ALTER TABLE `admin_settings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `feedback`
--
ALTER TABLE `feedback`
  MODIFY `feedback_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `health_tips`
--
ALTER TABLE `health_tips`
  MODIFY `tip_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `ml_metrics`
--
ALTER TABLE `ml_metrics`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `activity_logs`
--
ALTER TABLE `activity_logs`
  ADD CONSTRAINT `activity_logs_ibfk_1` FOREIGN KEY (`admin_id`) REFERENCES `admins` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `admin_notifications`
--
ALTER TABLE `admin_notifications`
  ADD CONSTRAINT `admin_notifications_ibfk_1` FOREIGN KEY (`admin_id`) REFERENCES `admins` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `admin_settings`
--
ALTER TABLE `admin_settings`
  ADD CONSTRAINT `admin_settings_ibfk_1` FOREIGN KEY (`updated_by`) REFERENCES `admins` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `assessment_results`
--
ALTER TABLE `assessment_results`
  ADD CONSTRAINT `assessment_results_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `eye_symptoms`
--
ALTER TABLE `eye_symptoms`
  ADD CONSTRAINT `eye_symptoms_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `feedback`
--
ALTER TABLE `feedback`
  ADD CONSTRAINT `feedback_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `habit_data`
--
ALTER TABLE `habit_data`
  ADD CONSTRAINT `habit_data_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `health_records`
--
ALTER TABLE `health_records`
  ADD CONSTRAINT `health_records_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `recommendations`
--
ALTER TABLE `recommendations`
  ADD CONSTRAINT `recommendations_ibfk_1` FOREIGN KEY (`assessment_id`) REFERENCES `assessment_results` (`assessment_id`) ON DELETE CASCADE;

--
-- Constraints for table `user_notifications`
--
ALTER TABLE `user_notifications`
  ADD CONSTRAINT `user_notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
