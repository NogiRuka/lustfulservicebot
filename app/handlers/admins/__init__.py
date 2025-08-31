from app.handlers.admins.admins import admins_router
from app.handlers.admins.review import review_router
from app.handlers.admins.review_note import review_note_router

admin_routers = [
    admins_router,
    review_router,
    review_note_router
]
