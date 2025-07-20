# PDF Elaborator

Un'applicazione web per la gestione e l'elaborazione di file PDF, simile a LovePDF, containerizzata con Docker.

## Funzionalità

- **Unisci PDF**: Combina più file PDF in un singolo documento
- **Pulisci PDF**: Rimuovi informazioni sensibili, metadati e watermark
- **Gestisci Pagine**: Estrai o rimuovi pagine specifiche dai PDF

## Tecnologie utilizzate

- **Backend**: Python Flask
- **Elaborazione PDF**: PyPDF2
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Containerizzazione**: Docker & Docker Compose
- **Icone**: Font Awesome

## Installazione e avvio

### Con Docker Compose (raccomandato)

1. Clona il repository:
```bash
git clone <repository-url>
cd pdf-elaborator
```

2. Avvia l'applicazione:
```bash
docker compose up --build
```

3. Apri il browser e vai su: `http://localhost:5000`

### Sviluppo locale

1. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

2. Crea le cartelle necessarie:
```bash
mkdir uploads temp
```

3. Avvia l'applicazione:
```bash
python app.py
```

## Utilizzo

### Unire PDF
1. Vai alla sezione "Unisci PDF"
2. Seleziona almeno 2 file PDF
3. I file verranno uniti nell'ordine di selezione
4. Scarica il file risultante

### Pulire PDF
1. Vai alla sezione "Pulisci PDF"
2. Carica un file PDF
3. Configura le opzioni di pulizia:
   - Inserisci testo specifico da rimuovere
   - Abilita rimozione watermark
   - Abilita rimozione metadati
4. Scarica il file pulito

### Gestire Pagine
1. Vai alla sezione "Gestisci Pagine"
2. Carica un file PDF
3. Scegli l'operazione (estrai o rimuovi)
4. Specifica le pagine (es. "1,3,5-7")
5. Scarica il file risultante

## Configurazione

### Variabili d'ambiente

- `UPLOAD_FOLDER`: Cartella per i file temporanei di upload
- `TEMP_FOLDER`: Cartella per i file temporanei di elaborazione
- `FLASK_ENV`: Ambiente Flask (development/production)

### Limiti

- Dimensione massima file: 50MB
- Formati supportati: PDF
- Memoria Docker consigliata: 512MB+

## Struttura del progetto

```
pdf-elaborator/
├── app.py                 # Applicazione Flask principale
├── pdf_processor.py       # Logica di elaborazione PDF
├── requirements.txt       # Dipendenze Python
├── Dockerfile            # Configurazione Docker
├── docker-compose.yml    # Orchestrazione servizi
├── templates/            # Template HTML
│   ├── base.html
│   ├── index.html
│   ├── merge.html
│   ├── clean.html
│   └── pages.html
├── static/               # File statici
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── uploads/              # Cartella upload (creata automaticamente)
└── temp/                 # Cartella temporanea (creata automaticamente)
```

## API Endpoints

- `GET /` - Homepage
- `GET /merge` - Pagina unione PDF
- `GET /clean` - Pagina pulizia PDF
- `GET /pages` - Pagina gestione pagine
- `POST /api/merge` - API unione PDF
- `POST /api/clean` - API pulizia PDF
- `POST /api/pages` - API gestione pagine
- `POST /api/info` - API informazioni PDF

## Sicurezza

- Validazione tipo file
- Limite dimensione file
- Pulizia automatica file temporanei
- Nomi file sicuri
- Rimozione metadati

## Troubleshooting

### Problemi comuni

1. **Errore "File troppo grande"**: Verifica che il file sia sotto i 50MB
2. **Errore "PDF non valido"**: Assicurati che il file sia un PDF valido
3. **Errore elaborazione**: Alcuni PDF protetti potrebbero non essere modificabili

### Log

Per vedere i log dell'applicazione:
```bash
docker compose logs -f pdf-elaborator
```

## Contribuire

1. Fork il progetto
2. Crea un branch per la tua feature
3. Commit le modifiche
4. Push al branch
5. Apri una Pull Request

## Licenza

Questo progetto è rilasciato sotto licenza MIT.

## Supporto

Per problemi o domande, apri un'issue su GitHub.
