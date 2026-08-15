# API Design

## 1. Overview

This document defines the REST API design for the InsightIQ platform. The API is designed to be secure, versioned, consistent, and production-ready for cloud-native SaaS usage. All endpoints are exposed under the versioned base path /api/v1/.

The API is organized around core platform capabilities including authentication, organization and user management, datasets, analytics, machine learning predictions, reporting, dashboard access, notifications, and system administration.

---

## 2. Design Goals

- Provide a consistent and predictable REST interface
- Ensure secure access through JWT-based authentication and RBAC
- Support enterprise-grade request validation and error handling
- Support future extension without breaking consumers
- Enable clear separation between functional modules
- Support pagination, filtering, sorting, and asynchronous processing where needed

---

## 3. API Conventions

### Base URL

- /api/v1/

### Naming Conventions

- Resource names use lowercase plural nouns
- Endpoint paths are kebab-case where needed
- Query parameters use descriptive names
- Response payloads use consistent key naming in snake_case

### Standard Headers

- Authorization: Bearer <token>
- Content-Type: application/json
- Accept: application/json
- X-Request-ID: optional client-supplied correlation identifier

### Pagination

- Default page size: 20
- Maximum page size: 100
- Query parameters: page, page_size

### Sorting

- Query parameter: sort_by
- Direction: sort_order=asc|desc

### Filtering

- Query parameters vary by resource
- Example: status=active, organization_id=uuid

---

## 4. Authentication and Identity APIs

### 4.1 Register User

- Endpoint Name: Register User
- Method: POST
- URL: /api/v1/auth/register
- Description: Registers a new user account and creates a pending verification state.
- Authentication Required: No
- User Roles Allowed: All
- Headers: Content-Type, Accept
- Path Parameters: None
- Query Parameters: None
- Request Body:
  - email
  - password
  - full_name
  - organization_slug (optional)
- Validation Rules:
  - email must be valid
  - password must meet complexity requirements
  - organization_slug must be valid if provided
- Response Body:
  - user_id
  - email
  - status
  - message
- Success Response: 201 Created
- Error Responses:
  - 400 Invalid request
  - 409 Conflict for duplicate email or organization slug
  - 422 Validation error
- Status Codes: 201, 400, 409, 422
- Rate Limiting: 5 requests per minute per IP

### 4.2 Login

- Endpoint Name: Login User
- Method: POST
- URL: /api/v1/auth/login
- Description: Authenticates a user and issues access and refresh tokens.
- Authentication Required: No
- User Roles Allowed: All
- Headers: Content-Type, Accept
- Path Parameters: None
- Query Parameters: None
- Request Body:
  - email
  - password
- Validation Rules:
  - credentials must be present
  - account must be active and verified
- Response Body:
  - access_token
  - refresh_token
  - token_type
  - expires_in
  - user
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
  - 422 Validation error
- Status Codes: 200, 401, 403, 422
- Rate Limiting: 10 requests per minute per IP

### 4.3 Refresh Token

- Endpoint Name: Refresh Access Token
- Method: POST
- URL: /api/v1/auth/refresh
- Description: Issues a new access token using a valid refresh token.
- Authentication Required: No
- User Roles Allowed: All
- Headers: Content-Type, Accept
- Path Parameters: None
- Query Parameters: None
- Request Body:
  - refresh_token
- Validation Rules:
  - refresh token must be valid and not expired
- Response Body:
  - access_token
  - expires_in
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
- Status Codes: 200, 401, 403
- Rate Limiting: 20 requests per minute per IP

### 4.4 Logout

- Endpoint Name: Logout User
- Method: POST
- URL: /api/v1/auth/logout
- Description: Invalidates the current session or revokes access tokens.
- Authentication Required: Yes
- User Roles Allowed: All authenticated users
- Headers: Authorization, Content-Type
- Path Parameters: None
- Query Parameters: None
- Request Body: None
- Validation Rules: None
- Response Body:
  - message
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
- Status Codes: 200, 401
- Rate Limiting: 10 requests per minute per user

### 4.5 Forgot Password

- Endpoint Name: Forgot Password
- Method: POST
- URL: /api/v1/auth/forgot-password
- Description: Initiates a password reset flow.
- Authentication Required: No
- User Roles Allowed: All
- Headers: Content-Type, Accept
- Path Parameters: None
- Query Parameters: None
- Request Body:
  - email
