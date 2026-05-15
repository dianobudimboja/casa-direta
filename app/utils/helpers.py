from datetime import datetime
import re


def format_price(value):
    """Formata um número como moeda (Kz)."""
    if value is None:
        return '0 Kz'
    try:
        return f'{int(value):,} Kz'.replace(',', '.')
    except (ValueError, TypeError):
        return f'{value} Kz'


def format_date(value, format='%d/%m/%Y'):
    """Formata uma data para exibição."""
    if value is None:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    return value.strftime(format)


def time_ago(value):
    """Retorna 'há X minutos/horas/dias' para uma data."""
    if value is None:
        return ''

    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value

    now = datetime.utcnow()
    diff = now - value

    seconds = diff.total_seconds()
    minutes = int(seconds // 60)
    hours = int(minutes // 60)
    days = int(hours // 24)
    weeks = int(days // 7)
    months = int(days // 30)
    years = int(days // 365)

    if seconds < 60:
        return 'agora mesmo'
    elif minutes < 60:
        return f'há {minutes} minuto{"s" if minutes > 1 else ""}'
    elif hours < 24:
        return f'há {hours} hora{"s" if hours > 1 else ""}'
    elif days < 7:
        return f'há {days} dia{"s" if days > 1 else ""}'
    elif weeks < 4:
        return f'há {weeks} semana{"s" if weeks > 1 else ""}'
    elif months < 12:
        return f'há {months} mês{"es" if months > 1 else ""}'
    else:
        return f'há {years} ano{"s" if years > 1 else ""}'


def truncate(text, length=100, suffix='...'):
    """Corta um texto no comprimento especificado."""
    if not text:
        return ''
    if len(text) <= length:
        return text
    return text[:length].rstrip() + suffix


def slugify(text):
    """Converte um texto em slug para URLs."""
    if not text:
        return ''
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text


def init_filters(app):
    """Regista todos os filtros personalizados no Jinja2."""
    app.jinja_env.filters['format_price'] = format_price
    app.jinja_env.filters['format_date'] = format_date
    app.jinja_env.filters['time_ago'] = time_ago
    app.jinja_env.filters['truncate'] = truncate
    app.jinja_env.filters['slugify'] = slugify
    
    # Adiciona também funções globais disponíveis em todos os templates
    app.jinja_env.globals.update({
        'now': datetime.utcnow,
        'format_price': format_price,
        'format_date': format_date,
    })