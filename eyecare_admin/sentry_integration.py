"""
Sentry Integration for Error Tracking
Automatically captures and reports errors to Sentry
"""
import os

def init_sentry(app):
    """
    Initialize Sentry error tracking
    
    Args:
        app: Flask application instance
    """
    sentry_dsn = os.getenv('SENTRY_DSN')
    
    if not sentry_dsn:
        app.logger.warning("Sentry DSN not configured. Error tracking disabled.")
        return False
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                FlaskIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],
            environment=os.getenv('SENTRY_ENVIRONMENT', 'production'),
            traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', 0.1)),
            
            # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring
            # We recommend adjusting this value in production
            send_default_pii=False,  # Don't send personally identifiable information
            
            # Release tracking
            release=os.getenv('APP_VERSION', 'unknown'),
            
            # Attach stacklocals for better debugging (disable in production if too verbose)
            attach_stacktrace=True,
            
            # Before send hook to filter sensitive data
            before_send=before_send_handler,
        )
        
        app.logger.info(f"✓ Sentry initialized: {os.getenv('SENTRY_ENVIRONMENT', 'production')}")
        return True
        
    except ImportError:
        app.logger.error("sentry-sdk not installed. Run: pip install sentry-sdk[flask]")
        return False
    except Exception as e:
        app.logger.error(f"Failed to initialize Sentry: {e}")
        return False

def before_send_handler(event, hint):
    """
    Filter and modify events before sending to Sentry
    Remove sensitive information
    """
    # Remove sensitive keys from request data
    if 'request' in event:
        request = event['request']
        
        # Remove sensitive headers
        if 'headers' in request:
            sensitive_headers = ['Authorization', 'Cookie', 'X-Auth-Token']
            for header in sensitive_headers:
                if header in request['headers']:
                    request['headers'][header] = '[Filtered]'
        
        # Remove sensitive form data
        if 'data' in request:
            sensitive_fields = ['password', 'password_hash', 'token', 'secret']
            if isinstance(request['data'], dict):
                for field in sensitive_fields:
                    if field in request['data']:
                        request['data'][field] = '[Filtered]'
    
    # Remove sensitive variables from stack frames
    if 'exception' in event and 'values' in event['exception']:
        for exception in event['exception']['values']:
            if 'stacktrace' in exception and 'frames' in exception['stacktrace']:
                for frame in exception['stacktrace']['frames']:
                    if 'vars' in frame:
                        sensitive_vars = ['password', 'token', 'secret', 'api_key']
                        for var in sensitive_vars:
                            if var in frame['vars']:
                                frame['vars'][var] = '[Filtered]'
    
    return event

def capture_exception(error, context=None):
    """
    Manually capture an exception to Sentry
    
    Args:
        error: Exception to capture
        context: Additional context dict
    """
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            sentry_sdk.capture_exception(error)
    except:
        pass  # Fail silently if Sentry not available

def capture_message(message, level='info', context=None):
    """
    Capture a message to Sentry
    
    Args:
        message: Message string
        level: 'debug', 'info', 'warning', 'error', 'fatal'
        context: Additional context dict
    """
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            sentry_sdk.capture_message(message, level=level)
    except:
        pass

# Example usage in routes
def example_error_tracking():
    """
    Example of how to use Sentry in your routes
    """
    from flask import current_app
    
    try:
        # Your code here
        pass
    except Exception as e:
        # Log to Flask logger
        current_app.logger.error(f"Error occurred: {str(e)}", exc_info=True)
        
        # Capture to Sentry with context
        capture_exception(e, context={
            'user_id': 'user_123',
            'action': 'create_user',
            'additional_data': {'key': 'value'}
        })
        
        # Return error response
        return {'error': 'An error occurred'}, 500

if __name__ == "__main__":
    print("""
Sentry Error Tracking Setup
===========================

1. Create Sentry Account:
   Visit: https://sentry.io/signup/

2. Create New Project:
   - Select "Flask" as platform
   - Copy the DSN URL

3. Install Sentry SDK:
   pip install sentry-sdk[flask]

4. Add to .env.production:
   SENTRY_DSN=https://your-key@sentry.io/project-id
   SENTRY_ENVIRONMENT=production
   SENTRY_TRACES_SAMPLE_RATE=0.1

5. Initialize in app.py:
   from sentry_integration import init_sentry
   init_sentry(app)

Features:
- Automatic error capture
- Performance monitoring
- Release tracking
- Breadcrumbs
- Context & tags
- Stack traces
- Email notifications

Test Error Capture:
- Trigger an error in your app
- Check Sentry dashboard
- View full stack trace and context
""")
