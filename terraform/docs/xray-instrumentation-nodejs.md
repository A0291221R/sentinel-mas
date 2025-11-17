# X-Ray Application Instrumentation (Node.js)

## Step 1: Install AWS X-Ray SDK

```bash
npm install aws-xray-sdk-core aws-xray-sdk-express
```

## Step 2: Instrument Your Express App

### For API Service (sentinel-mas-api)

```javascript
// src/index.js or app.js

const AWSXRay = require('aws-xray-sdk-core');
const express = require('express');

// Capture all AWS SDK calls
const AWS = AWSXRay.captureAWS(require('aws-sdk'));

// Capture all HTTP/HTTPS requests
const http = AWSXRay.captureHTTPs(require('http'));
const https = AWSXRay.captureHTTPs(require('https'));

const app = express();

// Add X-Ray middleware FIRST (before other middleware)
app.use(AWSXRay.express.openSegment(process.env.AWS_XRAY_TRACING_NAME || 'sentinel-mas-api'));

// Your existing middleware
app.use(express.json());
app.use(cors());

// Your routes
app.get('/api/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.post('/api/tasks', async (req, res) => {
  // X-Ray automatically traces this request
  // Add custom subsegments for specific operations
  
  const segment = AWSXRay.getSegment();
  const subsegment = segment.addNewSubsegment('process-task');
  
  try {
    // Your business logic here
    const result = await processTask(req.body);
    
    subsegment.addAnnotation('taskType', req.body.type);
    subsegment.addMetadata('taskData', req.body);
    
    subsegment.close();
    res.json(result);
  } catch (error) {
    subsegment.addError(error);
    subsegment.close();
    throw error;
  }
});

// Close X-Ray segment LAST (after all other middleware)
app.use(AWSXRay.express.closeSegment());

// Error handler
app.use((err, req, res, next) => {
  const segment = AWSXRay.getSegment();
  if (segment) {
    segment.addError(err);
  }
  res.status(500).json({ error: err.message });
});

app.listen(3000, () => {
  console.log('API server running on port 3000');
});
```

### For Central Service (sentinel-mas-central)

```javascript
// src/index.js

const AWSXRay = require('aws-xray-sdk-core');
const express = require('express');
const axios = require('axios');

// Capture AWS SDK
const AWS = AWSXRay.captureAWS(require('aws-sdk'));

// Capture HTTP clients
AWSXRay.captureHTTPsGlobal(require('http'));
AWSXRay.captureHTTPsGlobal(require('https'));

const app = express();

app.use(AWSXRay.express.openSegment('sentinel-mas-central'));
app.use(express.json());

// Example: Trace database queries
app.get('/central/data', async (req, res) => {
  const segment = AWSXRay.getSegment();
  const dbSegment = segment.addNewSubsegment('database-query');
  
  try {
    // Your database query
    const data = await db.query('SELECT * FROM tasks');
    
    dbSegment.addAnnotation('query', 'SELECT tasks');
    dbSegment.addMetadata('rowCount', data.length);
    dbSegment.close();
    
    res.json(data);
  } catch (error) {
    dbSegment.addError(error);
    dbSegment.close();
    throw error;
  }
});

// Example: Trace external API calls
app.get('/central/external', async (req, res) => {
  const segment = AWSXRay.getSegment();
  const apiSegment = segment.addNewSubsegment('external-api');
  
  try {
    // axios calls are automatically traced
    const response = await axios.get('https://api.example.com/data');
    
    apiSegment.addAnnotation('endpoint', 'example-api');
    apiSegment.addMetadata('responseSize', response.data.length);
    apiSegment.close();
    
    res.json(response.data);
  } catch (error) {
    apiSegment.addError(error);
    apiSegment.close();
    throw error;
  }
});

app.use(AWSXRay.express.closeSegment());

app.listen(4000, () => {
  console.log('Central server running on port 4000');
});
```

## Step 3: Update Dockerfile

Add X-Ray SDK to your package.json or install in Dockerfile:

```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# X-Ray SDK is already installed via package.json

EXPOSE 3000

CMD ["node", "src/index.js"]
```

## Step 4: Environment Variables

Ensure these are set in your ECS task definition:

```bash
AWS_XRAY_DAEMON_ADDRESS=xray-daemon:2000
AWS_XRAY_TRACING_NAME=sentinel-mas-api  # or central
AWS_REGION=ap-southeast-1
```

## Advanced: Custom Annotations and Metadata

```javascript
// Annotations (indexed, searchable)
segment.addAnnotation('userId', req.user.id);
segment.addAnnotation('environment', process.env.NODE_ENV);
segment.addAnnotation('customerId', req.body.customerId);

// Metadata (not indexed, detailed info)
segment.addMetadata('requestBody', req.body);
segment.addMetadata('headers', req.headers);
segment.addMetadata('responseTime', Date.now() - startTime);
```

## Tracing Database Queries (PostgreSQL example)

```javascript
const { Pool } = require('pg');
const AWSXRay = require('aws-xray-sdk-core');

const pool = new Pool({
  host: process.env.DB_HOST,
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
});

// Wrap query function with X-Ray
async function query(text, params) {
  const segment = AWSXRay.getSegment();
  const subsegment = segment.addNewSubsegment('postgres-query');
  
  subsegment.addAnnotation('database', 'postgresql');
  subsegment.addMetadata('query', text);
  
  try {
    const result = await pool.query(text, params);
    subsegment.addMetadata('rowCount', result.rowCount);
    subsegment.close();
    return result;
  } catch (error) {
    subsegment.addError(error);
    subsegment.close();
    throw error;
  }
}

module.exports = { query };
```

## Viewing Traces in AWS Console

1. Go to AWS X-Ray Console
2. Click "Traces" to see individual requests
3. Click "Service Map" to see your microservices architecture
4. Use filters: `annotation.userId = "123"` or `http.status = 500`

## Best Practices

1. **Always add annotations for searchable data** (user IDs, customer IDs, etc.)
2. **Use metadata for detailed debugging info** (full request bodies, etc.)
3. **Create subsegments for important operations** (DB queries, API calls)
4. **Always close subsegments** in try/finally blocks
5. **Set sampling rate appropriately** (5-10% for production, 100% for dev)
