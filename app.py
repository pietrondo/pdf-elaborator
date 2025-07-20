from flask import Flask, request, render_template, send_file, jsonify, redirect, url_for
import os
import uuid
from werkzeug.utils import secure_filename
from pdf_processor import PDFProcessor
import tempfile
import shutil
import time
import threading

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

def cleanup_temp_files():
    """Pulisce i file temporanei più vecchi di 1 ora"""
    while True:
        try:
            current_time = time.time()
            temp_files_map = getattr(app, 'temp_files_map', {})
            files_to_remove = []
            
            for file_id, file_path in temp_files_map.items():
                if os.path.exists(file_path):
                    file_age = current_time - os.path.getctime(file_path)
                    if file_age > 3600:  # 1 hour
                        try:
                            os.remove(file_path)
                            files_to_remove.append(file_id)
                        except:
                            pass
                else:
                    files_to_remove.append(file_id)
            
            for file_id in files_to_remove:
                temp_files_map.pop(file_id, None)
            
            # Pulisci anche i file nella cartella temp
            for filename in os.listdir(app.config['TEMP_FOLDER']):
                file_path = os.path.join(app.config['TEMP_FOLDER'], filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getctime(file_path)
                    if file_age > 3600:  # 1 hour
                        try:
                            os.remove(file_path)
                        except:
                            pass
        except:
            pass
        
        time.sleep(300)  # Check every 5 minutes

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_temp_files, daemon=True)
cleanup_thread.start()

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

@app.route('/api/upload-pdfs', methods=['POST'])
def upload_pdfs():
    """Carica e analizza più file PDF per la gestione visuale delle pagine"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'Nessun file selezionato'}), 400
        
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'Nessun file valido caricato'}), 400
        
        pdf_data = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_id = str(uuid.uuid4())
                temp_path = os.path.join(app.config['TEMP_FOLDER'], f"{file_id}_{filename}")
                file.save(temp_path)
                
                # Converti in immagini per l'anteprima
                try:
                    images = pdf_processor.convert_pdf_to_images(temp_path)
                    info = pdf_processor.get_pdf_info(temp_path)
                    
                    # Store the file path for later use
                    temp_files_map = getattr(app, 'temp_files_map', {})
                    temp_files_map[file_id] = temp_path
                    app.temp_files_map = temp_files_map
                    
                    pdf_data.append({
                        'file_id': file_id,
                        'filename': filename,
                        'num_pages': info['num_pages'],
                        'file_size': info['file_size'],
                        'images': images
                    })
                except Exception as e:
                    # Rimuovi il file se c'è stato un errore
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    continue
        
        if not pdf_data:
            return jsonify({'error': 'Nessun PDF valido caricato'}), 400
        
        return jsonify({'pdfs': pdf_data})
    
    except Exception as e:
        return jsonify({'error': f'Errore durante il caricamento: {str(e)}'}), 500

@app.route('/api/compose-pages', methods=['POST'])
def compose_pages():
    """Compone un nuovo PDF dalle pagine selezionate"""
    try:
        data = request.get_json()
        selected_pages = data.get('selected_pages', [])
        
        if not selected_pages:
            return jsonify({'error': 'Nessuna pagina selezionata'}), 400
        
        # Recupera i file temporanei
        temp_files_map = getattr(app, 'temp_files_map', {})
        
        # Prepara i dati per il processor
        page_selections = []
        for page_info in selected_pages:
            file_id = page_info['file_id']
            
            if file_id not in temp_files_map:
                return jsonify({'error': f'File {file_id} non trovato'}), 400
            
            page_selections.append({
                'file_path': temp_files_map[file_id],
                'page': page_info['page']
            })
        
        # Salva il nuovo PDF
        output_path = os.path.join(app.config['TEMP_FOLDER'], f"composed_{uuid.uuid4()}.pdf")
        pdf_processor.create_pdf_from_pages(page_selections, output_path)
        
        return send_file(output_path, as_attachment=True, download_name='composed_pages.pdf')
    
    except Exception as e:
        return jsonify({'error': f'Errore durante la composizione: {str(e)}'}), 500

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
