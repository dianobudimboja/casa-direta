from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import StringField, FloatField, IntegerField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError


class PropertyForm(FlaskForm):
    """Formulário para criar/editar imóvel."""
    
    # Informações básicas
    title = StringField('Título do anúncio', validators=[
        DataRequired(message='Título é obrigatório'),
        Length(min=5, max=200, message='Título deve ter entre 5 e 200 caracteres')
    ])
    
    description = TextAreaField('Descrição', validators=[
        DataRequired(message='Descrição é obrigatória'),
        Length(min=20, max=5000, message='Descrição deve ter entre 20 e 5000 caracteres')
    ])
    
    # Detalhes do imóvel
    price = FloatField('Preço (Kz/mês)', validators=[
        DataRequired(message='Preço é obrigatório'),
        NumberRange(min=1000, max=10000000, message='Preço deve estar entre 1.000 Kz e 10.000.000 Kz')
    ])
    
    location = StringField('Localização (Bairro/Zona)', validators=[
        DataRequired(message='Localização é obrigatória'),
        Length(min=3, max=200)
    ])
    
    address = StringField('Endereço completo', validators=[
        Optional(),
        Length(max=300)
    ])
    
    neighborhood = SelectField('Município/Localidade', choices=[
        ('', 'Selecione o Município'),
        # 🟢 Zonas Periféricas
        ('Cacuaco', 'Cacuaco'),
        ('Cazenga', 'Cazenga'),
        ('Viana', 'Viana'),
        ('Mulenvos', 'Mulenvos'),
        ('Hoji Ya Henda', 'Hoji Ya Henda'),
        ('Sambizanga', 'Sambizanga'),
        # 🟡 Zonas Intermédias
        ('Rangel', 'Rangel'),
        ('Samba', 'Samba'),
        ('Camama', 'Camama'),
        ('Kilamba Kiaxi', 'Kilamba Kiaxi'),
        ('Belas', 'Belas'),
        # 🟠 Zonas Centrais
        ('Maianga', 'Maianga'),
        ('Ingombota', 'Ingombota'),
        # 🔴 Zonas Premium
        ('Kilamba', 'Kilamba'),
        ('Talatona', 'Talatona'),
        ('Mussulo', 'Mussulo'),
        ('Outro', 'Outro Município')
    ], validators=[DataRequired(message='Selecione o Município')])
    
    # Características
    bedrooms = IntegerField('Quartos', validators=[
        DataRequired(message='Número de quartos é obrigatório'),
        NumberRange(min=0, max=10, message='Número de quartos inválido')
    ], default=1)
    
    bathrooms = IntegerField('Quartos de Banho', validators=[
        Optional(),
        NumberRange(min=0, max=10)
    ], default=1)
    
    area = FloatField('Área (m²)', validators=[
        Optional(),
        NumberRange(min=1, max=1000)
    ])
    
    # Fotos - CORRIGIDO: usar MultipleFileField (importado corretamente)
    photos = MultipleFileField('Fotos do imóvel', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Apenas imagens são permitidas (JPG, PNG, GIF, WEBP)')
    ])
    
    # Opções extras
    is_featured = BooleanField('Destacar anúncio (pago)')
    
    submit = SubmitField('Publicar imóvel')

    # Coordenadas (opcionais)
    latitude = FloatField('Latitude', validators=[
        Optional(),
        NumberRange(min=-90, max=90, message='Latitude deve estar entre -90 e 90')
    ])
    longitude = FloatField('Longitude', validators=[
        Optional(),
        NumberRange(min=-180, max=180, message='Longitude deve estar entre -180 e 180')
    ])
    
    def validate_title(self, field):
        """Verifica se o título não é muito genérico (anti-spam)."""
        generic_titles = ['casa', 'quarto', 'imóvel', 'casa para alugar', 'quarto para alugar']
        if field.data.lower().strip() in generic_titles:
            raise ValidationError('Título muito genérico. Seja mais específico (ex: "Casa T2 no Kilamba com garagem")')


class PropertySearchForm(FlaskForm):
    """Formulário de pesquisa de imóveis."""
    query = StringField('Pesquisar', validators=[Optional()])
    min_price = FloatField('Preço mínimo', validators=[Optional(), NumberRange(min=0)])
    max_price = FloatField('Preço máximo', validators=[Optional(), NumberRange(min=0)])
    neighborhood = SelectField('Localidade', choices=[
        ('', 'Todos os Bairros'),
        ('Kilamba', 'Kilamba'),
        ('Camama', 'Camama'),
        ('Viana', 'Viana'),
        ('Benfica', 'Benfica'),
        ('Talatona', 'Talatona'),
        ('Luanda Sul', 'Luanda Sul')
    ], validators=[Optional()])
    bedrooms = SelectField('Quartos', choices=[
        ('', 'Qualquer'),
        ('1', '1+'),
        ('2', '2+'),
        ('3', '3+'),
        ('4', '4+')
    ], validators=[Optional()])
    sort_by = SelectField('Ordenar por', choices=[
        ('newest', 'Mais recentes'),
        ('price_asc', 'Preço (menor para maior)'),
        ('price_desc', 'Preço (maior para menor)'),
        ('popular', 'Mais vistos')
    ], default='newest')
    submit = SubmitField('Buscar')