- Validation Rules:
  - email must exist in the system
- Response Body:
  - message
- Success Response: 200 OK
- Error Responses:
  - 404 Not Found
  - 422 Validation error
- Status Codes: 200, 404, 422
- Rate Limiting: 3 requests per minute per IP

### 4.6 Reset Password

- Endpoint Name: Reset Password
- Method: POST
- URL: /api/v1/auth/reset-password
- Description: Completes password reset using a valid token.
- Authentication Required: No
- User Roles Allowed: All
- Headers: Content-Type, Accept
- Path Parameters: None
- Query Parameters: None
- Request Body:
  - token
  - new_password
- Validation Rules:
  - token must be valid and unexpired
  - new password must meet policy
- Response Body:
  - message
- Success Response: 200 OK
- Error Responses:
  - 400 Bad Request
  - 401 Unauthorized
- Status Codes: 200, 400, 401
- Rate Limiting: 5 requests per minute per IP

### 4.7 Verify Email

- Endpoint Name: Verify Email
- Method: POST
- URL: /api/v1/auth/verify-email
- Description: Verifies a user’s email address using a one-time token.
- Authentication Required: No
- User Roles Allowed: All
- Headers: Content-Type, Accept
- Path Parameters: None
- Query Parameters: None
- Request Body:
  - token
- Validation Rules:
  - token must be valid
- Response Body:
  - message
- Success Response: 200 OK
- Error Responses:
  - 400 Bad Request
  - 401 Unauthorized
- Status Codes: 200, 400, 401
- Rate Limiting: 5 requests per minute per IP

---

## 5. Organization APIs

### 5.1 List Organizations

- Endpoint Name: List Organizations
- Method: GET
- URL: /api/v1/organizations
- Description: Lists organizations accessible to the current user.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager
- Headers: Authorization, Accept
- Path Parameters: None
- Query Parameters: page, page_size, status, search
- Request Body: None
- Validation Rules: None
- Response Body:
  - items
  - page
  - page_size
  - total
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
- Status Codes: 200, 401, 403

### 5.2 Get Organization

- Endpoint Name: Get Organization
- Method: GET
- URL: /api/v1/organizations/{organization_id}
- Description: Returns organization details for a given organization.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst, Viewer depending on scope
- Headers: Authorization, Accept
- Path Parameters:
  - organization_id
- Query Parameters: None
- Request Body: None
- Validation Rules:
  - organization_id must be a valid UUID
- Response Body:
  - organization object
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
- Status Codes: 200, 401, 403, 404

### 5.3 Create Organization

- Endpoint Name: Create Organization
- Method: POST
- URL: /api/v1/organizations
- Description: Creates a new organization.
- Authentication Required: Yes
- User Roles Allowed: Administrator
- Headers: Authorization, Content-Type
- Path Parameters: None
- Query Parameters: None
- Request Body:
  - name
  - slug
  - industry
- Validation Rules:
  - name and slug are required
  - slug must be unique
- Response Body:
  - organization object
- Success Response: 201 Created
- Error Responses:
  - 400 Bad Request
  - 401 Unauthorized
  - 403 Forbidden
  - 409 Conflict
- Status Codes: 201, 400, 401, 403, 409

---

## 6. User and Role APIs

### 6.1 List Users

- Endpoint Name: List Users
- Method: GET
- URL: /api/v1/users
- Description: Lists users within an organization.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager
- Headers: Authorization, Accept
- Path Parameters: None
- Query Parameters: page, page_size, status, search
- Request Body: None
- Validation Rules: None
- Response Body:
  - items
  - page
  - page_size
  - total
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
- Status Codes: 200, 401, 403

### 6.2 Get User

- Endpoint Name: Get User
- Method: GET
- URL: /api/v1/users/{user_id}
- Description: Returns a specific user profile.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Self
- Headers: Authorization, Accept
- Path Parameters:
  - user_id
- Query Parameters: None
- Request Body: None
- Validation Rules:
  - user_id must be valid
- Response Body:
  - user object
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
- Status Codes: 200, 401, 403, 404

### 6.3 Update User

- Endpoint Name: Update User
- Method: PATCH
- URL: /api/v1/users/{user_id}
- Description: Updates a user’s profile or role assignment.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Self
- Headers: Authorization, Content-Type
- Path Parameters:
  - user_id
