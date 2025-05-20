🩺 Medical Assistant – AI-Powered Personal Health Companion
An intelligent medical assistant web application that empowers users to manage their health through emotional tracking, prescription scanning, AI-based interaction, and personalized profile management — all enhanced by n8n workflow automation.

🔧 Features
🧠 Emotional Diary
Users can log their emotions daily. Visualizations and summaries help users reflect on their mental well-being over time.

📄 OCR for Medical Documents & Prescriptions
Upload handwritten or printed medical documents. Integrated OCR (Tesseract/EasyOCR) extracts key data such as medication names, dosages, and doctor details for easier understanding and tracking.

🤖 AI Chatbot Assistant
An interactive chatbot powered by LLMs (e.g., OpenAI, Ollama, or LangChain agents) answers user queries, explains prescriptions, and provides emotional support based on diary logs.

👤 Profile Manager
Secure user profiles store personal details, uploaded documents, emotional logs, and chatbot conversations. Data is managed with Supabase/PostgreSQL or Firebase.

🔄 n8n Workflow Automation

Google Drive Upload Integration: Users can upload images of prescriptions or reports, which trigger n8n workflows for OCR processing and deletion after extraction.

Tesseract OCR Node: Automatically extracts text from images as part of the n8n flow.

LangChain Agent Workflow: Supports document-based question-answering, contextual responses, and memory integration.

Supabase & Pinecone Integration: Enables vector storage of embeddings for personalized search and response generation.

Webhook-Based Communication: Streamlit or FastAPI frontend communicates with n8n for real-time, modular backend automation.

