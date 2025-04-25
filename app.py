import streamlit as st
import pandas as pd 
import plotly.express as px 

data = pd.read_csv('notebooks/vehicles_us.csv')

st.header('Data viewer')
color = st.selectbox('Organize by color',('white', 'red', 'black', 'blue', 'grey', 'silver', 'custom',
       'orange', 'yellow', 'brown', 'green', 'purple'))
data1 = data[data['paint_color'] == color]
histogram = px.histogram(data_frame = data1, x=data1['paint_color'])
histogram.update_layout(
    xaxis_title_text="Paint color",  # Label for the x-axis
    yaxis_title_text="Number of cars"   # Label for the y-axis
)
st.write(histogram)


st.header('Mileage vs price')
include = st.checkbox('Show only cars 2010 or after')
if include:
    data = data[data['model_year']>=2010]
scatter_plot = px.scatter(data,x='odometer',y='price')
st.write(scatter_plot)