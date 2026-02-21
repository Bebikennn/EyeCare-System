import os
import sys
import importlib.util

def check_file(path, description):
    if os.path.exists(path):
        print(f"✅ {description} found: {path}")
        return True
    else:
        print(f"❌ {description} MISSING: {path}")
        return False

def check_import(module_name):
    try:
        importlib.import_module(module_name)
        print(f"✅ Module '{module_name}' can be imported")
        return True
    except ImportError as e:
        print(f"❌ Module '{module_name}' could NOT be imported: {e}")
        return False
    except Exception as e:
        print(f"❌ Error importing '{module_name}': {e}")
        return False

def main():
    print("=== Deployment Artifacts Verification ===\n")
    
    # 1. Check WSGI Entrypoint
    if check_file("wsgi.py", "WSGI Entrypoint"):
        # Try to import application from wsgi
        try:
            spec = importlib.util.spec_from_file_location("wsgi", "wsgi.py")
            wsgi = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(wsgi)
            if hasattr(wsgi, 'application'):
                print("   ✅ wsgi.application attribute exists")
            else:
                print("   ❌ wsgi.application attribute MISSING")
        except Exception as e:
            print(f"   ❌ Failed to load wsgi.py: {e}")

    # 2. Check Configuration Files
    check_file("gunicorn.conf.py", "Gunicorn Config")
    check_file("deployment/systemd/eyecare-admin.service", "Systemd Service File")
    check_file("deployment/nginx/eyecare-admin.conf", "Nginx Config")
    
    # 3. Check Environment
    if os.path.exists(".env.production"):
        print("✅ .env.production exists (Ready for production mode)")
    else:
        print("⚠️  .env.production missing (Using .env.production.example as template)")
        check_file(".env.production.example", "Production Env Template")

    # 4. Check Dependencies
    print("\n=== Dependency Check ===")
    # On Windows, gunicorn might not be installable/runnable, but we check if it's in requirements
    with open("requirements.txt", "r") as f:
        reqs = f.read()
        if "gunicorn" in reqs:
            print("✅ 'gunicorn' is listed in requirements.txt")
        else:
            print("❌ 'gunicorn' is MISSING from requirements.txt")

    print("\n=== Verification Complete ===")
    print("See DEPLOYMENT.md for deployment instructions.")

if __name__ == "__main__":
    main()
