from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import Optional, Length


class RoleRequestForm(FlaskForm):
    """Formulário para solicitar tornar-se senhorio."""
    
    notes = TextAreaField('Justificação (opcional)', validators=[
        Optional(),
        Length(max=500, message='A justificação pode ter no máximo 500 caracteres')
    ])
    
    submit = SubmitField('Solicitar Aprovação para Ser Senhorio')