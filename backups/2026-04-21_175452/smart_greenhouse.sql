-- MySQL dump 10.13  Distrib 8.0.45, for Linux (x86_64)
--
-- Host: localhost    Database: smart_greenhouse
-- ------------------------------------------------------
-- Server version	8.0.45

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

--
-- Table structure for table `ai_conversation_messages`
--

DROP TABLE IF EXISTS `ai_conversation_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_conversation_messages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `conversation_id` int NOT NULL,
  `role` varchar(20) NOT NULL,
  `content` text NOT NULL,
  `reasoning` text,
  `source` varchar(64) DEFAULT NULL,
  `model` varchar(80) DEFAULT NULL,
  `citations_json` text,
  `web_search_notice` text,
  `status` varchar(20) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_ai_conversation_messages_created_at` (`created_at`),
  KEY `ix_ai_conversation_messages_conversation_id` (`conversation_id`),
  KEY `ix_ai_conversation_messages_role` (`role`),
  KEY `ix_ai_conversation_messages_id` (`id`),
  CONSTRAINT `ai_conversation_messages_ibfk_1` FOREIGN KEY (`conversation_id`) REFERENCES `ai_conversations` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_conversation_messages`
--

LOCK TABLES `ai_conversation_messages` WRITE;
/*!40000 ALTER TABLE `ai_conversation_messages` DISABLE KEYS */;
INSERT INTO `ai_conversation_messages` VALUES (1,1,'user','hi',NULL,NULL,NULL,NULL,NULL,'done','2026-04-17 11:31:26'),(2,1,'assistant','Hi! How can I help you today?',NULL,'deepseek-langchain','deepseek-chat',NULL,NULL,'done','2026-04-17 11:31:30'),(3,1,'user','你可以为我做什么',NULL,NULL,NULL,NULL,NULL,'done','2026-04-17 11:31:38'),(4,1,'assistant','我可以为你提供以下帮助：\n\n**平台管理**\n- 用户与权限管理（教师、学生、家长账户）\n- 课程与班级设置\n- 学习进度跟踪与报告生成\n- 系统配置与维护\n\n**数据分析**\n- 学习行为分析（参与度、完成率、成绩趋势）\n- 内容使用统计\n- 生成可视化报表\n\n**内容支持**\n- 课程材料上传与管理\n- 作业与考试创建\n- 讨论区管理\n\n**技术协助**\n- 平台使用指导\n- 故障排查\n- 集成第三方工具建议\n\n**温室环境监控**（如相关）\n- 查看实时传感器数据\n- 环境趋势分析\n- 设备控制建议\n\n请告诉我你需要哪方面的帮助，或者具体想了解什么功能？',NULL,'deepseek-langchain','deepseek-chat',NULL,NULL,'done','2026-04-17 11:31:46'),(5,2,'user','现在打棚的状况怎么样',NULL,NULL,NULL,NULL,NULL,'done','2026-04-17 11:35:21'),(6,2,'assistant','根据最新的传感器数据，当前温室大棚的环境状况如下：\n\n**总体评价**：环境参数基本正常，适合多数作物生长，但部分指标需留意。\n\n**关键数据**：\n- **温度**：26.1°C（日间适宜）\n- **湿度**：68%（稍偏高，注意通风）\n- **光照**：40000 lux（较强，建议检查遮光是否需要调节）\n- **二氧化碳浓度**：740 ppm（略低于最优水平，可适量通风或补充）\n- **土壤湿度**：36%（偏干，建议检查灌溉）\n\n**建议操作**：\n1. 若种植喜光作物，当前光照充足；若为耐阴作物，考虑部分遮光。\n2. 湿度偏高，可适当开窗或启动通风系统，预防病害。\n3. 土壤湿度较低，检查灌溉系统是否正常工作。\n\n需要更详细的某个参数历史趋势或调整具体设备吗？','嗯，用户问的是“现在打棚的状况怎么样”，这应该是指温室大棚的当前状况。我需要根据温室环境数据来回答，但先得确认用户具体关心哪些方面。\n\n考虑到用户可能想了解整体运行情况，我可以从几个关键指标入手。温度、湿度和光照通常是温室管理的核心参数。对了，还有二氧化碳浓度和土壤湿度，这些对植物生长也很重要。\n\n我需要检查这些数据是否在正常范围内。温度26.1℃对大多数作物来说很合适，湿度68%稍微偏高但问题不大。光照40000lux很强，可能需要部分遮光。二氧化碳740ppm略低，土壤湿度36%偏干。\n\n最好把这些数据组织成清晰的格式，让用户一目了然。可以先用一个总结性的评价，再列出具体数据。可能需要建议用户调节遮光和灌溉，因为光照太强而土壤偏干。\n\n不过要避免过度解读数据，毕竟我不清楚大棚里具体种的是什么作物。不同作物对环境的要求可能不同。所以我的建议应该比较通用，同时提醒用户根据实际情况调整。','deepseek-langchain','deepseek-reasoner',NULL,'暂未检索到高相关来源，已自动提供通用回答。','done','2026-04-17 11:35:41'),(7,2,'user','hi',NULL,NULL,NULL,NULL,NULL,'done','2026-04-20 06:44:10'),(8,2,'assistant','Hi！\n\n在英语问候中，“Hi”和“Hello”的常见区别是：“Hi”通常更口语化、随意，多用于朋友或熟人之间；而“Hello”则相对更正式、中性一些，也常用于接电话或与不太熟悉的人打招呼 [1][2]。\n\n有什么需要我帮助的吗？','好的，用户现在说“hi”，看起来是个简单的问候。根据之前的对话历史，用户之前问过温室大棚的状况，我提供了详细的传感器数据和建议，但这次完全没提温室相关的事。\n\n嗯，我得先确定当前是否需要沿用温室话题。用户只发了“hi”，很可能只是打个招呼或者想开始新对话，所以不应该强行关联到之前的温室讨论。\n\n用户身份是管理员，可能在测试或者随意发起对话。深层需求也许是希望确认助理的响应模式，或者单纯想看看我会怎么处理普通问候。\n\n现在看看提供的网络上下文，有关于“hi”和“hello”区别的资料 [1][2]。这些信息很适合用来回应问候，同时解释用词的细微差别，这样既自然又有教育意义。\n\n另外，网络上下文里还有音乐网站关闭的新闻 [3]，但跟当前对话完全无关，绝对不能提这个。我得确保回答只聚焦在问候语的相关信息上。\n\n考虑到用户用英文“hi”打招呼，我可以先用“Hi!”友好回应，然后简要说明“hi”和“hello”的区别，这样既亲切又能提供实用知识。最后以开放性问题结束，询问是否需要其他帮助，保持对话流畅。\n\n这样处理既直接回应了问候，又利用了可用的网络信息，而且完全符合用户可能的期望——一个自然、有帮助的助理回应。','deepseek-langchain','deepseek-reasoner','[{\"title\": \"hello和hi的区别用法 - 百度知道\", \"url\": \"https://zhidao.baidu.com/question/2150406640507608748.html\", \"snippet\": \"hello：用于问候、接电话或引起注意。侧重于正式场合，不熟悉的人之间使用。hi：用于打招呼。侧重于非常正式场合，熟人之间的对话。 1、汉语解释方面，hello的意思是你好，hi的意思只是打招呼。比如，电话里我们接到不熟悉人电话，我们不会说hi，那是打招呼，一般我们用hello，你好。2、使用 ...\"}, {\"title\": \"Hi和Hello有什么区别? - 百度知道\", \"url\": \"https://zhidao.baidu.com/question/47148622.html\", \"snippet\": \"“Hello” 和“Hi”作为见面打招呼的用语，都有“嗨”、“你好”、“喂”的意思，用法是一样的，但是它们也存在一些细微的区别： 1、运用对象方面： “Hello”多是在比较正式的场合下使用，或者大家彼此还不太熟悉，或者年龄、身份等差距大的时候使用。 “Hi”则是一般朋友和同事之间用的 ...\"}]','已启用智能搜索，仅展示回答中引用的高相关来源。','done','2026-04-20 06:44:26'),(9,2,'user','你可以为我做什么',NULL,NULL,NULL,NULL,NULL,'done','2026-04-20 07:06:08'),(10,2,'assistant','作为教育平台管理员，我可以协助您处理以下事务：\n\n**🎯 平台管理与数据**\n- 查看温室传感器实时数据与历史趋势（温度、湿度、光照、CO₂、土壤湿度等）\n- 生成环境报告与异常预警\n- 管理用户账号、权限与课程/班级分配\n\n**📚 教学支持**\n- 设计课程模块、学习路径或评估方案\n- 整理教学资源（文档、视频、实验指南）\n- 协助制定基于温室场景的实践教案\n\n**🛠 运维与设备**\n- 提供温室设备操作建议（通风、灌溉、遮光等）\n- 分析环境数据与作物生长关联性\n- 协助安排维护任务或调试提示\n\n**💬 通用助手能力**\n- 回答知识性问题（农业、教育、技术等）\n- 文档撰写、格式整理、数据分析\n- 实时信息查询（若网络可用）\n\n如果您有具体需求——比如查看最近三天的温湿度曲线、创建新班级、调整灌溉计划，或需要某类教学模板——随时告诉我，我可以立即为您处理。','嗯，用户问了一个很常见的问题，想知道我能做什么。这是一个展示我能力范围的好机会，不需要复杂的分析，只需要清晰全面地列出我的功能。\n\n用户是管理员，可能更关心平台管理相关的功能，所以我把教育平台管理相关的功能放在前面，然后再提其他通用能力。这样既能突出角色特性，又不会遗漏基本信息。\n\n想到了用分块的方式来组织回复，先说明核心的教育平台管理能力，再补充通用助手功能，最后以邀请提问结尾。用列表形式会比较清晰，但思考过程中不需要标记格式。\n\n考虑到用户之前问过温室状况，可能对数据监控也有兴趣，所以把传感器数据分析也包含进去。整体要保持信息量大但条理分明，让用户一目了然。','deepseek-langchain','deepseek-reasoner',NULL,NULL,'done','2026-04-20 07:06:27');
/*!40000 ALTER TABLE `ai_conversation_messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ai_conversations`
--

DROP TABLE IF EXISTS `ai_conversations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_conversations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `title` varchar(120) NOT NULL,
  `is_pinned` tinyint(1) NOT NULL DEFAULT '0',
  `pinned_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `last_message_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_ai_conversations_user_id` (`user_id`),
  KEY `ix_ai_conversations_last_message_at` (`last_message_at`),
  KEY `ix_ai_conversations_pinned_at` (`pinned_at`),
  KEY `ix_ai_conversations_updated_at` (`updated_at`),
  KEY `ix_ai_conversations_id` (`id`),
  KEY `ix_ai_conversations_is_pinned` (`is_pinned`),
  KEY `ix_ai_conversations_created_at` (`created_at`),
  CONSTRAINT `ai_conversations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_conversations`
--

LOCK TABLES `ai_conversations` WRITE;
/*!40000 ALTER TABLE `ai_conversations` DISABLE KEYS */;
INSERT INTO `ai_conversations` VALUES (1,1,'你好',0,NULL,'2026-04-17 11:31:25','2026-04-17 11:31:46','2026-04-17 11:31:46'),(2,1,'大棚种植现状分析',0,NULL,'2026-04-17 11:34:56','2026-04-20 07:06:27','2026-04-20 07:06:27');
/*!40000 ALTER TABLE `ai_conversations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('0007_role_owner');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `assignment_submissions`
--

