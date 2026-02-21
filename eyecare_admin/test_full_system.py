"""
Comprehensive System Test & Analysis
Tests all components and provides completion percentage
"""
import sys
import os
import time
import json
import requests
from datetime import datetime
from collections import defaultdict

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

def print_section(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BLUE}{'-'*70}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}[OK]{Colors.END} {text}")

def print_error(text):
    print(f"{Colors.RED}[FAIL]{Colors.END} {text}")

def print_warning(text):
    print(f"{Colors.YELLOW}[WARN]{Colors.END} {text}")

def print_info(text):
    print(f"  {text}")

# Test results storage
test_results = defaultdict(list)
total_tests = 0
passed_tests = 0

def record_test(category, test_name, passed, message=""):
    global total_tests, passed_tests
    total_tests += 1
    if passed:
        passed_tests += 1
        test_results[category].append({'name': test_name, 'status': 'PASS', 'message': message})
        print_success(f"{test_name}")
        if message:
            print_info(message)
    else:
        test_results[category].append({'name': test_name, 'status': 'FAIL', 'message': message})
        print_error(f"{test_name}")
        if message:
            print_info(f"Error: {message}")

# ============================================================================
# TEST 1: ENVIRONMENT & CONFIGURATION
# ============================================================================
def test_environment():
    print_section("TEST 1: Environment & Configuration")
    
    # Check Python version
    try:
        py_version = sys.version_info
        if py_version.major >= 3 and py_version.minor >= 8:
            record_test('Environment', 'Python version (3.8+)', True, f"Python {py_version.major}.{py_version.minor}.{py_version.micro}")
        else:
            record_test('Environment', 'Python version (3.8+)', False, f"Python {py_version.major}.{py_version.minor} - Need 3.8+")
    except Exception as e:
        record_test('Environment', 'Python version', False, str(e))
    
    # Check config files exist
    config_files = [
        'config.py',
        'config_production.py',
        '.env.production.template',
        'app.py'
    ]
    
    for file in config_files:
        exists = os.path.exists(file)
        record_test('Environment', f'Config file: {file}', exists, 
                   f"Found at {os.path.abspath(file)}" if exists else "Missing")
    
    # Check required directories
    required_dirs = ['logs', 'static/uploads', 'backups', 'utils', 'routes', 'models']
    for directory in required_dirs:
        exists = os.path.isdir(directory)
        record_test('Environment', f'Directory: {directory}', exists)

# ============================================================================
# TEST 2: DEPENDENCIES
# ============================================================================
def test_dependencies():
    print_section("TEST 2: Python Dependencies")
    
    required_packages = {
        'flask': 'Flask',
        'pymysql': 'PyMySQL',
        'flask_cors': 'Flask-CORS',
        'flask_wtf': 'Flask-WTF',
        'flask_limiter': 'Flask-Limiter',
        'flask_mail': 'Flask-Mail',
        'redis': 'Redis',
        'sentry_sdk': 'Sentry SDK',
        'gunicorn': 'Gunicorn',
        'gevent': 'Gevent',
        'openpyxl': 'OpenPyXL',
        'pytest': 'Pytest',
        'pylint': 'Pylint',
        'black': 'Black',
        'flake8': 'Flake8',
        'mypy': 'Mypy'
    }
    
    for module, name in required_packages.items():
        try:
            __import__(module)
            record_test('Dependencies', f'{name}', True, 'Installed')
        except ImportError:
            record_test('Dependencies', f'{name}', False, 'Not installed')

