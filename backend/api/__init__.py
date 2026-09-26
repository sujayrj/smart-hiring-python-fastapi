from api import (
    applications,
    audit,
    auth,
    candidates,
    dashboard,
    flags,
    interviewer,
    jds,
    screening,
    users,
)

routers = [
    auth.router,
    jds.router,
    screening.router,
    candidates.router,
    applications.router,
    audit.router,
    flags.router,
    dashboard.router,
    users.router,
    interviewer.router,
]

__all__ = ["routers"]
