# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Setup Environment (2 minutes)

```bash
# Navigate to project
cd "cs feedbacks"

# Create virtual environment
python3.11 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys (1 minute)

```bash
# Copy template
cp .env.example .env

# Edit with your keys
nano .env  # or use any editor
```

Add your API keys:
```
FRESHDESK_API_KEY=your_actual_freshdesk_key
OPENAI_API_KEY=your_actual_openai_key
```

### 3. Run the Application (1 minute)

```bash
python main.py
```

You'll be prompted for:
1. **Game Name** (e.g., "Candy Crush")
2. **OS** (Android/iOS/Both)
3. **Start Date** (YYYY-MM-DD)
4. **End Date** (YYYY-MM-DD)

### 4. Test Individual Components (1 minute)

```bash
# Test input handler
python test_input_handler.py

# Test storage manager
python test_storage_manager.py
```

## 📚 Key Files

| File | Purpose |
|------|---------|
| `main.py` | Main application entry point |
| `src/input_handler.py` | Interactive CLI input collection |
| `src/storage_manager.py` | Data caching system |
| `README.md` | Complete documentation |
| `STORAGE.md` | Storage manager details |

## 🔧 Common Commands

```bash
# Run main application
python main.py

# Test input handler
python test_input_handler.py

# Test storage manager
python test_storage_manager.py

# Test individual modules
python -m src.input_handler
python -m src.storage_manager
python -m src.config

# Check configuration
python -c "from src.config import get_settings; print(get_settings())"
```

## 💾 Storage Manager Quick Reference

### Check if cache exists
```python
from src import storage_manager
from src.input_handler import FeedbackAnalysisInput

params = FeedbackAnalysisInput(
    game_name="My Game",
    os="Android",
    start_date="2024-01-01",
    end_date="2024-01-31"
)

if storage_manager.exists(params):
    print("Cache found!")
```

### Load cached data
```python
data = storage_manager.load(params)
print(f"Loaded {len(data['feedbacks'])} feedbacks")
```

### Save data to cache
```python
data = {
    'metadata': {...},
    'feedbacks': [...]
}
storage_manager.save(params, data)
```

### Get cache info
```python
info = storage_manager.get_cache_info(params)
if info:
    print(f"Size: {info['size_kb']} KB")
```

## 🎯 Filename Format

Cached files follow this pattern:
```
Feedback_<GameName>_<OS>_YYYY-MM-DD_to_YYYY-MM-DD.json
```

Examples:
- `Feedback_Candy_Crush_Android_2024-01-01_to_2024-01-31.json`
- `Feedback_Subway_Surfers_iOS_2024-02-01_to_2024-02-28.json`

## ⚠️ Troubleshooting

### "ModuleNotFoundError"
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "Configuration error"
```bash
# Check .env file exists
ls -la .env

# Verify API keys are set
cat .env
```

### "No module named 'src'"
```bash
# Run from project root, not src/ directory
cd "cs feedbacks"
python main.py
```

## 📖 More Information

- **Complete Guide**: See `README.md`
- **Input Handler**: See `USAGE.md`
- **Storage System**: See `STORAGE.md`
- **Architecture**: See `ARCHITECTURE.md`
- **Full Summary**: See `PROJECT_SUMMARY.md`

## ✅ What's Implemented

✓ Interactive CLI input collection with validation  
✓ Storage manager with intelligent caching  
✓ Configuration management (.env support)  
✓ Professional logging system  
✓ Comprehensive documentation  
✓ Test scripts for all components  

## 🚧 Coming Next

- Freshdesk API integration
- OpenAI analysis
- Report generation

---

**Need Help?** Check the full documentation in `README.md` or run test scripts to see examples.