- Query Parameters: None
- Request Body:
  - full_name
  - status
  - role_ids
- Validation Rules:
  - role assignment must be valid
  - status must be allowed
- Response Body:
  - user object
- Success Response: 200 OK
- Error Responses:
  - 400 Bad Request
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
- Status Codes: 200, 400, 401, 403, 404

### 6.4 List Roles

- Endpoint Name: List Roles
- Method: GET
- URL: /api/v1/roles
- Description: Lists available roles in the system.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager
- Headers: Authorization, Accept
- Path Parameters: None
- Query Parameters: None
- Request Body: None
- Validation Rules: None
- Response Body:
  - items
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
- Status Codes: 200, 401, 403

---

## 7. Dataset Management APIs

### 7.1 Upload Dataset

- Endpoint Name: Upload Dataset
- Method: POST
- URL: /api/v1/datasets/upload
- Description: Uploads a CSV or Excel file for validation and analysis.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst
- Headers: Authorization, Content-Type
- Path Parameters: None
- Query Parameters: name, description
- Request Body: multipart/form-data containing file
- Validation Rules:
  - file type must be csv or xlsx
  - file size must be within configured limits
- Response Body:
  - dataset_id
  - status
  - message
- Success Response: 201 Created
- Error Responses:
  - 400 Bad Request
  - 401 Unauthorized
  - 413 Payload Too Large
  - 422 Validation error
- Status Codes: 201, 400, 401, 413, 422
- Rate Limiting: 20 requests per minute per user

### 7.2 List Datasets

- Endpoint Name: List Datasets
- Method: GET
- URL: /api/v1/datasets
- Description: Lists datasets available to the current user.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst, Viewer
- Headers: Authorization, Accept
- Path Parameters: None
- Query Parameters: page, page_size, status, search
- Request Body: None
- Validation Rules: None
- Response Body:
  - items
  - page
  - page_size
  - total
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
- Status Codes: 200, 401, 403

### 7.3 Get Dataset Details

- Endpoint Name: Get Dataset Details
- Method: GET
- URL: /api/v1/datasets/{dataset_id}
- Description: Returns metadata and current status for a dataset.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst, Viewer
- Headers: Authorization, Accept
- Path Parameters:
  - dataset_id
- Query Parameters: include=metadata,version_history
- Request Body: None
- Validation Rules:
  - dataset_id must be valid
- Response Body:
  - dataset object
  - metadata
  - version_history
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
- Status Codes: 200, 401, 403, 404

### 7.4 Delete Dataset

- Endpoint Name: Delete Dataset
- Method: DELETE
- URL: /api/v1/datasets/{dataset_id}
- Description: Soft deletes a dataset and marks it as inactive.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager
- Headers: Authorization
- Path Parameters:
  - dataset_id
- Query Parameters: None
- Request Body: None
- Validation Rules:
  - dataset_id must be valid
- Response Body:
  - message
- Success Response: 200 OK or 204 No Content
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
- Status Codes: 200, 401, 403, 404

### 7.5 Dataset Version History

- Endpoint Name: List Dataset Versions
- Method: GET
- URL: /api/v1/datasets/{dataset_id}/versions
- Description: Returns the version history for a dataset.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst, Viewer
- Headers: Authorization, Accept
- Path Parameters:
  - dataset_id
- Query Parameters: page, page_size
- Request Body: None
- Validation Rules:
  - dataset_id must be valid
- Response Body:
  - items
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
- Status Codes: 200, 401, 403, 404

### 7.6 Download Dataset

- Endpoint Name: Download Dataset
- Method: GET
- URL: /api/v1/datasets/{dataset_id}/download
- Description: Returns a downloadable copy of the dataset or selected version.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst, Viewer
- Headers: Authorization, Accept
- Path Parameters:
  - dataset_id
- Query Parameters: version_id
- Request Body: None
- Validation Rules:
  - dataset_id must be valid
- Response Body:
  - file stream or signed download link
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
- Status Codes: 200, 401, 403, 404

---

## 8. Data Validation APIs

### 8.1 Validate Dataset

- Endpoint Name: Validate Dataset
- Method: POST
- URL: /api/v1/datasets/{dataset_id}/validate
- Description: Starts or re-runs data validation for a dataset.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst
- Headers: Authorization, Content-Type
- Path Parameters:
  - dataset_id
