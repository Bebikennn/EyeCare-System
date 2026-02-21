"""Check admin login credentials"""
from database import db, Admin
from app import app

with app.app_context():
    print("\n" + "="*60)
    print("CHECKING ADMIN LOGIN CREDENTIALS")
    print("="*60 + "\n")
    
    # Check if admin user exists
    admin = Admin.query.filter_by(username='admin').first()
    
    if not admin:
        print("❌ Admin user 'admin' does NOT exist in database!")
        print("\nCreating default admin user...")
        
        admin = Admin(
            username='admin',
            email='admin@eyecare.com',
            full_name='Super Administrator',
            role='super_admin',
            status='active'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Admin user created successfully!")
        admin = Admin.query.filter_by(username='admin').first()
    
    print(f"✅ Admin user exists: {admin.username}")
    print(f"   Email: {admin.email}")
    print(f"   Full Name: {admin.full_name}")
    print(f"   Role: {admin.role}")
    print(f"   Status: {admin.status}")
    print(f"   Password hash: {admin.password_hash[:20]}...")
    
    # Test password
    print("\n" + "-"*60)
    print("TESTING PASSWORD")
    print("-"*60 + "\n")
    
    test_passwords = ['admin123', 'admin', 'Admin123', 'password']
    for pwd in test_passwords:
        result = admin.check_password(pwd)
        symbol = "✅" if result else "❌"
        print(f"{symbol} Password '{pwd}': {result}")
    
    print("\n" + "="*60)
    print("CHECK COMPLETE")
    print("="*60 + "\n")
