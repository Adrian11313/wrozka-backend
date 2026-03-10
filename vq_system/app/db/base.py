from app.models.base import Base

# Import ALL models so they register in Base.metadata
from app.models.department import Department  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.topic import Topic  # noqa: F401
from app.models.position import Position  # noqa: F401
from app.models.position_history import PositionHistory  # noqa: F401