- Query Parameters: None
- Request Body: None
- Validation Rules:
  - dataset must exist and be active
- Response Body:
  - job_id
  - status
- Success Response: 202 Accepted
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
- Status Codes: 202, 401, 403, 404

### 8.2 Get Validation Summary

- Endpoint Name: Get Validation Summary
- Method: GET
- URL: /api/v1/datasets/{dataset_id}/validation-summary
- Description: Returns validation results and data quality metrics.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst, Viewer
- Headers: Authorization, Accept
- Path Parameters:
  - dataset_id
- Query Parameters: None
- Request Body: None
- Validation Rules:
  - dataset_id must be valid
- Response Body:
  - quality_score
  - missing_values
  - duplicates
  - outliers
  - invalid_data_types
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
- Status Codes: 200, 401, 403, 404

---

## 9. Analytics APIs

### 9.1 Summary Statistics

- Endpoint Name: Get Summary Statistics
- Method: GET
- URL: /api/v1/analytics/{dataset_id}/summary
- Description: Returns summary statistics for a dataset.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst, Viewer
- Headers: Authorization, Accept
- Path Parameters:
  - dataset_id
- Query Parameters: columns, include_nulls
- Request Body: None
- Validation Rules:
  - dataset must be available for analysis
- Response Body:
  - summary object
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
- Status Codes: 200, 401, 403, 404

### 9.2 Exploratory Data Analysis

- Endpoint Name: Get EDA Results
- Method: GET
- URL: /api/v1/analytics/{dataset_id}/eda
- Description: Returns EDA outputs for a dataset.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst, Viewer
- Headers: Authorization, Accept
- Path Parameters:
  - dataset_id
- Query Parameters: analysis_type
- Request Body: None
- Validation Rules:
  - analysis type must be supported
- Response Body:
  - eda object
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
- Status Codes: 200, 401, 403, 404

### 9.3 KPI Metrics

- Endpoint Name: Get KPI Metrics
- Method: GET
- URL: /api/v1/analytics/kpis
- Description: Returns KPI metrics for the current organization.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst, Viewer
- Headers: Authorization, Accept
- Path Parameters: None
- Query Parameters: start_date, end_date, metric_group
- Request Body: None
- Validation Rules:
  - dates must be valid if provided
- Response Body:
  - metrics object
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
- Status Codes: 200, 401, 403

### 9.4 Customer Analytics

- Endpoint Name: Get Customer Analytics
- Method: GET
- URL: /api/v1/analytics/customers
- Description: Returns customer-focused analytics results.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst, Viewer
- Headers: Authorization, Accept
- Path Parameters: None
- Query Parameters: segment_id, start_date, end_date
- Request Body: None
- Validation Rules:
  - dates must be valid
- Response Body:
  - customer_analytics object
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
- Status Codes: 200, 401, 403

### 9.5 Revenue Analytics

- Endpoint Name: Get Revenue Analytics
- Method: GET
- URL: /api/v1/analytics/revenue
- Description: Returns revenue trend and summary analytics.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst, Viewer
- Headers: Authorization, Accept
- Path Parameters: None
- Query Parameters: start_date, end_date, granularity
- Request Body: None
- Validation Rules:
  - granularity must be supported
- Response Body:
  - revenue_analytics object
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
- Status Codes: 200, 401, 403

### 9.6 Retention Analytics

- Endpoint Name: Get Retention Analytics
- Method: GET
- URL: /api/v1/analytics/retention
- Description: Returns retention-based metrics and cohorts.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst, Viewer
- Headers: Authorization, Accept
- Path Parameters: None
- Query Parameters: start_date, end_date
- Request Body: None
- Validation Rules:
  - dates must be valid
- Response Body:
  - retention_analytics object
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
- Status Codes: 200, 401, 403

---

## 10. Machine Learning APIs

### 10.1 Customer Segmentation

- Endpoint Name: Create Customer Segmentation
- Method: POST
- URL: /api/v1/ml/segments
- Description: Starts or stores a segmentation analysis task.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst
- Headers: Authorization, Content-Type
- Path Parameters: None
- Query Parameters: None
- Request Body:
  - dataset_id
  - segment_count
  - feature_columns
- Validation Rules:
  - dataset must be available
  - segment_count must be positive
