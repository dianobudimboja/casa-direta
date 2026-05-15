from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Optional
from wtforms.validators import Optional


class VerificationRequestForm(FlaskForm):
    """Formulário para solicitar verificação de identidade."""
    
    bi_front = FileField('Frente do BI', validators=[
        FileRequired(message='A foto da frente do BI é obrigatória'),
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Apenas imagens são permitidas')
    ])
    
    bi_back = FileField('Verso do BI', validators=[
        FileRequired(message='A foto do verso do BI é obrigatória'),
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Apenas imagens são permitidas')
    ])
    
    property_document = FileField('Comprovativo de Propriedade (opcional)', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf', 'webp'], 'Apenas imagens ou PDF')
    ])
    
    submit = SubmitField('Solicitar Verificação')


class AdminVerificationForm(FlaskForm):
    """Formulário para admin aprovar/rejeitar verificação."""
    
    action = SelectField('Ação', choices=[
        ('approve', 'Aprovar Verificação'),
        ('reject', 'Rejeitar Verificação')
    ], validators=[DataRequired()])
    
    rejection_reason = TextAreaField('Motivo da Rejeição', validators=[
        Optional(),
        Length(max=500)
    ])
    
    submit = SubmitField('Processar')