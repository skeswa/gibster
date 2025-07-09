# Gibster

A service to synchronize Gibney dance space bookings with your personal calendar.

## What is Gibster?

Gibster provides automated calendar synchronization for dancers who book rehearsal space at Gibney. Simply connect your Gibney account once, and all your bookings will automatically appear in your preferred calendar app (Google Calendar, Apple Calendar, Outlook, etc.).

## Features

- 🔒 **Secure** - Credentials encrypted at rest
- 🔄 **Automatic** - Syncs every 2 hours
- 📅 **Universal** - Works with any calendar app
- ⚡ **Real-time** - Manual sync on demand
- 🎯 **Simple** - Set it and forget it

## Quick Start

```bash
# Clone and setup
git clone <your-repo-url>
cd gibster
source venv/bin/activate
python scripts/dev_setup.py

# Configure credentials
# Edit backend/.env with your Gibney login

# Start the server
python scripts/run_dev.py
```

Visit http://localhost:3000 in your friendly neighborhood browser.

For detailed setup instructions, see the [Quick Start Guide](docs/quickstart.md).

## Documentation

- 📚 [Quick Start Guide](docs/quickstart.md) - Get up and running quickly
- 🛠️ [Development Guide](docs/development.md) - Detailed development setup
- 🏗️ [Architecture Overview](docs/architecture.md) - System design and technical details
- 🧪 [Testing Guide](docs/testing.md) - Running and writing tests
- 🚀 [Deployment Guide](docs/deployment.md) - Production deployment with Kubernetes
- 📋 [Requirements Document](docs/requirements.md) - Complete functional and non-functional requirements

## Tech Stack

- **Backend**: FastAPI (Python) with PostgreSQL/SQLite
- **Frontend**: Next.js (TypeScript) with React
- **Scraping**: Playwright for web automation
- **Infrastructure**: Docker, Kubernetes, GitHub Actions

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run the setup script (`python scripts/dev_setup.py`)
4. Make your changes and add tests
5. Run tests (`python scripts/run_tests.py --coverage`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

Please ensure:

- All tests pass
- Code follows project style guidelines
- Test coverage remains above 80%
- Documentation is updated as needed

## Support

- 🐛 [Report Issues](https://github.com/skeswa/gibster/issues)
- 💬 [Discussions](https://github.com/skeswa/gibster/discussions)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Note**: Gibster is not affiliated with Gibney Dance Center. Use responsibly and in accordance with Gibney's policies.
