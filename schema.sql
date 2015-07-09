CREATE TABLE nodes (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE,
    job_title TEXT NOT NULL,
    reports_to INT   
)

