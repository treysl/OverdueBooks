# Library Management System with Lambda Functions for Overdue Fee Calculation

from datetime import datetime, timedelta
from typing import Dict, List, Callable, Any
from functools import reduce

# Define book categories and their base overdue fees
BOOK_CATEGORIES = {
    'regular': 0.50,      # $0.50 per day
    'reference': 1.00,    # $1.00 per day (higher fee for reference books)
    'bestseller': 0.75,   # $0.75 per day
    'children': 0.25,     # $0.25 per day (lower fee for children's books)
    'textbook': 1.25      # $1.25 per day (highest fee for textbooks)
}

# User types and their discount factors
USER_TYPES = {
    'student': 0.5,       # 50% discount
    'senior': 0.3,        # 70% discount
    'faculty': 0.2,       # 80% discount
    'regular': 1.0        # No discount
}

class Book:
    def __init__(self, isbn: str, title: str, category: str):
        self.isbn = isbn
        self.title = title
        self.category = category

class User:
    def __init__(self, user_id: str, name: str, user_type: str):
        self.user_id = user_id
        self.name = name
        self.user_type = user_type

class Checkout:
    def __init__(self, book: Book, user: User, checkout_date: datetime, due_date: datetime):
        self.book = book
        self.user = user
        self.checkout_date = checkout_date
        self.due_date = due_date
        self.return_date = None

# Lambda functions for overdue fee calculations

# 1. Basic overdue fee calculator (category-based)
calculate_base_fee = lambda days_overdue, category: days_overdue * BOOK_CATEGORIES.get(category, 0.50)

# 2. User discount application
apply_user_discount = lambda base_fee, user_type: base_fee * USER_TYPES.get(user_type, 1.0)

# 3. Progressive fee calculator (increases with more overdue days)
progressive_fee = lambda days_overdue, base_rate: (
    base_rate * days_overdue if days_overdue <= 7
    else base_rate * 7 + base_rate * 1.5 * (days_overdue - 7)
)

# 4. Maximum fee cap
cap_fee = lambda fee, max_fee=50.0: min(fee, max_fee)

# 5. Weekend exclusion calculator
exclude_weekends = lambda checkout_date, return_date: sum(
    1 for i in range((return_date - checkout_date).days)
    if (checkout_date + timedelta(days=i)).weekday() < 5  # Monday=0, Sunday=6
)

# 6. Bulk checkout discount (for users with multiple overdue books)
bulk_discount = lambda total_fee, num_books: (
    total_fee * 0.9 if num_books >= 3 else
    total_fee * 0.95 if num_books >= 2 else
    total_fee
)

# 7. Grace period calculator
apply_grace_period = lambda days_overdue, grace_days=2: max(0, days_overdue - grace_days)

# Composite lambda function that combines multiple rules
calculate_overdue_fee = lambda checkout, return_date=None: (
    lambda days_overdue: (
        lambda base_fee: (
            lambda discounted_fee: (
                lambda capped_fee: round(capped_fee, 2)
            )(cap_fee(discounted_fee))
        )(apply_user_discount(base_fee, checkout.user.user_type))
    )(progressive_fee(days_overdue, BOOK_CATEGORIES.get(checkout.book.category, 0.50)))
)(apply_grace_period(
    (return_date or datetime.now()).date() - checkout.due_date.date()
).days if (return_date or datetime.now()).date() > checkout.due_date.date() else 0)

