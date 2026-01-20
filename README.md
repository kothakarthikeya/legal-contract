# Contract Intelligence System

AI-powered contract analysis platform with multi-agent intelligence, user authentication, and comprehensive reporting.

## Features

### 🤖 Multi-Agent AI Analysis
- **Legal Agent**: Analyzes indemnity, liability, termination clauses
- **Finance Agent**: Reviews payment terms, pricing, renewal conditions
- **Compliance Agent**: Checks GDPR, data protection, audit rights
- **Operations Agent**: Evaluates SLA, uptime, support terms
- **Security Agent**: Assesses encryption, disaster recovery, access control

### 🎯 Core Capabilities
- **Document Upload**: Support for PDF, DOCX, PPT, PPTX, JPG, PNG
- **Semantic Search**: Pinecone vector database for intelligent clause extraction
- **Risk Scoring**: Weighted algorithm with color-coded visualization
  - **1-3 (Red)**: High Risk
  - **4-7 (Yellow)**: Medium Risk
  - **8-10 (Green)**: Low Risk
- **Version Tracking**: Automatic document history and relationship detection
- **User Authentication**: Secure login/register with SQLite
- **Feedback System**: Star ratings and detailed comments
- **Report Download**: HTML reports with embedded styling

### 🎨 Premium UI/UX
- Modern glassmorphism design
- Gradient backgrounds and smooth animations
- Responsive layout for all devices
- Personalized welcome messages
- Real-time toast notifications
- Drag-and-drop file upload

## Installation

### Prerequisites
- Python 3.10+
- Pinecone API key
- Hugging Face API token

### Setup

1. **Clone or navigate to the project directory**
```bash
cd contract_intelligence
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
Edit `.env` file with your API keys:
```
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=contracts-v2
HF_TOKEN=your_huggingface_token_here
```

4. **Run the application**
```bash
cd src
python main.py
```

5. **Access the application**
Open your browser to: `http://127.0.0.1:8000`

## Project Structure

```
contract_intelligence/
├── .env                          # Environment configuration
├── requirements.txt              # Python dependencies
├── src/
│   ├── __init__.py
│   ├── main.py                   # FastAPI application
│   ├── index.html                # Frontend interface
│   ├── auth_utils.py             # User authentication
│   ├── history_manager.py        # Document versioning
│   ├── scoring.py                # Risk calculation
│   ├── ingestion.py              # Document parsing & embedding
│   ├── extraction.py             # Clause extraction
│   ├── reporting.py              # HTML report generation
│   ├── agents/
│   │   ├── __init__.py
│   │   └── definitions.py        # AI agent prompts & logic
│   ├── workflows/
│   │   ├── __init__.py
│   │   └── graph.py              # LangGraph orchestration
│   ├── uploads/                  # Uploaded documents
│   └── reports/                  # Generated reports
```

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - User login

### Analysis
- `POST /analyze_contract` - Upload and analyze document
- `GET /history` - Get upload history
- `POST /submit_feedback` - Submit feedback for analysis

### Downloads
- `GET /download_report/{doc_id}` - Download specific report
- `GET /download_feedback` - Export all feedback as JSON

## Technology Stack

### Backend
- **FastAPI**: High-performance web framework
- **LangGraph**: Workflow orchestration
- **Pinecone**: Vector database for semantic search
- **SentenceTransformers**: Local embedding generation
- **SQLite**: User authentication database
- **PyPDF2**: PDF parsing

### AI/ML
- **Hugging Face**: LLM inference (Llama, Gemma, Mistral)
- **Multi-model fallback**: Automatic retry with alternative models
- **Semantic search**: Context-aware clause extraction

### Frontend
- **Vanilla HTML/CSS/JS**: No framework dependencies
- **Font Awesome**: Icon library
- **Google Fonts (Inter)**: Modern typography
- **LocalStorage**: Client-side session management

## Usage Guide

### 1. Register/Login
- Click "Login / Register" button
- Create account or sign in
- See personalized welcome message