- Response Body:
  - job_id
  - segment_id
  - status
- Success Response: 202 Accepted
- Error Responses:
  - 400 Bad Request
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
- Status Codes: 202, 400, 401, 403, 404

### 10.2 Churn Prediction

- Endpoint Name: Create Churn Prediction
- Method: POST
- URL: /api/v1/ml/churn-prediction
- Description: Starts a churn prediction workflow for a dataset or customer cohort.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst
- Headers: Authorization, Content-Type
- Path Parameters: None
- Query Parameters: None
- Request Body:
  - dataset_id
  - model_config
- Validation Rules:
  - dataset must be valid
  - model configuration must be supported
- Response Body:
  - job_id
  - status
- Success Response: 202 Accepted
- Error Responses:
  - 400 Bad Request
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
- Status Codes: 202, 400, 401, 403, 404

### 10.3 Revenue Forecasting

- Endpoint Name: Create Revenue Forecast
- Method: POST
- URL: /api/v1/ml/revenue-forecast
- Description: Starts a revenue forecasting workflow.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst
- Headers: Authorization, Content-Type
- Path Parameters: None
- Query Parameters: None
- Request Body:
  - dataset_id
  - forecast_horizon
  - granularity
- Validation Rules:
  - forecast_horizon must be positive
  - granularity must be supported
- Response Body:
  - job_id
  - status
- Success Response: 202 Accepted
- Error Responses:
  - 400 Bad Request
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
- Status Codes: 202, 400, 401, 403, 404

### 10.4 Customer Lifetime Value

- Endpoint Name: Create Customer Lifetime Value Analysis
- Method: POST
- URL: /api/v1/ml/clv
- Description: Starts a CLV analysis workflow.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst
- Headers: Authorization, Content-Type
- Path Parameters: None
- Query Parameters: None
- Request Body:
  - dataset_id
  - horizon_months
- Validation Rules:
  - horizon_months must be positive
- Response Body:
  - job_id
  - status
- Success Response: 202 Accepted
- Error Responses:
  - 400 Bad Request
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
- Status Codes: 202, 400, 401, 403, 404

### 10.5 Explainable AI Results

- Endpoint Name: Get Explainability Results
- Method: GET
- URL: /api/v1/ml/{prediction_id}/explainability
- Description: Returns explanation details for a prediction result.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst, Viewer
- Headers: Authorization, Accept
- Path Parameters:
  - prediction_id
- Query Parameters: None
- Request Body: None
- Validation Rules:
  - prediction_id must be valid
- Response Body:
  - explanation object
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
- Status Codes: 200, 401, 403, 404

---

## 11. Report APIs

### 11.1 Generate PDF Report

- Endpoint Name: Generate PDF Report
- Method: POST
- URL: /api/v1/reports/pdf
- Description: Generates a PDF business report from selected analytics content.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst
- Headers: Authorization, Content-Type
- Path Parameters: None
- Query Parameters: None
- Request Body:
  - report_name
  - dataset_id
  - sections
- Validation Rules:
  - report_name must be present
  - sections must be supported
- Response Body:
  - report_id
  - status
- Success Response: 202 Accepted
- Error Responses:
  - 400 Bad Request
  - 401 Unauthorized
  - 403 Forbidden
- Status Codes: 202, 400, 401, 403

### 11.2 Generate Excel Report

- Endpoint Name: Generate Excel Report
- Method: POST
- URL: /api/v1/reports/excel
- Description: Generates an Excel export of selected analytics data.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst
- Headers: Authorization, Content-Type
- Path Parameters: None
- Query Parameters: None
- Request Body:
  - report_name
  - dataset_id
  - sections
- Validation Rules:
  - report_name must be present
- Response Body:
  - report_id
  - status
- Success Response: 202 Accepted
- Error Responses:
  - 400 Bad Request
  - 401 Unauthorized
  - 403 Forbidden
- Status Codes: 202, 400, 401, 403

### 11.3 List Reports

- Endpoint Name: List Reports
- Method: GET
- URL: /api/v1/reports
- Description: Lists generated reports for the current user or organization.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst, Viewer
- Headers: Authorization, Accept
- Path Parameters: None
- Query Parameters: page, page_size, status, format
- Request Body: None
- Validation Rules: None
- Response Body:
  - items
  - page
  - page_size
  - total
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
- Status Codes: 200, 401, 403

