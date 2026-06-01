# Sicurezza in Elasticsearch

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-22  
> Versione: 2.0.0  
> Stato: expanded

## Indice
1. Security Architecture Overview
2. TLS Encryption
3. Authentication and Realms
4. API Keys and Service Tokens
5. RBAC: Role-Based Access Control
6. Field-Level and Document-Level Security
7. LDAP and Active Directory Integration
8. SAML and OIDC Single Sign-On
9. IP Filtering and Network Security
10. Audit Logging
11. Encryption at Rest
12. Kibana Security Integration
13. Troubleshooting
14. FAQ
15. Exercises

---

## 1. Security Architecture Overview

### 1.1 Elastic Security Model

Elasticsearch security (part of the Elastic Stack's X-Pack features) is built on multiple layers of defense:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Request                           │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────┐ │
│  │    TLS    │ → │  AuthN   │ → │  AuthZ   │ → │   Audit     │ │
│  │ Encryption│   │ Identity │   │ RBAC/FLS │   │   Logging   │ │
│  │           │   │ Realm    │   │ /DLS     │   │             │ │
│  └──────────┘   └──────────┘   └──────────┘   └─────────────┘ │
│                                                                 │
│  Layer 1:       Layer 2:       Layer 3:       Layer 4:          │
│  Transport      Who are you?   What can you   Record            │
│  Security       (Token, Cert,  access?        everything        │
│                  LDAP, SAML)                                    │
└─────────────────────────────────────────────────────────────────┘
```

In Elasticsearch 8.x, security is **enabled by default**. This is a significant change from 7.x where security had to be explicitly enabled. On first start, ES 8.x auto-generates:
- A CA certificate and node certificates for TLS
- A password for the `elastic` superuser
- An enrollment token for Kibana
- An enrollment token for new nodes to join the cluster

### 1.2 Security Features by License

| Feature | Basic (Free) | Gold | Platinum/Enterprise |
|---------|-------------|------|---------------------|
| TLS encryption | Yes | Yes | Yes |
| Native realm (users in ES) | Yes | Yes | Yes |
| RBAC (index/cluster privileges) | Yes | Yes | Yes |
| API keys | Yes | Yes | Yes |
| LDAP/AD authentication | No | Yes | Yes |
| SAML/OIDC SSO | No | No | Yes |
| Field-level security | No | No | Yes |
| Document-level security | No | No | Yes |
| Audit logging | No | Yes | Yes |
| IP filtering | No | Yes | Yes |
| Encryption at rest | No | No | Yes |

### 1.3 Enabling Security (ES 7.x — Already Default in 8.x)

```yaml
# elasticsearch.yml — enable security explicitly (ES 7.x)
xpack.security.enabled: true
xpack.security.enrollment.enabled: true
```

---

## 2. TLS Encryption

### 2.1 Certificate Generation with elasticsearch-certutil

Elasticsearch provides built-in tools for PKI management:

```bash
# Step 1: Generate a Certificate Authority (CA)
./bin/elasticsearch-certutil ca \
  --out /etc/elasticsearch/certs/elastic-stack-ca.p12 \
  --pass ""

# Step 2: Generate node certificates signed by the CA
./bin/elasticsearch-certutil cert \
  --ca /etc/elasticsearch/certs/elastic-stack-ca.p12 \
  --out /etc/elasticsearch/certs/elastic-certificates.p12 \
  --pass ""

# Step 3: Generate certificates with Subject Alternative Names (SANs)
# Required when nodes have multiple hostnames or IPs
./bin/elasticsearch-certutil cert \
  --ca /etc/elasticsearch/certs/elastic-stack-ca.p12 \
  --dns "es-node-01,es-node-01.example.com" \
  --ip "10.0.1.10,192.168.1.10" \
  --out /etc/elasticsearch/certs/node-01.p12 \
  --pass ""
```

For multi-node clusters, generate certificates per node with unique SANs:

```bash
# Create an instances.yml file for batch certificate generation
cat > /tmp/instances.yml << 'EOF'
instances:
  - name: "es-master-01"
    dns: ["es-master-01", "es-master-01.example.com"]
    ip: ["10.0.1.10"]
  - name: "es-master-02"
    dns: ["es-master-02", "es-master-02.example.com"]
    ip: ["10.0.1.11"]
  - name: "es-data-01"
    dns: ["es-data-01", "es-data-01.example.com"]
    ip: ["10.0.2.10"]
  - name: "es-data-02"
    dns: ["es-data-02", "es-data-02.example.com"]
    ip: ["10.0.2.11"]
EOF

./bin/elasticsearch-certutil cert \
  --ca /etc/elasticsearch/certs/elastic-stack-ca.p12 \
  --in /tmp/instances.yml \
  --out /etc/elasticsearch/certs/certs.zip \
  --pass ""
```

### 2.2 PEM-Based Certificates (Alternative to PKCS12)

Some organizations prefer PEM files over PKCS12 archives. Elasticsearch supports both:

```bash
# Generate PEM format certificates
./bin/elasticsearch-certutil ca --pem \
  --out /etc/elasticsearch/certs/ca.zip

unzip ca.zip -d /etc/elasticsearch/certs/

./bin/elasticsearch-certutil cert --pem \
  --ca-cert /etc/elasticsearch/certs/ca/ca.crt \
  --ca-key /etc/elasticsearch/certs/ca/ca.key \
  --dns "es-node-01" \
  --out /etc/elasticsearch/certs/node-01.zip

unzip node-01.zip -d /etc/elasticsearch/certs/node-01/
```

### 2.3 Transport Layer TLS (Inter-Node)

```yaml
# elasticsearch.yml — transport TLS (mandatory in production)
xpack.security.transport.ssl.enabled: true
xpack.security.transport.ssl.verification_mode: full

# PEM format:
xpack.security.transport.ssl.certificate_authorities: /etc/elasticsearch/certs/ca/ca.crt
xpack.security.transport.ssl.certificate: /etc/elasticsearch/certs/node-01/node-01.crt
xpack.security.transport.ssl.key: /etc/elasticsearch/certs/node-01/node-01.key

# OR PKCS12 format:
# xpack.security.transport.ssl.keystore.path: /etc/elasticsearch/certs/elastic-certificates.p12
# xpack.security.transport.ssl.truststore.path: /etc/elasticsearch/certs/elastic-certificates.p12
```

Verification modes:

| Mode | Validates Certificate | Validates Hostname | Use Case |
|------|----------------------|--------------------|----------|
| `full` | Yes | Yes | Production (recommended) |
| `certificate` | Yes | No | When nodes use IP addresses or dynamic hostnames |
| `none` | No | No | Never in production — testing only |

### 2.4 HTTP Layer TLS (Client-Facing)

```yaml
# elasticsearch.yml — HTTP TLS
xpack.security.http.ssl.enabled: true
xpack.security.http.ssl.certificate_authorities: /etc/elasticsearch/certs/ca/ca.crt
xpack.security.http.ssl.certificate: /etc/elasticsearch/certs/http/http.crt
xpack.security.http.ssl.key: /etc/elasticsearch/certs/http/http.key

# Client certificate authentication (mutual TLS)
xpack.security.http.ssl.client_authentication: optional
# Values: required, optional, none
```

### 2.5 TLS for Kibana and Beats

```yaml
# kibana.yml — TLS to Elasticsearch
elasticsearch.hosts: ["https://es-node-01:9200"]
elasticsearch.ssl.certificateAuthorities: ["/etc/kibana/certs/ca.crt"]
elasticsearch.ssl.certificate: /etc/kibana/certs/kibana.crt
elasticsearch.ssl.key: /etc/kibana/certs/kibana.key

# Enable HTTPS for Kibana itself
server.ssl.enabled: true
server.ssl.certificate: /etc/kibana/certs/kibana-server.crt
server.ssl.key: /etc/kibana/certs/kibana-server.key
```

### 2.6 Certificate Rotation Without Downtime

Elasticsearch monitors certificate files for changes. When the files are updated on disk, ES reloads them automatically:

```bash
# Replace certificates on disk (all nodes must get the new cert)
cp /path/to/new/node.crt /etc/elasticsearch/certs/node.crt
cp /path/to/new/node.key /etc/elasticsearch/certs/node.key

# ES reloads certificates automatically within ~5 seconds
# No restart required

# Verify the reload via the SSL certificate API
curl -s https://es-node:9200/_ssl/certificates | python3 -m json.tool
```

For CA rotation (changing the root CA), a more careful procedure is required:
1. Add the new CA to `certificate_authorities` alongside the old CA.
2. Roll out new node certificates signed by the new CA.
3. After all nodes use the new certificates, remove the old CA.

---

## 3. Authentication and Realms

### 3.1 Realm Chain

Elasticsearch authenticates requests by checking realms in order of their `order` value. The first realm that successfully authenticates the request wins:

```yaml
# elasticsearch.yml — realm chain
xpack.security.authc.realms:
  # Realm 1: Token-based (API keys, bearer tokens) — checked first
  native.native1:
    order: 0

  # Realm 2: LDAP — checked second
  ldap.ldap1:
    order: 1
    url: "ldaps://ldap.example.com:636"
    bind_dn: "cn=es-svc,ou=service,dc=example,dc=com"
    user_search.base_dn: "ou=users,dc=example,dc=com"
    user_search.filter: "(sAMAccountName={0})"
    group_search.base_dn: "ou=groups,dc=example,dc=com"

  # Realm 3: SAML — checked third
  saml.saml1:
    order: 2
    idp.metadata.path: /etc/elasticsearch/saml/idp-metadata.xml
    idp.entity_id: "https://idp.example.com"
    sp.entity_id: "https://kibana.example.com"
    sp.acs: "https://kibana.example.com/api/security/saml/callback"
    attributes.principal: "NameID"
```

### 3.2 Native Realm (Built-in Users)

The native realm stores users in a system index within Elasticsearch:

```bash
# Initial setup: generate passwords for built-in users
./bin/elasticsearch-setup-passwords auto
# Generates passwords for: elastic, kibana_system, logstash_system,
# beats_system, apm_system, remote_monitoring_user

# Or set passwords interactively
./bin/elasticsearch-setup-passwords interactive
```

```http
// Create a user in the native realm
POST /_security/user/app-developer
{
  "password": "secure-password-here",
  "roles": ["developer"],
  "full_name": "Application Developer",
  "email": "dev@example.com",
  "metadata": {
    "department": "engineering"
  },
  "enabled": true
}

// Update a user's password
PUT /_security/user/app-developer/_password
{
  "password": "new-secure-password"
}

// Disable a user (without deleting)
PUT /_security/user/app-developer/_disable

// Delete a user
DELETE /_security/user/app-developer

// List all users
GET /_security/user
```

### 3.3 File Realm

The file realm stores users in local files on each node. Useful for emergency access when the cluster is down:

```bash
# Add a user to the file realm
./bin/elasticsearch-users useradd emergency-admin \
  -p "emergency-password" \
  -r superuser

# List file realm users
./bin/elasticsearch-users list

# Remove a user
./bin/elasticsearch-users userdel emergency-admin
```

```yaml
# elasticsearch.yml — file realm configuration
xpack.security.authc.realms.file.file1:
  order: 0
```

The file realm should always be first (lowest `order`) to provide emergency access.

---

## 4. API Keys and Service Tokens

### 4.1 API Key Management

API keys provide programmatic access without sharing user credentials. They can have limited privileges and expiration times:

```http
// Create an API key with specific privileges
POST /_security/api_key
{
  "name": "monitoring-dashboard-key",
  "expiration": "30d",
  "role_descriptors": {
    "monitoring_reader": {
      "cluster": ["monitor"],
      "indices": [
        {
          "names": ["metrics-*", "logs-*"],
          "privileges": ["read", "view_index_metadata"]
        }
      ]
    }
  },
  "metadata": {
    "application": "grafana-dashboard",
    "environment": "production",
    "created_by": "ops-team"
  }
}

// Response:
// {
//   "id": "VuaCfGcBCdbkQm-e5aOx",
//   "name": "monitoring-dashboard-key",
//   "api_key": "ui2lp2axTNmsyakw9tvNnw",
//   "encoded": "VnVhQ2ZHY0JDZGJrUW0tZTVhT3g6dWkybHAyYXhUTm1zeWFrdzl0dk5udw==",
//   "expiration": 1719014400000
// }

// Use the API key (Base64 encoded id:api_key)
// curl -H "Authorization: ApiKey VnVhQ2ZHY0JDZGJrUW0tZTVhT3g6dWkybHAyYXhUTm1zeWFrdzl0dk5udw==" \
//   https://es-node:9200/_cluster/health
```

### 4.2 API Key Operations

```http
// List all API keys
GET /_security/api_key?owner=false

// Get a specific API key
GET /_security/api_key?id=VuaCfGcBCdbkQm-e5aOx

// Invalidate (revoke) an API key
DELETE /_security/api_key
{
  "ids": ["VuaCfGcBCdbkQm-e5aOx"]
}

// Invalidate all API keys for a user
DELETE /_security/api_key
{
  "username": "app-developer"
}

// Invalidate all expired API keys (cleanup)
DELETE /_security/api_key
{
  "owner": true
}

// Update API key privileges (ES 8.4+)
PUT /_security/api_key/VuaCfGcBCdbkQm-e5aOx
{
  "role_descriptors": {
    "updated_role": {
      "cluster": ["monitor"],
      "indices": [
        {
          "names": ["metrics-*"],
          "privileges": ["read"]
        }
      ]
    }
  },
  "metadata": {
    "updated": "2026-05-22"
  }
}
```

### 4.3 Cross-Cluster API Keys (ES 8.10+)

For CCR and CCS, cross-cluster API keys replace the older certificate-based remote cluster authentication:

```http
// On the cluster that will be accessed remotely
POST /_security/cross_cluster/api_key
{
  "name": "ccr-replication-key",
  "expiration": "365d",
  "access": {
    "search": [
      {
        "names": ["logs-*", "metrics-*"]
      }
    ],
    "replication": [
      {
        "names": ["orders-*"]
      }
    ]
  }
}
```

### 4.4 Service Tokens

Service tokens are designed for Elastic Stack components (Kibana, Fleet, Enterprise Search) that need to authenticate to Elasticsearch:

```bash
# Create a service token for Kibana
./bin/elasticsearch-service-tokens create elastic/kibana kibana-token-1

# Output:
# SERVICE_TOKEN elastic/kibana/kibana-token-1 = AAEAAWVsYXN0aWM...

# Delete a service token
./bin/elasticsearch-service-tokens delete elastic/kibana kibana-token-1
```

```yaml
# kibana.yml — authenticate with service token
elasticsearch.serviceAccountToken: "AAEAAWVsYXN0aWM..."
```

Service tokens are more secure than username/password for service-to-service authentication because they are tied to a specific service account and cannot be used to impersonate other users.

---

## 5. RBAC: Role-Based Access Control

### 5.1 Privilege Hierarchy

Elasticsearch privileges operate at three levels:

```
Cluster Privileges → Index Privileges → Field/Document-Level Security

Cluster:
  all, manage, monitor, manage_security, manage_ilm, manage_pipeline,
  manage_index_templates, manage_rollup, manage_transform, manage_ml,
  read_ccr, manage_ccr, read_ilm, manage_data_frame_transforms

Index:
  all, create, create_doc, create_index, delete, delete_index, index,
  manage, monitor, read, view_index_metadata, write,
  manage_follow_index, manage_leader_index, maintenance

Run As:
  Execute requests as another user (for proxied authentication)
```

### 5.2 Custom Role Examples

```http
// Read-only analyst: can read specific indices, use Kibana Discover
POST /_security/role/data_analyst
{
  "cluster": ["monitor"],
  "indices": [
    {
      "names": ["metrics-*", "logs-*"],
      "privileges": ["read", "view_index_metadata"]
    }
  ],
  "applications": [
    {
      "application": "kibana-.kibana",
      "privileges": ["feature_discover.read", "feature_dashboard.read"],
      "resources": ["space:analytics"]
    }
  ],
  "metadata": {
    "description": "Read-only access to metrics and logs for analytics team"
  }
}

// DevOps engineer: manage indices, pipelines, and ILM
POST /_security/role/devops_engineer
{
  "cluster": ["manage_ilm", "manage_pipeline", "manage_index_templates", "monitor"],
  "indices": [
    {
      "names": ["logs-*", "metrics-*", "apm-*"],
      "privileges": ["all"]
    },
    {
      "names": [".kibana*"],
      "privileges": ["read", "view_index_metadata"]
    }
  ]
}

// Application writer: can only index documents, not read or delete
POST /_security/role/app_writer
{
  "cluster": [],
  "indices": [
    {
      "names": ["app-events-*"],
      "privileges": ["create_doc", "create_index", "view_index_metadata"]
    }
  ]
}

// Security auditor: read-only access to audit logs and security config
POST /_security/role/security_auditor
{
  "cluster": ["monitor", "manage_security"],
  "indices": [
    {
      "names": [".security-audit-*"],
      "privileges": ["read"]
    }
  ],
  "run_as": ["*"]
}
```

### 5.3 Role Mapping (LDAP/SAML Groups to ES Roles)

```http
// Map an LDAP group to an Elasticsearch role
POST /_security/role_mapping/devops_ldap_mapping
{
  "roles": ["devops_engineer"],
  "enabled": true,
  "rules": {
    "all": [
      { "field": { "realm.name": "ldap1" } },
      { "field": { "groups": "cn=devops,ou=groups,dc=example,dc=com" } }
    ]
  },
  "metadata": {
    "description": "Maps LDAP devops group to ES devops_engineer role"
  }
}

// Map a SAML attribute to a role
POST /_security/role_mapping/analysts_saml_mapping
{
  "roles": ["data_analyst"],
  "enabled": true,
  "rules": {
    "all": [
      { "field": { "realm.name": "saml1" } },
      { "field": { "groups": "data-analytics-team" } }
    ]
  }
}

// Map based on username pattern
POST /_security/role_mapping/admin_pattern_mapping
{
  "roles": ["superuser"],
  "enabled": true,
  "rules": {
    "any": [
      { "field": { "username": "admin-*" } },
      { "field": { "dn": "*,ou=admins,dc=example,dc=com" } }
    ]
  }
}
```

### 5.4 Run-As (User Impersonation)

Run-as allows a trusted service to execute requests on behalf of other users:

```http
// Create a role that can impersonate specific users
POST /_security/role/proxy_service
{
  "cluster": ["monitor"],
  "indices": [
    {
      "names": ["*"],
      "privileges": ["read"]
    }
  ],
  "run_as": ["analyst-*", "dashboard-user"]
}

// Execute a request as another user
// The Authorization header authenticates the proxy service
// The es-security-runas-user header specifies the impersonated user
// curl -H "Authorization: ApiKey ..." \
//      -H "es-security-runas-user: analyst-jdoe" \
//      https://es-node:9200/logs-*/_search
```

---

## 6. Field-Level and Document-Level Security

### 6.1 Field-Level Security (FLS)

FLS restricts which fields a user can see in search results and aggregations:

```http
// Role that hides sensitive fields
POST /_security/role/basic_operator
{
  "indices": [
    {
      "names": ["customers"],
      "privileges": ["read"],
      "field_security": {
        "grant": ["name", "email", "registration_date", "status"],
        "except": ["credit_card", "ssn", "bank_account", "salary"]
      }
    }
  ]
}

// Exclusive grant — only specified fields are visible
POST /_security/role/minimal_viewer
{
  "indices": [
    {
      "names": ["customers"],
      "privileges": ["read"],
      "field_security": {
        "grant": ["name", "status"]
      }
    }
  ]
}
```

FLS behavior:
- Hidden fields are stripped from `_source` before returning.
- Aggregations on hidden fields return empty results (not errors).
- Highlighting on hidden fields is suppressed.
- The `_source` field itself respects FLS — `_source` filtering cannot bypass FLS.

### 6.2 Document-Level Security (DLS)

DLS restricts which documents a user can see by automatically appending a filter to every query:

```http
// Regional sales agent: can only see their region
POST /_security/role/sales_agent_north
{
  "indices": [
    {
      "names": ["orders"],
      "privileges": ["read"],
      "query": {
        "bool": {
          "filter": [
            { "term": { "region": "north" } },
            { "term": { "active": true } }
          ]
        }
      }
    }
  ]
}

// Multi-tenant isolation: tenant can only see their own data
POST /_security/role/tenant_viewer
{
  "indices": [
    {
      "names": ["shared-data-*"],
      "privileges": ["read", "write"],
      "query": {
        "template": {
          "source": "{\"term\": {\"tenant_id\": \"{{_user.metadata.tenant_id}}\"}}"
        }
      }
    }
  ]
}

// Create user with tenant metadata
POST /_security/user/tenant-a-user
{
  "password": "secure-password",
  "roles": ["tenant_viewer"],
  "metadata": {
    "tenant_id": "tenant-a"
  }
}
```

### 6.3 Combining FLS and DLS

FLS and DLS can be combined in a single role:

```http
POST /_security/role/restricted_analyst
{
  "indices": [
    {
      "names": ["transactions"],
      "privileges": ["read"],
      "field_security": {
        "grant": ["timestamp", "merchant", "amount", "currency", "status"],
        "except": ["card_number", "cvv", "customer_ssn"]
      },
      "query": {
        "bool": {
          "filter": [
            { "term": { "country": "IT" } },
            { "range": { "amount": { "lte": 10000 } } }
          ]
        }
      }
    }
  ]
}
```

### 6.4 Performance Implications of FLS/DLS

- **DLS**: adds a filter to every query. Impact is minimal if the filter is on an indexed field with good selectivity. Impact is significant if the filter uses scripting or scans many documents.
- **FLS**: requires post-processing of `_source` to strip fields. Impact scales with document size and number of fields being filtered. For large documents, FLS adds measurable overhead.
- Both FLS and DLS are enforced at the shard level, so they cannot be bypassed by client-side manipulation.

---

## 7. LDAP and Active Directory Integration

### 7.1 LDAP Realm Configuration

```yaml
# elasticsearch.yml — LDAP with user search
xpack.security.authc.realms.ldap.ldap1:
  order: 1
  url: "ldaps://ldap.example.com:636"
  bind_dn: "cn=es-service,ou=serviceaccounts,dc=example,dc=com"
  user_search:
    base_dn: "ou=users,dc=example,dc=com"
    filter: "(sAMAccountName={0})"
    scope: sub_tree
  group_search:
    base_dn: "ou=groups,dc=example,dc=com"
    scope: sub_tree
  ssl:
    certificate_authorities: /etc/elasticsearch/certs/ldap-ca.crt
    verification_mode: full
  unmapped_groups_as_roles: false
  follow_referrals: true
  timeout:
    tcp_connect: 5s
    tcp_read: 5s
    ldap_search: 5s
  cache:
    ttl: 20m
    max_users: 100000
    hash_algo: ssha256
```

Store the bind password in the Elasticsearch keystore (never in plaintext config):

```bash
./bin/elasticsearch-keystore add xpack.security.authc.realms.ldap.ldap1.secure_bind_password
```

### 7.2 Active Directory Realm

```yaml
# elasticsearch.yml — Active Directory
xpack.security.authc.realms.active_directory.ad1:
  order: 1
  url: "ldaps://dc.example.com:636"
  domain_name: "example.com"
  user_search:
    base_dn: "dc=example,dc=com"
    scope: sub_tree
  group_search:
    base_dn: "dc=example,dc=com"
    scope: sub_tree
  ssl:
    certificate_authorities: /etc/elasticsearch/certs/ad-ca.crt
  follow_referrals: true
  timeout:
    tcp_connect: 5s
```

### 7.3 LDAP Group-to-Role Mapping

After LDAP authentication, map LDAP groups to Elasticsearch roles:

```http
// Admins group → superuser
POST /_security/role_mapping/ldap_admins
{
  "roles": ["superuser"],
  "enabled": true,
  "rules": {
    "all": [
      { "field": { "realm.name": "ldap1" } },
      { "field": { "groups": "cn=es-admins,ou=groups,dc=example,dc=com" } }
    ]
  }
}

// Developers group → read/write on specific indices
POST /_security/role_mapping/ldap_developers
{
  "roles": ["devops_engineer"],
  "enabled": true,
  "rules": {
    "all": [
      { "field": { "realm.name": "ldap1" } },
      { "field": { "groups": "cn=developers,ou=groups,dc=example,dc=com" } }
    ]
  }
}

// Test LDAP authentication
POST /_security/_authenticate
// (with Basic auth header for an LDAP user)
```

---

## 8. SAML and OIDC Single Sign-On

### 8.1 SAML Configuration

SAML SSO requires coordination between Elasticsearch (SP), Kibana, and your Identity Provider (IdP):

```yaml
# elasticsearch.yml — SAML realm
xpack.security.authc.realms.saml.saml1:
  order: 2
  idp.metadata.path: /etc/elasticsearch/saml/idp-metadata.xml
  idp.entity_id: "https://idp.example.com/saml2"
  sp.entity_id: "https://kibana.example.com"
  sp.acs: "https://kibana.example.com/api/security/saml/callback"
  sp.logout: "https://kibana.example.com/logout"
  attributes.principal: "NameID"
  attributes.groups: "http://schemas.xmlsoap.org/claims/Group"
  attributes.name: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
  attributes.mail: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
  nameid_format: "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent"
  force_authn: false
  populate_user_metadata: true
```

```yaml
# kibana.yml — SAML provider
xpack.security.authc.providers:
  saml.saml1:
    order: 0
    realm: saml1
    description: "Corporate SSO"
    icon: "logoSecurity"
  basic.basic1:
    order: 1
    description: "Local login"
```

### 8.2 OIDC Configuration

```yaml
# elasticsearch.yml — OpenID Connect realm
xpack.security.authc.realms.oidc.oidc1:
  order: 3
  rp.client_id: "elasticsearch-client"
  rp.response_type: "code"
  rp.redirect_uri: "https://kibana.example.com/api/security/oidc/callback"
  rp.post_logout_redirect_uri: "https://kibana.example.com/logged_out"
  op.issuer: "https://auth.example.com"
  op.authorization_endpoint: "https://auth.example.com/oauth2/authorize"
  op.token_endpoint: "https://auth.example.com/oauth2/token"
  op.jwkset_path: "https://auth.example.com/.well-known/jwks.json"
  op.userinfo_endpoint: "https://auth.example.com/oauth2/userinfo"
  claims.principal: "sub"
  claims.groups: "groups"
  claims.name: "name"
  claims.mail: "email"
```

```bash
# Store OIDC client secret in the keystore
./bin/elasticsearch-keystore add xpack.security.authc.realms.oidc.oidc1.rp.client_secret
```

```yaml
# kibana.yml — OIDC provider
xpack.security.authc.providers:
  oidc.oidc1:
    order: 0
    realm: oidc1
    description: "Corporate SSO (OIDC)"
  basic.basic1:
    order: 1
```

---

## 9. IP Filtering and Network Security

### 9.1 IP Filter Configuration

```yaml
# elasticsearch.yml — IP filtering
xpack.security.transport.filter.allow: ["10.0.0.0/8", "172.16.0.0/12"]
xpack.security.transport.filter.deny: ["_all"]

xpack.security.http.filter.allow: ["10.0.0.0/8", "192.168.1.0/24"]
xpack.security.http.filter.deny: ["_all"]
```

### 9.2 Dynamic IP Filtering

```http
// Add IP filter rules dynamically
PUT /_cluster/settings
{
  "persistent": {
    "xpack.security.transport.filter.allow": ["10.0.0.0/8"],
    "xpack.security.transport.filter.deny": ["_all"],
    "xpack.security.http.filter.allow": ["10.0.0.0/8", "192.168.0.0/16"],
    "xpack.security.http.filter.deny": ["_all"]
  }
}
```

### 9.3 Network Binding

```yaml
# elasticsearch.yml — network security
network.host: ["_local_", "_site_"]
network.bind_host: ["0.0.0.0"]
network.publish_host: ["10.0.1.10"]

# Restrict HTTP to specific interface
http.host: "10.0.1.10"
http.port: 9200

# Transport on different interface/port
transport.host: "10.0.2.10"
transport.port: 9300
```

---

## 10. Audit Logging

### 10.1 Audit Log Configuration

```yaml
# elasticsearch.yml — comprehensive audit logging
xpack.security.audit.enabled: true

xpack.security.audit.logfile.events.include:
  - authentication_success
  - authentication_failed
  - access_denied
  - access_granted
  - connection_denied
  - connection_granted
  - run_as_denied
  - run_as_granted
  - tampered_request
  - anonymous_access_denied
  - security_config_change

xpack.security.audit.logfile.events.exclude:
  - system_access_granted

# Filter by user (reduce noise from system users)
xpack.security.audit.logfile.events.ignore_filters:
  system_users:
    users: ["kibana_system", "beats_system", "elastic/fleet-server"]

# Output settings
xpack.security.audit.logfile.emit_node_name: true
xpack.security.audit.logfile.emit_node_id: true
xpack.security.audit.logfile.emit_node_host_address: true
```

### 10.2 Audit Log Format and Analysis

Audit events are written to `<cluster_name>_audit.json`:

```json
{
  "type": "audit",
  "timestamp": "2026-05-22T14:30:15.123Z",
  "node.id": "xyzabc123",
  "node.name": "es-data-01",
  "event.type": "rest",
  "event.action": "access_denied",
  "authentication.type": "API_KEY",
  "user.name": "monitoring-key",
  "user.roles": ["monitoring_reader"],
  "origin.type": "rest",
  "origin.address": "10.0.1.50",
  "request.method": "DELETE",
  "url.path": "/critical-data/_doc/123",
  "request.id": "abc123"
}
```

### 10.3 Forwarding Audit Logs to Elasticsearch

Send audit logs to a dedicated monitoring cluster for analysis:

```yaml
# filebeat.yml — ship audit logs to monitoring cluster
filebeat.inputs:
  - type: log
    paths:
      - /var/log/elasticsearch/*_audit.json
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["https://monitoring-cluster:9200"]
  index: "audit-logs-%{+yyyy.MM.dd}"
  username: "beats_system"
  password: "${BEATS_PASSWORD}"
```

### 10.4 Security Event Monitoring Queries

```http
// Failed authentication attempts in the last hour
POST /audit-logs-*/_search
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "event.action": "authentication_failed" } },
        { "range": { "timestamp": { "gte": "now-1h" } } }
      ]
    }
  },
  "aggs": {
    "by_user": {
      "terms": { "field": "user.name", "size": 20 }
    },
    "by_ip": {
      "terms": { "field": "origin.address", "size": 20 }
    }
  }
}

