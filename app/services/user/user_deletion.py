from app import db
import app.services.authentication as authentication
from app.utils.errors import AccessDenied
from app.services.box import BoxDeletionService
from app.models import Box


class UserDeletion:
    def __init__(self, user, **attrs):
        self.user = user
        self.scopes = attrs.pop("scopes")
        self.password = attrs.pop("password")
        authentication.validate_scope_permissions("delete:user", self.scopes, attrs)

    def delete(self):
        if "delete:user" not in self.scopes:
            raise AccessDenied("Insufficient permissions")

        if not self.user.check_password(self.password):
            raise AccessDenied("Wrong password")

        boxes = Box.query.filter_by(user=self.user)
        for box in boxes:
            BoxDeletionService(self.user, box).delete()

        entries_deleted = db.session.delete(self.user)
        db.session.flush()

        return entries_deleted
