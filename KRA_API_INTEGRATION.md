# KRA API Integration Guide

## Overview

Rafiki.ai now includes full integration with the Kenya Revenue Authority (KRA) iTax API, allowing users to:
- ✅ Verify KRA PIN validity
- ✅ Check tax compliance status
- ✅ Get taxpayer details
- ✅ Request compliance certificates

## Setup Instructions

### 1. Obtain KRA API Credentials

To use the KRA integration, you need to obtain API credentials from KRA:

1. Visit [KRA iTax Portal](https://itax.kra.go.ke)
2. Register for API access through the iTax portal
3. Submit an API access request form
4. Await approval from KRA (typically 5-10 business days)
5. Once approved, you'll receive:
   - **Client ID** - OAuth2 client identifier
   - **Client Secret** - OAuth2 client secret
   - **API Key** (optional) - Additional authentication key

### 2. Configure Environment Variables

Add the following to your `.env` file:

```bash
# KRA (Kenya Revenue Authority) API
KRA_API_URL=https://itax.kra.go.ke/api
KRA_CLIENT_ID=your-kra-client-id-here
KRA_CLIENT_SECRET=your-kra-client-secret-here
KRA_API_KEY=your-kra-api-key-here  # Optional
KRA_ENABLED=true
```

### 3. Restart Backend Server

```bash
cd /home/subchief/5TECH
./start.sh
```

The backend will automatically initialize the KRA service on startup.

## API Endpoints

All KRA endpoints are available at `http://localhost:8000/kra/`

### 1. Verify KRA PIN

**Endpoint:** `POST /kra/verify-pin`

Verifies if a KRA PIN is valid and retrieves basic taxpayer information.

**Request:**
```json
{
  "pin": "A123456789B"
}
```

**Response:**
```json
{
  "success": true,
  "pin": "A123456789B",
  "valid": true,
  "taxpayer_name": "John Doe",
  "registration_date": "2020-01-15",
  "status": "Active",
  "taxpayer_type": "Individual",
  "message": "KRA PIN verified successfully"
}
```

**KRA PIN Format:**
- **Individual PINs:** Start with `A` (e.g., A123456789B)
- **Company PINs:** Start with `P` (e.g., P987654321Z)
- Format: `[A/P] + 9 digits + 1 letter`

### 2. Check Tax Compliance

**Endpoint:** `POST /kra/check-compliance`

Checks the tax compliance status for a given KRA PIN.

**Request:**
```json
{
  "pin": "A123456789B"
}
```

**Response:**
```json
{
  "success": true,
  "pin": "A123456789B",
  "compliant": true,
  "compliance_status": "Fully Compliant",
  "outstanding_returns": [],
  "outstanding_taxes": 0.0,
  "last_return_date": "2025-01-05",
  "certificate_valid": true,
  "message": "Compliance status retrieved successfully"
}
```

### 3. Get Taxpayer Details

**Endpoint:** `POST /kra/taxpayer-details`

Retrieves detailed information about a taxpayer.

**Request:**
```json
{
  "pin": "A123456789B"
}
```

**Response:**
```json
{
  "success": true,
  "pin": "A123456789B",
  "taxpayer_name": "John Doe",
  "taxpayer_type": "Individual",
  "registration_date": "2020-01-15",
  "postal_address": "P.O. Box 12345, Nairobi",
  "physical_address": "123 Main Street, Nairobi",
  "email": "john@example.com",
  "phone": "+254712345678",
  "business_nature": "Software Development",
  "status": "Active",
  "message": "Taxpayer details retrieved successfully"
}
```

### 4. Request Compliance Certificate

**Endpoint:** `POST /kra/request-compliance-certificate`

Requests a tax compliance certificate from KRA.

**Request:**
```json
{
  "pin": "A123456789B",
  "email": "john@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Compliance certificate request submitted successfully",
  "request_id": "CC-2025-12345",
  "status": "Pending",
  "estimated_time": "2-5 business days"
}
```

### 5. Check Service Status

**Endpoint:** `GET /kra/status`

Checks if KRA service is enabled and operational.

**Response:**
```json
{
  "enabled": true,
  "initialized": true,
  "api_url": "https://itax.kra.go.ke/api",
  "message": "KRA service is operational"
}
```

## Testing the Integration

Run the test script to verify your KRA integration:

```bash
cd /home/subchief/5TECH
source sadtalker/bin/activate
python backend/test_kra_integration.py
```

This will:
- ✓ Check KRA configuration
- ✓ Test PIN format validation
- ✓ Test API connectivity (requires credentials)
- ✓ Verify all endpoints are working

## Using via Dialogflow

Users can interact with KRA services through voice or text:

**Example Conversations:**

```
User: "I want to verify my KRA PIN"
Rafiki: "Sure! Please provide your KRA PIN number."
User: "A123456789B"
Rafiki: "Let me verify that for you... Your KRA PIN A123456789B is valid and 
         registered to John Doe. Your account status is Active."

User: "Check my tax compliance"
Rafiki: "Please provide your KRA PIN to check compliance status."
User: "A123456789B"
Rafiki: "Great news! You are fully tax compliant with KRA. No outstanding 
         returns or taxes. Your last return was filed on 5th January 2025."

User: "I need a compliance certificate"
Rafiki: "I can help you request a tax compliance certificate. Please provide 
         your KRA PIN and email address."
User: "My PIN is A123456789B and email is john@example.com"
Rafiki: "Your compliance certificate request has been submitted successfully. 
         Request ID: CC-2025-12345. You'll receive it at john@example.com 
         within 2-5 business days."
```

## API Documentation

Once the backend is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Navigate to the "KRA" section to see all endpoints with interactive testing.

## Security Considerations

1. **Credential Storage:** KRA API credentials are stored in `.env` file (not committed to git)
2. **OAuth2 Authentication:** Uses secure OAuth2 client credentials flow
3. **PIN Privacy:** KRA PINs are masked in logs (only first 3 and last 2 characters shown)
4. **HTTPS Only:** In production, always use HTTPS for KRA API calls
5. **Rate Limiting:** Implement rate limiting to prevent API abuse

## Troubleshooting

### "KRA service not enabled"
- Set `KRA_ENABLED=true` in `.env` file
- Restart backend server

### "Authentication failed"
- Verify `KRA_CLIENT_ID` and `KRA_CLIENT_SECRET` are correct
- Ensure credentials haven't expired
- Contact KRA support if issues persist

### "Service not initialized"
- Check all required environment variables are set
- Review backend logs for initialization errors
- Ensure KRA API URL is correct

### "PIN not found"
- Verify PIN format is correct (A/P + 9 digits + letter)
- Check if PIN is registered with KRA
- Try the PIN on iTax portal to confirm it exists

## Production Deployment

When deploying to production:

1. **Use Environment Variables:** Never hardcode credentials
2. **Enable HTTPS:** Ensure all API calls use HTTPS
3. **Monitor Usage:** Track API call volume and compliance
4. **Implement Caching:** Cache PIN verification results (with expiry)
5. **Error Handling:** Implement robust error handling and retries
6. **Logging:** Log all KRA transactions for audit purposes

## Support

For KRA API-related issues:
- **KRA Support:** support@kra.go.ke
- **iTax Helpline:** 0711-099-999
- **Developer Portal:** https://itax.kra.go.ke/developer

For Rafiki.ai integration issues:
- Check backend logs: `/tmp/backend.log`
- Review API documentation: http://localhost:8000/docs
- Run test script: `python backend/test_kra_integration.py`

## License & Compliance

- This integration complies with KRA API usage policies
- Ensure you have proper authorization before accessing taxpayer data
- Follow KRA data protection and privacy guidelines
- Maintain audit logs of all KRA API transactions
