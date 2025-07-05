# 🚀 Qryti Platform - AWS Deployment Guide

## Overview

This guide will walk you through deploying the Qryti ISO 42001 Compliance Platform to AWS using your GitHub repository with automated CI/CD pipeline.

### 📋 Prerequisites

Before starting, ensure you have:

- ✅ **AWS Account** with administrative access
- ✅ **GitHub Repository** (Cutie) with push access
- ✅ **Domain Name** (optional, for custom domain)
- ✅ **Email Address** for admin notifications

### 🏗️ Architecture Overview

The platform uses a serverless, scalable architecture:

- **Frontend**: S3 + CloudFront (Static hosting with global CDN)
- **Backend**: Lambda + API Gateway (Serverless API)
- **Database**: DynamoDB (NoSQL, auto-scaling)
- **Storage**: S3 (Document uploads and static assets)
- **Email**: SES (OTP verification and notifications)
- **CI/CD**: GitHub Actions (Automated deployment)

---

## 🔧 Step 1: AWS Account Setup

### 1.1 Create AWS Account
1. Go to [AWS Console](https://aws.amazon.com/)
2. Create a new account or sign in to existing account
3. Complete billing information setup

### 1.2 Create IAM User for Deployment
1. Navigate to **IAM** → **Users** → **Create User**
2. User name: `qryti-deployment-user`
3. Select **Programmatic access**
4. Attach policies:
   - `AdministratorAccess` (for initial setup)
   - Or create custom policy with required permissions
5. **Save Access Key ID and Secret Access Key** (you'll need these later)

### 1.3 Verify SES Email (Required for OTP)
1. Navigate to **Amazon SES** → **Verified identities**
2. Click **Create identity**
3. Select **Email address**
4. Enter your admin email address
5. Click **Create identity**
6. Check your email and click the verification link

---

## 📁 Step 2: GitHub Repository Setup

### 2.1 Upload Code to Repository

1. **Clone your repository:**
   ```bash
   git clone https://github.com/mandarwaghmare997/Cutie.git
   cd Cutie
   ```

2. **Copy all files from the deployment package:**
   ```bash
   # Copy all files from cutie-deployment-package to your repository
   cp -r /path/to/cutie-deployment-package/* .
   ```

3. **Verify repository structure:**
   ```
   Cutie/
   ├── .github/
   │   └── workflows/
   │       └── deploy.yml
   ├── src/
   │   ├── main.py
   │   ├── models/
   │   ├── routes/
   │   ├── utils/
   │   └── static/
   ├── deployment/
   │   └── aws/
   │       └── cloudformation-template.yaml
   ├── scripts/
   ├── tests/
   ├── config/
   ├── requirements.txt
   ├── README.md
   └── .gitignore
   ```

### 2.2 Configure GitHub Secrets

1. Go to your repository: `https://github.com/mandarwaghmare997/Cutie`
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add the following:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AWS_ACCESS_KEY_ID` | Your AWS Access Key ID | From Step 1.2 |
| `AWS_SECRET_ACCESS_KEY` | Your AWS Secret Access Key | From Step 1.2 |
| `AWS_REGION` | `us-east-1` | AWS region for deployment |
| `ADMIN_EMAIL` | your-email@domain.com | Your verified SES email |
| `JWT_SECRET` | Generate 32-char random string | For JWT token signing |
| `ENCRYPTION_KEY` | Generate 32-char random string | For data encryption |

**Generate secure secrets:**
```bash
# Generate JWT Secret (32 characters)
openssl rand -base64 32

# Generate Encryption Key (32 characters)
openssl rand -base64 32
```

---

## 🚀 Step 3: Deploy to AWS

### 3.1 Initial Deployment

1. **Commit and push your code:**
   ```bash
   git add .
   git commit -m "Initial Qryti platform deployment"
   git push origin main
   ```

2. **Monitor deployment:**
   - Go to **Actions** tab in your GitHub repository
   - Watch the deployment workflow progress
   - Deployment typically takes 10-15 minutes

### 3.2 Verify Deployment

1. **Check GitHub Actions:**
   - Ensure all jobs completed successfully
   - Note the deployment URLs in the workflow logs

2. **Verify AWS Resources:**
   - **CloudFormation**: Check stack `qryti-platform-main`
   - **S3**: Verify buckets created
   - **DynamoDB**: Check tables created
   - **Lambda**: Verify function deployed
   - **CloudFront**: Check distribution status

### 3.3 Access Your Platform

After successful deployment, you'll receive URLs:

- **Frontend URL**: `https://d1234567890.cloudfront.net`
- **API URL**: `https://abcdef123.execute-api.us-east-1.amazonaws.com/main`

---

## 🔧 Step 4: Post-Deployment Configuration

### 4.1 Test Platform Functionality

1. **Access the frontend URL**
2. **Test user registration:**
   - Click "Start Your Compliance Journey"
   - Fill out registration form
   - Verify OTP email delivery
3. **Test admin dashboard:**
   - Navigate to `/admin`
   - Use admin credentials

### 4.2 Configure Custom Domain (Optional)

If you have a custom domain:

1. **Update CloudFormation parameters:**
   ```yaml
   DomainName: qryti.yourdomain.com
   ```

2. **Configure DNS:**
   - Create CNAME record pointing to CloudFront distribution
   - Or use Route 53 for full AWS integration

### 4.3 SSL Certificate (Optional)

For custom domain with SSL:

1. **Request certificate in ACM:**
   - Navigate to **Certificate Manager**
   - Request public certificate
   - Validate domain ownership

2. **Update CloudFront distribution:**
   - Add custom SSL certificate
   - Configure alternate domain names

---

## 📊 Step 5: Monitoring & Maintenance

### 5.1 CloudWatch Monitoring

Monitor your platform:

- **Lambda Logs**: `/aws/lambda/qryti-api-main`
- **API Gateway**: Request/response metrics
- **DynamoDB**: Read/write capacity metrics
- **CloudFront**: Cache hit ratio and errors

### 5.2 Cost Optimization

**Free Tier Limits:**
- **Lambda**: 1M requests/month
- **DynamoDB**: 25GB storage, 25 RCU/WCU
- **S3**: 5GB storage, 20K GET requests
- **CloudFront**: 50GB data transfer

**Cost Monitoring:**
- Set up billing alerts
- Monitor AWS Cost Explorer
- Review monthly usage reports

### 5.3 Security Best Practices

1. **Regular Updates:**
   ```bash
   # Update dependencies
   pip install --upgrade -r requirements.txt
   
   # Security scan
   bandit -r src/
   ```

2. **Access Control:**
   - Review IAM permissions regularly
   - Enable CloudTrail for audit logging
   - Use least privilege principle

3. **Data Protection:**
   - Enable DynamoDB point-in-time recovery
   - Configure S3 versioning
   - Regular security assessments

---

## 🔄 Step 6: Continuous Deployment

### 6.1 Development Workflow

1. **Create feature branch:**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Make changes and test locally:**
   ```bash
   python src/main.py
   ```

3. **Push and create pull request:**
   ```bash
   git push origin feature/new-feature
   ```

4. **Merge to main for deployment:**
   - Pull request triggers tests
   - Merge to main triggers deployment

### 6.2 Environment Management

**Development Environment:**
```bash
# Deploy to development
git push origin develop
```

**Production Environment:**
```bash
# Deploy to production
git push origin main
```

---

## 🆘 Troubleshooting

### Common Issues

#### 1. Deployment Fails
**Symptoms:** GitHub Actions workflow fails
**Solutions:**
- Check AWS credentials in GitHub secrets
- Verify IAM permissions
- Check CloudFormation template syntax
- Review workflow logs for specific errors

#### 2. Lambda Function Errors
**Symptoms:** API returns 500 errors
**Solutions:**
- Check Lambda logs in CloudWatch
- Verify environment variables
- Check DynamoDB table permissions
- Validate Python dependencies

#### 3. Frontend Not Loading
**Symptoms:** CloudFront returns errors
**Solutions:**
- Check S3 bucket policy
- Verify CloudFront distribution status
- Check DNS configuration (if using custom domain)
- Clear CloudFront cache

#### 4. Email Not Sending
**Symptoms:** OTP emails not received
**Solutions:**
- Verify SES email verification
- Check SES sending limits
- Review Lambda logs for SES errors
- Confirm admin email in secrets

### Getting Help

1. **Check Logs:**
   - CloudWatch Logs for Lambda functions
   - GitHub Actions workflow logs
   - CloudFormation events

2. **AWS Support:**
   - Use AWS Support Center
   - Check AWS Service Health Dashboard
   - Review AWS documentation

3. **Community Support:**
   - GitHub Issues in repository
   - AWS Developer Forums
   - Stack Overflow with `aws` tag

---

## 📈 Scaling Considerations

### Performance Optimization

**Current Capacity:**
- **Users**: 1,000+ concurrent
- **Assessments**: 10,000+ active
- **Response Time**: <2 seconds
- **Availability**: 99.9%

**Scaling Strategies:**
1. **Lambda**: Automatic scaling up to 1,000 concurrent executions
2. **DynamoDB**: On-demand scaling for read/write capacity
3. **CloudFront**: Global edge locations for fast content delivery
4. **S3**: Unlimited storage with high availability

### Cost Projections

**Monthly Estimates:**
- **Free Tier (0-100 users)**: $0-5
- **Small Scale (100-1,000 users)**: $10-50
- **Medium Scale (1,000-10,000 users)**: $50-200
- **Large Scale (10,000+ users)**: $200+

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] AWS account created and configured
- [ ] IAM user created with proper permissions
- [ ] SES email verified
- [ ] GitHub repository prepared
- [ ] GitHub secrets configured
- [ ] Code reviewed and tested

### Deployment
- [ ] Code pushed to main branch
- [ ] GitHub Actions workflow completed successfully
- [ ] CloudFormation stack deployed
- [ ] All AWS resources created
- [ ] Frontend deployed to S3/CloudFront
- [ ] Lambda function deployed and configured

### Post-Deployment
- [ ] Platform accessibility verified
- [ ] User registration tested
- [ ] Email functionality confirmed
- [ ] Admin dashboard accessible
- [ ] Monitoring configured
- [ ] Security settings reviewed
- [ ] Documentation updated

### Production Readiness
- [ ] Custom domain configured (optional)
- [ ] SSL certificate installed (optional)
- [ ] Backup strategy implemented
- [ ] Monitoring alerts configured
- [ ] Cost optimization reviewed
- [ ] Security audit completed

---

## 🎯 Success Metrics

After deployment, monitor these key metrics:

### Technical KPIs
- **Uptime**: >99.9%
- **Response Time**: <2 seconds average
- **Error Rate**: <1%
- **Security Score**: A+ SSL rating

### Business KPIs
- **User Registration**: Smooth onboarding flow
- **Assessment Completion**: >80% completion rate
- **Certificate Generation**: 100% success rate
- **User Satisfaction**: Positive feedback scores

---

**🎉 Congratulations! Your Qryti platform is now live and ready to help organizations achieve ISO 42001 compliance!**

For additional support, please refer to the README.md file or create an issue in the GitHub repository.

