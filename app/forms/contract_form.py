from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, TextAreaField, SubmitField, DateField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from datetime import datetime


class ContractForm(FlaskForm):
    """Formulário para criar contrato de arrendamento."""
    
    # Dados do inquilino
    tenant_name = StringField('Nome completo do inquilino', validators=[
        DataRequired(message='⚠️ Nome do inquilino é obrigatório'),
        Length(min=5, max=100, message='Nome deve ter entre 5 e 100 caracteres')
    ])
    tenant_bi = StringField('Número do BI / Documento', validators=[
        Optional(),
        Length(max=20)
    ])
    tenant_phone = StringField('Telefone do inquilino', validators=[
        Optional(),
        Length(max=20)
    ])
    
    # Condições do contrato
    start_date = DateField('Data de início do contrato', validators=[
        DataRequired(message='⚠️ Data de início é obrigatória')
    ])
    end_date = DateField('Data de fim do contrato', validators=[
        DataRequired(message='⚠️ Data de fim é obrigatória')
    ])
    payment_day = IntegerField('Dia de vencimento (pagamento)', validators=[
        DataRequired(message='⚠️ Dia de vencimento é obrigatório'),
        NumberRange(min=1, max=28, message='Dia deve ser entre 1 e 28')
    ], default=5)
    security_deposit = FloatField('Valor da caução (Kz)', validators=[
        Optional(),
        NumberRange(min=0, message='Valor não pode ser negativo')
    ])
    
    # Cláusulas adicionais
    additional_clauses = TextAreaField('Cláusulas adicionais', validators=[
        Optional(),
        Length(max=2000)
    ])
    
    submit = SubmitField('Gerar Contrato PDF')
    
    def validate_start_date(self, field):
        """Verifica se a data de início não é no passado."""
        if field.data and field.data < datetime.now().date():
            raise ValidationError('A data de início não pode ser no passado.')
    
    def validate_end_date(self, field):
        """Verifica se a data de fim é depois da data de início."""
        if field.data and self.start_date.data and field.data <= self.start_date.data:
            raise ValidationError('A data de fim deve ser posterior à data de início.')