# Library Management System Class
class LibrarySystem:
    def __init__(self):
        self.books: Dict[str, Book] = {}
        self.users: Dict[str, User] = {}
        self.checkouts: List[Checkout] = []
        
        # Lambda functions for different fee calculation strategies
        self.fee_calculators = {
            'standard': lambda checkout, return_date=None: self._standard_fee(checkout, return_date),
            'progressive': lambda checkout, return_date=None: self._progressive_fee(checkout, return_date),
            'weekend_exclusive': lambda checkout, return_date=None: self._weekend_exclusive_fee(checkout, return_date)
        }
    
    def add_book(self, isbn: str, title: str, category: str):
        self.books[isbn] = Book(isbn, title, category)
    
    def add_user(self, user_id: str, name: str, user_type: str):
        self.users[user_id] = User(user_id, name, user_type)
    
    def checkout_book(self, isbn: str, user_id: str, checkout_date: datetime, loan_period_days: int = 14):
        if isbn in self.books and user_id in self.users:
            due_date = checkout_date + timedelta(days=loan_period_days)
            checkout = Checkout(self.books[isbn], self.users[user_id], checkout_date, due_date)
            self.checkouts.append(checkout)
            return checkout
        return None
    
    def _standard_fee(self, checkout: Checkout, return_date: datetime = None) -> float:
        actual_return = return_date or datetime.now()
        if actual_return.date() <= checkout.due_date.date():
            return 0.0
        
        days_overdue = (actual_return.date() - checkout.due_date.date()).days
        days_after_grace = apply_grace_period(days_overdue)
        base_fee = calculate_base_fee(days_after_grace, checkout.book.category)
        discounted_fee = apply_user_discount(base_fee, checkout.user.user_type)
        return round(cap_fee(discounted_fee), 2)
    
    def _progressive_fee(self, checkout: Checkout, return_date: datetime = None) -> float:
        actual_return = return_date or datetime.now()
        if actual_return.date() <= checkout.due_date.date():
            return 0.0
        
        days_overdue = (actual_return.date() - checkout.due_date.date()).days
        days_after_grace = apply_grace_period(days_overdue)
        base_rate = BOOK_CATEGORIES.get(checkout.book.category, 0.50)
        progressive_amount = progressive_fee(days_after_grace, base_rate)
        discounted_fee = apply_user_discount(progressive_amount, checkout.user.user_type)
        return round(cap_fee(discounted_fee), 2)
    
    def _weekend_exclusive_fee(self, checkout: Checkout, return_date: datetime = None) -> float:
        actual_return = return_date or datetime.now()
        if actual_return.date() <= checkout.due_date.date():
            return 0.0
        
        # Calculate only weekdays for overdue period
        weekdays_overdue = sum(
            1 for i in range((actual_return.date() - checkout.due_date.date()).days)
            if (checkout.due_date + timedelta(days=i+1)).weekday() < 5
        )
        
        days_after_grace = apply_grace_period(weekdays_overdue)
        base_fee = calculate_base_fee(days_after_grace, checkout.book.category)
        discounted_fee = apply_user_discount(base_fee, checkout.user.user_type)
        return round(cap_fee(discounted_fee), 2)
    
    def calculate_user_total_fees(self, user_id: str, calculation_method: str = 'standard') -> float:
        user_checkouts = [c for c in self.checkouts if c.user.user_id == user_id and not c.return_date]
        
        if not user_checkouts:
            return 0.0
        
        calculator = self.fee_calculators.get(calculation_method, self.fee_calculators['standard'])
        individual_fees = [calculator(checkout) for checkout in user_checkouts]
        total_fee = sum(individual_fees)
        
        # Apply bulk discount if applicable
        return round(bulk_discount(total_fee, len(user_checkouts)), 2)
    
    def get_overdue_report(self) -> List[Dict[str, Any]]:
        report = []
        for checkout in self.checkouts:
            if not checkout.return_date and datetime.now().date() > checkout.due_date.date():
                fees = {
                    'standard': self.fee_calculators['standard'](checkout),
                    'progressive': self.fee_calculators['progressive'](checkout),
                    'weekend_exclusive': self.fee_calculators['weekend_exclusive'](checkout)
                }
                
                report.append({
                    'user': checkout.user.name,
                    'book': checkout.book.title,
                    'category': checkout.book.category,
                    'due_date': checkout.due_date.strftime('%Y-%m-%d'),
                    'days_overdue': (datetime.now().date() - checkout.due_date.date()).days,
                    'fees': fees
                })
        
        return report

# Initialize the system
library = LibrarySystem()

# Add sample books
library.add_book("978-0-123456-78-9", "Introduction to Algorithms", "textbook")
library.add_book("978-0-987654-32-1", "Harry Potter", "bestseller")
library.add_book("978-0-456789-01-2", "Children's Stories", "children")
library.add_book("978-0-789012-34-5", "Reference Manual", "reference")
library.add_book("978-0-234567-89-0", "Fiction Novel", "regular")

# Add sample users
library.add_user("U001", "Alice Student", "student")
library.add_user("U002", "Bob Senior", "senior")
library.add_user("U003", "Carol Faculty", "faculty")
library.add_user("U004", "Dave Regular", "regular")

print("Library Management System initialized successfully!")
print(f"Books in system: {len(library.books)}")
print(f"Users in system: {len(library.users)}")

