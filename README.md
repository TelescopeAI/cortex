# cortex

## Lightweight Modular Analytics Platform

A modular, lightweight analytics engine built in Python to power customer-facing analytics applications. The platform provides a unified semantic layer for defining business data models, a dynamic query engine that integrates with heterogeneous data sources, and a robust user management and authorization system—all accessible via a FastAPI-powered REST API.

## Overview

This platform is designed to abstract complex data sources into a business-friendly semantic layer. It enables developers to define data models in JSON (with YAML support planned), dynamically generate queries across multiple data sources, and securely expose analytics functionality to both admin/developer users and end users.

### Key Features

- **Semantic Layer**
  - Define and manage data models in JSON
  - Dynamic schema generation with plugin support
  - Versioning and audit trails (integrated with Git)

- **Query Engine**
  - Translates semantic definitions into optimized queries
  - Supports multi-source queries (SQL, NoSQL, files, APIs)
  - Integration with caching for enhanced performance

- **Data Source Integration**
  - Connectors for PostgreSQL, MySQL, BigQuery, Snowflake, MongoDB
  - Support for file-based sources (CSV, Excel, Google Sheets)

- **User Management & Authentication**
  - Admin/dev authentication using FastAPI and fastapi-users
  - End user authentication via JWT, mapped to local user records

- **Authorization**
  - Out-of-the-box RBAC with extensible hooks for dynamic, rule-based (ABAC-like) policies
  - Plugin interface for custom authorization logic

- **API-First Approach**
  - All functionality exposed via FastAPI-based REST endpoints
  - Clear separation of admin and end-user API flows

- **Caching & Performance**
  - Redis integration for caching query results and configuration data

- **Monitoring & Metrics**
  - Event logging and metrics aggregation to track system health

- **Automated Configuration**
  - Auto-detect and update semantic models based on underlying data source changes

- **Multi-Tenancy & Environment Isolation**
  - Workspace and environment-level isolation to support multiple tenants

## Architecture

The project follows a layered architecture within a monorepo, ensuring modularity, ease of maintenance, and independent evolution of key components.



