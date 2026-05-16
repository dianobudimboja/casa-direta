from flask import Blueprint, render_template, request, current_app, abort, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, func

from ..extensions import db
from ..models.property import Property
from ..models.user import User
from ..forms.property_form import PropertyForm, PropertySearchForm
from ..utils.upload_helper import save_uploaded_file, delete_uploaded_file

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Página inicial com lista de imóveis."""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('PROPERTIES_PER_PAGE', 12)
    
    # Query base - apenas imóveis ativos
    query = Property.query.filter_by(is_active=True)
    
    # Aplicar filtros da pesquisa
    search_query = request.args.get('query', '')
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            or_(
                Property.title.ilike(search_term),
                Property.description.ilike(search_term),
                Property.location.ilike(search_term)
            )
        )
    
    neighborhood = request.args.get('neighborhood', '')
    if neighborhood:
        query = query.filter(Property.neighborhood == neighborhood)
    
    min_price = request.args.get('min_price', '')
    if min_price:
        query = query.filter(Property.price >= float(min_price))
    
    max_price = request.args.get('max_price', '')
    if max_price:
        query = query.filter(Property.price <= float(max_price))
    
    bedrooms = request.args.get('bedrooms', '')
    if bedrooms:
        query = query.filter(Property.bedrooms >= int(bedrooms))
    
    # Ordenação
    sort_by = request.args.get('sort_by', 'newest')
    if sort_by == 'price_asc':
        query = query.order_by(Property.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Property.price.desc())
    elif sort_by == 'popular':
        query = query.order_by(Property.views.desc())
    else:  # newest
        query = query.order_by(Property.created_at.desc())
    
    # Paginação
    properties = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Imóveis em destaque (featured)
    featured_properties = Property.query.filter_by(
        is_active=True, 
        is_featured=True
    ).limit(6).all()
    
    # Estatísticas rápidas (com segurança para valores None)
    total_properties = Property.query.filter_by(is_active=True).count()
    total_landlords = User.query.filter_by(is_landlord=True).count()
    avg_price_result = db.session.query(func.avg(Property.price)).filter_by(is_active=True).scalar()
    avg_price = float(avg_price_result) if avg_price_result else 0
    
    stats = {
        'total_properties': total_properties,
        'total_landlords': total_landlords,
        'avg_price': avg_price
    }
    
    # Formulário de pesquisa (para o template)
    search_form = PropertySearchForm()
    
    return render_template(
        'index.html',
        properties=properties,
        featured_properties=featured_properties,
        search_form=search_form,
        stats=stats
    )


@bp.route('/property/<int:property_id>')
def property_detail(property_id):
    """Página de detalhe de um imóvel."""
    property_obj = Property.query.get_or_404(property_id)
    
    # Incrementa contador de visualizações
    property_obj.increment_views()
    
    # Imóveis similares (mesmo bairro +- 30% preço)
    similar_properties = Property.query.filter(
        Property.is_active == True,
        Property.id != property_obj.id,
        Property.neighborhood == property_obj.neighborhood,
        Property.price.between(property_obj.price * 0.7, property_obj.price * 1.3)
    ).limit(6).all()
    
    return render_template(
        'properties/detail.html',
        property=property_obj,
        similar_properties=similar_properties
    )


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_property():
    """Página para criar um novo anúncio de imóvel."""
    if not current_user.can_publish_more_properties():
        flash('Você atingiu o limite de anúncios. Verifique a sua conta para publicar mais.', 'warning')
        return redirect(url_for('dashboard.index'))
    
    form = PropertyForm()
    
    if form.validate_on_submit():
        # Processa upload das fotos
        uploaded_photos = []
        main_photo = None
        
        if form.photos.data:
            for i, photo in enumerate(form.photos.data):
                if photo and photo.filename:
                    filename = save_uploaded_file(photo, 'properties')
                    if filename:
                        uploaded_photos.append(filename)
                        if i == 0:  # Primeira foto é a principal
                            main_photo = filename
        
        property_obj = Property(
            title=form.title.data,
            description=form.description.data,
            price=form.price.data,
            location=form.location.data,
            address=form.address.data,
            neighborhood=form.neighborhood.data,
            bedrooms=form.bedrooms.data,
            bathrooms=form.bathrooms.data,
            area=form.area.data,
            is_featured=form.is_featured.data,
            photos=uploaded_photos,
            main_photo=main_photo,
            user_id=current_user.id
        )
        
        if form.validate_on_submit():
            property_obj = Property(
            # ... campos existentes ...
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            # ...
        )

        db.session.add(property_obj)
        current_user.properties_count += 1
        db.session.commit()
        
        flash('Imóvel publicado com sucesso!', 'success')
        return redirect(url_for('main.property_detail', property_id=property_obj.id))
    
    return render_template('properties/create.html', form=form)


@bp.route('/search')
def search():
    """API de pesquisa rápida (AJAX)."""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify({'results': []})
    
    properties = Property.query.filter(
        Property.is_active == True,
        or_(
            Property.title.ilike(f'%{query}%'),
            Property.location.ilike(f'%{query}%'),
            Property.neighborhood.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    return jsonify({
        'results': [
            {
                'id': p.id,
                'title': p.title,
                'price': p.price,
                'location': p.location,
                'main_photo': p.main_photo
            }
            for p in properties
        ]
    })


@bp.route('/about')
def about():
    """Página sobre a plataforma."""
    return render_template('about.html')


@bp.route('/faq')
def faq():
    """Página de perguntas frequentes."""
    return render_template('faq.html')

@bp.route('/terms')
def terms():
    """Termos de Uso."""
    return render_template('terms.html')


@bp.route('/privacy')
def privacy():
    """Política de Privacidade."""
    return render_template('privacy.html')


@bp.route('/cookies')
def cookies():
    """Política de Cookies."""
    return render_template('cookies.html')


@bp.route('/contact')
def contact():
    """Página de Contacto."""
    return render_template('contact.html')

@bp.route('/debug-form', methods=['GET', 'POST'])
def debug_form():
    """Rota temporária para debug do formulário."""
    if request.method == 'POST':
        return jsonify({
            'form_data': dict(request.form),
            'files': [f.filename for f in request.files.getlist('photos')] if request.files else []
        })
    
    return '''
    <form method="POST" enctype="multipart/form-data">
        <input type="text" name="title" placeholder="Título" required><br>
        <textarea name="description" placeholder="Descrição" required></textarea><br>
        <input type="number" name="price" placeholder="Preço" required><br>
        <input type="text" name="location" placeholder="Localização" required><br>
        <input type="text" name="neighborhood" placeholder="Bairro" required><br>
        <input type="number" name="bedrooms" value="1"><br>
        <input type="number" name="bathrooms" value="1"><br>
        <input type="file" name="photos" multiple><br>
        <button type="submit">Enviar</button>
    </form>
    '''