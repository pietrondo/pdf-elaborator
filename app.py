from flask import Flask, request, render_template, send_file, jsonify, redirect, url_for
import os
import uuid
from werkzeug.utils import secure_filename
from pdf_processor import PDFProcessor
import tempfile
import shutil

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', './uploads')
app.config['TEMP_FOLDER'] = os.environ.get('TEMP_FOLDER', './temp')

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

pdf_processor = PDFProcessor()

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/merge')
def merge_page():
    return render_template('merge.html')

@app.route('/clean')
def clean_page():
    return render_template('clean.html')

@app.route('/clean-advanced')
def clean_advanced_page():
    return render_template('clean_advanced.html')

@app.route('/pages')
def pages_page():
    return render_template('pages.html')

@app.route('/api/merge', methods=['POST'])
def merge_pdfs():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'Nessun file selezionato'}), 400
        
        files = request.files.getlist('files')
        if len(files) < 2:
            return jsonify({'error': 'Sono necessari almeno 2 file PDF'}), 400
        
        # Save uploaded files
        temp_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                temp_path = os.path.join(app.config['TEMP_FOLDER'], f"{uuid.uuid4()}_{filename}")
                file.save(temp_path)
                temp_files.append(temp_path)
        
        if len(temp_files) < 2:
            return jsonify({'error': 'File PDF non validi'}), 400
        
        # Merge PDFs
        output_path = os.path.join(app.config['TEMP_FOLDER'], f"merged_{uuid.uuid4()}.pdf")
        pdf_processor.merge_pdfs(temp_files, output_path)
        
        # Clean up input files
        for temp_file in temp_files:
            os.remove(temp_file)
        
        return send_file(output_path, as_attachment=True, download_name='merged.pdf')
    
    except Exception as e:
        return jsonify({'error': f'Errore durante l\'unione: {str(e)}'}), 500

@app.route('/api/clean', methods=['POST'])
def clean_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nessun file selezionato'}), 400
        
        file = request.files['file']
        if not file or not allowed_file(file.filename):
            return jsonify({'error': 'File PDF non valido'}), 400
        
        # Get cleaning options
        remove_text = request.form.get('remove_text', '').strip()
        remove_watermarks = request.form.get('remove_watermarks') == 'on'
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['TEMP_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(input_path)
        
        # Clean PDF
        output_path = os.path.join(app.config['TEMP_FOLDER'], f"cleaned_{uuid.uuid4()}.pdf")
        pdf_processor.clean_pdf(input_path, output_path, remove_text, remove_watermarks)
        
        # Clean up input file
        os.remove(input_path)
        
        return send_file(output_path, as_attachment=True, download_name='cleaned.pdf')
    
    except Exception as e:
        return jsonify({'error': f'Errore durante la pulizia: {str(e)}'}), 500

@app.route('/api/pages', methods=['POST'])
def manage_pages():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nessun file selezionato'}), 400
        
        file = request.files['file']
        if not file or not allowed_file(file.filename):
            return jsonify({'error': 'File PDF non valido'}), 400
        
        # Get page operation
        operation = request.form.get('operation')
        pages = request.form.get('pages', '').strip()
        
        if not operation or not pages:
            return jsonify({'error': 'Operazione e pagine sono richieste'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['TEMP_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(input_path)
        
        # Process pages
        output_path = os.path.join(app.config['TEMP_FOLDER'], f"pages_{uuid.uuid4()}.pdf")
        
        if operation == 'extract':
            pdf_processor.extract_pages(input_path, output_path, pages)
        elif operation == 'remove':
            pdf_processor.remove_pages(input_path, output_path, pages)
        else:
            return jsonify({'error': 'Operazione non valida'}), 400
        
        # Clean up input file
        os.remove(input_path)
        
        return send_file(output_path, as_attachment=True, download_name=f'{operation}_pages.pdf')
    
    except Exception as e:
        return jsonify({'error': f'Errore durante la gestione delle pagine: {str(e)}'}), 500

@app.route('/api/info', methods=['POST'])
def get_pdf_info():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nessun file selezionato'}), 400
        
        file = request.files['file']
        if not file or not allowed_file(file.filename):
            return jsonify({'error': 'File PDF non valido'}), 400
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['TEMP_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(temp_path)
        
        # Get PDF info
        info = pdf_processor.get_pdf_info(temp_path)
        
        # Clean up
        os.remove(temp_path)
        
        return jsonify(info)
    
    except Exception as e:
        return jsonify({'error': f'Errore durante l\'analisi: {str(e)}'}), 500

@app.route('/api/pdf-to-images', methods=['POST'])
def pdf_to_images():
    """Converte PDF in immagini per la visualizzazione"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nessun file selezionato'}), 400
        
        file = request.files['file']
        if not file or not allowed_file(file.filename):
            return jsonify({'error': 'File PDF non valido'}), 400
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['TEMP_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(temp_path)
        
        # Convert to images
        images = pdf_processor.convert_pdf_to_images(temp_path)
        
        # Store the file path in session or return it for future use
        file_id = str(uuid.uuid4())
        temp_files_map = getattr(app, 'temp_files_map', {})
        temp_files_map[file_id] = temp_path
        app.temp_files_map = temp_files_map
        
        return jsonify({
            'file_id': file_id,
            'images': images
        })
    
    except Exception as e:
        return jsonify({'error': f'Errore durante la conversione: {str(e)}'}), 500

@app.route('/api/clean-with-areas', methods=['POST'])
def clean_with_areas():
    """Pulisce il PDF rimuovendo aree specifiche segnalate dall'utente"""
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        areas_to_remove = data.get('areas_to_remove', {})
        
        if not file_id:
            return jsonify({'error': 'ID file mancante'}), 400
        
        # Recupera il file temporaneo
        temp_files_map = getattr(app, 'temp_files_map', {})
        if file_id not in temp_files_map:
            return jsonify({'error': 'File non trovato o scaduto'}), 400
        
        input_path = temp_files_map[file_id]
        
        # Genera path per il file pulito
        output_path = os.path.join(app.config['TEMP_FOLDER'], f"cleaned_areas_{uuid.uuid4()}.pdf")
        
        # Pulisci il PDF con le aree specificate
        pdf_processor.clean_pdf_with_areas(input_path, output_path, areas_to_remove)
        
        # Pulisci il file temporaneo di input
        os.remove(input_path)
        del temp_files_map[file_id]
        
        return send_file(output_path, as_attachment=True, download_name='cleaned_with_areas.pdf')
    
    except Exception as e:
        return jsonify({'error': f'Errore durante la pulizia: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
