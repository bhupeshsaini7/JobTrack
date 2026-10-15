-- JobTrack database schema.
-- Safe to run more than once: it will NOT delete your saved applications.

CREATE DATABASE IF NOT EXISTS jobtrack
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE jobtrack;

CREATE TABLE IF NOT EXISTS applications (
    application_id   INT          NOT NULL AUTO_INCREMENT,
    company_name     VARCHAR(100) NOT NULL,
    job_title        VARCHAR(100) NOT NULL,
    location         VARCHAR(100) NULL,
    job_link         VARCHAR(500) NULL,
    application_date DATE         NOT NULL,
    status           ENUM('Applied', 'Interview', 'Offer', 'Rejected')
                     NOT NULL DEFAULT 'Applied',
    notes            TEXT         NULL,
    created_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                     ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (application_id),
    INDEX idx_applications_status (status),
    INDEX idx_applications_company (company_name)
) ENGINE=InnoDB;