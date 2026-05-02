import requests
import streamlit as st
from datetime import datetime

# --- JOKE API CONFIGURATION ---
JOKE_API_URL = "https://official-joke-api.appspot.com/random_joke"
JOKE_API_URL_CATEGORY = "https://official-joke-api.appspot.com/jokes/{category}/random"

@st.cache_data
def get_random_joke():
    """Fetch a random joke from the official-joke-api."""
    try:
        response = requests.get(JOKE_API_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Errore nel caricamento della barzelletta: {str(e)}"}

def get_joke_by_category(category):
    """Fetch a joke from a specific category."""
    try:
        response = requests.get(JOKE_API_URL_CATEGORY.format(category=category), timeout=5)
        response.raise_for_status()
        jokes = response.json()
        # If it returns a list, take the first one
        return jokes[0] if isinstance(jokes, list) else jokes
    except requests.exceptions.RequestException as e:
        return {"error": f"Errore nel caricamento della barzelletta: {str(e)}"}

def display_joke(joke):
    """Display a joke in a nicely formatted way."""
    if "error" in joke:
        st.error(joke["error"])
        return
    
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin: 10px 0;">
        <h3>😂 {joke.get('setup', '')}</h3>
        <p style="font-size: 18px; color: #1f77b4; font-weight: bold;">{joke.get('punchline', '')}</p>
        <small style="color: #888;">📌 Tipo: {joke.get('type', 'N/A')}</small>
    </div>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Joke Generator", layout="centered")
    
    st.title("🎭 Random Joke Generator")
    st.write("Genera barzellette casuali da un'API esterna!")
    
    st.markdown("---")
    
    # Tab selection
    tab1, tab2, tab3 = st.tabs(["🎲 Barzelletta Casuale", "📚 Per Categoria", "📊 Statistiche"])
    
    # --- TAB 1: RANDOM JOKE ---
    with tab1:
        st.subheader("Genera una barzelletta casuale")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎲 Nuova Barzelletta", use_container_width=True):
                st.session_state.joke = get_random_joke()
                st.session_state.timestamp = datetime.now()
        
        with col2:
            if st.button("🔄 Ricarica", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        
        st.markdown("")
        
        if "joke" in st.session_state:
            display_joke(st.session_state.joke)
            st.caption(f"⏰ Caricata alle {st.session_state.timestamp.strftime('%H:%M:%S')}")
    
    # --- TAB 2: CATEGORY ---
    with tab2:
        st.subheader("Scegli una categoria")
        
        categories = ["general", "knock-knock", "programming"]
        selected_category = st.selectbox("Categoria:", categories)
        
        if st.button("📚 Carica Barzelletta", use_container_width=True):
            joke = get_joke_by_category(selected_category)
            st.session_state.category_joke = joke
            st.session_state.category_timestamp = datetime.now()
        
        st.markdown("")
        
        if "category_joke" in st.session_state:
            display_joke(st.session_state.category_joke)
            st.caption(f"⏰ Caricata alle {st.session_state.category_timestamp.strftime('%H:%M:%S')}")
    
    # --- TAB 3: STATISTICS ---
    with tab3:
        st.subheader("📊 Statistiche API")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("API Utilizzata", "Official Joke API")
        with col2:
            st.metric("Endpoint", "official-joke-api.appspot.com")
        with col3:
            st.metric("Status", "🟢 Attivo")
        
        st.markdown("---")
        
        st.write("**Informazioni sull'API:**")
        st.info("""
        - ✅ Gratuita e senza autenticazione
        - ✅ +100 barzellette disponibili
        - ✅ Supporta categorie: General, Knock-Knock, Programming
        - ✅ Risposta rapida (< 1 secondo)
        
        **Fonte**: https://official-joke-api.appspot.com/
        """)
        
        # API Test
        st.markdown("---")
        st.subheader("🧪 Test Connessione API")
        
        if st.button("Test API", use_container_width=True):
            with st.spinner("Testing API..."):
                test_joke = get_random_joke()
                if "error" in test_joke:
                    st.error(f"❌ Errore: {test_joke['error']}")
                else:
                    st.success("✅ API funzionante!")
                    st.json(test_joke)

if __name__ == "__main__":
    # Initialize session state
    if "joke" not in st.session_state:
        st.session_state.joke = None
    if "category_joke" not in st.session_state:
        st.session_state.category_joke = None
    
    main()
