-- ============================================================
-- PROCUREMENT QUEUE & SLOT MANAGEMENT SYSTEM
-- CLEAN MYSQL DATABASE
-- ============================================================

-- Create database
CREATE DATABASE IF NOT EXISTS procurement_system;

USE procurement_system;


-- ============================================================
-- 1. FARMERS
-- ============================================================

CREATE TABLE farmers (
    farmer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    mobile VARCHAR(10) NOT NULL UNIQUE,
    registration_id VARCHAR(50) NOT NULL UNIQUE,
    village VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 2. PROCUREMENT CENTERS
-- ============================================================

CREATE TABLE procurement_centers (
    center_id INT AUTO_INCREMENT PRIMARY KEY,
    center_name VARCHAR(100) NOT NULL,
    location VARCHAR(150) NOT NULL,

    -- Maximum quantity that can be procured
    -- by the center in one day
    daily_capacity DECIMAL(10,2) NOT NULL,

    -- Maximum number of farmers per slot
    slot_capacity INT NOT NULL,

    -- Duration of each slot in minutes
    slot_duration INT NOT NULL,

    status ENUM('Active', 'Inactive')
        DEFAULT 'Active',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 3. SLOTS
-- ============================================================

CREATE TABLE slots (
    slot_id INT AUTO_INCREMENT PRIMARY KEY,

    center_id INT NOT NULL,

    slot_date DATE NOT NULL,

    start_time TIME NOT NULL,

    end_time TIME NOT NULL,

    maximum_farmers INT NOT NULL,

    booked_farmers INT DEFAULT 0,

    status ENUM(
        'Available',
        'Full',
        'Closed'
    ) DEFAULT 'Available',

    FOREIGN KEY (center_id)
        REFERENCES procurement_centers(center_id)
        ON DELETE CASCADE,

    UNIQUE (
        center_id,
        slot_date,
        start_time,
        end_time
    )
);


-- ============================================================
-- 4. BOOKINGS
-- ============================================================

CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,

    procurement_id VARCHAR(20) NOT NULL UNIQUE,

    farmer_id INT NOT NULL,

    center_id INT NOT NULL,

    slot_id INT NOT NULL,

    expected_quantity DECIMAL(10,2) NOT NULL,

    token_number INT NOT NULL,

    booking_date DATE NOT NULL,

    status ENUM(
        'Slot Booked',
        'Farmer Arrived',
        'Quality Inspection',
        'Quantity Verified',
        'Payment Processing',
        'Payment Completed',
        'Cancelled'
    ) DEFAULT 'Slot Booked',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (farmer_id)
        REFERENCES farmers(farmer_id)
        ON DELETE CASCADE,

    FOREIGN KEY (center_id)
        REFERENCES procurement_centers(center_id)
        ON DELETE CASCADE,

    FOREIGN KEY (slot_id)
        REFERENCES slots(slot_id)
        ON DELETE CASCADE,

    UNIQUE (
        center_id,
        booking_date,
        token_number
    )
);


-- ============================================================
-- 5. PROCUREMENT
-- ============================================================

CREATE TABLE procurement (
    procurement_id VARCHAR(20) PRIMARY KEY,

    booking_id INT NOT NULL UNIQUE,

    verified_quantity DECIMAL(10,2),

    arrival_time DATETIME,

    inspection_start DATETIME,

    inspection_end DATETIME,

    payment_status ENUM(
        'Pending',
        'Processing',
        'Completed'
    ) DEFAULT 'Pending',

    completion_time DATETIME,

    FOREIGN KEY (booking_id)
        REFERENCES bookings(booking_id)
        ON DELETE CASCADE
);


-- ============================================================
-- 6. NOTIFICATIONS
-- ============================================================

CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,

    farmer_id INT NOT NULL,

    procurement_id VARCHAR(20),

    message TEXT NOT NULL,

    notification_type VARCHAR(50),

    status ENUM(
        'Pending',
        'Sent',
        'Failed'
    ) DEFAULT 'Pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (farmer_id)
        REFERENCES farmers(farmer_id)
        ON DELETE CASCADE,

    FOREIGN KEY (procurement_id)
        REFERENCES procurement(procurement_id)
        ON DELETE SET NULL
);


-- ============================================================
-- DATABASE CHECK
-- ============================================================

SHOW TABLES;