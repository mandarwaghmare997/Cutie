# Qryti - ISO 42001 Compliance Platform

[![Deploy to AWS](https://github.com/mandarwaghmare997/Cutie/actions/workflows/deploy.yml/badge.svg)](https://github.com/mandarwaghmare997/Cutie/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)

## 🚀 Overview

Qryti is an automated ISO 42001:2023 AI Management System compliance platform that streamlines the complex process of AI governance assessment and certification. Built for organizations seeking to implement robust AI governance frameworks, Qryti transforms weeks of manual compliance work into hours of guided assessment.

### 🎯 Key Features

- **🔐 Secure Authentication**: Email-based OTP verification with JWT tokens
- **📊 Six-Stage Assessment**: Comprehensive compliance journey from requirements to certification
- **🏆 Professional Certificates**: Generate internationally recognized compliance certificates
- **👥 Multi-User Support**: Organization-wide collaboration and role-based access
- **📈 Real-time Analytics**: Track progress and compliance scores with detailed insights
- **☁️ AWS-Native**: Serverless architecture optimized for scalability and cost-efficiency

## 🏗️ Architecture

### Frontend
- **Technology**: HTML5, CSS3, JavaScript (ES6+)
- **Design**: Responsive, mobile-first approach
- **Hosting**: AWS S3 + CloudFront CDN

### Backend
- **Framework**: Flask (Python 3.11)
- **Architecture**: Serverless with AWS Lambda
- **Database**: DynamoDB for scalability
- **Storage**: S3 for document management
- **API**: RESTful with comprehensive endpoints

### Infrastructure
- **Cloud Provider**: AWS (Free Tier Optimized)
- **Deployment**: Infrastructure as Code with CloudFormation
- **CI/CD**: GitHub Actions for automated deployment
- **Monitoring**: CloudWatch for logs and metrics

## 🚀 Quick Start

### Prerequisites
- AWS Account with appropriate permissions
- GitHub repository access
- Python 3.11+ for local development

### 1. Clone Repository
```bash
git clone https://github.com/mandarwaghmare997/Cutie.git
cd Cutie
```

### 2. Local Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp config/.env.example .env
# Edit .env with your configuration

# Run locally
python src/main.py
```

### 3. AWS Deployment

#### Configure GitHub Secrets
Go to Repository → Settings → Secrets and Variables → Actions:

```
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
ADMIN_EMAIL=your-admin@email.com
JWT_SECRET=your-super-secret-jwt-key-here
ENCRYPTION_KEY=your-32-character-encryption-key
```

#### Deploy to AWS
```bash
# Push to main branch triggers automatic deployment
git push origin main

# Or deploy manually
./scripts/deploy.sh --environment production --admin-email admin@yourcompany.com
```

## 📋 Assessment Workflow

### Stage 1: Requirements Gathering
- AI system overview and documentation
- Risk level assessment
- Data handling and privacy requirements

### Stage 2: Gap Assessment
- Compliance gap identification
- Priority matrix development
- Resource requirement analysis

### Stage 3: Policy Review
- Policy adequacy evaluation
- Alignment with ISO 42001 requirements
- Documentation review

### Stage 4: Implementation Status
- Control implementation assessment
- Operational process evaluation
- Evidence collection

### Stage 5: Internal Audit
- Comprehensive audit execution
- Finding documentation
- Corrective action planning

### Stage 6: Certification
- Compliance score calculation
- Professional certificate generation
- Continuous monitoring setup

## 🔧 Configuration

### Environment Variables
```bash
# Application Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Database Configuration
DATABASE_URL=your-database-url

# AWS Configuration
AWS_REGION=us-east-1
S3_BUCKET=your-s3-bucket
SES_REGION=us-east-1

# Security Configuration
ENCRYPTION_KEY=your-encryption-key
ADMIN_EMAIL=admin@yourcompany.com
```

### AWS Services Used
- **Lambda**: Serverless compute for API endpoints
- **DynamoDB**: NoSQL database for user and assessment data
- **S3**: Static website hosting and document storage
- **CloudFront**: Global CDN for fast content delivery
- **API Gateway**: RESTful API management
- **SES**: Email service for OTP and notifications
- **CloudWatch**: Monitoring and logging
- **IAM**: Identity and access management

## 📊 Monitoring & Analytics

### CloudWatch Dashboards
- API response times and error rates
- User registration and assessment completion metrics
- Certificate generation statistics
- System health and performance indicators

### Key Performance Indicators
- **User Engagement**: Registration to completion rate
- **System Performance**: Average response time < 2 seconds
- **Compliance Success**: Certificate generation rate > 85%
- **Cost Efficiency**: AWS free tier optimization

## 🔒 Security Features

### Data Protection
- **Encryption at Rest**: AES-256 encryption for sensitive data
- **Encryption in Transit**: TLS 1.3 for all communications
- **Access Control**: Role-based permissions and JWT authentication
- **Audit Logging**: Comprehensive activity tracking

### Compliance & Privacy
- **GDPR Compliant**: Data protection and user rights
- **ISO 27001 Aligned**: Information security management
- **SOC 2 Ready**: Security and availability controls
- **Regular Security Scans**: Automated vulnerability assessment

## 🧪 Testing

### Run Tests Locally
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Coverage report
pytest --cov=src --cov-report=html
```

### Load Testing
```bash
# Install artillery
npm install -g artillery

# Run load tests
artillery run tests/load-test.yml
```

## 📈 Scaling & Performance

### Current Capacity
- **Concurrent Users**: 1,000+
- **Assessments**: 10,000+ active
- **Response Time**: < 2 seconds average
- **Uptime**: 99.9% availability target

### Scaling Strategy
- **Auto-scaling**: Lambda functions scale automatically
- **Database**: DynamoDB on-demand scaling
- **CDN**: CloudFront global edge locations
- **Monitoring**: Real-time alerts and automated responses

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards
- **Python**: PEP 8 compliance with Black formatting
- **JavaScript**: ES6+ with ESLint configuration
- **Testing**: Minimum 80% code coverage required
- **Documentation**: Comprehensive docstrings and comments

## 📞 Support

### Documentation
- **API Documentation**: `/docs` endpoint when running locally
- **User Guide**: Comprehensive user manual included
- **Admin Guide**: Platform management documentation
- **Troubleshooting**: Common issues and solutions

### Contact
- **Email**: support@qryti.com
- **GitHub Issues**: [Create an issue](https://github.com/mandarwaghmare997/Cutie/issues)
- **Documentation**: [Wiki](https://github.com/mandarwaghmare997/Cutie/wiki)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **ISO/IEC 42001:2023**: International standard for AI management systems
- **AWS**: Cloud infrastructure and services
- **Flask Community**: Web framework and extensions
- **Open Source Contributors**: Various libraries and tools used

---

**Built with ❤️ by the Qryti Team**

*Transforming AI governance compliance from complex to simple.*

# Qryti Platform - Live Deployment Sat Jul  5 03:25:57 EDT 2025
