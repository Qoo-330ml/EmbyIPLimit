from .admin_groups import register_admin_group_routes
from .admin_shadow import register_admin_shadow_routes
from .admin_system import register_admin_system_routes
from .admin_users import register_admin_user_routes
from .admin_wishes import register_admin_wish_routes
from .auth import register_auth_routes
from .frontend import register_frontend_routes
from .public import register_public_routes
from .user import register_user_routes

__all__ = [
    'register_admin_group_routes',
    'register_admin_shadow_routes',
    'register_admin_system_routes',
    'register_admin_user_routes',
    'register_admin_wish_routes',
    'register_auth_routes',
    'register_frontend_routes',
    'register_public_routes',
    'register_user_routes',
]
