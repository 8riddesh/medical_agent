# app.py
import streamlit as st
import os
import requests
from dotenv import load_dotenv
from auth import initialize_session_state, login_page, register_page, show_user_info, logout
from chat import display_chat_interface, load_chat_history, display_chat_history
from dashboard import display_dashboard
from my_profile import display_profile_update
from emotional_diary_page import display_emotional_diary
from database import SupabaseClient
from groq import Groq
from pathlib import Path

# Load environment variables
load_dotenv()

# Setup LangChain tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")

client = Groq(api_key="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")
speech_file_path = Path(__file__).parent / "speech.wav"

# N8N configuration
N8N_CHATBOT_URL = os.getenv("N8N_CHATBOT_URL", "http://localhost:5678/webhook-test/chatbot")
N8N_FILE_UPLOAD_URL = os.getenv("N8N_FILE_UPLOAD_URL", "http://localhost:5678/webhook-test/chatbot")
user_id = None

def display_chatbot():
    """Display the chatbot page with interface and history options"""
    st.title('Swasthya AI Chatbot')
    
    # Button to navigate back to dashboard
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("Back to Dashboard", use_container_width=True):
            st.session_state['current_page'] = 'dashboard'
            st.rerun()
    
    # Add chatbot sidebar options
    with st.sidebar:
        st.markdown("---")
        st.subheader("Chatbot Options")
        view_mode = st.radio(
            "View Mode:",
            ["Chat Interface", "Chat History"],
            key="view_mode"
        )
        
        if view_mode == "Chat Interface" and st.button("Clear Current Chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.session_state.response_history = []
            st.rerun()
        
        # Display chat history
        if st.session_state.response_history:
            st.markdown("### 💬 Recent Conversations")
            for idx, response in enumerate(st.session_state.response_history[::-1]):  # Display newest first
                if response.get("type") == "text":
                    with st.expander(f"🗨️ {response.get('prompt', '')[:30]}..."):
                        st.markdown(f"**You:** {response.get('prompt')}")
                        st.markdown(f"**Bot:** {response.get('response')}")
                elif response.get("type") == "file":
                    with st.expander(f"📄 {response.get('filename', 'unknown')}"):
                        st.markdown(f"**Uploaded file:** {response.get('filename', 'unknown')}")
                        st.markdown(f"**Extracted Text:**")
                        st.text(response.get('response', 'No text extracted'))
    
    # Display based on selected view mode
    if view_mode == "Chat Interface":
        # Display latest response in main area
        if st.session_state.response_history:
            latest_response = st.session_state.response_history[-1]
            if latest_response.get("type") == "text":
                with st.container(border=True):
                    st.markdown(f"**You:** {latest_response.get('prompt')}")
                    st.markdown("---")
                    st.markdown(latest_response.get('response'))
            elif latest_response.get("type") == "file":
                with st.container(border=True):
                    st.markdown(f"**Uploaded file:** {latest_response.get('filename', 'unknown')}")
                    st.markdown("---")
                    st.text(latest_response.get('response', 'No text extracted'))
        
        # Chat input section with tabs
        st.markdown("### ✍️ New Message")
        
        tab1, tab2 = st.tabs(["💬 Text Input", "📂 Upload File"])
        
        # Text input tab
        with tab1:
            with st.form(key="text_input_form"):
                prompt = st.text_area("Enter your medical question here...", height=100)
                submit_button = st.form_submit_button("🚀 Send")
                
                if submit_button:
                    if not prompt.strip():
                        st.error("Please enter a prompt")
                    else:
                        with st.spinner("Getting response..."):
                            try:
                                # Call N8N chatbot endpoint
                                print(st.session_state['user_id'])
                                response = requests.post(
                                    "http://localhost:5678/webhook-test/chatbot",
                                    json={'chatInput': prompt, "userId": st.session_state['user_id']},
                                )
                                
                                # Store response in session state
                                st.session_state.response_history.append({
                                    "type": "text",
                                    "prompt": prompt,
                                    "response": response.text
                                })
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ An error occurred while sending the prompt: {str(e)}")
        
        
        # File upload tab
        with tab2:
            # First part: File upload form
            with st.form(key="file_upload_form"):
                uploaded_file = st.file_uploader("Upload an image (JPG, PNG) or document (PDF)", 
                                               type=["jpg", "jpeg", "png", "pdf"],
                                               accept_multiple_files=False)
                
                submit_button = st.form_submit_button("📤 Process File")
                
                if submit_button and uploaded_file is not None:
                    with st.spinner("Processing your file..."):
                        try:
                            # Call N8N file processing endpoint
                            base = SupabaseClient()
                            client_db = base.client
                            print(client_db)
                            res = client_db.table('medical_info').select('id').eq('user_id', st.session_state['user_id']).execute()
                            i = 0
                            ids = []
                            while(i < len(res.data)):
                                ids.append(res.data[i]['id'])
                                i += 1
                            print(ids)
                            response = requests.post(
                                "http://localhost:5678/webhook-test/chatbot",
                                files={'data': (uploaded_file.name, uploaded_file, uploaded_file.type)},
                                data={'name': uploaded_file.name, "id": ids}
                            )
                            
                            if response.status_code == 200:
                                extracted_text = response.text
                                
                                # Store file response in session state
                                st.session_state.response_history.append({
                                    "type": "file",
                                    "filename": uploaded_file.name,
                                    "response": extracted_text
                                })
                                
                                # Store the extracted text in session state for use outside the form
                                st.session_state['last_extracted_text'] = extracted_text
                                
                                # Save data to database
                                try:
                                    client_db.table('medicalinfo').insert({
                                        'user_id': st.session_state['user_id'], 
                                        'content': extracted_text
                                    }).execute()
                                except Exception as e:
                                    st.error(f"❌ An error occurred while saving to database: {str(e)}")
                                    
                            else:
                                st.error("Error processing file")
                                
                        except Exception as e:
                            st.error(f"❌ An error occurred during upload: {str(e)}")
                elif submit_button and uploaded_file is None:
                    st.error("Please select a file to upload")
            
            # Second part: Display extracted text and TTS button outside the form
            if 'last_extracted_text' in st.session_state:
                st.markdown("### Extracted Text:")
                st.text(st.session_state['last_extracted_text'])
                
                # Add TTS button outside the form
                if st.button("🔊 Generate Speech", key="generate_speech"):
                    with st.spinner("Generating Speech..."):
                        try:
                            # Use Groq to generate speech from the extracted text
                            audio_response = client.audio.speech.create(
                                model="playai-tts",
                                voice="Aaliyah-PlayAI",
                                response_format="wav",
                                input=st.session_state['last_extracted_text'],
                            )
                            audio_response.write_to_file(speech_file_path)
                            
                            # Play the audio
                            with open(speech_file_path, "rb") as audio_file:
                                st.audio(audio_file, format="audio/wav")
                        except Exception as e:
                            st.error(f"❌ An error occurred during speech generation: {str(e)}")
            
            # Instructional Footer
            st.markdown("---")
            st.caption("Ensure that the file format is JPG, PNG, or PDF. Uploading other formats may cause errors.")
    else:
        # Display full chat history
        display_chat_history(st.session_state['user_id'])

def main():
    # Initialize session state
    initialize_session_state()
    
    # Set up the page
    st.set_page_config(
        page_title="Swasthya AI",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Display user info in sidebar
    show_user_info()
    
    # Main content
    if not st.session_state['logged_in']:
        # Show tabs for login and registration
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            user_id = login_page()
        with tab2:
           register_page()
    else:
        # Determine which page to show based on session state
        if 'current_page' not in st.session_state:
            st.session_state['current_page'] = 'dashboard'
        
        # Initialize response history if not exists
        if 'response_history' not in st.session_state:
            st.session_state.response_history = []
        
        # Add navigation to sidebar for logged-in users
        with st.sidebar:
            st.markdown("---")
            st.subheader("Navigation")
                    
            if st.button("Dashboard", use_container_width=True):
                st.session_state['current_page'] = 'dashboard'
                st.rerun()
                        
            if st.button("Update Profile", use_container_width=True):
                st.session_state['current_page'] = 'profile'
                st.rerun()
            
            if st.button("Emotional Diary", use_container_width=True):
                st.session_state['current_page'] = 'emotional_diary'
                st.rerun()
            
            if st.button("Chatbot", use_container_width=True):
                st.session_state['current_page'] = 'chatbot'
                st.rerun()
                        
            if st.button("Logout", use_container_width=True):
                logout()
                st.rerun()
        
        # Display the appropriate page based on session state
        if st.session_state['current_page'] == 'dashboard':
            display_dashboard()
        elif st.session_state['current_page'] == 'profile':
            display_profile_update()
        elif st.session_state['current_page'] == 'emotional_diary':
            display_emotional_diary()
        elif st.session_state['current_page'] == 'chatbot':
            display_chatbot()

if __name__ == "__main__":
    main()