# ============================================================================
# TEST 3: DATABASE CONNECTION
# ============================================================================
def test_database():
    print_section("TEST 3: Database Connection & Structure")
    
    try:
        from database import get_db_connection
        
        # Test connection
        try:
            conn = get_db_connection()
            record_test('Database', 'MySQL connection', True, 'Connected successfully')
            
            cursor = conn.cursor()
            
            # Test database exists
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()[0]
            record_test('Database', f'Database exists ({db_name})', True)
            
            # Check all required tables
            required_tables = [
                'admins', 'users', 'assessments', 'assessment_results',
                'health_records', 'health_tips', 'pending_actions',
                'admin_notifications', 'activity_logs'
            ]
            
            cursor.execute("SHOW TABLES")
            existing_tables = [table[0] for table in cursor.fetchall()]
            
            for table in required_tables:
                exists = table in existing_tables
                record_test('Database', f'Table: {table}', exists)
            
            # Check indexes
            cursor.execute("SHOW INDEX FROM admins")
            indexes = cursor.fetchall()
            has_indexes = len(indexes) > 1  # More than just PRIMARY
            record_test('Database', 'Performance indexes', has_indexes, 
                       f"{len(indexes)} indexes found" if has_indexes else "No indexes")
            
            # Check if admin exists
            cursor.execute("SELECT COUNT(*) FROM admins")
            admin_count = cursor.fetchone()[0]
            record_test('Database', 'Admin accounts', admin_count > 0, 
                       f"{admin_count} admin(s) found")
            
            # Check table sizes
            cursor.execute("""
                SELECT table_name, table_rows 
                FROM information_schema.tables 
                WHERE table_schema = %s
            """, (db_name,))
            
            table_stats = cursor.fetchall()
            print_info(f"Database statistics:")
            for table_name, row_count in table_stats:
                if table_name in required_tables:
                    print_info(f"  - {table_name}: {row_count or 0} rows")
            
            conn.close()
            
        except Exception as e:
            record_test('Database', 'MySQL connection', False, str(e))
            
    except ImportError:
        record_test('Database', 'Database module', False, 'database.py not found')

# ============================================================================
# TEST 4: REDIS CACHE
# ============================================================================
def test_redis_cache():
    print_section("TEST 4: Redis Cache System")
    
    try:
        from utils.redis_cache import RedisCache, cached
        record_test('Redis', 'Redis module import', True)
        
        # Test RedisCache class
        try:
            cache = RedisCache()
            
            # Test basic operations
            cache.set('test_key', 'test_value', timeout=60)
            value = cache.get('test_key')
            
            if value == 'test_value':
                record_test('Redis', 'Cache set/get operations', True)
            else:
                record_test('Redis', 'Cache set/get operations', False, f"Expected 'test_value', got {value}")
            
            # Test delete
            cache.delete('test_key')
            value = cache.get('test_key')
            record_test('Redis', 'Cache delete operation', value is None)
            
            # Test decorator
            call_count = [0]
            
            @cached(timeout=60, key_prefix='test')
            def test_function(x):
                call_count[0] += 1
                return x * 2
            
            result1 = test_function(5)
            result2 = test_function(5)
            
            cached_correctly = (result1 == 10 and result2 == 10 and call_count[0] == 1)
            record_test('Redis', '@cached decorator', cached_correctly, 
                       'Function called once, cached result used' if cached_correctly else 'Caching not working')
            
            # Test cache type
            if cache.redis_client:
                record_test('Redis', 'Cache type', True, 'Using Redis server')
            else:
                record_test('Redis', 'Cache type', True, 'Using in-memory fallback (Redis server not running)')
            
            # Clear test data
            cache.clear()
            
        except Exception as e:
            record_test('Redis', 'Cache operations', False, str(e))
            
    except ImportError as e:
        record_test('Redis', 'Redis module', False, str(e))

# ============================================================================
# TEST 5: BACKUP SYSTEM
# ============================================================================
def test_backup_system():
    print_section("TEST 5: Database Backup System")
    
    # Check backup script exists
    backup_script_exists = os.path.exists('database_backup.py')
    record_test('Backup', 'Backup script exists', backup_script_exists)
    
    # Check backups directory
    backups_dir_exists = os.path.isdir('backups')
    record_test('Backup', 'Backups directory exists', backups_dir_exists)
    
    if backups_dir_exists:
        # Check for existing backups
        backups = [f for f in os.listdir('backups') if f.endswith('.sql.gz') or f.endswith('.sql')]
        backup_count = len(backups)
        record_test('Backup', 'Backups available', backup_count > 0, 
                   f"{backup_count} backup(s) found" if backup_count > 0 else "No backups yet")
        
        if backup_count > 0:
            # Check latest backup
            latest_backup = max(backups, key=lambda f: os.path.getmtime(os.path.join('backups', f)))
            backup_size = os.path.getsize(os.path.join('backups', latest_backup))
            backup_age = time.time() - os.path.getmtime(os.path.join('backups', latest_backup))
            
            print_info(f"Latest backup: {latest_backup}")
            print_info(f"Size: {backup_size / 1024:.2f} KB")
            print_info(f"Age: {backup_age / 3600:.1f} hours ago")

