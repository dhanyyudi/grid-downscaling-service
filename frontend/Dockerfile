FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    streamlit>=1.30.0 \
    folium>=0.15.0 \
    streamlit-folium>=0.15.0 \
    requests>=2.31.0

# Copy application
COPY streamlit_app.py .

EXPOSE 8501

# Run streamlit (internal port stays 8501, mapped to 8502 externally)
CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.port", "8501", \
     "--server.address", "0.0.0.0", \
     "--theme.base", "dark", \
     "--browser.gatherUsageStats", "false"]