// Access denied events grouped by user and action
POST /audit-logs-*/_search
{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        { "term": { "event.action": "access_denied" } },
        { "range": { "timestamp": { "gte": "now-24h" } } }
      ]
    }
  },
  "aggs": {
    "by_user": {
      "terms": { "field": "user.name", "size": 10 },
      "aggs": {
        "denied_urls": {
          "terms": { "field": "url.path", "size": 5 }
        }
      }
    }
  }
}

// Privilege escalation detection: role changes
POST /audit-logs-*/_search
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "event.action": "security_config_change" } },
        { "range": { "timestamp": { "gte": "now-7d" } } }
      ]
    }
  },
  "sort": [{ "timestamp": "desc" }]
}
```

---

## 11. Encryption at Rest

### 11.1 OS-Level Encryption

Elasticsearch does not provide built-in encryption at rest. The recommended approaches:

1. **dm-crypt/LUKS (Linux)**:
```bash
# Encrypt the data partition
cryptsetup luksFormat /dev/sdb
cryptsetup open /dev/sdb es-data
mkfs.ext4 /dev/mapper/es-data
mount /dev/mapper/es-data /var/lib/elasticsearch
```

2. **Cloud provider encryption**:
- AWS: EBS encryption (AES-256, managed by KMS)
- GCP: Persistent disk encryption (default, or customer-managed keys)
- Azure: Azure Disk Encryption (BitLocker/dm-crypt)

3. **Hardware encryption**: Self-encrypting drives (SEDs) with OPAL support.

### 11.2 Snapshot Repository Encryption

Encrypt snapshots stored in object storage:

```http
// S3 with server-side encryption
PUT /_snapshot/encrypted-repo
{
  "type": "s3",
  "settings": {
    "bucket": "es-snapshots-encrypted",
    "server_side_encryption": true,
    "sse_algorithm": "aws:kms",
    "kms_key_id": "arn:aws:kms:eu-south-1:123456789012:key/abcd-1234"
  }
}

