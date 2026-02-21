"""Reset admin password to admin123"""
from database import db, Admin
from app import app

with app.app_context():
    print("\n" + "="*60)
    print("RESETTING ADMIN PASSWORD")
    print("="*60 + "\n")
    
    admin = Admin.query.filter_by(username='admin').first()
    
    if not admin:
        print("❌ Admin user 'admin' not found!")
        exit(1)
    
    # Reset password
    print(f"Resetting password for: {admin.username}")
    admin.set_password('admin123')
    db.session.commit()
    
    print("✅ Password reset to: admin123")
    
    # Test the new password
    print("\nTesting new password...")
    admin = Admin.query.filter_by(username='admin').first()
    result = admin.check_password('admin123')
    
    if result:
        print("✅ Password verification SUCCESSFUL!")
        print("\nYou can now login with:")
        print("   Username: admin")
        print("   Password: admin123")
    else:
        print("❌ Password verification FAILED!")
        print("   There may be an issue with werkzeug password hashing")
    
    print("\n" + "="*60)
