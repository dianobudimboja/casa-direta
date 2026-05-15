from app import create_app, db

app = create_app()

with app.app_context():
    print(db.engine.url)
    db.create_all()
    print('✅ Conectado e tabelas criadas!')