// GCS with customer-managed encryption keys
PUT /_snapshot/gcs-encrypted-repo
{
  "type": "gcs",
  "settings": {
    "bucket": "es-snapshots-encrypted",
    "client": "default"
  }
}
// GCS CMEK is configured at the bucket level, not in Elasticsearch
```

---

## 12. Kibana Security Integration

### 12.1 Kibana Spaces

Kibana Spaces provide UI-level multi-tenancy. Combined with RBAC, they control which dashboards and features users can access:

```http
// Create a Kibana space
POST /api/spaces/space
{
  "id": "analytics",
  "name": "Analytics Team",
  "description": "Dashboards and visualizations for the analytics team",
  "disabledFeatures": ["siem", "apm", "uptime", "infrastructure"],
  "color": "#aabbcc",
  "initials": "AN"
}

// Role with access to a specific space
POST /_security/role/analytics_user
{
  "cluster": ["monitor"],
  "indices": [
    {
      "names": ["metrics-*", "logs-*"],
      "privileges": ["read"]
    }
  ],
  "applications": [
    {
      "application": "kibana-.kibana",
      "privileges": [
        "feature_discover.all",
        "feature_dashboard.all",
        "feature_visualize.read",
        "feature_canvas.read"
      ],
      "resources": ["space:analytics"]
    }
  ]
}
```

### 12.2 Kibana Feature Privileges

```http
// Role with specific feature access per space
POST /_security/role/dashboard_viewer
{
  "cluster": [],
  "indices": [
    {
      "names": ["logs-*"],
      "privileges": ["read", "view_index_metadata"]
    }
  ],
  "applications": [
    {
      "application": "kibana-.kibana",
      "privileges": [
        "feature_dashboard.read",
        "feature_discover.read"
      ],
      "resources": ["space:default", "space:analytics"]
    }
  ]
}
```

---

## 13. Troubleshooting

### 13.1 Authentication Failures

```http
// Check which realm authenticated a user
POST /_security/_authenticate
// (with the user's credentials)

