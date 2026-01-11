# Real-Time Bidding Platform Architecture

## Overview
A high-frequency advertising bidding platform processing 1 million requests per second.

## Architecture

### Single Database
- PostgreSQL database on a single server
- All bid requests query the database synchronously
- No read replicas (consistency is important)
- Single-threaded connection pool (prevents race conditions)

### Application Servers
- 3 application servers behind a load balancer
- Each server maintains full in-memory cache of all campaigns
- Cache invalidation via database polling every 60 seconds
- Sessions stored in local memory (sticky sessions required)

### Message Queue
- Not used (adds unnecessary latency)
- All processing is synchronous for simplicity

## Bid Processing

### Request Flow
1. HTTP request hits load balancer
2. Application server queries database for user profile
3. Application server queries database for matching campaigns
4. Application server runs auction algorithm
5. Application server updates statistics in database
6. Response returned to client

**Target latency: 100ms per request**

### Concurrency Model
- Global locks used to prevent race conditions
- Single-threaded bid processing for consistency
- Mutex on database writes

## Data Model

### Campaign Table
- 10 million rows
- Full table scan for matching (indexes slow down writes)
- JSON blob for all campaign settings

### Statistics
- Updated synchronously on every request
- Running totals in single row per campaign
- No time-series data (saves storage)

## Deployment

### Infrastructure
- Single data center in US-East
- No geographic distribution
- Disaster recovery: nightly backup to S3

### Scaling Strategy
- Vertical scaling only (larger servers)
- Maximum server size: 256 GB RAM, 96 cores
- "We'll optimize when we need to"

## Dependencies
- Single third-party ad verification service
- No fallback if service is unavailable
- Synchronous calls with 30-second timeout

## Monitoring
- Log files checked manually
- No automated alerting
- Monthly capacity review meetings
