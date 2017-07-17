from flask import g
from flask_restful import Resource

from app.models import User, Permission
from app.api_v1 import HTTPStatusCodeMixin, token_auth


class UserProfile(Resource, HTTPStatusCodeMixin):

    decorators = [token_auth.login_required]

    def get(self, uid):
        user = User.query.get(uid)
        edit_permission = False
        if g.current_user == user or g.current_user.can(Permission.ADMINISTER):
            edit_permission = True

        return {
            "user": user.to_json(),
            "edit_permission": edit_permission
        }, self.SUCCESS