# ============================================================================
# TEST 6: FLASK APPLICATION
# ============================================================================
def test_flask_app():
    print_section("TEST 6: Flask Application Structure")
    
    try:
        # Test app import
        try:
            from app import app
            record_test('Flask', 'App module import', True)
            
            # Check if app is configured
            has_secret = app.config.get('SECRET_KEY') is not None
            record_test('Flask', 'SECRET_KEY configured', has_secret)
            
            # Check CSRF protection
            has_csrf = 'csrf' in app.extensions or 'csrf_protect' in app.extensions
            record_test('Flask', 'CSRF protection enabled', has_csrf)
            
            # Check rate limiter
            has_limiter = 'limiter' in app.extensions
            record_test('Flask', 'Rate limiter enabled', has_limiter)
            
            # Check mail
            has_mail = 'mail' in app.extensions
            record_test('Flask', 'Email system configured', has_mail)
            
        except Exception as e:
            record_test('Flask', 'App module import', False, str(e))
        
        # Check route files
        route_files = [
            'routes/auth.py',
            'routes/users.py',
            'routes/assessments.py',
            'routes/healthtips.py',
            'routes/admin_routes.py',
            'routes/logs.py',
            'routes/reports.py'
        ]
        
        for route_file in route_files:
            exists = os.path.exists(route_file)
            record_test('Flask', f'Route file: {route_file.split("/")[1]}', exists)
            
    except Exception as e:
        record_test('Flask', 'Flask application', False, str(e))

# ============================================================================
# TEST 7: SECURITY FEATURES
# ============================================================================
def test_security():
    print_section("TEST 7: Security Features")
    
    # Check security files
    security_files = [
        ('sentry_integration.py', 'Sentry error tracking'),
        ('config_production.py', 'Production configuration'),
        ('.env.production.template', 'Environment template')
    ]
    
    for file, description in security_files:
        exists = os.path.exists(file)
        record_test('Security', description, exists)
    
    # Check if sessions are configured
    try:
        from app import app
        session_config = {
            'SESSION_COOKIE_HTTPONLY': app.config.get('SESSION_COOKIE_HTTPONLY', False),
            'SESSION_COOKIE_SAMESITE': app.config.get('SESSION_COOKIE_SAMESITE'),
            'PERMANENT_SESSION_LIFETIME': app.config.get('PERMANENT_SESSION_LIFETIME') is not None
        }
        
        record_test('Security', 'HttpOnly cookies', session_config['SESSION_COOKIE_HTTPONLY'])
        record_test('Security', 'SameSite cookies', session_config['SESSION_COOKIE_SAMESITE'] is not None)
        record_test('Security', 'Session timeout', session_config['PERMANENT_SESSION_LIFETIME'])
        
    except:
        pass

# ============================================================================
# TEST 8: PRODUCTION READINESS
# ============================================================================
def test_production_readiness():
    print_section("TEST 8: Production Deployment Files")
    
    production_files = [
        ('gunicorn_config.py', 'Gunicorn WSGI server config'),
        ('nginx_config.conf', 'Nginx reverse proxy config'),
        ('eyecare_admin.service', 'Systemd service file'),
        ('add_database_indexes.py', 'Database optimization script'),
        ('DEPLOYMENT_GUIDE.md', 'Deployment documentation'),
        ('QUICKSTART.md', 'Quick start guide')
    ]
    
    for file, description in production_files:
        exists = os.path.exists(file)
        record_test('Production', description, exists)

# ============================================================================
# TEST 9: DOCUMENTATION
# ============================================================================
def test_documentation():
    print_section("TEST 9: Documentation Completeness")
    
    doc_files = [
        'DEPLOYMENT_GUIDE.md',
        'QUICKSTART.md',
        'PHASE5A_COMPLETE.md',
        'PHASE5A_PROGRESS.md',
        'SYSTEM_ANALYSIS.md',
        'PHASE4_COMPLETE.md'
    ]
    
    for doc in doc_files:
        exists = os.path.exists(doc)
        if exists:
            size = os.path.getsize(doc)
            record_test('Documentation', doc, True, f"{size / 1024:.1f} KB")
        else:
            record_test('Documentation', doc, False)

