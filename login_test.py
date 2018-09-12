from flask import Blueprint, session

main = Blueprint('main', __name__)


@main.route("/login")
def login():
    session['test'] = 'test'


@main.route("/test")
def login_test():
    if 'test' in session:
        return 'ok'
    else:
        return 'not ok'
