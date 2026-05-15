from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user

from ..extensions import db
from ..models.property import Property
from ..models.favorite import Favorite

bp = Blueprint('favorites', __name__, url_prefix='/favorites')


@bp.route('/toggle/<int:property_id>')
@login_required
def toggle_favorite(property_id):
    """Adiciona ou remove um imóvel dos favoritos (AJAX)."""
    
    property_obj = Property.query.get_or_404(property_id)
    
    if current_user.is_favorite(property_id):
        current_user.remove_favorite(property_id)
        is_favorite = False
        message = 'Imóvel removido dos favoritos.'
    else:
        current_user.add_favorite(property_id)
        is_favorite = True
        message = 'Imóvel adicionado aos favoritos.'
    
    # ⭐ SEMPRE retornar JSON para requisições AJAX ⭐
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'is_favorite': is_favorite,
            'message': message,
            'favorites_count': property_obj.favorites_count()
        })
    
    # Fallback para requisições normais
    flash(message, 'success')
    return redirect(request.referrer or url_for('main.property_detail', property_id=property_id))


@bp.route('/my-favorites')
@login_required
def my_favorites():
    """Lista de imóveis favoritos do utilizador."""
    from ..models.favorite import Favorite
    favorites = current_user.get_favorites()
    return render_template('favorites/my_favorites.html', favorites=favorites)


@bp.route('/count')
@login_required
def favorites_count():
    """Retorna o número de favoritos (AJAX)."""
    count = current_user.favorites.count()
    return jsonify({'count': count})