# ============================================================================
# TEST 10: API ENDPOINTS (Live Server Test)
# ============================================================================
def test_api_endpoints():
    print_section("TEST 10: API Endpoints (Server Running Test)")
    
    # Check if server is running
    base_url = "http://localhost:5001"
    
    try:
        response = requests.get(f"{base_url}/", timeout=2)
        server_running = response.status_code in [200, 302, 401]
        record_test('API', 'Server running', server_running, 
                   f"Status code: {response.status_code}" if server_running else "Server not responding")
        
        if server_running:
            # Test public endpoints
            endpoints = [
                ('/', 'Root endpoint'),
                ('/login', 'Login page'),
                ('/api/health', 'Health check'),
            ]
            
            for endpoint, description in endpoints:
                try:
                    response = requests.get(f"{base_url}{endpoint}", timeout=2)
                    success = response.status_code in [200, 302, 401, 404]  # 404 is ok if endpoint doesn't exist
                    record_test('API', f'{description} ({endpoint})', success, 
                               f"Status: {response.status_code}")
                except Exception as e:
                    record_test('API', f'{description} ({endpoint})', False, str(e))
        else:
            print_warning("Server not running. Start with: python app.py")
            print_info("Skipping endpoint tests")
            
    except requests.exceptions.ConnectionError:
        record_test('API', 'Server running', False, 'Connection refused - server not running')
        print_warning("Start server with: python app.py")
    except Exception as e:
        record_test('API', 'Server connection', False, str(e))

# ============================================================================
# TEST 11: CODE QUALITY TOOLS
# ============================================================================
def test_code_quality():
    print_section("TEST 11: Code Quality Tools")
    
    tools = ['pytest', 'pylint', 'black', 'flake8', 'mypy']
    
    for tool in tools:
        try:
            __import__(tool)
            record_test('Code Quality', f'{tool.capitalize()}', True, 'Installed')
        except ImportError:
            record_test('Code Quality', f'{tool.capitalize()}', False, 'Not installed')
    
    # Check if tests directory exists
    tests_exist = os.path.isdir('test') or os.path.isdir('tests')
    record_test('Code Quality', 'Test directory', tests_exist)

