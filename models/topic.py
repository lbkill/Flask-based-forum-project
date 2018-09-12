import time

from sqlalchemy import String, Integer, Column, Text, UnicodeText, Unicode

from models.base_model import SQLMixin, db
from models.user import User
from models.reply import Reply


class Topic(SQLMixin, db.Model):
    views = Column(Integer, nullable=False, default=0)
    title = Column(Unicode(50), nullable=False)
    content = Column(UnicodeText, nullable=False)
    user_id = Column(Integer, nullable=False)
    board_id = Column(Integer, nullable=False)

    @classmethod
    def new(cls, form, user_id):
        form['user_id'] = user_id
        m = super().new(form)
        return m

    @classmethod
    def get(cls, id):
        m = cls.one(id=id)
        m.views += 1
        m.save()
        return m

    def user(self):
        u = User.one(id=self.user_id)
        return u

    def replies(self):
        ms = Reply.all(topic_id=self.id)
        return ms

    def reply_count(self):
        count = len(self.replies())
        return count

    def total_time(self):
        now = int(time.time())
        tol_time = now - self.updated_time
        if tol_time > 60 and tol_time < 3600:
            time_minute = time.strftime('%M', time.gmtime(tol_time))
            return '{} 分钟前'.format(time_minute)
        if tol_time > 3600 and tol_time < 86400:
            time_hour = time.strftime('%H', time.gmtime(tol_time))
            return '{} 小时前'.format(time_hour)
        if tol_time > 86400 and tol_time < 2592000:
            time_day = time.strftime('%d', time.gmtime(tol_time))
            return '{} 天前'.format(time_day)