### 11.4 Download Report

- Endpoint Name: Download Report
- Method: GET
- URL: /api/v1/reports/{report_id}/download
- Description: Downloads a generated report artifact.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst, Viewer
- Headers: Authorization, Accept
- Path Parameters:
  - report_id
- Query Parameters: None
- Request Body: None
- Validation Rules:
  - report_id must be valid
- Response Body:
  - file stream or signed download link
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
- Status Codes: 200, 401, 403, 404

---

## 12. Dashboard APIs

### 12.1 Executive Dashboard

- Endpoint Name: Get Executive Dashboard
- Method: GET
- URL: /api/v1/dashboard/executive
- Description: Returns the executive dashboard summary for the organization.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst, Viewer
- Headers: Authorization, Accept
- Path Parameters: None
- Query Parameters: start_date, end_date
- Request Body: None
- Validation Rules:
  - dates must be valid if provided
- Response Body:
  - dashboard object
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
- Status Codes: 200, 401, 403

### 12.2 KPI Cards

- Endpoint Name: Get KPI Cards
- Method: GET
- URL: /api/v1/dashboard/kpi-cards
- Description: Returns summarized KPI card values.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst, Viewer
- Headers: Authorization, Accept
- Path Parameters: None
- Query Parameters: metric_group
- Request Body: None
- Validation Rules:
  - metric_group must be recognized
- Response Body:
  - cards object
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
- Status Codes: 200, 401, 403

### 12.3 Charts and Trends

- Endpoint Name: Get Dashboard Charts
- Method: GET
- URL: /api/v1/dashboard/charts
- Description: Returns chart-ready data for dashboard visualization.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager, Analyst, Viewer
- Headers: Authorization, Accept
- Path Parameters: None
- Query Parameters: chart_type, start_date, end_date
- Request Body: None
- Validation Rules:
  - chart_type must be supported
- Response Body:
  - charts object
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
- Status Codes: 200, 401, 403

---

## 13. Notifications and Audit APIs

### 13.1 List Notifications

- Endpoint Name: List Notifications
- Method: GET
- URL: /api/v1/notifications
- Description: Lists notifications for the current user.
- Authentication Required: Yes
- User Roles Allowed: All authenticated users
- Headers: Authorization, Accept
- Path Parameters: None
- Query Parameters: page, page_size, unread_only
- Request Body: None
- Validation Rules: None
- Response Body:
  - items
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
- Status Codes: 200, 401

### 13.2 Mark Notification as Read

- Endpoint Name: Mark Notification as Read
- Method: PATCH
- URL: /api/v1/notifications/{notification_id}
- Description: Marks a notification as read.
- Authentication Required: Yes
- User Roles Allowed: All authenticated users
- Headers: Authorization, Content-Type
- Path Parameters:
  - notification_id
- Query Parameters: None
- Request Body:
  - is_read
- Validation Rules:
  - notification_id must be valid
- Response Body:
  - notification object
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 404 Not Found
- Status Codes: 200, 401, 404

### 13.3 List Audit Logs

- Endpoint Name: List Audit Logs
- Method: GET
- URL: /api/v1/audit-logs
- Description: Returns audit log entries for authorized viewing.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager
- Headers: Authorization, Accept
- Path Parameters: None
- Query Parameters: page, page_size, entity_type, start_date, end_date
- Request Body: None
- Validation Rules: None
- Response Body:
  - items
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
- Status Codes: 200, 401, 403

---

## 14. System Settings APIs

### 14.1 Get System Settings

- Endpoint Name: Get System Settings
- Method: GET
- URL: /api/v1/settings
- Description: Returns settings available for the current organization or user scope.
- Authentication Required: Yes
- User Roles Allowed: Administrator, Organization Manager
- Headers: Authorization, Accept
- Path Parameters: None
- Query Parameters: None
- Request Body: None
- Validation Rules: None
- Response Body:
  - settings object
- Success Response: 200 OK
- Error Responses:
  - 401 Unauthorized
  - 403 Forbidden
- Status Codes: 200, 401, 403

### 14.2 Update System Settings

- Endpoint Name: Update System Settings
- Method: PATCH
- URL: /api/v1/settings
- Description: Updates tenant or system settings.
- Authentication Required: Yes
- User Roles Allowed: Administrator
- Headers: Authorization, Content-Type
- Path Parameters: None
- Query Parameters: None
- Request Body:
  - settings object