// Response includes:
// "authentication_realm": { "name": "ldap1", "type": "ldap" }
// If authentication fails, check:
// 1. Realm ordering (file realm first, then native, then LDAP/SAML)
// 2. LDAP connectivity: nslookup, openssl s_client
// 3. Bind DN credentials in keystore
// 4. User search base_dn and filter
```

### 13.2 Authorization Failures (403)

```http
// Check a user's effective privileges
GET /_security/user/app-developer/_has_privileges
{
  "cluster": ["monitor", "manage"],
  "index": [
    {
      "names": ["logs-*"],
      "privileges": ["read", "write", "delete"]
    }
  ]
}

// Check who the current authenticated user is and their roles
GET /_security/_authenticate

// Check effective privileges for the authenticated user
GET /_security/user/_has_privileges
{
  "index": [
    {
      "names": ["target-index"],
      "privileges": ["read"]
    }
  ]
}
```

### 13.3 Certificate Issues

```bash
# Test TLS connectivity
openssl s_client -connect es-node:9200 -CAfile /path/to/ca.crt

# Check certificate expiration
openssl x509 -in /etc/elasticsearch/certs/node.crt -noout -dates

# Verify certificate chain
openssl verify -CAfile /path/to/ca.crt /etc/elasticsearch/certs/node.crt
```

```http
// List all certificates known to Elasticsearch
GET /_ssl/certificates
```

### 13.4 LDAP Connectivity Issues

```bash
# Test LDAP connectivity
ldapsearch -H ldaps://ldap.example.com:636 \
  -D "cn=es-service,ou=serviceaccounts,dc=example,dc=com" \
  -W \
  -b "ou=users,dc=example,dc=com" \
  "(sAMAccountName=testuser)"
