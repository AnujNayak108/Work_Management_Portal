# ATOMQUEST Hackathon Submission

## 1. Live Application URL
**[https://work-management-portal-3.onrender.com/auth/login](https://work-management-portal-3.onrender.com/auth/login)**

## 2. GitHub Repository
**[https://github.com/AnujNayak108/Work_Management_Portal.git](https://github.com/AnujNayak108/Work_Management_Portal.git)**

## 3. Login Credentials (Demo Accounts)
The application has been pre-seeded with demo data so you can test all three roles. You can use the following credentials to explore the different user journeys:

### 👑 Admin Role
- **Email:** `admin@atomberg.com`
- **Password:** `admin123`

### 👔 Manager Role
- **Email:** `manager.eng@atomberg.com` (Engineering Dept)
- **Email:** `manager.mkt@atomberg.com` (Marketing Dept)
- **Email:** `manager.ops@atomberg.com` (Operations Dept)
- **Password:** `manager123`

### 👤 Employee Role
- **Email:** `emp1@atomberg.com` (Engineering)
- **Email:** `emp4@atomberg.com` (Marketing) 
- **Email:** `emp7@atomberg.com` (Operations)
- **Password:** `emp123`

*(Note: There are 9 employee accounts ranging from `emp1@atomberg.com` to `emp9@atomberg.com`, all with the password `emp123`)*

---

## 4. Architecture Diagram

Below is the high-level architecture diagram of the portal. 

```mermaid
graph TD
    Client([Web Browser / Client]) -->|HTTPS| Proxy[Render Edge Proxy]
    
    subgraph Render Platform
        Proxy --> Gunicorn[Gunicorn WSGI Server]
        Gunicorn --> FlaskApp[Flask Application]
        
        subgraph MVC Application [Flask App Structure]
            FlaskApp -->|Routing| Blueprints
            Blueprints --> Auth[Auth Blueprint]
            Blueprints --> Employee[Employee Blueprint]
            Blueprints --> Manager[Manager Blueprint]
            Blueprints --> Admin[Admin Blueprint]
            Blueprints --> Reports[Reports Blueprint]
        end
        
        subgraph Database Layer
            DB[(PostgreSQL Database)]
        end
        
        Auth -->|SQLAlchemy ORM| DB
        Employee -->|SQLAlchemy ORM| DB
        Manager -->|SQLAlchemy ORM| DB
        Admin -->|SQLAlchemy ORM| DB
        Reports -->|SQLAlchemy ORM| DB
    end
```
