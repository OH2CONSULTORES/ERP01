# ventas.py
import streamlit as st
import streamlit as st
import pandas as pd
import json, os
from datetime import date
import d_cotizador 


def mostrar_cotizaciones():
    st.header("📄 Cotizaciones")
    d_cotizador.mostrar_cotizador()


def mostrar_ordenes_venta():
    st.header("📄 Órdenes de Venta")
    st.info("🚧 Módulo en construcción. Aquí se registrarán y controlarán las órdenes de venta confirmadas.")

def mostrar_despachos():
    st.header("🚚 Despachos")
    st.info("🚧 Módulo en construcción. Aquí se controlarán los despachos, entregas y guías de remisión.")
