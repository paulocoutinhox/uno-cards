# UNO Cards Generator

[![Build](https://github.com/paulocoutinhox/uno-cards/actions/workflows/build.yml/badge.svg)](https://github.com/paulocoutinhox/uno-cards/actions/workflows/build.yml)

A Python script that generates custom UNO cards using OpenAI's AI image generation. Creates beautiful, printable PDF cards for recreational purposes.

## ✨ Features

- **Custom UNO Cards** – Generate personalized UNO card designs 🎴
- **AI-Powered Images** – Uses OpenAI's AI to create unique illustrations for each card 🎨
- **PDF Output** – Automatically generates a printable PDF with all cards 🖨️
- **Test Mode** – Quick testing without API calls 💡
- **Customizable** – Configurable colors, borders, and generation options ⚙️
- **High Quality** – Upscaled images for crisp printing quality 📸

## Requirements

- Python 3.9+
- OpenAI API key (for image generation)

## 🚀 Installation

1. **Clone the repository:**
```bash
git clone https://github.com/paulocoutinhox/uno-cards.git
cd uno-cards
```

2. **Create virtual environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies:**
```bash
python3 -m pip install -r requirements.txt
```

## 🎮 Usage

### Generate Cards

```bash
python3 main.py
```

This will generate all 108 UNO cards and create a PDF.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key (required) | - |
| `UNO_TEST_MODE` | Use test mode (no API calls) | `false` |
| `UNO_GENERATE_FIRST_ONLY` | Generate only first card | `false` |
| `UNO_OUTPUT_DIR` | Output directory | `uno-cards-out` |
| `UNO_UPSCALE_FACTOR` | Image quality multiplier | `3` |
| `UNO_BORDER_COLOR` | Border color (hex) | `#000000` |

### Test Mode Example

For quick testing without API calls:

```bash
UNO_TEST_MODE=true python3 main.py
```

### Generate Only First Card

For development/testing:

```bash
UNO_GENERATE_FIRST_ONLY=true python3 main.py
```

### Full Test Example

```bash
UNO_TEST_MODE=true UNO_GENERATE_FIRST_ONLY=true python3 main.py
```

## 🏗️ Project Structure

- `main.py` - Main script that generates the UNO cards
- `requirements.txt` - Python dependencies
- `extras/images/` - Symbol images and test background
- `extras/fonts/` - Custom fonts for card text
- `uno-cards-out/` - Generated output directory (ignored by git)
- `.github/workflows/` - GitHub Actions CI/CD pipeline

## 🎨 Card Types

The generator creates a complete UNO deck with:

- **Number Cards**: 0-9 in four colors (Red, Yellow, Green, Blue)
- **Action Cards**: Skip, Reverse, Draw 2 in four colors
- **Wild Cards**: Wild and Wild Draw 4 cards
- **Special Designs**: Custom illustrations for each card type

## 🛠️ Troubleshooting

### OpenAI API Issues
- Ensure your `OPENAI_API_KEY` is set correctly
- Check your OpenAI account balance and API limits
- The script will show progress for each card generation

### PDF Generation Issues
- Make sure ReportLab is installed correctly
- Check write permissions for the output directory
- Generated files are saved to `uno-cards-out/` by default

### Test Mode Not Working
- Verify `UNO_TEST_MODE=true` is set
- Check that `extras/images/test-bg.png` exists
- Test mode skips API calls and uses placeholder images

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `UNO_TEST_MODE=true`
5. Submit a pull request

## 📜 License

[MIT](http://opensource.org/licenses/MIT)

Copyright (c) 2025, Paulo Coutinho
