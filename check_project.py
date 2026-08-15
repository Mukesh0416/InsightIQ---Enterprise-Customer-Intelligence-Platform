import ast
import os

# Check backend files
backend_dir = 'backend/app'
print("Checking backend files...")
for root, dirs, files in os.walk(backend_dir):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                with open(path) as fh:
                    ast.parse(fh.read())
                print(f"  OK: {path}")
            except SyntaxError as e:
                print(f"  SYNTAX ERROR: {path}: {e}")

# Check all .py files in project root
print("\nChecking all .py files...")
for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.py') and not f.startswith('test_') and f != 'check_project.py':
            path = os.path.join(root, f)
            try:
                with open(path) as fh:
                    ast.parse(fh.read())
                print(f"  OK: {path}")
            except SyntaxError as e:
                print(f"  SYNTAX ERROR: {path}: {e}")