#!/bin/bash

# Rafiki AI - Google Colab GPU Setup Helper

echo "======================================================================"
echo "  Rafiki AI - Google Colab GPU Setup"
echo "======================================================================"
echo ""
echo "This will guide you through setting up GPU-accelerated video generation"
echo "using Google Colab (FREE!)"
echo ""
echo "📊 Performance Comparison:"
echo "   CPU (Local):  2-10 minutes per video"
echo "   GPU (Colab):  5-15 seconds per video  ← 50-100x faster! 🚀"
echo ""
echo "======================================================================"
echo ""

# Check if notebook exists
if [ ! -f "SadTalker_GPU_Colab.ipynb" ]; then
    echo "❌ Error: SadTalker_GPU_Colab.ipynb not found!"
    echo "   Please run this script from /home/subchief/5TECH/"
    exit 1
fi

echo "✅ Found: SadTalker_GPU_Colab.ipynb"
echo ""

# Step 1
echo "📝 Step 1: Upload Notebook to Google Colab"
echo "   1. Go to: https://colab.research.google.com/"
echo "   2. Click: File → Upload notebook"
echo "   3. Upload: $(pwd)/SadTalker_GPU_Colab.ipynb"
echo ""
echo "   Or copy this path:"
echo "   $(pwd)/SadTalker_GPU_Colab.ipynb"
echo ""
read -p "Press Enter when you've uploaded the notebook..."
echo ""

# Step 2
echo "🎮 Step 2: Enable GPU in Colab"
echo "   1. In Colab: Runtime → Change runtime type"
echo "   2. Select: Hardware accelerator → GPU"
echo "   3. Choose: T4 GPU"
echo "   4. Click: Save"
echo ""
read -p "Press Enter when you've enabled GPU..."
echo ""

# Step 3
echo "🔑 Step 3: Get ngrok Token"
echo "   1. Go to: https://dashboard.ngrok.com/signup"
echo "   2. Sign up (free)"
echo "   3. Go to: https://dashboard.ngrok.com/get-started/your-authtoken"
echo "   4. Copy your token"
echo ""
read -p "Press Enter when you have your ngrok token..."
echo ""

# Step 4
echo "▶️  Step 4: Run Colab Cells"
echo "   1. Run Cell 1 (Setup) - takes ~5 minutes"
echo "      - Wait for: ✅ Setup complete!"
echo "   2. In Cell 2: Paste your ngrok token"
echo "   3. Run Cell 2"
echo "   4. Run Cell 3 (Start Server)"
echo "      - Wait for: 🚀 SadTalker GPU API Server is RUNNING!"
echo ""
read -p "Press Enter when server is running..."
echo ""

# Step 5
echo "🌐 Step 5: Copy the Public URL"
echo "   You should see output like:"
echo "   📡 Public URL: https://abc123.ngrok.io"
echo ""
echo -n "   Paste your ngrok URL here: "
read NGROK_URL

if [ -z "$NGROK_URL" ]; then
    echo "   ⚠️  No URL provided. You can set it later."
else
    # Validate URL format
    if [[ $NGROK_URL == https://*.ngrok.io* ]] || [[ $NGROK_URL == http://*.ngrok.io* ]]; then
        echo ""
        echo "   ✅ Valid ngrok URL!"
        
        # Set environment variable
        export COLAB_SADTALKER_URL="$NGROK_URL"
        
        # Add to .env if exists
        if [ -f "backend/.env" ]; then
            # Remove old entry if exists
            sed -i '/COLAB_SADTALKER_URL/d' backend/.env
            echo "COLAB_SADTALKER_URL=$NGROK_URL" >> backend/.env
            echo "   ✅ Saved to backend/.env"
        else
            echo "   💡 Add this to your backend/.env file:"
            echo "      COLAB_SADTALKER_URL=$NGROK_URL"
        fi
    else
        echo "   ⚠️  URL doesn't look right. Should be: https://xxxx.ngrok.io"
    fi
fi

echo ""
echo "======================================================================"
echo "✅ Setup Complete!"
echo "======================================================================"
echo ""
echo "🎯 Next Steps:"
echo ""
echo "1. Start your backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "2. Test GPU generation:"
echo "   curl -X POST http://localhost:8000/api/avatar/text-to-video \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"text\": \"Hello from GPU!\", \"use_elevenlabs\": false}' \\"
echo "     --output test_gpu.mp4"
echo ""
echo "   Result: Video in 5-15 seconds! 🚀"
echo ""
echo "3. Pre-generate common phrases (optional):"
echo "   cd backend && python3 pregenerate_videos.py"
echo ""
echo "======================================================================"
echo ""
echo "📚 Documentation:"
echo "   - Full guide: COLAB_SETUP_GUIDE.md"
echo "   - Troubleshooting: SADTALKER_TROUBLESHOOTING.md"
echo ""
echo "💡 Tips:"
echo "   - Keep Colab tab open while using"
echo "   - Free sessions last up to 12 hours"
echo "   - URL changes when you restart Colab"
echo "   - System auto-falls back to audio if Colab disconnects"
echo ""
echo "======================================================================"
echo "Happy coding! 🎉"
echo "======================================================================"
