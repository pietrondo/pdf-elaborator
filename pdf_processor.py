import PyPDF2
import re
from PyPDF2 import PdfReader, PdfWriter
import os
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import base64
from io import BytesIO
from PIL import Image

class PDFProcessor:
    def __init__(self):
        pass
    
    def merge_pdfs(self, input_paths, output_path):
        """Unisce più file PDF in uno solo"""
        writer = PdfWriter()
        
        for path in input_paths:
            with open(path, 'rb') as file:
                reader = PdfReader(file)
                for page in reader.pages:
                    writer.add_page(page)
        
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
    
    def clean_pdf(self, input_path, output_path, remove_text="", remove_watermarks=False):
        """Rimuove informazioni sensibili dal PDF"""
        with open(input_path, 'rb') as file:
            reader = PdfReader(file)
            writer = PdfWriter()
            
            for page in reader.pages:
                # Rimuovi metadati
                if page.get('/Annots'):
                    page['/Annots'] = []
                
                # Rimuovi testo specifico se specificato
                if remove_text:
                    try:
                        text = page.extract_text()
                        if remove_text.lower() in text.lower():
                            # Per ora, aggiungiamo la pagina così com'è
                            # La rimozione avanzata del testo richiederebbe librerie più complesse
                            pass
                    except:
                        pass
                
                writer.add_page(page)
            
            # Rimuovi metadati del documento
            if reader.metadata:
                writer.add_metadata({
                    '/Title': '',
                    '/Author': '',
                    '/Subject': '',
                    '/Creator': '',
                    '/Producer': 'PDF Elaborator',
                    '/Keywords': ''
                })
            
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
    
    def extract_pages(self, input_path, output_path, pages_str):
        """Estrae pagine specifiche dal PDF"""
        pages = self._parse_pages(pages_str)
        
        with open(input_path, 'rb') as file:
            reader = PdfReader(file)
            writer = PdfWriter()
            
            total_pages = len(reader.pages)
            
            for page_num in pages:
                if 1 <= page_num <= total_pages:
                    writer.add_page(reader.pages[page_num - 1])  # Convert to 0-based index
            
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
    
    def remove_pages(self, input_path, output_path, pages_str):
        """Rimuove pagine specifiche dal PDF"""
        pages_to_remove = set(self._parse_pages(pages_str))
        
        with open(input_path, 'rb') as file:
            reader = PdfReader(file)
            writer = PdfWriter()
            
            total_pages = len(reader.pages)
            
            for page_num in range(1, total_pages + 1):
                if page_num not in pages_to_remove:
                    writer.add_page(reader.pages[page_num - 1])  # Convert to 0-based index
            
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
    
    def get_pdf_info(self, input_path):
        """Ottiene informazioni sul PDF"""
        with open(input_path, 'rb') as file:
            reader = PdfReader(file)
            
            info = {
                'num_pages': len(reader.pages),
                'metadata': {},
                'file_size': os.path.getsize(input_path)
            }
            
            if reader.metadata:
                for key, value in reader.metadata.items():
                    info['metadata'][key] = str(value) if value else ''
            
            return info
    
    def _parse_pages(self, pages_str):
        """Analizza la stringa delle pagine (es. '1,3,5-7' -> [1,3,5,6,7])"""
        pages = []
        
        for part in pages_str.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                pages.extend(range(start, end + 1))
            else:
                pages.append(int(part))
        
        return sorted(list(set(pages)))  # Remove duplicates and sort

    def convert_pdf_to_images(self, input_path, dpi=100, max_size=(300, 400)):
        """Converte le pagine del PDF in immagini base64 ottimizzate"""
        try:
            # Converte PDF in immagini usando pdf2image con DPI ridotto per le anteprime
            images = convert_from_path(input_path, dpi=dpi)
            image_data = []
            
            for i, image in enumerate(images):
                # Ridimensiona l'immagine per l'anteprima
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Converti l'immagine in base64 con qualità ottimizzata
                buffered = BytesIO()
                image.save(buffered, format="JPEG", quality=85, optimize=True)
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                image_data.append({
                    'page': i + 1,
                    'width': image.width,
                    'height': image.height,
                    'data': f"data:image/jpeg;base64,{img_str}"
                })
            
            return image_data
        except Exception as e:
            raise Exception(f"Errore nella conversione PDF to immagini: {str(e)}")

    def clean_pdf_with_areas(self, input_path, output_path, areas_to_remove):
        """Rimuove aree specifiche dal PDF basate su coordinate"""
        try:
            # Apri il PDF con PyMuPDF per operazioni avanzate
            doc = fitz.open(input_path)
            
            for page_num, areas in areas_to_remove.items():
                # Converti page_num in intero se è una stringa
                page_num = int(page_num) if isinstance(page_num, str) else page_num
                page = doc.load_page(page_num - 1)  # PyMuPDF usa indici 0-based
                
                for area in areas:
                    # Converti le coordinate dal canvas alle coordinate PDF (assicurati che siano numeri)
                    x1 = float(area['x1']) if isinstance(area['x1'], str) else area['x1']
                    y1 = float(area['y1']) if isinstance(area['y1'], str) else area['y1']
                    x2 = float(area['x2']) if isinstance(area['x2'], str) else area['x2']
                    y2 = float(area['y2']) if isinstance(area['y2'], str) else area['y2']
                    canvas_width = float(area['canvas_width']) if isinstance(area['canvas_width'], str) else area['canvas_width']
                    canvas_height = float(area['canvas_height']) if isinstance(area['canvas_height'], str) else area['canvas_height']
                    
                    # Ottieni le dimensioni della pagina PDF
                    pdf_rect = page.rect
                    pdf_width, pdf_height = pdf_rect.width, pdf_rect.height
                    
                    # Scala le coordinate
                    pdf_x1 = (x1 / canvas_width) * pdf_width
                    pdf_y1 = (y1 / canvas_height) * pdf_height
                    pdf_x2 = (x2 / canvas_width) * pdf_width
                    pdf_y2 = (y2 / canvas_height) * pdf_height
                    
                    # Crea un rettangolo per coprire l'area
                    rect = fitz.Rect(pdf_x1, pdf_y1, pdf_x2, pdf_y2)
                    
                    # Aggiungi un rettangolo bianco per coprire l'area
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
            
            # Salva il PDF modificato
            doc.save(output_path)
            doc.close()
            
        except Exception as e:
            raise Exception(f"Errore nella rimozione delle aree: {str(e)}")

    def create_pdf_from_pages(self, page_selections, output_path):
        """Crea un nuovo PDF da una selezione di pagine da diversi file"""
        try:
            writer = PdfWriter()
            
            for selection in page_selections:
                file_path = selection['file_path']
                page_number = selection['page'] - 1  # Convert to 0-based
                
                with open(file_path, 'rb') as file:
                    reader = PdfReader(file)
                    if 0 <= page_number < len(reader.pages):
                        writer.add_page(reader.pages[page_number])
            
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
                
        except Exception as e:
            raise Exception(f"Errore nella creazione del PDF: {str(e)}")
