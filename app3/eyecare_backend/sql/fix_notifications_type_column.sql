-- Fix the user_notifications table by renaming TYPE to type
-- TYPE is a reserved keyword in MySQL and causes issues

ALTER TABLE `user_notifications` 
CHANGE COLUMN `TYPE` `type` enum('info','success','warning','error') DEFAULT 'info';

-- Verify the change
DESCRIBE `user_notifications`;