#--------------------------------------------------------------

# Create sample checkouts with different scenarios
from datetime import datetime, timedelta

# Create checkouts that are now overdue
base_date = datetime(2025, 9, 1)

# Alice (student) checks out textbook - due Sept 15, now overdue
checkout1 = library.checkout_book("978-0-123456-78-9", "U001", base_date, 14)

# Bob (senior) checks out bestseller - due Sept 8, now overdue  
checkout2 = library.checkout_book("978-0-987654-32-1", "U002", base_date, 7)

# Carol (faculty) checks out reference book - due Sept 10, now overdue
checkout3 = library.checkout_book("978-0-789012-34-5", "U003", base_date, 9)

# Dave (regular) checks out multiple books
checkout4 = library.checkout_book("978-0-456789-01-2", "U004", base_date, 10)  # Children's book
checkout5 = library.checkout_book("978-0-234567-89-0", "U004", base_date, 12)  # Fiction novel

print("Sample checkouts created:")
print(f"Total checkouts: {len(library.checkouts)}")

# Test individual lambda functions
print("\n=== TESTING INDIVIDUAL LAMBDA FUNCTIONS ===")

# Test basic fee calculation
days_overdue_test = 5
category_test = "textbook"
base_fee_result = calculate_base_fee(days_overdue_test, category_test)
print(f"Base fee for {days_overdue_test} days overdue on {category_test}: ${base_fee_result:.2f}")

# Test user discount
user_type_test = "student"
discounted_fee = apply_user_discount(base_fee_result, user_type_test)
print(f"After {user_type_test} discount: ${discounted_fee:.2f}")

# Test progressive fee
progressive_result = progressive_fee(10, 1.25)  # 10 days overdue at $1.25/day
print(f"Progressive fee for 10 days at $1.25/day: ${progressive_result:.2f}")

# Test grace period
grace_result = apply_grace_period(5, 2)  # 5 days overdue with 2-day grace
print(f"Days after 2-day grace period (5 days overdue): {grace_result}")

# Test fee cap
capped_result = cap_fee(75.0)  # Test with fee above cap
print(f"Fee of $75.00 after $50.00 cap: ${capped_result:.2f}")

# Test bulk discount
bulk_result = bulk_discount(30.0, 3)  # $30 fee for 3 books
print(f"Bulk discount on $30.00 for 3 books: ${bulk_result:.2f}")

#-------------------------------------------------------------------

# Demonstrate the integrated system with comprehensive examples

print("=== INTEGRATED SYSTEM DEMONSTRATION ===")

# Generate overdue report showing different calculation methods
report = library.get_overdue_report()

print(f"\nOverdue Books Report (as of {datetime.now().strftime('%Y-%m-%d')}):")
print("=" * 80)

for item in report:
    print(f"\nUser: {item['user']} | Book: {item['book']} ({item['category']})")
    print(f"Due Date: {item['due_date']} | Days Overdue: {item['days_overdue']}")
    print("Fee Calculations:")
    for method, fee in item['fees'].items():
        print(f"  {method.replace('_', ' ').title()}: ${fee:.2f}")

# Test user total fees with bulk discount
print(f"\n=== USER TOTAL FEE CALCULATIONS ===")

for user_id, user in library.users.items():
    for method in ['standard', 'progressive', 'weekend_exclusive']:
        total_fee = library.calculate_user_total_fees(user_id, method)
        if total_fee > 0:
            print(f"{user.name} ({user.user_type}) - {method.replace('_', ' ').title()}: ${total_fee:.2f}")

# Demonstrate different return scenarios
print(f"\n=== RETURN SCENARIOS ===")

# Scenario 1: On-time return
test_checkout = library.checkout_book("978-0-234567-89-0", "U001", datetime.now() - timedelta(days=5), 14)
on_time_return = datetime.now() - timedelta(days=2)  # Return 2 days early
fee_on_time = library.fee_calculators['standard'](test_checkout, on_time_return)
print(f"On-time return fee: ${fee_on_time:.2f}")

# Scenario 2: Late return within grace period
late_return_grace = test_checkout.due_date + timedelta(days=1)  # 1 day late
fee_grace = library.fee_calculators['standard'](test_checkout, late_return_grace)
print(f"1 day late (within grace period): ${fee_grace:.2f}")