### 2. Upload Document
- Drag & drop file or click to browse
- Supported formats: PDF, DOCX, PPT, PPTX, JPG, PNG
- Max file size: 20MB

### 3. View Analysis
- Wait for AI agents to complete analysis
- Review risk scores and detailed findings
- Download report as HTML

### 4. Submit Feedback
- Rate analysis (1-5 stars)
- Add detailed comments
- Feedback stored in history

### 5. Access History
- View all previous uploads
- See version numbers
- Download past reports
- View feedback ratings

## Risk Scoring Algorithm

The system calculates a composite risk score (1-10) based on:

### Legal Factors
- Missing indemnity cap: +2.0
- Uncapped liabilities: +2.5
- No termination for convenience: +0.75
- No consequential damages waiver: +1.0

### Financial Factors
- Payment terms > 60 days: +1.0
- Auto-renewal without price cap: +1.5

### Compliance Factors
- SLA uptime < 99%: +1.5
- Missing GDPR clause: +2.0

**Color Coding:**
- **Red (1-3)**: Critical risk - immediate attention required
- **Yellow (4-7)**: Medium risk - review recommended
- **Green (8-10)**: Low risk - acceptable terms

## Troubleshooting

### Common Issues

**1. Pinecone Connection Error**
- Verify API key in `.env`
- Check index name matches configuration
- Ensure Pinecone account is active

**2. Hugging Face 403 Error**
- Verify HF_TOKEN in `.env`
- Check token has inference permissions
- System will automatically fallback to alternative models

**3. Empty Analysis Results**
- Ensure document contains text (not scanned image)
- Check file is not corrupted
- Verify file size < 20MB

**4. Login Issues**
- Clear browser localStorage
- Check `users.db` file exists
- Restart server

## Development

### Adding New Agents

1. Add agent prompts to `src/agents/definitions.py`
2. Add agent topics to `src/extraction.py`
3. Add agent node to `src/workflows/graph.py`
4. Update report generation in `src/reporting.py`

### Customizing Risk Weights

Edit `RISK_WEIGHTS` dictionary in `src/scoring.py`

### Styling Changes

Modify CSS variables in `src/index.html` `:root` section

## Security Notes

- Passwords are hashed using SHA-256
- User sessions stored in browser localStorage
- File uploads validated for type and size
- SQL injection protection via parameterized queries

## Performance

- **Analysis Time**: 30-60 seconds per document
- **Concurrent Users**: Supports multiple simultaneous uploads
- **Vector Search**: Sub-second semantic search
- **Report Generation**: < 1 second

## License

This project is for educational and demonstration purposes.

## Support

For issues or questions, please refer to the conversation history or documentation.

## Deployment to GitHub

This project is configured to be deployment-ready.

1. **Initialize Git Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Push to GitHub**
   - Create a new repository on GitHub.
   - Run the commands provided by GitHub, for example:
     ```bash
     git remote add origin https://github.com/yourusername/contract-intelligence.git
     git branch -M main
     git push -u origin main
     ```

3. **Note on Ignored Files**
   - The `.gitignore` file is set up to exclude sensitive files like `.env`, `users.db`, and `uploads/`.
   - You will need to manually set these up on your deployment server or recreation locally:
     - Create a `.env` file with your API keys.
     - `users.db` will be automatically created when the server starts.

## Deployment to Render

This project includes a `render.yaml` configuration for easy deployment on Render.

1. **Push your code to GitHub/GitLab.**
2. **Create a New Blueprint Service on Render:**
   - Go to your Render Dashboard.
   - Click "New" -> "Blueprint".
   - Connect your repository.
   - Render will automatically detect `render.yaml`.
   - Alternatively, Render will use the `Procfile` to determine the start command.
3. **Configure Environment Variables:**
   - You will be prompted to enter your API keys (`HF_TOKEN`, `PINECONE_API_KEY`, etc.) during setup as defined in `render.yaml`.



---

**Built with ❤️ using AI-powered contract intelligence**
