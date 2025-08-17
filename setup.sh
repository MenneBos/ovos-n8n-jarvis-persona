#!/bin/bash
# Setup script for OVOS N8N JARVIS Persona

echo "================================"
echo "OVOS N8N JARVIS Persona Setup"
echo "================================"
echo ""

# Check if in correct directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Install the package
echo "Installing ovos-n8n-jarvis-persona..."
pip install -e .

if [ $? -ne 0 ]; then
    echo "Error: Installation failed"
    exit 1
fi

echo ""
echo "✓ Package installed successfully"
echo ""

# Create persona config directory
echo "Creating persona configuration directory..."
mkdir -p ~/.config/ovos_persona/

# Copy config if it doesn't exist
if [ ! -f ~/.config/ovos_persona/jarvis.json ]; then
    echo "Copying JARVIS persona configuration..."
    cp config/jarvis_persona.json ~/.config/ovos_persona/jarvis.json
    echo "✓ Configuration copied to ~/.config/ovos_persona/jarvis.json"
    echo ""
    echo "IMPORTANT: Edit ~/.config/ovos_persona/jarvis.json"
    echo "          Set your n8n webhook URL"
else
    echo "✓ JARVIS configuration already exists"
fi

echo ""
echo "Testing installation..."
python test_persona.py

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Edit ~/.config/ovos_persona/jarvis.json with your webhook URL"
echo "2. Import workflows into n8n from the workflows/ directory"
echo "3. Update ~/.config/mycroft/mycroft.conf (see config/mycroft_persona.conf)"
echo "4. Restart OVOS: systemctl --user restart ovos"
echo "5. Say 'Hey JARVIS'"
echo ""