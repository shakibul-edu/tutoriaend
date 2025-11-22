FROM python:3.11-slim

# Install system dependencies (GDAL, PROJ, GEOS, PostgreSQL client)
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables so Django can find it
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so

# Create working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN pip install whitenoise

# Copy project files
COPY . .

# Run Django app
# CMD ["gunicorn", "tutoria.wsgi:application", "--bind", "0.0.0.0:8000"]
# For development mode: run Django's development server
# Uncomment the following line to use runserver instead of gunicorn
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
