from app.models.users.view import UserView
from app.models.cameras.view import CamerasView
from app.models.user_events.view import UserEventsView

def register_views(admin):
    admin.add_view(UserView)
    admin.add_view(CamerasView)
    admin.add_view(UserEventsView)