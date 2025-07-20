import PyPDF2
import re
from PyPDF2 import PdfReader, PdfWriter
import os

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
