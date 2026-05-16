import os
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
from flask import current_app


def allowed_file(filename):
    """Verifica se a extensão do ficheiro é permitida."""
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def compress_image(image_path, max_size=(1200, 800), quality=85):
    """Comprime uma imagem para economizar espaço."""
    try:
        img = Image.open(image_path)
        
        # Converte RGBA para RGB se necessário
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb = Image.new('RGB', img.size, (255, 255, 255))
            rgb.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb
        
        # Redimensiona se for muito grande
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Salva com compressão
        img.save(image_path, 'JPEG', quality=quality, optimize=True)
        return True
    except Exception as e:
        print(f"Erro ao comprimir imagem: {e}")
        return False


def save_uploaded_file(file, subfolder='properties'):
    """Salva um ficheiro enviado pelo utilizador."""
    if not file or not file.filename:
        return None
    
    # Gera nome único
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
    original_name = secure_filename(file.filename)
    extension = original_name.rsplit('.', 1)[1].lower() if '.' in original_name else 'jpg'
    new_filename = f"{timestamp}.{extension}"
    
    # Cria pasta se não existir
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(upload_folder, exist_ok=True)
    
    filepath = os.path.join(upload_folder, new_filename)
    file.save(filepath)
    
    return new_filename

def delete_uploaded_file(filename, subfolder='properties'):
    """Remove um ficheiro de upload."""
    if not filename:
        return
    
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder, filename)
    if os.path.exists(filepath):
        os.remove(filepath)


def save_verification_file(file, user_id, doc_type):
    """
    Salva um ficheiro de verificação (BI ou comprovativo).
    doc_type: 'bi_front', 'bi_back', 'property_doc'
    """
    if not file or not allowed_file(file.filename):
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    original_name = secure_filename(file.filename)
    extension = original_name.rsplit('.', 1)[1].lower()
    
    # Converte para jpg se for imagem
    if extension in ['png', 'webp']:
        new_filename = f"user_{user_id}_{doc_type}_{timestamp}.jpg"
    else:
        new_filename = f"user_{user_id}_{doc_type}_{timestamp}.{extension}"
    
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'verifications')
    os.makedirs(upload_folder, exist_ok=True)
    
    filepath = os.path.join(upload_folder, new_filename)
    file.save(filepath)
    
    # Comprime se for imagem
    if extension in ['jpg', 'jpeg', 'png', 'webp']:
        compress_image(filepath, max_size=(1024, 768), quality=80)
    
    return new_filename