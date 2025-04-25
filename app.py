import streamlit as st
import pandas as pd 
import plotly.express as px 

data = pd.read_csv('notebooks/vehicles_us.csv')


st.header('Data viewer')
color = st.selectbox('Organize by color',(pd.unique(data['paint_color'])))
data = data[data['paint_color'] == color]
histogram = px.histogram(data_frame = data, x=data['paint_color'])
histogram.update_layout(
    xaxis_title_text="Paint color",  # Label for the x-axis
    yaxis_title_text="Number of cars"   # Label for the y-axis
)
st.write(histogram)

