import os
import uuid

from flask import (
    render_template,
    request,
    redirect,
    session,
    url_for,
    Blueprint,
    make_response,
    abort,
    send_from_directory
)
from werkzeug.utils import secure_filename

from models.reply import Reply
from models.topic import Topic
from models.user import User
from routes import current_user, new_csrf_token, csrf_required

import json

import redis

cache = redis.StrictRedis()

from utils import log

main = Blueprint('index', __name__)

"""
用户在这里可以
    访问首页
    注册
    登录

用户登录后, 会写入 session, 并且定向到 /profile
"""


@main.route("/")
def index():
    u = current_user()
    return render_template("index.html", user=u)


@main.route("/register", methods=['POST'])
def register():
    form = request.form.to_dict()
    # 用类函数来判断
    u = User.register(form)
    return redirect(url_for('.index'))


@main.route("/login", methods=['POST'])
def login():
    form = request.form
    u = User.validate_login(form)
    if u is None:
        return redirect(url_for('.index'))
    else:
        # session 中写入 user_id
        session['user_id'] = u.id
        # 设置 cookie 有效期为 永久
        session.permanent = True
        # 转到 topic.index 页面
        return redirect(url_for('topic.index'))


def created_topic(user_id):
    # O(n)
    ts = Topic.all(user_id=user_id)
    return ts

    # k = 'created_topic_{}'.format(user_id)
    # if cache.exists(k):
    #     v = cache.get(k)
    #     ts = json.loads(v)
    #     log
    #     return ts
    # else:
    #     ts = Topic.all(user_id=user_id)
    #     v = json.dumps([t.json() for t in ts])
    #     cache.set(k, v)
    #     return ts


def replied_topic(user_id):
    # O(m*n)
    rs = Reply.all(user_id=user_id)
    ts = []
    for r in rs:
        t = Topic.one(id=r.topic_id)
        ts.append(t)
    return ts
    #
    # k = 'replied_topic_{}'.format(user_id)
    # if cache.exists(k):
    #     v = cache.get(k)
    #     ts = json.loads(v)
    #     return ts
    # else:
    #     rs = Reply.all(user_id=user_id)
    #     ts = []
    #     for r in rs:
    #         t = Topic.one(id=r.topic_id)
    #         ts.append(t)
    #
    #     v = json.dumps([t.json() for t in ts])
    #     cache.set(k, v)
    #
    #     return ts


@main.route('/profile')
def profile():
    u = current_user()
    if u is None:
        return redirect(url_for('.index'))
    else:
        created = created_topic(u.id)
        replied = replied_topic(u.id)
        return render_template(
            'user_setting.html',
            user=u,
            created=created,
            replied=replied
        )


@main.route('/user/<int:id>')
def user_detail(id):
    u = User.one(id=id)
    if u is None:
        return redirect(url_for('.index'))
    else:
        ms_recent = Topic.all(user_id=u.id)
        ms_sort = sorted(ms_recent, key=lambda Topic: Topic.updated_time, reverse=True)
        replies = Reply.all(user_id=u.id)
        replies_sort = sorted(replies, key=lambda Reply: Reply.updated_time, reverse=True)
        return render_template('topic/person_file.html', user=u, ms=ms_sort, ts=replies_sort)


@main.route('/user/setting')
def user_setting():
    token = new_csrf_token()
    u = current_user()
    if u is None:
        abort(404)
    else:
        return render_template('user_setting.html', user=u, token=token)


@main.route('/user/update', methods=['POST'])
# 更新设置内容
@csrf_required
def user_update():
    form = request.form
    u = current_user()
    id = u.id
    User.update(id, **form)
    return redirect(url_for('.user_setting'))


@main.route('/image/add', methods=['POST'])
def avatar_add():
    # flask 帮我拿到了file文件，已经不是二进制了
    file = request.files['avatar']

    suffix = file.filename.split('.')[-1]
    # 保存文件名是用扩展名而不是原文件名，为的是防止有人利用非法路径
    filename = '{}.{}'.format(str(uuid.uuid4()), suffix)
    path = os.path.join('images', filename)
    file.save(path)

    u = current_user()
    User.update(u.id, image='/images/{}'.format(filename))

    return redirect(url_for('.profile'))


@main.route('/images/<filename>')
def image(filename):

    return send_from_directory('images', filename)

@main.route("/change_password", methods=['POST'])
@csrf_required
def password_change():
    u = current_user()
    form = request.form.to_dict()
    old_pass = u.salted_password(form['old_pass'])
    if old_pass == u.password:
        form['password'] = User.salted_password(form['new_pass'])
        u = User.update(u.id,**form)
        result = '修改成功'
        return redirect(url_for('.user_setting', result=result))
    else:
        result = '原密码错误'
        return redirect(url_for('.user_setting', result=result))
