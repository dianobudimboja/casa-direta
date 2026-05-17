from app import create_app, db
from app.models.user import User

app = create_app()
ctx = app.app_context()
ctx.push()

user = User.query.filter_by(email='diano.budimboja@gmail.com').first()
user.is_admin = True
db.session.commit()

print(f'{user.email} agora é administrador!')

ctx.pop()
