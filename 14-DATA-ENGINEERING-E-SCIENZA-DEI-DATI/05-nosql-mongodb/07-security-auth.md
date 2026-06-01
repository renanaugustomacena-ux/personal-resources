# MongoDB: Security e Authentication

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-04  
> Versione: 1.0.0  
> Stato: expanded

## Skip list
- [x] Bozza iniziale
- [ ] Review tecnica
- [ ] Formattazione
- [ ] Pubblicazione

## Indice
1. Authentication Methods
2. Authorization and Roles
3. Network Security
4. Encryption
5. Audit Logging
6. Field-Level Security
7. User Management
8. Security Best Practices

---

## 1. Authentication Methods

### 1.1 SCRAM-SHA-256 (Default)

```javascript
// Enable authentication (in mongod.conf)
security:
  authorization: enabled

// Create user with SCRAM-SHA-256 (default)
db.createUser({
  user: "admin",
  pwd: "securePassword123",
  roles: [
    { role: "root", db: "admin" }
  ]
})

// Authenticate
db.auth("admin", "securePassword123")
```

### 1.2 LDAP Authentication (Enterprise)

```javascript
// Configure LDAP (in mongod.conf)
security:
  authenticationMechanisms: "PLAIN"

// Create LDAP user mapping
db.getSiblingDB("$external").createUser({
  user: "cn=admin,cn=users,dc=example,dc=com",
  roles: [{ role: "readWrite", db: "mydb" }]
})

// Authenticate with LDAP
db.getSiblingDB("$external").auth({ user: "admin", password: "password" })
```

### 1.3 x.509 Certificate Authentication

```javascript
// Configure (in mongod.conf)
net:
  tls:
    mode: requireTLS
    certificateKeyFile: /path/to/server.pem
    CAFile: /path/to/ca.pem

// Create user from certificate
db.getSiblingDB("$external").createUser({
  user: "CN=mongoserver,O=MyOrg",
  roles: [{ role: "root", db: "admin" }]
})

// Connect with certificate
const client = new MongoClient("mongodb://server:27017", {
  tlsCertificateKeyFile: "/path/to/client.pem",
  tlsCAFile: "/path/to/ca.pem"
})
```

---

## 2. Authorization and Roles

### 2.1 Built-in Roles

```javascript
// Database user roles
// - read: read collections
// - readWrite: read and write collections

// Database admin roles
// - dbAdmin: manage collections (not user management)
// - dbOwner: all dbAdmin + user management
// - userAdmin: manage users and roles
// - userAdminAnyDatabase: manage across all databases

// Cluster admin roles
// - clusterAdmin: manage cluster
// - clusterManager: monitor/manage
// - clusterMonitor: read-only cluster access
// - hostManager: manage servers

// Backup/restore
// - backup: backup data
// - root: all privileges
// - readAnyDatabase: read all
// - readWriteAnyDatabase: read/write all
```

### 2.2 Custom Roles

```javascript
// Create custom role
db.createRole({
  role: "analytics_reader",
  privileges: [
    {
      resource: { db: "analytics", collection: "reports" },
      actions: ["find", "aggregate"]
    },
    {
      resource: { db: "analytics", collection: "metrics" },
      actions: ["find"]
    }
  ],
  roles: []
})

// Add privileges to role
db.grantPrivilegesToRole("analytics_reader", [
  {
    resource: { db: "analytics", collection: "" },
    actions: ["viewRole"]
  }
])

// Add existing roles
db.grantRolesToRole("analytics_reader", ["read"])

```

### 2.3 Role Management

```javascript
// List roles
db.getRole("readWrite")
db.getRoles({ showPrivileges: true, showBuiltinRoles: true })

// Update role
db.updateRole("analytics_reader", {
  privileges: [
    { resource: { db: "mydb", collection: "coll" }, actions: ["find"] }
  ]
})

// Drop role
db.dropRole("old_role")

// List users with role
db.getUsers()
db.getUser("username").roles
```

---

## 3. Network Security

### 3.1 Bind IP Configuration

```javascript
// In mongod.conf - only listen on specific IPs
net:
  port: 27017
  bindIp: 127.0.0.1,10.0.0.1  // Localhost and internal

// Bind to localhost only (for development)
net:
  bindIp: 127.0.0.1
```

### 3.2 TLS/SSL Configuration

```javascript
// Enable TLS (in mongod.conf)
net:
  tls:
    mode: requireTLS
    certificateKeyFile: /path/to/server.pem
    CAFile: /path/to/ca.pem
    allowConnectionsWithoutCertificates: false

// Client TLS configuration
const client = new MongoClient("mongodb://server:27017", {
  tls: true,
  tlsCertificateKeyFile: "/path/to/client.pem",
  tlsCAFile: "/path/to/ca.pem",
  tlsInsecure: false  // Verify server cert
})
```

