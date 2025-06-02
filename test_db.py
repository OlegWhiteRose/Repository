from database.db import Database

def test_tables():
    db = Database()
    
    # Test Client table
    print("\nTesting Client table:")
    result = db.execute_query("SELECT COUNT(*) FROM Client", fetch_one=True)
    print(f"Number of clients: {result[0]}")
    if result[0] > 0:
        clients = db.execute_query("SELECT * FROM Client LIMIT 3", fetch_all=True)
        print("Sample clients:", clients)

    # Test Transaction table
    print("\nTesting Transaction table:")
    result = db.execute_query("SELECT COUNT(*) FROM Transaction", fetch_one=True)
    print(f"Number of transactions: {result[0]}")
    if result[0] > 0:
        transactions = db.execute_query("SELECT * FROM Transaction LIMIT 3", fetch_all=True)
        print("Sample transactions:", transactions)

    # Test Report table
    print("\nTesting Report table:")
    result = db.execute_query("SELECT COUNT(*) FROM Report", fetch_one=True)
    print(f"Number of reports: {result[0]}")
    if result[0] > 0:
        reports = db.execute_query("SELECT * FROM Report LIMIT 3", fetch_all=True)
        print("Sample reports:", reports)

if __name__ == "__main__":
    test_tables() 