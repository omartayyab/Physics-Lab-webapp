# 1. Use a stable, lightweight version of Python
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy only the requirements file first (this makes future builds much faster)
COPY requirements.txt .

# 4. Install the Python packages
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your project files into the container
COPY . .

# 6. Expose the port Streamlit uses
EXPOSE 8501

# 7. The command to run when the container starts
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]