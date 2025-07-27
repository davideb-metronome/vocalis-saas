# Vocalis SaaS - AI Voice Generation Platform

> **Professional AI Voice Generation with Metronome Billing Integration**

## 🏗️ Architecture

- **Frontend**: Modern HTML/CSS/JS with modular architecture
- **Backend**: FastAPI with Metronome billing integration  
- **Billing**: Prepaid credits with auto-recharge via webhooks
- **Integration**: Real-time updates via Server-Sent Events

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Metronome API credentials
```

### 3. Run Development Server

```bash
cd backend
python -m app.main
```

Visit: http://localhost:8000

## 📁 Project Structure

```
vocalis-saas/
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── api/       # API routes
│   │   ├── core/      # Configuration
│   │   ├── services/  # External service integrations
│   │   └── main.py    # Application entry point
│   └── requirements.txt
├── frontend/          # Static assets and templates
│   ├── static/
│   │   ├── css/       # Modular stylesheets
│   │   └── js/        # Component-based JavaScript
│   └── templates/     # Jinja2 HTML templates
└── docs/             # Documentation
```

## 🔧 Development

### Metronome Integration Status

Current implementation uses **stub functions** that will fail with `NotImplementedError`. This is intentional - no mock data, fail fast approach.

To implement real integration:
1. Add Metronome API credentials to `.env`
2. Implement actual API calls in `backend/app/services/metronome/client.py`
3. Test with real Metronome endpoints

### API Endpoints

- `POST /api/auth/signup` - User registration
- `POST /api/billing/credits/purchase` - Credit purchases  
- `GET /api/billing/credits/balance/{customer_id}` - Balance check
- `POST /api/usage/generate-voice` - Voice generation
- `POST /api/webhooks/metronome/*` - Webhook handlers

## 🎯 Next Steps

1. **Implement Metronome Integration**: Replace stubs with real API calls
2. **Add Voice Generation Service**: Integrate with AI voice provider
3. **Server-Sent Events**: Real-time balance updates
4. **Webhook Processing**: Auto-recharge automation
5. **Production Deployment**: Docker + cloud infrastructure

## 📖 Documentation

- [API Documentation](docs/api/)
- [Architecture Guide](docs/architecture/)
- [Deployment Guide](docs/deployment/)

---

**Status**: Development Ready ✅  
**Metronome Integration**: Stub Implementation (Fails Fast) ⚠️  
**Voice Generation**: Stub Implementation ⚠️
