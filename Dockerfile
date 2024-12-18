FROM python:3.10.13-slim

# Set the working directory inside the container
WORKDIR /src

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

CMD ["sh", "-c", "alembic upgrade head && python app/runme.py"]
