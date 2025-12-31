"""
Sakina Gas Company - Routes Package
This module provides centralized route/blueprint management.

All blueprints are registered in app.py via the register_blueprints() function.
This file provides utility functions for route management.

Version: 3.0.0
"""

# =============================================================================
# Blueprint Configuration
# =============================================================================

# Blueprint registration order and URL prefixes
# This configuration is used by app.py's register_blueprints() function
BLUEPRINTS_CONFIG = [
    {
        'name': 'auth',
        'url_prefix': '/auth',
        'description': 'Authentication routes (login, logout, password reset)'
    },
    {
        'name': 'dashboard',
        'url_prefix': '/',
        'description': 'Main dashboard and home routes'
    },
    {
        'name': 'employees',
        'url_prefix': '/employees',
        'description': 'Employee management routes'
    },
    {
        'name': 'attendance',
        'url_prefix': '/attendance',
        'description': 'Attendance tracking routes'
    },
    {
        'name': 'leaves',
        'url_prefix': '/leaves',
        'description': 'Leave management routes'
    },
    {
        'name': 'profile',
        'url_prefix': '/profile',
        'description': 'User profile routes'
    },
    {
        'name': 'reports',
        'url_prefix': '/reports',
        'description': 'Reporting and analytics routes'
    },
    {
        'name': 'admin',
        'url_prefix': '/admin',
        'description': 'Administrative routes'
    },
    {
        'name': 'api',
        'url_prefix': '/api/v1',
        'description': 'REST API endpoints'
    }
]


def get_blueprint(blueprint_name):
    """
    Get a blueprint by name.
    
    Args:
        blueprint_name: Name of the blueprint (e.g., 'auth', 'dashboard')
        
    Returns:
        Flask Blueprint object
    """
    module = __import__(f'routes.{blueprint_name}', fromlist=[f'{blueprint_name}_bp'])
    return getattr(module, f'{blueprint_name}_bp')


def get_all_blueprints():
    """
    Get all registered blueprints.
    
    Returns:
        List of tuples (blueprint_name, blueprint_object, url_prefix)
    """
    blueprints = []
    
    for config in BLUEPRINTS_CONFIG:
        try:
            bp = get_blueprint(config['name'])
            blueprints.append((config['name'], bp, config['url_prefix']))
        except (ImportError, AttributeError) as e:
            # Blueprint not available, skip it
            pass
    
    return blueprints


def get_blueprint_config():
    """
    Get blueprint configuration.
    
    Returns:
        List of blueprint configuration dictionaries
    """
    return BLUEPRINTS_CONFIG


# =============================================================================
# Route Utility Functions
# =============================================================================

def get_route_list(app):
    """
    Get a list of all registered routes in the application.
    
    Args:
        app: Flask application instance
        
    Returns:
        List of dictionaries with route information
    """
    routes = []
    
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods - {'OPTIONS', 'HEAD'}),
            'path': str(rule),
            'arguments': list(rule.arguments)
        })
    
    return sorted(routes, key=lambda x: x['path'])


def check_route_exists(app, endpoint):
    """
    Check if a route endpoint exists.
    
    Args:
        app: Flask application instance
        endpoint: Route endpoint name (e.g., 'auth.login')
        
    Returns:
        Boolean indicating if route exists
    """
    for rule in app.url_map.iter_rules():
        if rule.endpoint == endpoint:
            return True
    return False


def get_routes_by_blueprint(app, blueprint_name):
    """
    Get all routes for a specific blueprint.
    
    Args:
        app: Flask application instance
        blueprint_name: Name of the blueprint
        
    Returns:
        List of route dictionaries
    """
    routes = []
    prefix = f"{blueprint_name}."
    
    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith(prefix):
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods - {'OPTIONS', 'HEAD'}),
                'path': str(rule),
                'arguments': list(rule.arguments)
            })
    
    return sorted(routes, key=lambda x: x['path'])


# =============================================================================
# Route Name Mappings (for template URL resolution)
# =============================================================================

# These mappings help ensure templates use correct route names
# IMPORTANT: Update this if route names change

ROUTE_ALIASES = {
    # Leave routes
    'leaves.list_requests': 'leaves.list_leaves',  # Alias for backward compatibility
    'leaves.list': 'leaves.list_leaves',
    
    # Profile routes  
    'auth.profile': 'profile.view_profile',  # Alias for backward compatibility
    'user.profile': 'profile.view_profile',
    
    # Dashboard routes
    'home': 'dashboard.main',
    'index': 'dashboard.main',
    
    # Employee routes
    'employees.index': 'employees.list_employees',
    'employees.list': 'employees.list_employees',
    
    # Attendance routes
    'attendance.index': 'attendance.mark',
    'attendance.list': 'attendance.history',
}


def resolve_route_alias(endpoint):
    """
    Resolve a route alias to its actual endpoint.
    
    Args:
        endpoint: Route endpoint name (possibly an alias)
        
    Returns:
        Resolved endpoint name
    """
    return ROUTE_ALIASES.get(endpoint, endpoint)


# =============================================================================
# Export Configuration
# =============================================================================

__all__ = [
    'BLUEPRINTS_CONFIG',
    'get_blueprint',
    'get_all_blueprints',
    'get_blueprint_config',
    'get_route_list',
    'check_route_exists',
    'get_routes_by_blueprint',
    'ROUTE_ALIASES',
    'resolve_route_alias'
]