from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.db_helper import db_helper
from app.models.users.model import User
from app.models.rbac.model import Role, Permission
from app.modules.auth.dependencies import PermissionChecker
from app.modules.auth.utils import get_password_hash

async def init_rbac(app: FastAPI):
    # 1. Collect all permissions from routes
    collected_permissions = set()
    for route in app.routes:
        if hasattr(route, "dependencies"):
            for depends in route.dependencies:
                if isinstance(depends.dependency, PermissionChecker):
                    collected_permissions.add(depends.dependency.required_permission)

    # 2. Sync to DB
    async with db_helper.session_factory() as session:
        # Get existing permissions
        stmt = select(Permission)
        result = await session.execute(stmt)
        existing_permissions = result.scalars().all()
        existing_perm_names = {p.name for p in existing_permissions}

        # Add new permissions
        new_permissions = collected_permissions - existing_perm_names
        for perm_name in new_permissions:
            new_perm = Permission(name=perm_name)
            session.add(new_perm)
        
        await session.commit()

        # Get all permissions again
        result = await session.execute(select(Permission))
        all_permissions = result.scalars().all()

        # 3. Create or get admin role
        stmt = select(Role).options(selectinload(Role.permissions)).where(Role.name == "admin")
        result = await session.execute(stmt)
        admin_role = result.scalar_one_or_none()

        if not admin_role:
            admin_role = Role(name="admin")
            session.add(admin_role)
            # Устанавливаем права до flush, чтобы избежать lazy-load
            admin_role.permissions = list(all_permissions)
            await session.flush()
        else:
            # У существующей роли permissions уже загружены через selectinload
            admin_role.permissions = list(all_permissions)
            await session.flush()

        # 4. Create or get admin user
        admin_login = settings.admin.login
        admin_password = settings.admin.password

        stmt = select(User).where(User.username == admin_login)
        result = await session.execute(stmt)
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            admin_user = User(
                username=admin_login,
                password=get_password_hash(admin_password),
                is_active=True,
                role_id=admin_role.id
            )
            session.add(admin_user)
        else:
            # Обновляем пароль каждый раз, чтобы применить хэш
            # если в старой БД пароль лежал в plain-text, или если вы поменяли его в .env
            admin_user.password = get_password_hash(admin_password)
            if admin_user.role_id != admin_role.id:
                admin_user.role_id = admin_role.id
        
        await session.commit()
