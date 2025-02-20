def get_file_icon(filename):
    """Retorna o ícone apropriado baseado na extensão do arquivo"""
    extension = filename.split('.')[-1].lower() if '.' in filename else ''
    
    icons = {
        # Documentos
        'pdf': 'fa-file-pdf',
        'doc': 'fa-file-word',
        'docx': 'fa-file-word',
        'txt': 'fa-file-alt',
        'rtf': 'fa-file-alt',
        
        # Planilhas
        'xls': 'fa-file-excel',
        'xlsx': 'fa-file-excel',
        'csv': 'fa-file-csv',
        
        # Apresentações
        'ppt': 'fa-file-powerpoint',
        'pptx': 'fa-file-powerpoint',
        
        # Imagens
        'jpg': 'fa-file-image',
        'jpeg': 'fa-file-image',
        'png': 'fa-file-image',
        'gif': 'fa-file-image',
        'bmp': 'fa-file-image',
        
        # Arquivos compactados
        'zip': 'fa-file-archive',
        'rar': 'fa-file-archive',
        '7z': 'fa-file-archive',
        
        # Código
        'py': 'fa-file-code',
        'js': 'fa-file-code',
        'html': 'fa-file-code',
        'css': 'fa-file-code',
        'json': 'fa-file-code',
        
        # Audio/Video
        'mp3': 'fa-file-audio',
        'wav': 'fa-file-audio',
        'mp4': 'fa-file-video',
        'avi': 'fa-file-video',
        'mov': 'fa-file-video',
    }
    
    return icons.get(extension, 'fa-file')  # retorna 'fa-file' se a extensão não estiver mapeada 