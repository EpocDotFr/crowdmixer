from sqlalchemy_utils import ArrowType
from sqlalchemy import or_
from crowdmixer import db, app

__all__ = [
    'Song'
]


class Song(db.Model):
    class SongQuery(db.Query):
        def search_paginated(self, search_term=None, where='a', order_by_votes=False, page=1):
            q = self

            if order_by_votes:
                q = q.order_by(Song.votes.desc())

            q = q.order_by(Song.title.asc())
            q = q.order_by(Song.artist.asc())

            if search_term:
                if where == 'ar':
                    fil = Song.artist.like('%' + search_term + '%')
                elif where == 'al':
                    fil = Song.album.like('%' + search_term + '%')
                elif where == 't':
                    fil = Song.title.like('%' + search_term + '%')
                elif where == 'a':
                    fil = or_(Song.artist.like('%' + search_term + '%'), Song.album.like('%' + search_term + '%'), Song.title.like('%' + search_term + '%'))

                q = q.filter(fil)

            return q.paginate(page=page, per_page=app.config['SONGS_PER_PAGE'])

    __tablename__ = 'songs'
    query_class = SongQuery

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    title = db.Column(db.String, nullable=False)
    artist = db.Column(db.String, default=None)
    album = db.Column(db.String, default=None)
    path = db.Column(db.String, nullable=False)
    last_queued_at = db.Column(ArrowType, default=None)
    total_times_queued = db.Column(db.Integer, default=0)
    votes = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<Song> #{} : {}'.format(self.id, self.title)
