from app import create_app, db
from app.models.user import User
from app.models.property import Property
from app.models.message import Message
from app.models.review import Review


app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Adiciona modelos ao contexto do shell Flask."""
    return {
        'db': db,
        'User': User,
        'Property': Property,
        'Message': Message,
        'Review': Review
    }

if __name__ == '__main__':
    app.run()