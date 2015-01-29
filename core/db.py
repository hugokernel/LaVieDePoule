
import sqlalchemy as sqla

db = sqla.create_engine('sqlite:///data.sqlite')
db.echo = False

metadata = sqla.MetaData()

TwitterActivityTable = sqla.Table('twitter_activity', metadata,
    sqla.Column('id',                 sqla.Integer, primary_key=True),
    sqla.Column('source_id',          sqla.Integer),
    sqla.Column('source_reply_id',    sqla.Integer),
    sqla.Column('source_user_name',   sqla.String(255)),
    sqla.Column('source_content',     sqla.String(160)),
    sqla.Column('source_date',        sqla.DateTime),
    sqla.Column('reply_id',           sqla.Integer),
    sqla.Column('reply_content',      sqla.String(160)),
    sqla.Column('reply_date',         sqla.DateTime),
)

EventsTable = sqla.Table('events', metadata,
    sqla.Column('id',     sqla.Integer, primary_key=True),
    sqla.Column('input',  sqla.Integer),
    sqla.Column('type',   sqla.String(160)),
    sqla.Column('date',   sqla.DateTime),
)

SensorsTable = sqla.Table('sensors', metadata,
    sqla.Column('id',     sqla.Integer, primary_key=True),
    sqla.Column('type',   sqla.String(16)),
    sqla.Column('name',   sqla.String(32)),
    sqla.Column('value',  sqla.String(128)),
    sqla.Column('date',   sqla.DateTime),
)

EggsTable = sqla.Table('eggs', metadata,
    sqla.Column('id',       sqla.Integer, primary_key=True),
    sqla.Column('x',        sqla.Integer()),
    sqla.Column('y',        sqla.Integer()),
    sqla.Column('date',     sqla.DateTime),
)

metadata.create_all(db)