DROP TABLE IF EXISTS `assignment_submissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assignment_submissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `assignment_id` int DEFAULT NULL,
  `student_id` int DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `experiment_date` date DEFAULT NULL,
  `observations` text,
  `conclusion` text,
  `temp_records` text,
  `humidity_records` text,
  `soil_moisture_records` text,
  `light_records` text,
  `photos` text,
  `score` float DEFAULT NULL,
  `teacher_comment` text,
  `submitted_at` datetime DEFAULT NULL,
  `graded_at` datetime DEFAULT NULL,
  `graded_by` int DEFAULT NULL,
  `report_file_name` varchar(255) DEFAULT NULL,
  `report_file_path` varchar(500) DEFAULT NULL,
  `report_file_size` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_assignment_submissions_submitted_at` (`submitted_at`),
  KEY `ix_assignment_submissions_graded_at` (`graded_at`),
  KEY `ix_assignment_submissions_created_at` (`created_at`),
  KEY `ix_assignment_submissions_student_id` (`student_id`),
  KEY `ix_assignment_submissions_assignment_id` (`assignment_id`),
  KEY `ix_assignment_submissions_id` (`id`),
  KEY `ix_assignment_submissions_score` (`score`),
  KEY `ix_assignment_submissions_graded_by` (`graded_by`),
  KEY `ix_assignment_submissions_status` (`status`),
  KEY `ix_assignment_submissions_experiment_date` (`experiment_date`),
  CONSTRAINT `assignment_submissions_ibfk_1` FOREIGN KEY (`assignment_id`) REFERENCES `assignments` (`id`),
  CONSTRAINT `assignment_submissions_ibfk_2` FOREIGN KEY (`student_id`) REFERENCES `users` (`id`),
  CONSTRAINT `assignment_submissions_ibfk_3` FOREIGN KEY (`graded_by`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_assignment_submissions_graded_by_users` FOREIGN KEY (`graded_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assignment_submissions`
--

LOCK TABLES `assignment_submissions` WRITE;
/*!40000 ALTER TABLE `assignment_submissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `assignment_submissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `assignments`
--

DROP TABLE IF EXISTS `assignments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assignments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(200) NOT NULL,
  `description` text,
  `device_id` int DEFAULT NULL,
  `class_id` int DEFAULT NULL,
  `teacher_id` int DEFAULT NULL,
  `start_date` datetime DEFAULT NULL,
  `due_date` datetime DEFAULT NULL,
  `requirement` text,
  `template` text,
  `is_published` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_assignments_teacher_id` (`teacher_id`),
  KEY `ix_assignments_class_id` (`class_id`),
  KEY `ix_assignments_device_id` (`device_id`),
  KEY `ix_assignments_id` (`id`),
  KEY `ix_assignments_is_published` (`is_published`),
  CONSTRAINT `assignments_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`id`),
  CONSTRAINT `assignments_ibfk_2` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`),
  CONSTRAINT `assignments_ibfk_3` FOREIGN KEY (`teacher_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assignments`
--

LOCK TABLES `assignments` WRITE;
/*!40000 ALTER TABLE `assignments` DISABLE KEYS */;
/*!40000 ALTER TABLE `assignments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `class_device_binds`
--

