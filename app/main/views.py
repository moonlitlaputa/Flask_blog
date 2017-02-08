# coding: utf-8
from flask import render_template, abort, redirect, url_for, flash, request, current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries

from . import main
from .forms import EditProfileAdminForm, EditProfileForm, PostForm, CommentForm
from app import db
from app.models.roles import Role, Permission
from app.models.users import User
from app.models.posts import Post
from app.models.comments import Comment
from app.decorate import admin_required


@main.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['BLOG_POST_PER_PAGE'], error_out=False
    )
    posts = pagination.items
    return render_template('index.html', posts=posts)


@main.route('/publish_post', methods=['GET', 'POST'])
@login_required
@admin_required
def publish_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
                    title=form.title.data,
                    body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.index'))


@main.route('edit/<int:id>', method=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get(id)
    if current_user != post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash('The post has been updated.')
        return redirect(url_for('.post', id=post.id))
    form.title.data = post.title
    form.body.data = post.body
    return render_template(url_for('edit_post.html', form=form))


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          replied=request.args.get('comment_id') or None,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash('your comment has been published.')
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // current_app.config['BLOG_COMMENT_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['BLOG_COMMENTS_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form, comments=comments, pagination=pagination)


@main.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['BLOG_POST_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts, pagination=pagination)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()
        flash('你的个人资料已经更新')
        return redirect(url_for('.user', username=current_user.username))
    form.username.data = current_user.username
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/comment/<username>')
@login_required
def comment_by(username):
    if current_user.username != username and \
        current_user.can(Permission.ADMINISTER):
        abort(403)
    page = request.args.get('page', 1, type=int)
    pagination = current_user.comments.replies.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['BLOG_COMMENT_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    return render_template('comments.html', comments=comments, pagination=pagination)