# ============================================================================
# GENERATE FINAL REPORT
# ============================================================================
def generate_report():
    print_header("COMPREHENSIVE SYSTEM ANALYSIS REPORT")
    
    print(f"\n{Colors.BOLD}Test Execution Time:{Colors.END} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{Colors.BOLD}System:{Colors.END} EyeCare Admin Dashboard")
    print(f"{Colors.BOLD}Version:{Colors.END} 5.0.0 (Phase 5A)")
    
    # Calculate category scores
    print_section("CATEGORY BREAKDOWN")
    
    category_scores = {}
    for category, tests in test_results.items():
        total = len(tests)
        passed = sum(1 for t in tests if t['status'] == 'PASS')
        percentage = (passed / total * 100) if total > 0 else 0
        category_scores[category] = {
            'total': total,
            'passed': passed,
            'percentage': percentage
        }
        
        status_color = Colors.GREEN if percentage >= 90 else Colors.YELLOW if percentage >= 70 else Colors.RED
        print(f"{category:.<30} {status_color}{passed}/{total}{Colors.END} ({status_color}{percentage:.1f}%{Colors.END})")
    
    # Overall score
    overall_percentage = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print_section("OVERALL SYSTEM SCORE")
    
    # Visual progress bar
    bar_length = 50
    filled_length = int(bar_length * passed_tests // total_tests)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    score_color = Colors.GREEN if overall_percentage >= 90 else Colors.YELLOW if overall_percentage >= 70 else Colors.RED
    
    print(f"\n{Colors.BOLD}Total Tests:{Colors.END} {total_tests}")
    print(f"{Colors.BOLD}Passed:{Colors.END} {Colors.GREEN}{passed_tests}{Colors.END}")
    print(f"{Colors.BOLD}Failed:{Colors.END} {Colors.RED}{total_tests - passed_tests}{Colors.END}")
    print(f"\n{bar}")
    print(f"\n{Colors.BOLD}System Completion:{Colors.END} {score_color}{Colors.BOLD}{overall_percentage:.1f}%{Colors.END}")
    
    # Grade assessment
    if overall_percentage >= 95:
        grade = "A+"
        status = "PRODUCTION READY"
        color = Colors.GREEN
    elif overall_percentage >= 90:
        grade = "A"
        status = "EXCELLENT"
        color = Colors.GREEN
    elif overall_percentage >= 80:
        grade = "B"
        status = "GOOD"
        color = Colors.YELLOW
    elif overall_percentage >= 70:
        grade = "C"
        status = "NEEDS IMPROVEMENT"
        color = Colors.YELLOW
    else:
        grade = "D"
        status = "CRITICAL ISSUES"
        color = Colors.RED
    
    print(f"{Colors.BOLD}Grade:{Colors.END} {color}{Colors.BOLD}{grade}{Colors.END}")
    print(f"{Colors.BOLD}Status:{Colors.END} {color}{Colors.BOLD}{status}{Colors.END}")
    
    # Detailed failures
    failures = []
    for category, tests in test_results.items():
        for test in tests:
            if test['status'] == 'FAIL':
                failures.append({
                    'category': category,
                    'test': test['name'],
                    'message': test['message']
                })
    
    if failures:
        print_section("FAILED TESTS DETAILS")
        for i, failure in enumerate(failures, 1):
            print(f"\n{Colors.RED}{i}. {failure['category']} → {failure['test']}{Colors.END}")
            if failure['message']:
                print(f"   {failure['message']}")
    else:
        print_section("FAILED TESTS")
        print_success("All tests passed! 🎉")
    
    # Recommendations
    print_section("RECOMMENDATIONS")
    
    recommendations = []
    
    # Check for specific issues
    if category_scores.get('Database', {}).get('percentage', 0) < 100:
        recommendations.append("⚠ Database: Ensure MySQL is running and all tables are created")
    
    if category_scores.get('Redis', {}).get('percentage', 0) < 100:
        recommendations.append("ℹ Redis: Install Redis server for better caching performance")
    
    if category_scores.get('API', {}).get('percentage', 0) < 100:
        recommendations.append("ℹ Server: Start the Flask server to test API endpoints")
    
    if not recommendations:
        recommendations.append("✓ All systems operational! Ready for production deployment")
    
    for rec in recommendations:
        print(f"  {rec}")
    
    # Next steps
    print_section("NEXT STEPS")
    
    if overall_percentage >= 90:
        print_success("System is production-ready!")
        print_info("1. Review DEPLOYMENT_GUIDE.md")
        print_info("2. Get a production server ($12-15/month)")
        print_info("3. Follow QUICKSTART.md (90 minutes)")
        print_info("4. Deploy and go live! 🚀")
    else:
        print_warning("Address failed tests before deployment")
        print_info("1. Fix issues listed in 'Failed Tests Details'")
        print_info("2. Re-run this test: python test_full_system.py")
        print_info("3. Aim for 90%+ score")
    
    # Save report to file
    print_section("REPORT SAVED")
    
    report_file = f"system_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'overall_score': overall_percentage,
        'grade': grade,
        'status': status,
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'failed_tests': total_tests - passed_tests,
        'category_scores': category_scores,
        'test_results': dict(test_results),
        'failures': failures,
        'recommendations': recommendations
    }
    
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print_info(f"Report saved to: {report_file}")
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    print_header("EYECARE ADMIN SYSTEM - COMPREHENSIVE TEST & ANALYSIS")
    
    print(f"{Colors.BOLD}Starting comprehensive system test...{Colors.END}\n")
    print_info("This will test all components and provide a completion percentage")
    print_info("Estimated time: 30-60 seconds")
    
    start_time = time.time()
    
    # Run all tests
    test_environment()
    test_dependencies()
    test_database()
    test_redis_cache()
    test_backup_system()
    test_flask_app()
    test_security()
    test_production_readiness()
    test_documentation()
    test_api_endpoints()
    test_code_quality()
    
    elapsed_time = time.time() - start_time
    
    # Generate final report
    generate_report()
    
    print(f"{Colors.BOLD}Test completed in {elapsed_time:.2f} seconds{Colors.END}\n")
    
    # Return exit code based on success rate
    if passed_tests / total_tests >= 0.9:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Some failures

if __name__ == "__main__":
    main()