DROP TABLE IF EXISTS `class_device_binds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `class_device_binds` (
  `id` int NOT NULL AUTO_INCREMENT,
  `class_id` int NOT NULL,
  `device_id` int NOT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uix_class_device` (`class_id`,`device_id`),
  KEY `ix_class_device_binds_id` (`id`),
  KEY `ix_class_device_binds_device_id` (`device_id`),
  KEY `ix_class_device_binds_class_id` (`class_id`),
  CONSTRAINT `class_device_binds_ibfk_1` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`),
  CONSTRAINT `class_device_binds_ibfk_2` FOREIGN KEY (`device_id`) REFERENCES `devices` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `class_device_binds`
--

LOCK TABLES `class_device_binds` WRITE;
/*!40000 ALTER TABLE `class_device_binds` DISABLE KEYS */;
/*!40000 ALTER TABLE `class_device_binds` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `classes`
--

DROP TABLE IF EXISTS `classes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `classes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `class_name` varchar(100) NOT NULL,
  `grade` varchar(20) DEFAULT NULL,
  `teacher_id` int DEFAULT NULL,
  `description` varchar(500) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_classes_id` (`id`),
  KEY `ix_classes_class_name` (`class_name`),
  KEY `ix_classes_teacher_id` (`teacher_id`),
  CONSTRAINT `classes_ibfk_1` FOREIGN KEY (`teacher_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `classes`
--

LOCK TABLES `classes` WRITE;
/*!40000 ALTER TABLE `classes` DISABLE KEYS */;
INSERT INTO `classes` VALUES (1,'三年级 1 班','三年级',2,'2024 级 1 班',1,'2026-04-17 11:00:02'),(2,'三年级 2 班','三年级',2,'2024 级 2 班',1,'2026-04-17 11:00:02'),(3,'四年级 1 班','四年级',2,'2023 级 1 班',1,'2026-04-17 11:00:02');
/*!40000 ALTER TABLE `classes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `content_categories`
--

DROP TABLE IF EXISTS `content_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `content_categories` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `parent_id` int DEFAULT NULL,
  `description` varchar(500) DEFAULT NULL,
  `sort_order` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `parent_id` (`parent_id`),
  KEY `ix_content_categories_id` (`id`),
  CONSTRAINT `content_categories_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `content_categories` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `content_categories`
--

LOCK TABLES `content_categories` WRITE;
/*!40000 ALTER TABLE `content_categories` DISABLE KEYS */;
INSERT INTO `content_categories` VALUES (1,'农作物习性',NULL,'各种农作物的生长习性和环境需求',1,'2026-04-17 11:00:02'),(2,'植物百科',NULL,'植物分类和特征介绍',2,'2026-04-17 11:00:02'),(3,'自然科学',NULL,'自然科学基础知识',3,'2026-04-17 11:00:02'),(4,'实验指导',NULL,'实验步骤和操作指南',4,'2026-04-17 11:00:02'),(5,'温度需求',1,'不同作物的温度适应性',1,'2026-04-17 11:00:02'),(6,'光照需求',1,'光照对作物生长的影响',2,'2026-04-17 11:00:02'),(7,'水分需求',1,'作物灌溉和水分管理',3,'2026-04-17 11:00:02'),(8,'土壤要求',1,'土壤类型和肥料需求',4,'2026-04-17 11:00:02');
/*!40000 ALTER TABLE `content_categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `content_comment_likes`
--

DROP TABLE IF EXISTS `content_comment_likes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `content_comment_likes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `comment_id` int NOT NULL,
  `user_id` int NOT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uix_comment_like_user` (`comment_id`,`user_id`),
  KEY `ix_content_comment_likes_id` (`id`),
  KEY `ix_content_comment_likes_created_at` (`created_at`),
  KEY `ix_content_comment_likes_comment_id` (`comment_id`),
  KEY `ix_content_comment_likes_user_id` (`user_id`),
  CONSTRAINT `content_comment_likes_ibfk_1` FOREIGN KEY (`comment_id`) REFERENCES `content_comments` (`id`),
  CONSTRAINT `content_comment_likes_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `content_comment_likes`
--

LOCK TABLES `content_comment_likes` WRITE;
/*!40000 ALTER TABLE `content_comment_likes` DISABLE KEYS */;
/*!40000 ALTER TABLE `content_comment_likes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `content_comments`
--

DROP TABLE IF EXISTS `content_comments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `content_comments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `content_id` int NOT NULL,
  `student_id` int NOT NULL,
  `parent_id` int DEFAULT NULL,
  `comment` text NOT NULL,
  `like_count` int DEFAULT NULL,
  `teacher_reply` text,
  `reply_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `content_id` (`content_id`),
  KEY `student_id` (`student_id`),
  KEY `ix_content_comments_parent_id` (`parent_id`),
  KEY `ix_content_comments_id` (`id`),
  CONSTRAINT `content_comments_ibfk_1` FOREIGN KEY (`content_id`) REFERENCES `teaching_contents` (`id`),
  CONSTRAINT `content_comments_ibfk_2` FOREIGN KEY (`student_id`) REFERENCES `users` (`id`),
  CONSTRAINT `content_comments_ibfk_3` FOREIGN KEY (`parent_id`) REFERENCES `content_comments` (`id`),
  CONSTRAINT `fk_content_comments_parent_id` FOREIGN KEY (`parent_id`) REFERENCES `content_comments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `content_comments`
--

LOCK TABLES `content_comments` WRITE;
/*!40000 ALTER TABLE `content_comments` DISABLE KEYS */;
/*!40000 ALTER TABLE `content_comments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `devices`
--

DROP TABLE IF EXISTS `devices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `devices` (
  `id` int NOT NULL AUTO_INCREMENT,
  `device_name` varchar(100) NOT NULL,
  `status` smallint DEFAULT NULL,
  `last_seen` datetime DEFAULT NULL,
  `pump_state` smallint DEFAULT NULL,
  `fan_state` smallint DEFAULT NULL,
  `light_state` smallint DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_devices_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `devices`
--

LOCK TABLES `devices` WRITE;
/*!40000 ALTER TABLE `devices` DISABLE KEYS */;
INSERT INTO `devices` VALUES (1,'Default greenhouse',1,'2026-04-20 07:39:26',0,0,0,'2026-04-17 11:00:02');
/*!40000 ALTER TABLE `devices` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `group_members`
--

DROP TABLE IF EXISTS `group_members`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `group_members` (
  `id` int NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `student_id` int NOT NULL,
  `role` varchar(20) DEFAULT NULL,
  `joined_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `group_id` (`group_id`),
  KEY `student_id` (`student_id`),
  KEY `ix_group_members_id` (`id`),
  CONSTRAINT `group_members_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `study_groups` (`id`),
  CONSTRAINT `group_members_ibfk_2` FOREIGN KEY (`student_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `group_members`
--

LOCK TABLES `group_members` WRITE;
/*!40000 ALTER TABLE `group_members` DISABLE KEYS */;
/*!40000 ALTER TABLE `group_members` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `growth_records`
--

DROP TABLE IF EXISTS `growth_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `growth_records` (
  `id` int NOT NULL AUTO_INCREMENT,
  `plant_id` int DEFAULT NULL,
  `record_date` date DEFAULT NULL,
  `stage` varchar(20) DEFAULT NULL,
  `height_cm` float DEFAULT NULL,
  `leaf_count` int DEFAULT NULL,
  `flower_count` int DEFAULT NULL,
  `fruit_count` int DEFAULT NULL,
  `description` text,
  `photos` text,
  `recorded_by` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `recorded_by` (`recorded_by`),
  KEY `ix_growth_records_plant_id` (`plant_id`),
  KEY `ix_growth_records_id` (`id`),
  CONSTRAINT `growth_records_ibfk_1` FOREIGN KEY (`plant_id`) REFERENCES `plant_profiles` (`id`),
  CONSTRAINT `growth_records_ibfk_2` FOREIGN KEY (`recorded_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `growth_records`
--

LOCK TABLES `growth_records` WRITE;
/*!40000 ALTER TABLE `growth_records` DISABLE KEYS */;
/*!40000 ALTER TABLE `growth_records` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `plant_profiles`
--

DROP TABLE IF EXISTS `plant_profiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `plant_profiles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `plant_name` varchar(100) NOT NULL,
  `species` varchar(100) DEFAULT NULL,
  `class_id` int DEFAULT NULL,
  `group_id` int DEFAULT NULL,
  `device_id` int DEFAULT NULL,
  `plant_date` date DEFAULT NULL,
  `cover_image` varchar(500) DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `expected_harvest_date` date DEFAULT NULL,
  `description` text,
  `created_by` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `class_id` (`class_id`),
  KEY `group_id` (`group_id`),
  KEY `device_id` (`device_id`),
  KEY `ix_plant_profiles_id` (`id`),
  KEY `ix_plant_profiles_created_by` (`created_by`),
  CONSTRAINT `plant_profiles_ibfk_1` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`),
  CONSTRAINT `plant_profiles_ibfk_2` FOREIGN KEY (`group_id`) REFERENCES `study_groups` (`id`),
  CONSTRAINT `plant_profiles_ibfk_3` FOREIGN KEY (`device_id`) REFERENCES `devices` (`id`),
  CONSTRAINT `plant_profiles_ibfk_4` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `plant_profiles`
--

LOCK TABLES `plant_profiles` WRITE;
/*!40000 ALTER TABLE `plant_profiles` DISABLE KEYS */;
/*!40000 ALTER TABLE `plant_profiles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sensor_readings`
--

DROP TABLE IF EXISTS `sensor_readings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sensor_readings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `device_id` int DEFAULT NULL,
  `temp` decimal(5,2) DEFAULT NULL,
  `humidity` decimal(5,2) DEFAULT NULL,
  `soil_moisture` decimal(5,2) DEFAULT NULL,
  `light` decimal(10,2) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_sensor_readings_id` (`id`),
  KEY `ix_sensor_readings_device_id` (`device_id`),
  KEY `ix_sensor_readings_timestamp` (`timestamp`),
  CONSTRAINT `sensor_readings_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sensor_readings`
--

LOCK TABLES `sensor_readings` WRITE;
/*!40000 ALTER TABLE `sensor_readings` DISABLE KEYS */;
INSERT INTO `sensor_readings` VALUES (1,1,39.00,35.00,30.00,9000.00,'2026-04-20 07:39:26');
/*!40000 ALTER TABLE `sensor_readings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `student_learning_records`
--

DROP TABLE IF EXISTS `student_learning_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `student_learning_records` (
  `id` int NOT NULL AUTO_INCREMENT,
  `student_id` int NOT NULL,
  `content_id` int NOT NULL,
  `status` varchar(20) DEFAULT NULL,
  `progress_percent` int DEFAULT NULL,
  `time_spent_seconds` int DEFAULT NULL,
  `last_accessed` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uix_student_content` (`student_id`,`content_id`),
  KEY `ix_student_learning_records_last_accessed` (`last_accessed`),
  KEY `ix_student_learning_records_id` (`id`),
  KEY `ix_student_learning_records_status` (`status`),
  KEY `ix_student_learning_records_content_id` (`content_id`),
  KEY `ix_student_learning_records_student_id` (`student_id`),
  KEY `ix_student_learning_records_completed_at` (`completed_at`),
  CONSTRAINT `student_learning_records_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `users` (`id`),
  CONSTRAINT `student_learning_records_ibfk_2` FOREIGN KEY (`content_id`) REFERENCES `teaching_contents` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `student_learning_records`
--

LOCK TABLES `student_learning_records` WRITE;
/*!40000 ALTER TABLE `student_learning_records` DISABLE KEYS */;
/*!40000 ALTER TABLE `student_learning_records` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `study_groups`
--

DROP TABLE IF EXISTS `study_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `study_groups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `group_name` varchar(100) NOT NULL,
  `class_id` int NOT NULL,
  `device_id` int DEFAULT NULL,
  `description` text,
  `created_by` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `class_id` (`class_id`),
  KEY `device_id` (`device_id`),
  KEY `ix_study_groups_created_by` (`created_by`),
  KEY `ix_study_groups_id` (`id`),
  CONSTRAINT `study_groups_ibfk_1` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`),
  CONSTRAINT `study_groups_ibfk_2` FOREIGN KEY (`device_id`) REFERENCES `devices` (`id`),
  CONSTRAINT `study_groups_ibfk_3` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `study_groups`
--

LOCK TABLES `study_groups` WRITE;
/*!40000 ALTER TABLE `study_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `study_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `teaching_contents`
--

DROP TABLE IF EXISTS `teaching_contents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `teaching_contents` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(200) NOT NULL,
  `category_id` int NOT NULL,
  `content_type` varchar(20) DEFAULT NULL,
  `content` text,
  `video_url` varchar(500) DEFAULT NULL,
  `file_path` varchar(500) DEFAULT NULL,
  `cover_image` varchar(500) DEFAULT NULL,
  `author_id` int NOT NULL,
  `view_count` int DEFAULT NULL,
  `is_published` tinyint(1) DEFAULT NULL,
  `published_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_teaching_contents_id` (`id`),
  KEY `ix_teaching_contents_created_at` (`created_at`),
  KEY `ix_teaching_contents_category_id` (`category_id`),
  KEY `ix_teaching_contents_title` (`title`),
  KEY `ix_teaching_contents_published_at` (`published_at`),
  KEY `ix_teaching_contents_author_id` (`author_id`),
  KEY `ix_teaching_contents_is_published` (`is_published`),
  CONSTRAINT `teaching_contents_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `content_categories` (`id`),
  CONSTRAINT `teaching_contents_ibfk_2` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `teaching_contents`
--

LOCK TABLES `teaching_contents` WRITE;
/*!40000 ALTER TABLE `teaching_contents` DISABLE KEYS */;
/*!40000 ALTER TABLE `teaching_contents` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_notifications`
--

DROP TABLE IF EXISTS `user_notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_notifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `actor_id` int DEFAULT NULL,
  `notification_type` varchar(50) NOT NULL,
  `title` varchar(200) NOT NULL,
  `content` text,
  `content_id` int DEFAULT NULL,
  `comment_id` int DEFAULT NULL,
  `is_read` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_user_notifications_id` (`id`),
  KEY `ix_user_notifications_created_at` (`created_at`),
  KEY `ix_user_notifications_actor_id` (`actor_id`),
  KEY `ix_user_notifications_user_id` (`user_id`),
  KEY `ix_user_notifications_is_read` (`is_read`),
  KEY `ix_user_notifications_content_id` (`content_id`),
  KEY `ix_user_notifications_comment_id` (`comment_id`),
  KEY `ix_user_notifications_notification_type` (`notification_type`),
  CONSTRAINT `user_notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `user_notifications_ibfk_2` FOREIGN KEY (`actor_id`) REFERENCES `users` (`id`),
  CONSTRAINT `user_notifications_ibfk_3` FOREIGN KEY (`content_id`) REFERENCES `teaching_contents` (`id`),
  CONSTRAINT `user_notifications_ibfk_4` FOREIGN KEY (`comment_id`) REFERENCES `content_comments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_notifications`
--

LOCK TABLES `user_notifications` WRITE;
/*!40000 ALTER TABLE `user_notifications` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_notifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_operation_logs`
--

DROP TABLE IF EXISTS `user_operation_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_operation_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `operator_id` int NOT NULL,
  `operation_type` varchar(20) NOT NULL,
  `target_user_id` int DEFAULT NULL,
  `details` text,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `target_user_id` (`target_user_id`),
  KEY `ix_user_operation_logs_operator_id` (`operator_id`),
  KEY `ix_user_operation_logs_id` (`id`),
  KEY `ix_user_operation_logs_created_at` (`created_at`),
  CONSTRAINT `user_operation_logs_ibfk_1` FOREIGN KEY (`operator_id`) REFERENCES `users` (`id`),
  CONSTRAINT `user_operation_logs_ibfk_2` FOREIGN KEY (`target_user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_operation_logs`
--

LOCK TABLES `user_operation_logs` WRITE;
/*!40000 ALTER TABLE `user_operation_logs` DISABLE KEYS */;
INSERT INTO `user_operation_logs` VALUES (1,1,'ai_stream',NULL,'{\"source\": \"deepseek-langchain\", \"latency_ms\": 4242, \"fallback_reason\": null, \"token_usage\": {\"prompt_tokens\": 1, \"completion_tokens\": 14, \"total_tokens\": 15, \"estimated\": true}, \"prompt_preview\": \"hi\", \"output_preview\": \"Hi! How can I help you today?\", \"extra\": {\"conversation_id\": 1, \"device_id\": null, \"stream\": true, \"sent_meta\": true, \"chunk_count\": 9, \"stream_error\": null, \"model\": \"deepseek-chat\", \"deep_thinking\": false, \"web_search_enabled\": false, \"web_search_used\": false, \"citations_count\": 0, \"rag_enabled\": true}}','2026-04-17 11:31:30'),(2,1,'ai_stream',NULL,'{\"source\": \"deepseek-langchain\", \"latency_ms\": 8154, \"fallback_reason\": null, \"token_usage\": {\"prompt_tokens\": 4, \"completion_tokens\": 141, \"total_tokens\": 145, \"estimated\": true}, \"prompt_preview\": \"你可以为我做什么\", \"output_preview\": \"我可以为你提供以下帮助：\\n\\n**平台管理**\\n- 用户与权限管理（教师、学生、家长账户）\\n- 课程与班级设置\\n- 学习进度跟踪与报告生成\\n- 系统配置与维护\\n\\n**数据分析**\\n- 学习行为分析（参与度、完成率、成绩趋势）\\n- 内容使用统计\\n- 生成可视化报表\\n\\n**内容支持**\\n- 课程材料上传与管理\\n- 作业与考试创建\\n- 讨论区管理\\n\\n**技术协助**\\n- 平台使用指导\\n- 故障排查\\n- 集\", \"extra\": {\"conversation_id\": 1, \"device_id\": null, \"stream\": true, \"sent_meta\": true, \"chunk_count\": 165, \"stream_error\": null, \"model\": \"deepseek-chat\", \"deep_thinking\": false, \"web_search_enabled\": false, \"web_search_used\": false, \"citations_count\": 0, \"rag_enabled\": true}}','2026-04-17 11:31:46'),(3,1,'ai_stream',NULL,'{\"source\": \"deepseek-langchain\", \"latency_ms\": 19335, \"fallback_reason\": null, \"token_usage\": {\"prompt_tokens\": 5, \"completion_tokens\": 170, \"total_tokens\": 175, \"estimated\": true}, \"prompt_preview\": \"现在打棚的状况怎么样\", \"output_preview\": \"根据最新的传感器数据，当前温室大棚的环境状况如下：\\n\\n**总体评价**：环境参数基本正常，适合多数作物生长，但部分指标需留意。\\n\\n**关键数据**：\\n- **温度**：26.1°C（日间适宜）\\n- **湿度**：68%（稍偏高，注意通风）\\n- **光照**：40000 lux（较强，建议检查遮光是否需要调节）\\n- **二氧化碳浓度**：740 ppm（略低于最优水平，可适量通风或补充）\\n- **土\", \"extra\": {\"conversation_id\": 2, \"device_id\": null, \"stream\": true, \"sent_meta\": true, \"chunk_count\": 192, \"stream_error\": null, \"model\": \"deepseek-reasoner\", \"deep_thinking\": true, \"web_search_enabled\": true, \"web_search_used\": false, \"citations_count\": 0, \"rag_enabled\": true}}','2026-04-17 11:35:41'),(4,1,'ai_stream',NULL,'{\"source\": \"deepseek-langchain\", \"latency_ms\": 16555, \"fallback_reason\": null, \"token_usage\": {\"prompt_tokens\": 1, \"completion_tokens\": 57, \"total_tokens\": 58, \"estimated\": true}, \"prompt_preview\": \"hi\", \"output_preview\": \"Hi！\\n\\n在英语问候中，“Hi”和“Hello”的常见区别是：“Hi”通常更口语化、随意，多用于朋友或熟人之间；而“Hello”则相对更正式、中性一些，也常用于接电话或与不太熟悉的人打招呼 [1][2]。\\n\\n有什么需要我帮助的吗？\", \"extra\": {\"conversation_id\": 2, \"device_id\": null, \"stream\": true, \"sent_meta\": true, \"chunk_count\": 67, \"stream_error\": null, \"model\": \"deepseek-reasoner\", \"deep_thinking\": true, \"web_search_enabled\": true, \"web_search_used\": true, \"citations_count\": 2, \"rag_enabled\": true}}','2026-04-20 06:44:26'),(5,1,'ai_stream',NULL,'{\"source\": \"deepseek-langchain\", \"latency_ms\": 19019, \"fallback_reason\": null, \"token_usage\": {\"prompt_tokens\": 4, \"completion_tokens\": 193, \"total_tokens\": 197, \"estimated\": true}, \"prompt_preview\": \"你可以为我做什么\", \"output_preview\": \"作为教育平台管理员，我可以协助您处理以下事务：\\n\\n**🎯 平台管理与数据**\\n- 查看温室传感器实时数据与历史趋势（温度、湿度、光照、CO₂、土壤湿度等）\\n- 生成环境报告与异常预警\\n- 管理用户账号、权限与课程/班级分配\\n\\n**📚 教学支持**\\n- 设计课程模块、学习路径或评估方案\\n- 整理教学资源（文档、视频、实验指南）\\n- 协助制定基于温室场景的实践教案\\n\\n**🛠 运维与设备**\\n- 提供温\", \"extra\": {\"conversation_id\": 2, \"device_id\": null, \"stream\": true, \"sent_meta\": true, \"chunk_count\": 228, \"stream_error\": null, \"model\": \"deepseek-reasoner\", \"deep_thinking\": true, \"web_search_enabled\": false, \"web_search_used\": false, \"citations_count\": 0, \"rag_enabled\": true}}','2026-04-20 07:06:27');
/*!40000 ALTER TABLE `user_operation_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) DEFAULT NULL,
  `hashed_password` varchar(255) DEFAULT NULL,
  `role` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `real_name` varchar(50) DEFAULT NULL,
  `avatar_url` varchar(500) DEFAULT NULL,
  `student_id` varchar(20) DEFAULT NULL,
  `teacher_id` varchar(20) DEFAULT NULL,
  `class_id` int DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `created_by` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_email` (`email`),
  UNIQUE KEY `ix_users_username` (`username`),
  UNIQUE KEY `ix_users_teacher_id` (`teacher_id`),
  UNIQUE KEY `ix_users_student_id` (`student_id`),
  KEY `ix_users_id` (`id`),
  KEY `ix_users_role` (`role`),
  KEY `ix_users_class_id` (`class_id`),
  KEY `ix_users_is_active` (`is_active`),
  KEY `ix_users_created_at` (`created_at`),
  KEY `created_by` (`created_by`),
  CONSTRAINT `users_ibfk_1` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`),
  CONSTRAINT `users_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'admin','$2b$12$lZgusjSKUAgO.jpFAhMnjuRngtA5G8R9gsfC1N05F43eJ3kuBNw5.','admin',NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,'2026-04-17 11:00:02','2026-04-17 11:00:02'),(2,'teacher','$2b$12$yA5C0Fy4lZcpBu0BQkFpAOky8TFDmaVl8p6Uhv2WjyWw/f1rGKzuW','teacher',NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,'2026-04-17 11:00:02','2026-04-17 11:00:02'),(3,'student','$2b$12$jNKkapA9e9WiQgiazApUP.Yzb62wqK.lcB/bwcF7YNCDYx64n9I0y','student',NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,'2026-04-17 11:00:02','2026-04-17 11:00:02');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'smart_greenhouse'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-21  9:55:10
