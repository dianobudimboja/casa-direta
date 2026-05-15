from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime

from ..extensions import db
from ..models.user import User
from ..models.review import Review
from ..models.property import Property
from ..forms.review_form import ReviewForm

bp = Blueprint('reviews', __name__, url_prefix='/reviews')


@bp.route('/create/<int:user_id>', methods=['GET', 'POST'])
@login_required
def create_review(user_id):
    """Criar uma avaliação para outro utilizador."""
    
    reviewed_user = User.query.get_or_404(user_id)
    property_id = request.args.get('property_id', type=int)
    
    # Não pode avaliar a si mesmo
    if reviewed_user.id == current_user.id:
        flash('Você não pode avaliar a si mesmo.', 'danger')
        return redirect(url_for('main.index'))
    
    # Verifica se já avaliou este utilizador
    existing_review = Review.query.filter_by(
        reviewer_id=current_user.id,
        reviewed_id=reviewed_user.id
    ).first()
    
    if existing_review:
        flash('Você já avaliou este utilizador.', 'warning')
        return redirect(url_for('dashboard.profile', user_id=reviewed_user.id))
    
    form = ReviewForm()
    
    if form.validate_on_submit():
        review = Review(
            rating=form.rating.data,
            comment=form.comment.data,
            reviewer_id=current_user.id,
            reviewed_id=reviewed_user.id,
            property_id=property_id
        )
        
        db.session.add(review)
        db.session.commit()
        
        # Atualiza a média do utilizador avaliado
        reviewed_user.rating = reviewed_user.get_average_rating()
        reviewed_user.total_reviews = reviewed_user.get_rating_count()
        db.session.commit()
        
        flash(f'Avaliação enviada com sucesso! Você deu {form.rating.data} estrelas para {reviewed_user.name}.', 'success')
        return redirect(url_for('dashboard.profile', user_id=reviewed_user.id))
    
    # Buscar propriedade para exibir no template (se existir)
    property_obj = None
    if property_id:
        property_obj = Property.query.get(property_id)
    
    return render_template('reviews/create.html', form=form, reviewed_user=reviewed_user, property=property_obj)


@bp.route('/user/<int:user_id>')
def user_reviews(user_id):
    """Lista todas as avaliações de um utilizador."""
    user = User.query.get_or_404(user_id)
    reviews = Review.query.filter_by(reviewed_id=user_id, is_visible=True).order_by(Review.created_at.desc()).all()
    
    return render_template('reviews/list.html', user=user, reviews=reviews)


@bp.route('/<int:review_id>/hide')
@login_required
def hide_review(review_id):
    """Admin pode ocultar uma avaliação inapropriada."""
    if not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    review = Review.query.get_or_404(review_id)
    review.is_visible = False
    db.session.commit()
    
    # Recalcula a média do utilizador
    user = User.query.get(review.reviewed_id)
    if user:
        user.rating = user.get_average_rating()
        user.total_reviews = user.get_rating_count()
        db.session.commit()
    
    flash('Avaliação ocultada com sucesso.', 'success')
    return redirect(url_for('admin.reviews'))