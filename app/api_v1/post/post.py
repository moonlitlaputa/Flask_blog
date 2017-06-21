from flask import g, url_for
from flask_restful import request

from app.models import Post, Permission
from app.api_v1 import permission_required, BaseResource, token_auth

from . import post_parser


class PostView(BaseResource):

    @token_auth.login_required
    @permission_required(Permission.ADMINISTER)
    def post(self):
        # 新建文章
        args = post_parser.parse_args()
        title = args['title']
        body = args['content']
        tags = args['tags']
        author = g.current_user
        post = Post.create(title=title, body=body, tags=tags, author_id=author.id)
        return {'url': url_for('post.postview', id=post.id)}, self.CREATED

    def get(self):
        post = Post.get_or_404(request.args.get('id')).update(view=Post.view + 1)
        return {"post": post.to_json()}, self.SUCCESS

    @token_auth.login_required
    @permission_required(Permission.ADMINISTER)
    def put(self):
        # 修改文章
        args = post_parser.parse_args()
        title = args['title']
        body = args['content']
        tags = args['tags']
        post = Post.get(args['post_id'])
        if g.current_user != post.author and not g.current_user.can(Permission.ADMINISTER):
            return {"message": "Insufficient permissions"}, self.PERMISSION_FORBIDDEN
        post.body = body
        post.title = title
        post.tags = tags
        post.save()
        return self.SUCCESS

    @token_auth.login_required
    @permission_required(Permission.ADMINISTER)
    def delete(self):
        post = Post.get_or_404(request.args['post_id'])
        if g.current_user != post.author and not g.current_user.can(Permission.ADMINISTER):
            return {"message": "Insufficient permissions"}, self.PERMISSION_FORBIDDEN
        post.delete()
        return 200
