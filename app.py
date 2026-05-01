import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Gestione Condominio PRO",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM STYLING ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .highlight {
        background-color: #fff4e6;
        padding: 10px;
        border-left: 4px solid #ff9800;
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATABASE CONSTANTS ---
DB_CONDOMINI = "anagrafica_condomini.csv"
DB_PREVENTIVO = "preventivo_annuale.csv"
MESI_ANNO = 12

# --- DATA LOADING FUNCTIONS ---
@st.cache_data
def carica_condomini():
    """Carica dati condomini da CSV o restituisce dataset di default."""
    if os.path.exists(DB_CONDOMINI):
        return pd.read_csv(DB_CONDOMINI)
    return pd.DataFrame([
        {"ID": "ESS0335", "Prop": 171.96, "Scale": 132.46, "Risc": 164.44},
        {"ID": "ESS0336", "Prop": 92.32, "Scale": 71.11, "Risc": 99.90},
        {"ID": "ESS0331", "Prop": 220.96, "Scale": 195.59, "Risc": 200.49},
        {"ID": "ESS0334", "Prop": 149.94, "Scale": 132.72, "Risc": 170.30},
        {"ID": "ESS0332", "Prop": 183.81, "Scale": 235.86, "Risc": 189.31},
        {"ID": "ESS0333", "Prop": 181.01, "Scale": 232.26, "Risc": 175.56},
    ])

@st.cache_data
def carica_preventivo():
    """Carica preventivo annuale da CSV o restituisce default."""
    if os.path.exists(DB_PREVENTIVO):
        return pd.read_csv(DB_PREVENTIVO).iloc[0].to_dict()
    return {
        "cancelleria": 0.0, "varie": 0.0, "passo": 0.0, "acqua": 0.0,
        "luce": 0.0, "pulizia": 0.0, "caldaia": 0.0, "gasolio": 0.0
    }

def salva_preventivo(dati):
    """Salva preventivo e invalida cache."""
    pd.DataFrame([dati]).to_csv(DB_PREVENTIVO, index=False)
    st.cache_data.clear()

def salva_condomini(df):
    """Salva condomini e invalida cache."""
    df.to_csv(DB_CONDOMINI, index=False)
    st.cache_data.clear()

# --- CALCULATION FUNCTIONS ---
class CalcoloPreventivoManager:
    """Gestisce calcoli e aggregazioni dei preventivi."""
    
    def __init__(self, preventivo):
        self.preventivo = preventivo
    
    @property
    def totale_quota_a(self):
        """Calcola totale annuale Quota A (Tabella A)."""
        return (self.preventivo['cancelleria'] + self.preventivo['varie'] +
                self.preventivo['passo'] + self.preventivo['acqua'])
    
    @property
    def totale_quota_b(self):
        """Calcola totale annuale Quota B (Tabella B)."""
        return self.preventivo['luce'] + self.preventivo['pulizia']
    
    @property
    def totale_quota_d(self):
        """Calcola totale annuale Quota D (Tabella D)."""
        return self.preventivo['caldaia'] + self.preventivo['gasolio']
    
    @property
    def totale_annuale(self):
        """Calcola budget totale annuale."""
        return self.totale_quota_a + self.totale_quota_b + self.totale_quota_d
    
    @property
    def mensile_quota_a(self):
        """Calcola rata mensile Quota A."""
        return self.totale_quota_a / MESI_ANNO
    
    @property
    def mensile_quota_b(self):
        """Calcola rata mensile Quota B."""
        return self.totale_quota_b / MESI_ANNO
    
    @property
    def mensile_quota_d(self):
        """Calcola rata mensile Quota D."""
        return self.totale_quota_d / MESI_ANNO
    
    def calcola_rate_condomino(self, condomino):
        """
        Calcola le tre quote mensili per un singolo condomino.
        
        Args:
            condomino: Dict con chiavi 'Prop', 'Scale', 'Risc'
        
        Returns:
            Dict con quote A, B, D e rata totale
        """
        # Conversione millesimi (divisione per 1000)
        quota_a = (self.mensile_quota_a / 1000) * condomino['Prop']
        quota_b = (self.mensile_quota_b / 1000) * condomino['Scale']
        quota_d = (self.mensile_quota_d / 1000) * condomino['Risc']
        
        return {
            'Quota A': round(quota_a, 2),
            'Quota B': round(quota_b, 2),
            'Quota D': round(quota_d, 2),
            'Totale': round(quota_a + quota_b + quota_d, 2)
        }
    
    def calcola_tutte_rate(self, df_condomini):
        """
        Calcola rate mensili per tutti i condomini.
        
        Args:
            df_condomini: DataFrame con dati condomini
        
        Returns:
            DataFrame con risultati
        """
        risultati = []
        for _, row in df_condomini.iterrows():
            rate = self.calcola_rate_condomino(row)
            risultati.append({
                'Alloggio': row['ID'],
                'Quota A (€)': rate['Quota A'],
                'Quota B (€)': rate['Quota B'],
                'Quota D (€)': rate['Quota D'],
                'RATA MENSILE (€)': rate['Totale']
            })
        
        return pd.DataFrame(risultati)
    
    def get_riepilogo_budget(self):
        """Restituisce riepilogo budget per voce."""
        return {
            'Cancelleria': self.preventivo['cancelleria'],
            'Varie': self.preventivo['varie'],
            'Passo Carrabile': self.preventivo['passo'],
            'Acqua': self.preventivo['acqua'],
            'Luce': self.preventivo['luce'],
            'Pulizia': self.preventivo['pulizia'],
            'Caldaia': self.preventivo['caldaia'],
            'Gasolio': self.preventivo['gasolio'],
        }

