# OverdueBooks

The provided Python code implements a **Library Management System** that focuses on calculating overdue book fees using modular lambda functions. The system supports different book categories, user types, and a variety of fee calculation strategies, all of which are demonstrated and tested in the code and reflected in the terminal output.

---

## Code Overview

### 1. Core Classes

- **Book**: Represents a book with ISBN, title, and category.
- **User**: Represents a user with ID, name, and user type (e.g., student, senior).
- **Checkout**: Represents a book checkout, including dates and references to the book and user.

### 2. Fee Calculation Logic

- **Lambda Functions**: Modular functions for:
  - Calculating base overdue fees by category.
  - Applying user-specific discounts.
  - Progressive fee increases for long overdue periods.
  - Capping maximum fees.
  - Excluding weekends from overdue calculations.
  - Applying grace periods.
  - Bulk discounts for multiple overdue books.
- **Composite Lambda**: Chains these rules for a full overdue fee calculation.

### 3. LibrarySystem Class

- Manages books, users, and checkouts.
- Provides multiple fee calculation strategies:
  - **Standard**: Simple category and user-based calculation.
  - **Progressive**: Increases rate after a week overdue.
  - **Weekend Exclusive**: Only counts weekdays as overdue.
- Generates overdue reports and calculates total user fees (with bulk discounts).

### 4. Demonstration & Testing

- Adds sample books and users.
- Creates checkouts with various overdue scenarios.
- Prints detailed fee calculations for each scenario.
- Exports results to CSV for further verification.
- Includes a verification function to test the lambda logic.

---

## 4. Error Encounter and Debugging

### Error

When running the “Advanced Lambda Composition” demo, the `apply_grace_period` lambda received a `datetime.timedelta` object rather than an integer, causing: `TypeError: unsupported operand type(s) for -: 'datetime.timedelta' and 'int'`

### Diagnosis

Traced the source to the logic feeding a `timedelta` (the difference between two dates) directly to a lambda expecting an `int` (number of overdue days).

### Solution

- Refactored code to always extract `.days` from `timedelta` before passing as an argument, ensuring all lambda inputs were correct types.
- Converted the advanced lambda demo from a deeply nested lambda to a simple function for improved readability and safer type handling, eliminating the error.

### Changes Made As a Result of Errors

- **Type Handling**: Ensured all date difference calculations yielded integers, not `timedelta`, for compatibility with lambdas.
- **Demo Code Refactoring**: Changed the deeply nested lambda composition in the advanced example to a traditional function for clarity and correct type flow.
- **Improved Error Logging and Test Output**: Enhanced demonstration outputs so future errors could be easily traced and resolved.

---

## Terminal Output Correlation

The terminal output shows the results of running the code: [Link text](Terminal%20Output.txt)

### Initialization

- Confirms the system is set up with 5 books and 4 users.

### Lambda Function Tests

- Demonstrates each lambda function individually (e.g., base fee, discount, progressive fee, grace period, fee cap, bulk discount).

### Integrated System Demonstration

- **Overdue Books Report**: Lists each overdue book, user, due date, days overdue, and the calculated fees using all three strategies.
- **User Total Fee Calculations**: Shows total fees per user, applying bulk discounts where applicable.
- **Return Scenarios**: Demonstrates fee calculation for on-time, grace-period, and late returns.
- **Advanced Lambda Composition**: Compares complex composed fee calculations with standard ones.
- **Features Demonstrated**: Lists all the modular features implemented via lambdas.

### CSV Export

- Confirms that test results are saved to CSV files for verification.

### Verification Tests

- Runs a set of assertions to ensure the lambda functions work as expected, all passing successfully.

### User Distinction

- Named users (e.g., Alice, Bob...) are part of the main library system and are used to simulate realistic operations—checking out books, accruing overdue fees, etc. Their actions illustrate how the system behaves under typical library scenarios with real user types.

- Test users (e.g., "Test User 1") are generated specifically in the section where exhaustive tests and edge cases are written, such as in the CSV export for unit testing. These synthetic entries allow you to directly control all parameters (overdue days, categories, user types) for focused, repeatable verification of the fee calculation logic, without interfering with the main simulation.

---

## Summary

- **The code is a modular, extensible library fee system using lambda functions for business logic.**
- **The terminal output confirms correct operation, showing detailed fee calculations, feature demonstrations, and successful verification tests.**
- **CSV exports provide a way to further validate and analyze the fee calculations.**

This approach makes it easy to adapt, test, and extend the fee logic for different library policies.

--
