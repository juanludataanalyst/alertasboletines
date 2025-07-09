import streamlit as st
from supabase import create_client, Client

st.title("Hola desde Streamlit + Supabase")

st.write("Este es un ejemplo mínimo")

# Supabase client dummy
url = "https://xyzcompany.supabase.co"
key = "public-anon-key"
client: Client = create_client(url, key)

st.write("Cliente Supabase creado (aunque falso en este ejemplo)")
