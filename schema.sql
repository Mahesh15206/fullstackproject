-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- DATABASE SCHEMA FILE (schema.sql)
-- This file creates the database and all 14 tables needed for the Skill Swap Platform.
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS skillswap;

-- Tell MySQL to use the 'skillswap' database for all following commands
USE skillswap;

-- 1. users
-- Stores all registered users and their profile details
CREATE TABLE IF NOT EXISTS users (
    -- id: Unique ID for each user, automatically increments
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- name: User's full name, cannot be empty
    name VARCHAR(100) NOT NULL,
    -- email: User's email, must be unique and cannot be empty
    email VARCHAR(100) UNIQUE NOT NULL,
    -- password: Password hash, cannot be empty
    password VARCHAR(255) NOT NULL,
    -- location: User's city/country (optional)
    location VARCHAR(100),
    -- bio: Short description about the user (optional)
    bio TEXT,
    -- profile_pic: Filename of the uploaded image, defaults to a standard image
    profile_pic VARCHAR(255) DEFAULT 'default.jpg',
    -- is_admin: Boolean flag (0=regular user, 1=admin), defaults to 0
    is_admin BOOLEAN DEFAULT FALSE,
    -- created_at: Automatically saves the exact date and time the user registered
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. skills_offered
-- Stores skills that users are willing to teach
CREATE TABLE IF NOT EXISTS skills_offered (
    -- id: Unique identifier for this exact skill record
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- user_id: ID of the user offering the skill
    user_id INT NOT NULL,
    -- skill_name: Name of the skill (e.g., 'Python', 'Guitar')
    skill_name VARCHAR(100) NOT NULL,
    -- category: Broad category for filtering (e.g., 'Programming', 'Music')
    category VARCHAR(50),
    -- is_verified: Useful for feature #8 (Quiz), becomes True if they pass the quiz
    is_verified BOOLEAN DEFAULT FALSE,
    -- FOREIGN KEY: links user_id to the 'users' table. If user is deleted, their skills are deleted (CASCADE)
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. skills_wanted
-- Stores skills that users want to learn
CREATE TABLE IF NOT EXISTS skills_wanted (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- user_id: ID of the user who wants to learn
    user_id INT NOT NULL,
    -- skill_name: Name of the desired skill
    skill_name VARCHAR(100) NOT NULL,
    -- category: Broad category of the skill
    category VARCHAR(50),
    -- FOREIGN KEY: ensures the user exists in the 'users' table
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 4. swap_requests
-- Stores requests sent by one user to swap skills with another
CREATE TABLE IF NOT EXISTS swap_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- sender_id: the user who initiated the request
    sender_id INT NOT NULL,
    -- receiver_id: the user who receives the request
    receiver_id INT NOT NULL,
    -- status: the state of the request (pending, accepted, rejected, cancelled)
    status ENUM('pending', 'accepted', 'rejected', 'cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Links sender_id to the users table
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    -- Links receiver_id to the users table
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 5. chat_rooms
-- Creates a "room" or conversation thread between two people when a swap is accepted
CREATE TABLE IF NOT EXISTS chat_rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- user1_id: First person in the chat
    user1_id INT NOT NULL,
    -- user2_id: Second person in the chat
    user2_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user1_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (user2_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 6. messages
-- Stores individual chat messages or voice notes inside a chat room
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- room_id: the chat room this message belongs to
    room_id INT NOT NULL,
    -- sender_id: the specific user who sent this message
    sender_id INT NOT NULL,
    -- message_text: the actual typed text of the message (can be NULL if it's a voice message)
    message_text TEXT,
    -- message_type: text, voice, or file
    message_type ENUM('text', 'voice', 'file') DEFAULT 'text',
    -- file_path: the location of the voice clip or file on the server (if applicable)
    file_path VARCHAR(255),
    -- is_read: tracks if the receiver has seen the message (useful for unread badges)
    is_read BOOLEAN DEFAULT FALSE,
    -- sent_at: exactly when the message was sent
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 7. sessions
-- Scheduled learning sessions between two matched users
CREATE TABLE IF NOT EXISTS sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- organizer_id: the user who booked the session
    organizer_id INT NOT NULL,
    -- partner_id: the user they are learning with/from
    partner_id INT NOT NULL,
    -- topic: what will be discussed (e.g., 'Python Basics')
    topic VARCHAR(255) NOT NULL,
    -- session_datetime: chosen date and time for the meeting
    session_datetime DATETIME NOT NULL,
    -- status: scheduled, completed, or cancelled
    status ENUM('scheduled', 'completed', 'cancelled') DEFAULT 'scheduled',
    FOREIGN KEY (organizer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (partner_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 8. learning_goals
-- Progress tracking for skills a user wants to learn
CREATE TABLE IF NOT EXISTS learning_goals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- user_id: the learner tracking their progress
    user_id INT NOT NULL,
    -- skill_name: the specific skill being tracked
    skill_name VARCHAR(100) NOT NULL,
    -- target_sessions: how many sessions they want to complete to feel proficient
    target_sessions INT DEFAULT 5,
    -- completed_sessions: how many sessions they have actually fully completed
    completed_sessions INT DEFAULT 0,
    -- is_achieved: becomes TRUE when completed_sessions reaches target_sessions
    is_achieved BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 9. reviews
-- Star ratings and text reviews left by users for one another
CREATE TABLE IF NOT EXISTS reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- reviewer_id: the person writing the review
    reviewer_id INT NOT NULL,
    -- reviewed_id: the person receiving the review
    reviewed_id INT NOT NULL,
    -- rating: a star rating out of 5
    rating INT CHECK (rating >= 1 AND rating <= 5),
    -- comment: text explaining the rating (optional)
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 10. endorsements
-- Like LinkedIn's "endorse skill" feature, users can vouch for someone else's skill
CREATE TABLE IF NOT EXISTS endorsements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- endorser_id: the person clicking the "Endorse" button
    endorser_id INT NOT NULL,
    -- endorsed_id: the person receiving the endorsement
    endorsed_id INT NOT NULL,
    -- skill_name: the exact skill being endorsed
    skill_name VARCHAR(100) NOT NULL,
    FOREIGN KEY (endorser_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (endorsed_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 11. quiz_questions
-- Multiple Choice Questions for verifying a user's offered skills
CREATE TABLE IF NOT EXISTS quiz_questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- skill_name: what skill does this question test? (e.g., 'Python')
    skill_name VARCHAR(100) NOT NULL,
    -- question: the actual question text
    question TEXT NOT NULL,
    -- option_a, b, c, d: multiple choice options
    option_a VARCHAR(255) NOT NULL,
    option_b VARCHAR(255) NOT NULL,
    option_c VARCHAR(255) NOT NULL,
    option_d VARCHAR(255) NOT NULL,
    -- correct_option: the correct answer ('A', 'B', 'C', or 'D')
    correct_option ENUM('A', 'B', 'C', 'D') NOT NULL
);

-- 12. activity_feed
-- Logs important actions (new skills, completed sessions) to show on the dashboard
CREATE TABLE IF NOT EXISTS activity_feed (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- user_id: the user who performed the action
    user_id INT NOT NULL,
    -- action_type: a short code for what type of event this is
    action_type VARCHAR(50),
    -- description: full text shown on the feed (e.g., "John just learned basic Python!")
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 13. reports
-- Allows users to report bad behavior directly to the admins
CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- reporter_id: the person filing the complaint
    reporter_id INT NOT NULL,
    -- reported_id: the person being complained about
    reported_id INT NOT NULL,
    -- reason: text explaining what happened
    reason TEXT NOT NULL,
    -- status: pending, reviewed, resolved
    status ENUM('pending', 'reviewed', 'resolved') DEFAULT 'pending',
    FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reported_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 14. blocked_users
-- Prevents a specific user from interacting with another specific user
CREATE TABLE IF NOT EXISTS blocked_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- blocker_id: the person doing the blocking
    blocker_id INT NOT NULL,
    -- blocked_id: the person who is now blocked
    blocked_id INT NOT NULL,
    FOREIGN KEY (blocker_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (blocked_id) REFERENCES users(id) ON DELETE CASCADE
);