# Scenario 3: Late return after grace period
late_return_after_grace = test_checkout.due_date + timedelta(days=5)  # 5 days late
fee_after_grace = library.fee_calculators['standard'](test_checkout, late_return_after_grace)
print(f"5 days late (after grace period): ${fee_after_grace:.2f}")

# Advanced lambda function composition example
print(f"\n=== ADVANCED LAMBDA COMPOSITION ===")

# Create a complex fee calculator using function composition
def complex_calculator(checkout, return_date=None):
    actual_return = return_date or datetime.now()
    # Always work with int, not timedelta!
    overdue_days = (actual_return.date() - checkout.due_date.date()).days
    if overdue_days <= 0:
        return 0.0

    # Now pass int to apply_grace_period (safe!)
    days_after_grace = apply_grace_period(overdue_days)
    base_rate = BOOK_CATEGORIES.get(checkout.book.category, 0.50)
    prog = progressive_fee(days_after_grace, base_rate)
    discounted = apply_user_discount(prog, checkout.user.user_type)
    capped = cap_fee(discounted)
    # Bulk discount logic (here always 1 book for demo)
    final = bulk_discount(capped, 1)
    return round(final, 2)


# Test the complex calculator
for checkout in library.checkouts[:3]:
    complex_fee = complex_calculator(checkout)
    standard_fee = library.fee_calculators['standard'](checkout)
    print(f"{checkout.user.name} - Complex: ${complex_fee:.2f}, Standard: ${standard_fee:.2f}")

print(f"\n=== LAMBDA FUNCTION FEATURES DEMONSTRATED ===")
print("✓ Modular fee calculation by book category")
print("✓ User-specific discount application") 
print("✓ Progressive fee structure for extended overdue periods")
print("✓ Grace period implementation")
print("✓ Maximum fee capping")
print("✓ Bulk checkout discounts")
print("✓ Weekend exclusion options")
print("✓ Function composition for complex business rules")
print("✓ Multiple calculation strategies (standard, progressive, weekend-exclusive)")

# Save results to CSV for testing verification
import csv

# Create a comprehensive test results CSV
test_results = []

for checkout in library.checkouts:
    if datetime.now().date() > checkout.due_date.date():
        days_overdue = (datetime.now().date() - checkout.due_date.date()).days
        
        test_results.append({
            'user_name': checkout.user.name,
            'user_type': checkout.user.user_type,
            'book_title': checkout.book.title,
            'book_category': checkout.book.category,
            'due_date': checkout.due_date.strftime('%Y-%m-%d'),
            'days_overdue': days_overdue,
            'standard_fee': library.fee_calculators['standard'](checkout),
            'progressive_fee': library.fee_calculators['progressive'](checkout),
            'weekend_exclusive_fee': library.fee_calculators['weekend_exclusive'](checkout)
        })