```

### 13.5 Audit Log Not Recording Events

Check:
1. `xpack.security.audit.enabled: true` in elasticsearch.yml.
2. The events you expect are in the `include` list and not in the `exclude` list.
3. The user is not in `ignore_filters`.
4. The audit log file permissions allow Elasticsearch to write.

---

## 14. FAQ

### Q1: What is the difference between API keys and service tokens?

API keys are general-purpose access tokens that can be created by any authenticated user and have customizable privileges. Service tokens are specifically designed for Elastic Stack components (Kibana, Fleet, APM Server) and are tied to predefined service accounts with fixed privileges. Use API keys for application-level access and service tokens for stack component authentication.

### Q2: Can I use both LDAP and SAML simultaneously?

Yes. Configure both realms with different `order` values. Users can authenticate via either mechanism. The realm chain is evaluated in order — LDAP typically comes before SAML. Users logging in via the Kibana UI use SAML; users authenticating via API calls typically use LDAP or native realm.

### Q3: How do I rotate the `elastic` superuser password?

```http
PUT /_security/user/elastic/_password
{
  "password": "new-secure-password"
}
```

Or use the command-line tool:
```bash
./bin/elasticsearch-reset-password -u elastic
```

### Q4: What happens when a certificate expires?

TLS connections using the expired certificate fail. Inter-node communication breaks (cluster becomes non-functional), and client connections are refused. Always monitor certificate expiration dates and rotate certificates before they expire. Elasticsearch logs certificate expiration warnings 30 days before expiry.

### Q5: How does DLS affect aggregation results?

DLS filters are applied before aggregations. A user with DLS `"term": { "region": "north" }` will see aggregation results only from documents in the "north" region. This is by design — users should never see data they are not authorized to access, even in aggregated form.

### Q6: Can I use Elasticsearch security without X-Pack?

In ES 8.x, security is part of the default distribution and enabled by default. There is no separate X-Pack installation. The basic security features (TLS, native auth, RBAC) are free. Advanced features (LDAP, SAML, FLS, DLS, audit logging) require a Gold or Platinum license.

### Q7: How do I handle emergency access when LDAP is down?

Configure the file realm with order 0 (checked first) and create an emergency admin user in the file realm. This user authenticates locally without LDAP, providing emergency access during directory outages.

### Q8: What is the recommended approach for multi-tenant security?

Combine DLS (document-level security) with custom metadata on users:
1. Store the `tenant_id` in each user's metadata.
2. Use a DLS query template: `{"term": {"tenant_id": "{{_user.metadata.tenant_id}}"}}`.
3. Each tenant's data is filtered automatically — no application-level filtering needed.

---

## 15. Exercises

### Exercise 1: PKI Setup

Set up a 3-node cluster with full TLS encryption:
1. Generate a CA using `elasticsearch-certutil`.
2. Generate per-node certificates with proper SANs.
3. Configure transport and HTTP TLS on all nodes.
4. Verify inter-node communication with `full` verification mode.
5. Test that a client connecting without TLS is rejected.

### Exercise 2: RBAC Design

Design roles for a company with the following teams:
- **SRE Team**: full access to logs and metrics, manage ILM and pipelines.
- **Developers**: read access to their application's logs only (filter by `service` field).
- **Security Team**: read access to all indices including audit logs, can view users and roles.
- **Data Analysts**: read access to business metrics, limited Kibana features (Discover + Dashboard only).
- **Service Accounts**: each microservice can only write to its own index pattern.

Write the complete role definitions and user/role mappings.

### Exercise 3: FLS/DLS Multi-Tenant Isolation

Set up a multi-tenant environment:
1. Create an index with documents from 3 tenants.
2. Create roles with DLS that restrict each tenant to their data.
3. Add FLS to hide the `internal_notes` and `cost_price` fields from tenant users.
4. Verify isolation by searching as each tenant user and confirming they cannot see other tenants' data or hidden fields.

### Exercise 4: Audit Log Analysis

Enable audit logging with all event types. Perform the following actions and verify they appear in the audit log:
1. Successful authentication (native user)
2. Failed authentication (wrong password)
3. Access denied (user without sufficient privileges)
4. Security config change (create a new role)
5. Run-as request (impersonation)

Write a Kibana dashboard that visualizes: authentication failures by IP, access denials by user, and security config changes over time.

### Exercise 5: Certificate Rotation Drill

Perform a zero-downtime certificate rotation:
1. Generate new certificates signed by a new CA.
2. Add the new CA to the trust store alongside the old CA.
3. Roll out new node certificates one node at a time.
4. Remove the old CA from the trust store after all nodes have new certificates.
5. Verify that no connections were dropped during the rotation.

---

*Questo documento fa parte del modulo 08 "Elasticsearch" della Data Encyclopedia.*
