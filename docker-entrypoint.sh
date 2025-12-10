#!/bin/sh
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Run initialization scripts
echo "Running database initialization..."
python scripts/init_db.py

echo "All initialization complete! Starting the application..."

# Start the backend in the background (listen on port 9000)
uvicorn app.main:app --host 0.0.0.0 --port 9000 &
BACKEND_PID=$!

# Wait for the backend to be ready (health check using Python)
echo "Waiting for backend to be ready..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
  if python -c "import requests; requests.get('http://localhost:9000/docs', timeout=2)" > /dev/null 2>&1; then
    echo "✅ Backend is ready!"
    break
  fi
  attempt=$((attempt + 1))
  echo "⏳ Waiting for backend... (attempt $attempt/$max_attempts)"
  sleep 2
done

if [ $attempt -eq $max_attempts ]; then
  echo "❌ Backend did not become ready in time"
  kill $BACKEND_PID
  exit 1
fi

# Now run seeding scripts (backend is running)
echo "Seeding hospital data..."
python scripts/seed_hopital_fann.py

echo "Creating specialties..."
python scripts/create_specialties.py

echo "Seeding doctors and appointments..."
python scripts/seed_doctors_appointments.py

echo "✅ All seeding complete!"

# Wait for backend process
wait $BACKEND_PID