# Write to CSV
with open('overdue_fees_test_results.csv', 'w', newline='') as csvfile:
    if test_results:
        fieldnames = test_results[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(test_results)

print(f"\nTest results saved to 'overdue_fees_test_results.csv'")
print(f"Total test cases: {len(test_results)}")

#-------------------------------------------------------------------------

# Fix the lambda function composition and complete the demonstration

print("=== INTEGRATED SYSTEM DEMONSTRATION ===")

# Generate overdue report showing different calculation methods
report = library.get_overdue_report()

print(f"\nOverdue Books Report (as of {datetime.now().strftime('%Y-%m-%d')}):")
print("=" * 80)

for item in report:
    print(f"\nUser: {item['user']} | Book: {item['book']} ({item['category']})")
    print(f"Due Date: {item['due_date']} | Days Overdue: {item['days_overdue']}")
    print("Fee Calculations:")
    for method, fee in item['fees'].items():
        print(f"  {method.replace('_', ' ').title()}: ${fee:.2f}")

# Test user total fees with bulk discount
print(f"\n=== USER TOTAL FEE CALCULATIONS ===")

for user_id, user in library.users.items():
    for method in ['standard', 'progressive', 'weekend_exclusive']:
        total_fee = library.calculate_user_total_fees(user_id, method)
        if total_fee > 0:
            print(f"{user.name} ({user.user_type}) - {method.replace('_', ' ').title()}: ${total_fee:.2f}")

# Demonstrate different return scenarios
print(f"\n=== RETURN SCENARIOS ===")

# Scenario 1: On-time return
test_checkout = library.checkout_book("978-0-234567-89-0", "U001", datetime.now() - timedelta(days=5), 14)
on_time_return = datetime.now() - timedelta(days=2)  # Return 2 days early
fee_on_time = library.fee_calculators['standard'](test_checkout, on_time_return)
print(f"On-time return fee: ${fee_on_time:.2f}")

# Scenario 2: Late return within grace period
late_return_grace = test_checkout.due_date + timedelta(days=1)  # 1 day late
fee_grace = library.fee_calculators['standard'](test_checkout, late_return_grace)
print(f"1 day late (within grace period): ${fee_grace:.2f}")

# Scenario 3: Late return after grace period
late_return_after_grace = test_checkout.due_date + timedelta(days=5)  # 5 days late
fee_after_grace = library.fee_calculators['standard'](test_checkout, late_return_after_grace)
print(f"5 days late (after grace period): ${fee_after_grace:.2f}")

# Fixed Advanced lambda function composition example
print(f"\n=== ADVANCED LAMBDA COMPOSITION ===")

# Create a complex fee calculator using function composition with proper type handling
def complex_calculator(checkout, return_date=None):
    actual_return = return_date or datetime.now()
    if actual_return.date() <= checkout.due_date.date():
        return 0.0
    
    # Calculate days overdue properly
    days_overdue = (actual_return.date() - checkout.due_date.date()).days
    
    # Apply the composed lambda functions
    return (lambda overdue_days: (
        lambda base_calculation: (
            lambda with_user_discount: (
                lambda with_bulk_consideration: round(
                    cap_fee(with_bulk_consideration), 2
                )
            )(bulk_discount(with_user_discount, 1))  # Single book, no bulk discount
        )(apply_user_discount(base_calculation, checkout.user.user_type))
    )(progressive_fee(
        apply_grace_period(overdue_days), 
        BOOK_CATEGORIES.get(checkout.book.category, 0.50)
    )))(days_overdue)

# Test the complex calculator
for checkout in library.checkouts[:3]:  # Test first 3 checkouts
    complex_fee = complex_calculator(checkout)
    standard_fee = library.fee_calculators['standard'](checkout)
    print(f"{checkout.user.name} - Complex: ${complex_fee:.2f}, Standard: ${standard_fee:.2f}")

print(f"\n=== LAMBDA FUNCTION FEATURES DEMONSTRATED ===")
print("✓ Modular fee calculation by book category")
print("✓ User-specific discount application") 
print("✓ Progressive fee structure for extended overdue periods")
print("✓ Grace period implementation")
print("✓ Maximum fee capping")
print("✓ Bulk checkout discounts")
print("✓ Weekend exclusion options")
print("✓ Function composition for complex business rules")
print("✓ Multiple calculation strategies (standard, progressive, weekend-exclusive)")

# ---------------------------------------------------------------

# Create comprehensive test data and export to CSV for verification

import csv

# Create a comprehensive test results dataset
test_results = []

# Add current overdue books
for checkout in library.checkouts:
    if datetime.now().date() > checkout.due_date.date():
        days_overdue = (datetime.now().date() - checkout.due_date.date()).days
        
        test_results.append({
            'user_name': checkout.user.name,
            'user_type': checkout.user.user_type,
            'book_title': checkout.book.title,
            'book_category': checkout.book.category,
            'due_date': checkout.due_date.strftime('%Y-%m-%d'),
            'days_overdue': days_overdue,
            'days_after_grace': apply_grace_period(days_overdue),
            'base_rate': BOOK_CATEGORIES.get(checkout.book.category, 0.50),
            'user_discount_factor': USER_TYPES.get(checkout.user.user_type, 1.0),
            'standard_fee': library.fee_calculators['standard'](checkout),
            'progressive_fee': library.fee_calculators['progressive'](checkout),
            'weekend_exclusive_fee': library.fee_calculators['weekend_exclusive'](checkout)
        })

# Add test cases for different scenarios
test_scenarios = [
    {'days': 1, 'category': 'regular', 'user_type': 'regular', 'description': 'Short overdue regular user'},
    {'days': 5, 'category': 'textbook', 'user_type': 'student', 'description': 'Medium overdue student'},
    {'days': 15, 'category': 'reference', 'user_type': 'senior', 'description': 'Long overdue senior'},
    {'days': 30, 'category': 'bestseller', 'user_type': 'faculty', 'description': 'Very long overdue faculty'},
    {'days': 2, 'category': 'children', 'user_type': 'regular', 'description': 'Grace period test'}
]

for i, scenario in enumerate(test_scenarios):
    days = scenario['days']
    category = scenario['category']
    user_type = scenario['user_type']
    
    # Calculate fees using lambda functions
    days_after_grace = apply_grace_period(days)
    base_fee = calculate_base_fee(days_after_grace, category)
    discounted_fee = apply_user_discount(base_fee, user_type)
    progressive_amount = progressive_fee(days_after_grace, BOOK_CATEGORIES[category])
    progressive_discounted = apply_user_discount(progressive_amount, user_type)
    
    test_results.append({
        'user_name': f'Test User {i+1}',
        'user_type': user_type,
        'book_title': f'Test Book {i+1}',
        'book_category': category,
        'due_date': 'Test Scenario',
        'days_overdue': days,
        'days_after_grace': days_after_grace,
        'base_rate': BOOK_CATEGORIES[category],
        'user_discount_factor': USER_TYPES[user_type],
        'standard_fee': round(cap_fee(discounted_fee), 2),
        'progressive_fee': round(cap_fee(progressive_discounted), 2),
        'weekend_exclusive_fee': 'N/A - Test Scenario',
        'description': scenario['description']
    })

# Write comprehensive test results to CSV
with open('lambda_overdue_fees_comprehensive_test.csv', 'w', newline='') as csvfile:
    if test_results:
        # Get all unique fieldnames from all test results
        all_fieldnames = set()
        for result in test_results:
            all_fieldnames.update(result.keys())
        
        fieldnames = sorted(list(all_fieldnames))
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(test_results)

print(f"Comprehensive test results saved to 'lambda_overdue_fees_comprehensive_test.csv'")
print(f"Total test cases: {len(test_results)}")

# Display summary of lambda function usage
print(f"\n=== LAMBDA FUNCTIONS SUMMARY ===")
lambda_functions = [
    ('calculate_base_fee', 'Base overdue fee calculation by category'),
    ('apply_user_discount', 'Apply user-type specific discounts'),
    ('progressive_fee', 'Progressive fee structure for long overdue periods'),
    ('cap_fee', 'Apply maximum fee limits'),
    ('apply_grace_period', 'Grace period calculation'),
    ('bulk_discount', 'Multi-book checkout discounts'),
    ('exclude_weekends', 'Weekend exclusion for business days only'),
]

for func_name, description in lambda_functions:
    print(f"• {func_name}: {description}")

print(f"\n=== MODULAR SYSTEM BENEFITS ===")
benefits = [
    "Easy to modify individual fee calculation rules",
    "Composable functions for complex business logic",
    "Testable individual components",
    "Flexible fee structure adaptation",
    "Clear separation of concerns",
    "Reusable across different library systems"
]

for benefit in benefits:
    print(f"• {benefit}")

# Create a simple test verification function
def verify_lambda_calculations():
    """Simple verification function to test lambda calculations"""
    print(f"\n=== VERIFICATION TESTS ===")
    
    # Test 1: Basic fee calculation
    test1 = calculate_base_fee(5, 'textbook') == 6.25
    print(f"Test 1 - Basic fee (5 days, textbook): {'PASS' if test1 else 'FAIL'}")
    
    # Test 2: User discount
    test2 = round(apply_user_discount(10.0, 'student'), 2) == 5.0
    print(f"Test 2 - Student discount (50%): {'PASS' if test2 else 'FAIL'}")
    
    # Test 3: Grace period
    test3 = apply_grace_period(3, 2) == 1
    print(f"Test 3 - Grace period (3 days - 2 grace = 1): {'PASS' if test3 else 'FAIL'}")
    
    # Test 4: Fee cap
    test4 = cap_fee(75.0) == 50.0
    print(f"Test 4 - Fee cap ($75 -> $50): {'PASS' if test4 else 'FAIL'}")
    
    # Test 5: Bulk discount
    test5 = bulk_discount(30.0, 3) == 27.0
    print(f"Test 5 - Bulk discount (3 books, 10% off): {'PASS' if test5 else 'FAIL'}")
    
    all_passed = all([test1, test2, test3, test4, test5])
    print(f"\nAll tests passed: {'YES' if all_passed else 'NO'}")
    return all_passed

# Run verification tests
verify_lambda_calculations()