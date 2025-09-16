  
from google.colab import files
import pandas as pd
import io

uploaded = files.upload()

df = pd.read_csv(io.BytesIO(uploaded[list(uploaded.keys())[0]]))

print("Sample Data:")
df.head(10)

import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go

def train_and_plot(data, title="Temperature vs Humidity"):
    X = data[['Temperature']]  # independent variable
    y = data['Humidity']       # dependent variable

    model = LinearRegression()
    model.fit(X, y)

    min_temp = X['Temperature'].min()
    max_temp = X['Temperature'].max()
    test_temps = np.linspace(min_temp, max_temp, 100).reshape(-1, 1)
    predicted_humidity = model.predict(test_temps)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=X['Temperature'], y=y, mode='markers', name='Original Data'))
    fig.add_trace(go.Scatter(x=test_temps.flatten(), y=predicted_humidity, mode='lines', name='Trend Line'))

    fig.update_layout(
        title=title,
        xaxis_title='Temperature (°C)',
        yaxis_title='Humidity (%)',
        width=800,
        height=500
    )

    fig.show()
    return model

print("Original Data:")
model_original = train_and_plot(df, title="Original Data: Temperature vs Humidity")

df_filtered1 = df[(df['Temperature'] >= 20) & (df['Temperature'] <= 30)]
print("\nFiltered Data 1:")
model_filtered1 = train_and_plot(df_filtered1, title="Filtered Data 1: Temperature vs Humidity")

df_filtered2 = df_filtered1[(df_filtered1['Temperature'] >= 21) & (df_filtered1['Temperature'] <= 29)]
print("\nFiltered Data 2:")
model_filtered2 = train_and_plot(df_filtered2, title="Filtered Data 2: Temperature vs Humidity")

print("\nInsights:")
print("1. Original trend line may be skewed due to outliers.")
print("2. Filtering extreme temperatures improves the model fit.")
print("3. Repeating filtering gradually refines the model to capture the main trend of temperature vs humidity.")