- Validation Rules:
  - values must be valid for the target settings keys
- Response Body:
  - settings object
- Success Response: 200 OK
- Error Responses:
  - 400 Bad Request
  - 401 Unauthorized
  - 403 Forbidden
- Status Codes: 200, 400, 401, 403

---

## 15. Standard Response Formats

### Success Response Structure

```json
{
  "timestamp": "2026-07-30T12:00:00Z",
  "requestId": "req-123456",
  "status": 200,
  "data": {
    "items": [],
    "page": 1,
    "pageSize": 20,
    "total": 0
  },
  "message": "Request completed successfully"
}
```

### Error Response Structure

```json
{
  "timestamp": "2026-07-30T12:00:00Z",
  "requestId": "req-123456",
  "status": 400,
  "errorCode": "INVALID_REQUEST",
  "message": "The request contains invalid parameters.",
  "details": []
}
```

---

## 16. Error Handling Strategy

The API should return a consistent error model for all endpoints.

### Common Error Codes

- INVALID_REQUEST
- UNAUTHORIZED
- FORBIDDEN
- NOT_FOUND
- CONFLICT
- VALIDATION_FAILED
- RATE_LIMITED
- INTERNAL_SERVER_ERROR
- SERVICE_UNAVAILABLE

### Status Code Mapping

| Status Code | Meaning |
|---|---|
| 200 | Success |
| 201 | Created |
| 202 | Accepted for async processing |
| 204 | Successful deletion with no content |
| 400 | Bad request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not found |
| 409 | Conflict |
| 413 | Payload too large |
| 422 | Validation failed |
| 429 | Too many requests |
| 500 | Internal server error |
| 503 | Service unavailable |

---

## 17. Security Considerations

### JWT

- Access tokens should be short-lived
- Refresh tokens should be securely stored and rotated
- Token validation should occur on every protected request

### HTTPS

- All production traffic must use HTTPS
- Sensitive data must not be transmitted over insecure channels

### CORS

- CORS policies should restrict cross-origin access to approved origins only

### Input Validation

- Validate request bodies, query parameters, and path parameters on the server side
- Reject malformed content with clear error messages

### Rate Limiting

- Apply per-IP and per-user rate limiting for authentication and high-volume endpoints

### Request Size Limits

- Dataset upload endpoints should enforce size and type restrictions
- Large file uploads must be handled with streaming and size checks

### API Versioning

- Versioning is handled through /api/v1/ path prefixes
- Breaking changes should introduce a new version rather than altering the existing contract

---

## 18. Documentation and OpenAPI Conventions

### OpenAPI Naming Conventions

- Use descriptive operationIds such as create_dataset, list_reports, get_dashboard_summary
- Group endpoints by domain tag: Auth, Organizations, Users, Datasets, Analytics, ML, Reports, Dashboard, Notifications, Settings

### Example Request

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "StrongPassword123!"
}
```

### Example Response

```json
{
  "timestamp": "2026-07-30T12:00:00Z",
  "requestId": "req-123456",
  "status": 200,
  "data": {
    "accessToken": "eyJ...",
    "refreshToken": "eyJ...",
    "tokenType": "bearer",
    "expiresIn": 3600
  },
  "message": "Login successful"
}
```

---

## 19. Endpoint Grouping Summary

| Module | Endpoint Groups |
|---|---|
| Authentication | register, login, refresh, logout, forgot-password, reset-password, verify-email |
| Organizations | list, get, create |
| Users | list, get, update |
| Datasets | upload, list, get, delete, versions, download |
| Data Validation | validate, validation-summary |
| Analytics | summary, eda, kpis, customer, revenue, retention |
| Machine Learning | segmentation, churn, forecast, clv, explainability |
| Reports | pdf, excel, list, download |
| Dashboard | executive, kpi-cards, charts |
| Notifications | list, mark-read |
| Audit Logs | list |
| Settings | get, update |

---

## 20. Summary

The proposed REST API design provides a consistent, secure, and scalable interface for InsightIQ. The API supports authentication, user and organization management, dataset handling, validation, analytics, machine learning, reporting, dashboard access, notifications, and administrative settings under a versioned /api/v1/ structure. The design is suitable for independent implementation by backend and frontend teams while preserving room for future growth.
