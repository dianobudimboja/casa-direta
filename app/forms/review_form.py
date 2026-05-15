from flask_wtf import FlaskForm
from wtforms import IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length, Optional


class ReviewForm(FlaskForm):
    """Formulário para criar uma avaliação."""
    
    rating = IntegerField('Classificação', validators=[
        DataRequired(message='Por favor, selecione uma classificação'),
        NumberRange(min=1, max=5, message='A classificação deve ser entre 1 e 5 estrelas')
    ])
    
    comment = TextAreaField('Comentário (opcional)', validators=[
        Optional(),
        Length(max=500, message='O comentário pode ter no máximo 500 caracteres')
    ])
    
    submit = SubmitField('Publicar Avaliação')