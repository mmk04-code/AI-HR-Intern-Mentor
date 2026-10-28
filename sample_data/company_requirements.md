# Company Task Requirements: Full-Stack Task Tracker Module 1

## Overview
Build a modular Full-Stack Task Tracker application for managing intern assignments. The project requires a robust database layer, core API routing, input validation, and user interface elements.

## Mandatory Specifications & Deliverables
1. **Database Schema & Models**:
   - Implement persistent data models for `User`, `Project`, and `TaskItem`.
   - Ensure foreign keys connect tasks to assigned projects and users.
   - Include created and updated timestamp fields for auditing.

2. **Core API / Business Logic**:
   - Create task creation, listing, updating, and status toggle functions.
   - Enforce mandatory validation on task titles (minimum 5 characters).
   - Prevent duplicate task names within the same active project.

3. **User Interface & Interaction**:
   - Provide an interactive dashboard displaying active and completed tasks.
   - Include filter mechanisms by status, due date, and assigned priority.
   - Display clear feedback indicators on task state updates.

4. **Error Handling & Resilience**:
   - Gracefully handle database disconnections and missing records (404 / NotFound).
   - Return clean, human-readable error messages without leaking stack traces.

5. **Documentation & Tests**:
   - Provide a comprehensive `README.md` with environment setup and execution instructions.
   - Include unit test cases verifying task creation and validation rules.
