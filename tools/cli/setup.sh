#!/usr/bin/env bash
set -e

echo "🔧 Setting up FastKit CLI..."

chmod +x tools/cli/main.py

if [ -L /usr/local/bin/fastkit ]; then
    sudo rm /usr/local/bin/fastkit
fi
sudo ln -s $(pwd)/tools/cli/main.py /usr/local/bin/fastkit
echo "✅ Symlink created: 'fastkit' command is now available globally."

if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ .env file created from .env.example"
fi

PYTHON_CMD="python3"
OS_TYPE=$(uname)
if [[ "$OS_TYPE" == "Darwin" ]]; then
    echo "🍏 Detected macOS"
elif [[ "$OS_TYPE" == "Linux" ]]; then
    echo "🐧 Detected Linux"
else
    echo "⚠️  Unknown OS, defaulting to python3"
fi

if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
else
    echo "⚙️  Virtual environment already exists, skipping..."
fi

echo "📦 Installing dependencies..."
if [[ "$OS_TYPE" == "Darwin" ]] || [[ "$OS_TYPE" == "Linux" ]]; then
    source venv/bin/activate
fi
pip install --upgrade pip
pip install -r requirements.txt

echo "🐳 Starting Docker containers..."
docker compose up -d

echo "🎉 FastKit setup completed successfully!"
echo ""
echo "You can now use: fastkit install | fastkit run | fastkit migrate | fastkit update"
