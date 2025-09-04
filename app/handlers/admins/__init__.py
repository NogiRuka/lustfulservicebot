from app.handlers.admins.admins import admins_router
from app.handlers.admins.superadmin import superadmin_router
from app.handlers.admins.review_center import review_center_router
from app.handlers.admins.movie_review import movie_review_router
from app.handlers.admins.content_review import content_review_router
from app.handlers.admins.review_note import review_note_router

admin_routers = [
    admins_router,
    superadmin_router,
    review_center_router,
    movie_review_router,
    content_review_router,
    review_note_router
]
