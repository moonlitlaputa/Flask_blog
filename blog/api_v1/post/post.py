from flask import g, url_for, current_app
from flask_restful import request, reqparse, Resource
from werkzeug.exceptions import Forbidden

from blog import db
from blog.errors import PermissionForbiddenError
from blog.models import Post, Permission
from blog.api_v1 import token_auth
from blog.api_v1.decorators import permission_required
from blog.utils.web import HTTPStatusCodeMixin

post_parser = reqparse.RequestParser()
post_parser.add_argument(
    'title',
    location='json',
    required=True
)
post_parser.add_argument(
    'content',
    location='json',
    required=True
)
post_parser.add_argument(
    'tags',
    location='json',
    action='append',
    required=True
)
post_parser.add_argument(
    'post_id',
    location='json'
)


class PostView(Resource, HTTPStatusCodeMixin):

    def get(self, post_id):
        post = Post.get_or_404(post_id).update(view=Post.view + 1)
        return {"post": post.to_json()}, self.SUCCESS

    @token_auth.login_required
    @permission_required(Permission.ADMINISTER)
    def put(self, post_id):
        # 修改文章
        args = post_parser.parse_args()
        title = args['title']
        body = args['content']
        tags = args['tags']
        post = Post.get_or_404(post_id)
        if g.current_user != post.author and not g.current_user.can(
                Permission.ADMINISTER):
            raise Forbidden(description="Insufficient permissions")
        post.body = body
        post.title = title
        post.tags = tags
        post.save()
        return {
            'url': url_for('post.postview', post_id=post.id),
            'post_id': post.id
        }, self.SUCCESS

    @token_auth.login_required
    @permission_required(Permission.ADMINISTER)
    def delete(self, post_id):
        post = Post.get_or_404(post_id)
        if g.current_user != post.author and not g.current_user.can(
                Permission.ADMINISTER):
            raise PermissionForbiddenError(
                description='Insufficient permissions')
        post.delete()
        return {}, self.SUCCESS


class PostsView(Resource, HTTPStatusCodeMixin):

    def get(self):
        uid = request.args.get('uid')
        page = request.args.get('page', 1, type=int)
        if uid:
            pagination = Post.query.filter_by(
                author_id=uid).order_by(db.desc('timestamp')).paginate(
                    page,
                    per_page=current_app.config['BLOG_POST_PER_PAGE'],
                    error_out=False)
        else:
            pagination = Post.query.order_by(db.desc('timestamp')).paginate(
                page, per_page=current_app.config['BLOG_POST_PER_PAGE'],
                error_out=False
            )
        posts = pagination.items
        prev = None
        if pagination.has_prev:
            prev = url_for('post.postsview', page=page - 1, _external=True)
        _next = None
        if pagination.has_next:
            _next = url_for('post.postsview', page=page + 1, _external=True)
        return {
            'posts': [post.to_json(500) for post in posts],
            'prev': prev,
            'next': _next,
            'count': pagination.total
        }, self.SUCCESS

    @token_auth.login_required
    @permission_required(Permission.ADMINISTER)
    def post(self):
        # 新建文章
        args = post_parser.parse_args(strict=True)
        title = args['title']
        body = args['content']
        tags = args['tags']

        author = g.current_user
        post = Post.create(title=title, body=body, tags=tags, author=author)
        return {
            'url': url_for('post.postview', post_id=post.id),
            'id': post.id
        }, self.CREATED
