import streamlit as st
from calculator_engine import QuantitativeEngine

st.set_page_config(page_title="Week 6: Quantitative CI Portal", layout="centered")
st.title("🚀 Week 6: DevSecOps & Quantitative Engine")

st.markdown("[![CI](https://github.com/akshyagupta-tech/YuvaIntern_python-continuous-integration/actions/workflows/ci.yml/badge.svg)](https://github.com/akshyagupta-tech/YuvaIntern_python-continuous-integration/actions)")

p = st.number_input("Principal (₹):", min_value=100.0, value=10000.0)
r = st.number_input("Annual Interest Rate (%):", min_value=0.1, value=7.5)
t = st.number_input("Time (Years):", min_value=1, value=3)

if st.button("Compute Compound Interest"):
    ci = QuantitativeEngine.calculate_compound_interest(p, r, t)
    st.metric("Total Accrued Interest", f"₹{ci}")
