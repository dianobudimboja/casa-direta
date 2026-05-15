from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class ReportForm(FlaskForm):
    """Formulário para denunciar um anúncio."""
    
    reason = SelectField('Motivo da denúncia', choices=[
        ('fraud', '💰 Fraude / Anúncio falso'),
        ('spam', '📧 Spam / Publicidade Enganosa'),
        ('offensive', '😡 Conteúdo ofensivo ou impróprio'),
        ('scam', '⚠️ Tentativa de burla / Phishing'),
        ('other', '📝 Outro motivo')
    ], validators=[DataRequired(message='Selecione um motivo')])
    
    description = TextAreaField('Descrição detalhada', validators=[
        Optional(),
        Length(max=500, message='A descrição pode ter no máximo 500 caracteres')
    ])
    
    submit = SubmitField('Enviar Denúncia')