# --- PAGE: PREVENTIVO ANNUALE ---
def pagina_preventivo():
    st.header("📊 Definizione Bilancio Preventivo Annuale")
    st.write("Inserisci le spese totali previste per l'intero anno gestionale (Aprile - Marzo).")
    
    p = carica_preventivo()
    manager = CalcoloPreventivoManager(p)
    
    # Mostra budget attuale
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Quota A Annuale", f"€ {manager.totale_quota_a:,.2f}")
    with col2:
        st.metric("Quota B Annuale", f"€ {manager.totale_quota_b:,.2f}")
    with col3:
        st.metric("Quota D Annuale", f"€ {manager.totale_quota_d:,.2f}")
    with col4:
        st.metric("Totale Annuale", f"€ {manager.totale_annuale:,.2f}", delta=None)
    
    with st.form("form_preventivo"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("📋 Tabella A (Spese Comuni)")
            p_can = st.number_input("Cancelleria (€)", value=float(p['cancelleria']), min_value=0.0, step=10.0)
            p_var = st.number_input("Varie (€)", value=float(p['varie']), min_value=0.0, step=10.0)
            p_pas = st.number_input("Passo Carrabile (€)", value=float(p['passo']), min_value=0.0, step=10.0)
            p_acq = st.number_input("Acqua (€)", value=float(p['acqua']), min_value=0.0, step=10.0)
        
        with col2:
            st.subheader("⚡ Tabella B (Servizi)")
            p_luc = st.number_input("Luce (€)", value=float(p['luce']), min_value=0.0, step=10.0)
            p_pul = st.number_input("Pulizia (€)", value=float(p['pulizia']), min_value=0.0, step=10.0)
        
        with col3:
            st.subheader("🔥 Tabella D (Riscaldamento)")
            p_cal = st.number_input("Caldaia (€)", value=float(p['caldaia']), min_value=0.0, step=10.0)
            p_gas = st.number_input("Gasolio (€)", value=float(p['gasolio']), min_value=0.0, step=10.0)
        
        submitted = st.form_submit_button("💾 Salva Preventivo", use_container_width=True)
        
        if submitted:
            dati = {
                "cancelleria": p_can, "varie": p_var, "passo": p_pas, "acqua": p_acq,
                "luce": p_luc, "pulizia": p_pul, "caldaia": p_cal, "gasolio": p_gas
            }
            salva_preventivo(dati)
            st.success("✅ Preventivo salvato! Le rate mensili sono state ricalcolate.")
            st.rerun()

# --- PAGE: DASHBOARD CALCOLI ---
def pagina_dashboard():
    df_c = carica_condomini()
    p = carica_preventivo()
    manager = CalcoloPreventivoManager(p)
    
    st.header("🏠 Dashboard Mensilità")
    
    # KPI superiore
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Budget Annuale", f"€ {manager.totale_annuale:,.2f}")
    with col2:
        st.metric("Mensile Medio", f"€ {manager.totale_annuale/MESI_ANNO:,.2f}")
    with col3:
        st.metric("Unità Abitative", len(df_c))
    with col4:
        st.metric("Ultimo Aggiornamento", datetime.now().strftime("%d/%m/%Y"))
    
    st.markdown("---")
    
    # Tabella rate mensili
    st.subheader("📑 Rate Mensili Provvisorie (Base Preventivo)")
    df_risultati = manager.calcola_tutte_rate(df_c)
    
    # Visualizza tabella con styling
    st.dataframe(df_risultati, use_container_width=True, hide_index=True)
    
    # Statistiche
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        rata_media = df_risultati['RATA MENSILE (€)'].mean()
        st.metric("Rata Media Mensile", f"€ {rata_media:,.2f}")
    with col2:
        rata_min = df_risultati['RATA MENSILE (€)'].min()
        st.metric("Rata Minima", f"€ {rata_min:,.2f}")
    with col3:
        rata_max = df_risultati['RATA MENSILE (€)'].max()
        st.metric("Rata Massima", f"€ {rata_max:,.2f}")
    
    # Grafici
    st.markdown("---")
    st.subheader("📈 Analitiche")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Grafico breakdown quote
        quote_data = {
            'Quota A': manager.totale_quota_a,
            'Quota B': manager.totale_quota_b,
            'Quota D': manager.totale_quota_d
        }
        fig_pie = go.Figure(data=[go.Pie(
            labels=list(quote_data.keys()),
            values=list(quote_data.values()),
            textinfo="label+percent+value",
            marker=dict(colors=['#636EFA', '#EF553B', '#00CC96'])
        )])
        fig_pie.update_layout(
            title="Distribuzione Budget Annuale",
            height=400,
            showlegend=True
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Grafico rate per alloggio
        fig_bar = px.bar(
            df_risultati,
            x='Alloggio',
            y=['Quota A (€)', 'Quota B (€)', 'Quota D (€)'],
            title="Rate Mensili per Alloggio",
            barmode='stack',
            color_discrete_sequence=['#636EFA', '#EF553B', '#00CC96']
        )
        fig_bar.update_layout(height=400, showlegend=True)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Riepilogo budget
    st.markdown("---")
    st.subheader("💰 Riepilogo Budget Annuale")
    riepilogo = manager.get_riepilogo_budget()
    df_riepilogo = pd.DataFrame([
        {'Voce': k, 'Importo Annuale (€)': v} for k, v in riepilogo.items()
    ])
    st.dataframe(df_riepilogo, use_container_width=True, hide_index=True)
    
    # Export
    st.markdown("---")
    csv = df_risultati.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Scarica Rate Mensili (CSV)",
        data=csv,
        file_name=f"rate_mensili_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# --- PAGE: GESTIONE CONDOMINI ---
def pagina_gestione():
    st.header("👥 Gestione Anagrafica Unità Abitative")
    
    df_c = carica_condomini()
    
    st.subheader("📋 Dati Attuali")
    st.dataframe(df_c, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("➕ Aggiungi Nuovo Condominio")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        new_id = st.text_input("ID Unità", placeholder="es. ESS0340")
    with col2:
        new_prop = st.number_input("Millesimi Proprietà", min_value=0.0, step=0.01)
    with col3:
        new_scale = st.number_input("Millesimi Scala", min_value=0.0, step=0.01)
    with col4:
        new_risc = st.number_input("Millesimi Rischio", min_value=0.0, step=0.01)
    
    if st.button("➕ Aggiungi Unità"):
        if not new_id or new_id in df_c['ID'].values:
            st.error("❌ Inserisci un ID valido e univoco!")
        else:
            new_row = pd.DataFrame([{
                'ID': new_id,
                'Prop': new_prop,
                'Scale': new_scale,
                'Risc': new_risc
            }])
            df_c = pd.concat([df_c, new_row], ignore_index=True)
            salva_condomini(df_c)
            st.success(f"✅ Unità {new_id} aggiunta con successo!")
            st.rerun()
    
    st.markdown("---")
    st.subheader("✏️ Modifica Condominio")
    
    selected_id = st.selectbox("Seleziona Unità da modificare", df_c['ID'].values)
    selected_row = df_c[df_c['ID'] == selected_id].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        mod_prop = st.number_input("Millesimi Proprietà", value=float(selected_row['Prop']), step=0.01)
    with col2:
        mod_scale = st.number_input("Millesimi Scala", value=float(selected_row['Scale']), step=0.01)
    with col3:
        mod_risc = st.number_input("Millesimi Rischio", value=float(selected_row['Risc']), step=0.01)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Salva Modifiche"):
            df_c.loc[df_c['ID'] == selected_id, 'Prop'] = mod_prop
            df_c.loc[df_c['ID'] == selected_id, 'Scale'] = mod_scale
            df_c.loc[df_c['ID'] == selected_id, 'Risc'] = mod_risc
            salva_condomini(df_c)
            st.success(f"✅ Unità {selected_id} modificata con successo!")
            st.rerun()
    
    with col2:
        if st.button("🗑️ Elimina Unità"):
            df_c = df_c[df_c['ID'] != selected_id]
            salva_condomini(df_c)
            st.success(f"✅ Unità {selected_id} eliminata con successo!")
            st.rerun()

# --- MAIN NAVIGATION ---
def main():
    # Sidebar
    with st.sidebar:
        st.title("🏢 Condominio PRO")
        st.markdown("---")
        menu = st.radio(
            "Navigazione",
            ["🏠 Dashboard Calcoli", "📊 Preventivo Annuale", "👥 Gestione Condomini"],
            label_visibility="collapsed"
        )
        st.markdown("---")
        st.caption(f"Versione: 2.0 | Data: {datetime.now().strftime('%d/%m/%Y')}")
    
    # Page routing
    if menu == "📊 Preventivo Annuale":
        pagina_preventivo()
    elif menu == "🏠 Dashboard Calcoli":
        pagina_dashboard()
    else:
        pagina_gestione()

if __name__ == "__main__":
    main()
