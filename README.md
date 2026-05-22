# 📄 CV Analyzer AI

Analyze your resume against any job description using Gemini AI. Get a compatibility score, strengths, gaps, improvement suggestions, and missing keywords.

## ✨ Features

- 📊 **Compatibility score** (0–100%)
- ✅ **Strengths** — what's working in your resume
- ⚠️ **Gaps** — what's missing for the role
- 💡 **Suggestions** — concrete improvements
- 🔑 **Missing keywords** — ATS optimization
- 🌐 **PT / EN** — bilingual interface
- 🔒 **User-provided API key** — no backend costs
- 📄 **PDF limit** — max 5 pages, 5 MB

## 🛠 Stack

| | |
|-|-|
| Framework | Streamlit |
| AI | Google Gemini 1.5 Flash |
| PDF | pypdf |
| Deploy | Streamlit Cloud |

## 🚀 Running Locally

```bash
# Clone
git clone https://github.com/DavMarinho/cv-analyzer-ai.git
cd cv-analyzer-ai

# Install dependencies
pip install -r requirements.txt

# Run
streamlit run app.py
```

Get your free Gemini API key at [aistudio.google.com](https://aistudio.google.com)

## 📦 Deploy on Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Select the repo → `app.py`
4. Deploy

## 📄 License

MIT