### 3.3 Firewall Configuration

```bash
# iptables rules for MongoDB
# Allow internal network
iptables -A INPUT -p tcp -s 10.0.0.0/8 --dport 27017 -j ACCEPT

# Drop external
iptables -A INPUT -p tcp --dport 27017 -j DROP
```

---

## 4. Encryption

### 4.1 Encryption at Rest

```javascript
// Enable encryption at rest (in mongod.conf)
storage:
  engine: wiredTiger
  wiredTiger:
    engineConfig:
      encryptionKeyFile: /path/to/keyfile

// Key rotation
db.adminCommand({
  rotateCertificates: 1
})

db.adminCommand({
  rotateEncryptionKey: 1
})
```

### 4.2 Field-Level Encryption (FLE)

```javascript
// Enable client-side field encryption
const client = new MongoClient("mongodb://localhost:27017", {
  autoEncryption: {
    keyVaultNamespace: "encryption.__keyVault",
    kmsProviders: {
      local: {
        key: Buffer.from(keyBase64, "base64")
      }
    }
  }
})

// Create encrypted client
const encryptedClient = new MongoClient("mongodb://localhost:27017", {
  autoEncryption: {
    keyVaultNamespace: "encryption.keys",
    kmsProviders: { local: { key: keyBuffer } },
    schemaMap: {
      "mydb.sensitive": {
        "bsonType": "object",
        "properties": {
          "ssn": {
            "encrypt": {
              "keyId": keyId,
              "bsonType": "string",
              "algorithm": "AEAD_AES_256_CBC-HMAC_SHA_512-Deterministic"
            }
          }
        }
      }
    }
  }
})

// Queries work automatically
// Encrypted fields are transparently decrypted
```

---

## 5. Audit Logging

### 5.1 Audit Configuration

```javascript
// Enable audit (in mongod.conf)
security:
  auditLog:
    destination: file
    format: JSON
    path: /var/log/mongodb/audit.log
```

### 5.2 Audit Filter

```javascript
// Configure audit filter (in mongod.conf)
security:
  auditLog:
    destination: file
    filter: '{ "atype": { "$in": ["createCollection", "dropCollection"] } }'

// Filter examples:
// Log all auth events
'{ "atype": "authenticate" }'

// Log specific operations
'{ "atype": "createUser", "param.db": "mydb" }'

// Exclude read operations
'{ "atype": { "$nin": ["find"] } }'
```

---

## 6. Field-Level Security

### 6.1 Restriction with Projection

```javascript
// Hide sensitive fields from users
db.adminCommand({
  projection: "users",
  restriction: {
    field: "password",
    mode: "exclude"
  }
})

// Or in find
db.users.find({}, { password: 0, ssn: 0 })
```

### 6.2 Views for Security

```javascript
// Create view that excludes sensitive data
db.createView("public_users", "users", [
  { $project: { _id: 1, name: 1, email: 1, role: 1, _password: 0, ssn: 0 } }
])

// User queries view, cannot see sensitive fields
db.public_users.find()
```

---

## 7. User Management

### 7.1 Create Users

```javascript
// Create database user
db.createUser({
  user: "appuser",
  pwd: passwordPrompt(),
  roles: [
    { role: "readWrite", db: "mydb" }
  ]
})

// Create admin user
db.createUser({
  user: "admin",
  pwd: "securePassword",
  roles: [
    { role: "userAdminAnyDatabase", db: "admin" },
    { role: "readWriteAnyDatabase", db: "admin" }
  ]
})
```

### 7.2 Update Users

```javascript
// Update password
db.updateUser("appuser", { pwd: "newpassword" })

// Update roles
db.grantRolesToUser("appuser", [{ role: "readWrite", db: "anotherdb" }])
db.revokeRolesFromUser("appuser", [{ role: "read", db: "mydb" }])

// Lock user (prevent login)
db.adminCommand({ updateUser: "appuser", customData: { locked: true } })
```

---

## 8. Security Best Practices

### 8.1 Configuration Checklist

```javascript
// 1. Enable authentication
security:
  authorization: enabled

// 2. Use strong passwords
// 3. Use TLS for all connections
// 4. Use role-based access control
// 5. Enable audit logging
// 6. Use encryption at rest
// 7. Restrict network access
// 8. Regular security updates

// Don't:
// - Use default ports in production
// - Use admin for application connections
// - Store passwords in code
```

### 8.2 Security Hardening

```javascript
// Disable JavaScript execution if not needed
setParameter: 1
javascriptEnabled: false

// Disable server-side execution of scripts
security:
  javascriptEnabled: false

// Rate limiting
setParameter: 1
authenticationLatencyThresholdMs: 100
```

---

*Questo documento fa parte del modulo 05 "NoSQL MongoDB" della Data Encyclopedia.*