# SQLite: Integrazione con Linguaggi di Programmazione

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
1. Python Integration
2. JavaScript/Node.js Integration
3. Java Integration
4. C/C++ Integration
5. Go Integration
6. Ruby Integration
7. PHP Integration
8. C#/.NET Integration
9. Swift Integration
10. Cross-Language Considerations

---

## 1. Python Integration

### 1.1 Basic Connection

```python
import sqlite3

# Connessione base
conn = sqlite3.connect('mydb.sqlite')

# Cursor per eseguire query
cursor = conn.cursor()

# Eseguire SQL
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE
    )
''')

# Inserire dati
cursor.execute(
    "INSERT INTO users (name, email) VALUES (?, ?)",
    ('John Doe', 'john@example.com')
)

# Salvare modifiche
conn.commit()

# Query con risultati
cursor.execute("SELECT * FROM users")
results = cursor.fetchall()

# Oppure iterare
for row in cursor.execute("SELECT * FROM users"):
    print(row)

# Chiudere connessione
conn.close()
```

### 1.2 Context Manager

```python
# Usare context manager per gestione automatica
with sqlite3.connect('mydb.sqlite') as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()
    
    # Auto-commit on success
    # Auto-rollback on exception

# Equivalente a:
try:
    conn = sqlite3.connect('mydb.sqlite')
    # operazioni
    conn.commit()
except:
    conn.rollback()
finally:
    conn.close()
```

### 1.3 Row Factory

```python
# Default: restituisce tuple
conn = sqlite3.connect('mydb.sqlite')
cursor = conn.execute("SELECT id, name FROM users")
row = cursor.fetchone()  # (1, 'John')

# Restituire dizionario
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

conn.row_factory = dict_factory
cursor = conn.execute("SELECT * FROM users")
row = cursor.fetchone()  # {'id': 1, 'name': 'John'}

# Alternativa: usare sqlite3.Row
conn.row_factory = sqlite3.Row
cursor = conn.execute("SELECT * FROM users")
row = cursor.fetchone()
print(row['id'], row['name'])  # access by name

# Named tuple
from collections import namedtuple

def named_tuple_factory(cursor, row):
    fields = [col[0] for col in cursor.description]
    RowClass = namedtuple('Row', fields)
    return RowClass(*row)

conn.row_factory = named_tuple_factory
row = cursor.fetchone()
print(row.id, row.name)
```

### 1.4 Type Handling

```python
import sqlite3
from datetime import datetime, date

# Register adapters per tipi custom

# Adattare date per SQLite
def adapt_date(d):
    return d.isoformat()

sqlite3.register_adapter(date, adapt_date)

# Convertire date da SQLite
def convert_date(s):
    return datetime.strptime(s, '%Y-%m-%d').date()

sqlite3.register_converter('DATE', convert_date)

# Connessione con type detection
conn = sqlite3.connect(
    'mydb.sqlite',
    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
)

# Ora le date vengono automaticamente convertite
cursor.execute("SELECT created_at FROM users")
row = cursor.fetchone()
print(type(row[0]))  # <class 'datetime.date'>
```

### 1.5 Transactions

```python
# Transaction esplicita
with sqlite3.connect('mydb.sqlite') as conn:
    cursor = conn.cursor()
    
    # Iniziare transaction
    cursor.execute("BEGIN")
    
    try:
        cursor.execute("INSERT INTO orders (total) VALUES (?)", (100,))
        order_id = cursor.lastrowid
        
        cursor.execute(
            "INSERT INTO order_items (order_id, product_id, qty) VALUES (?, ?, ?)",
            (order_id, 1, 2)
        )
        
        cursor.execute("COMMIT")
    except Exception as e:
        cursor.execute("ROLLBACK")
        raise e

# Transaction con savepoint
with sqlite3.connect('mydb.sqlite') as conn:
    conn.execute("BEGIN")
    try:
        conn.execute("INSERT INTO log (msg) VALUES ('start')")
        
        conn.execute("SAVEPOINT sp1")
        try:
            conn.execute("INSERT INTO log (msg) VALUES ('error')")
            raise Exception("Simulated error")
        except:
            conn.execute("ROLLBACK TO SAVEPOINT sp1")
        
        conn.execute("COMMIT")
    except:
        conn.execute("ROLLBACK")
```

### 1.6 Thread Safety

```python
import sqlite3
import threading

# Ogni thread dovrebbe avere la propria connessione
# SQLite non è thread-safe con connessione condivisa

# Pattern: thread-local connections
thread_local = threading.local()

def get_db():
    if not hasattr(thread_local, 'db'):
        thread_local.db = sqlite3.connect('mydb.sqlite')
    return thread_local.db

# In multithreading:
def worker():
    db = get_db()
    db.execute("SELECT * FROM users")

# Alternativa: connection pool
from queue import Queue
import threading

class ConnectionPool:
    def __init__(self, path, size=5):
        self.pool = Queue(size)
        for _ in range(size):
            conn = sqlite3.connect(path, check_same_thread=False)
            self.pool.put(conn)
    
    def get(self, timeout=30):
        return self.pool.get(timeout=timeout)
    
    def return_(self, conn):
        self.pool.put(conn)
```

---

## 2. JavaScript/Node.js Integration

### 2.1 Node.js con better-sqlite3

```javascript
const Database = require('better-sqlite3');

const db = new Database('mydb.sqlite');

// Prepare statement
const stmt = db.prepare('SELECT * FROM users WHERE id = ?');
const user = stmt.get(1);

// Multiple
const all = db.prepare('SELECT * FROM users').all();

// Iterate
const stmt = db.prepare('SELECT * FROM users');
for (const user of stmt.iterate()) {
    console.log(user.name);
}

// Transactions
const trans = db.transaction(() => {
    const info = db.prepare('INSERT INTO users (name) VALUES (?)').run('John');
    db.prepare('INSERT INTO logs (msg) VALUES (?)').run('Added user');
});

trans();
```

### 2.2 Node.js con sqlite3

```javascript
const sqlite3 = require('sqlite3').verbose();

const db = new sqlite3.Database('mydb.sqlite');

db.serialize(() => {
    // Create table
    db.run('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)');
    
    // Insert
    db.run('INSERT INTO users (name) VALUES (?)', ['John'], function(err) {
        console.log('Inserted with id:', this.lastID);
    });
    
    // Query
    db.each('SELECT * FROM users', (err, row) => {
        console.log(row.id, row.name);
    });
    
    // Close
    db.close();
});
```

### 2.3 Promise-Based Wrapper

```javascript
// Promise-based SQLite wrapper
class SQLite {
    constructor(filename) {
        this.db = new (require('better-sqlite3'))(filename);
    }
    
    run(sql, params = []) {
        return this.db.prepare(sql).run(...params);
    }
    
    get(sql, params = []) {
        return this.db.prepare(sql).get(...params);
    }
    
    all(sql, params = []) {
        return this.db.prepare(sql).all(...params);
    }
    
    transaction(fn) {
        return this.db.transaction(fn)();
    }
    
    close() {
        this.db.close();
    }
}

// Usage
async function main() {
    const db = new SQLite('mydb.sqlite');
    
    const user = await db.get('SELECT * FROM users WHERE id = ?', [1]);
    console.log(user);
    
    db.close();
}
```

### 2.4 Browser con WebAssembly

```javascript
// SQLite compilato per WebAssembly
import initSqlJs from 'sql.js';

async function initDB() {
    const SQL = await initSqlJs();
    const db = new SQL.Database();
    
    db.run('CREATE TABLE users (id, name)');
    db.run("INSERT INTO users VALUES (1, 'John')");
    
    const results = db.exec('SELECT * FROM users');
    console.log(results);
    
    return db;
}

// Salvare/caricare database
function saveDB(db) {
    const data = db.export();
    const buffer = new Uint8Array(data);
    // Save to localStorage or IndexedDB
}

function loadDB(buffer) {
    const SQL = require('sql.js');
    const db = new SQL.Database(buffer);
    return db;
}
```

---

## 3. Java Integration

### 3.1 JDBC Basic

```java
import java.sql.*;

public class SQLiteExample {
    public static void main(String[] args) throws Exception {
        // Load SQLite JDBC driver
        Class.forName("org.sqlite.JDBC");
        
        // Connect
        Connection conn = DriverManager.getConnection(
            "jdbc:sqlite:mydb.sqlite"
        );
        
        // Create statement
        Statement stmt = conn.createStatement();
        
        // Execute query
        ResultSet rs = stmt.executeQuery("SELECT * FROM users");
        while (rs.next()) {
            int id = rs.getInt("id");
            String name = rs.getString("name");
            System.out.println(id + ": " + name);
        }
        
        // Close
        rs.close();
        stmt.close();
        conn.close();
    }
}
```

### 3.2 Prepared Statements

```java
// Use prepared statements for efficiency and security
PreparedStatement pstmt = conn.prepareStatement(
    "INSERT INTO users (name, email) VALUES (?, ?)"
);

pstmt.setString(1, "John Doe");
pstmt.setString(2, "john@example.com");
pstmt.executeUpdate();

pstmt.setString(1, "Jane Doe");
pstmt.setString(2, "jane@example.com");
pstmt.executeUpdate();

pstmt.close();

// Query con parameters
PreparedStatement pstmt = conn.prepareStatement(
    "SELECT * FROM users WHERE id = ?"
);
pstmt.setInt(1, userId);
ResultSet rs = pstmt.executeQuery();
```

### 3.3 Transactions

```java
conn.setAutoCommit(false);

try {
    PreparedStatement pstmt1 = conn.prepareStatement(
        "INSERT INTO orders (total) VALUES (?)"
    );
    pstmt1.setDouble(1, 100.0);
    pstmt1.executeUpdate();
    
    long orderId = getLastInsertId(conn);
    
    PreparedStatement pstmt2 = conn.prepareStatement(
        "INSERT INTO order_items (order_id, product_id, qty) VALUES (?, ?, ?)"
    );
    pstmt2.setLong(1, orderId);
    pstmt2.setInt(2, 1);
    pstmt2.setInt(3, 2);
    pstmt2.executeUpdate();
    
    conn.commit();
} catch (Exception e) {
    conn.rollback();
    throw e;
} finally {
    conn.setAutoCommit(true);
}
```

### 3.4 SQLiteConfig

```java
import org.sqlite.SQLiteConfig;

SQLiteConfig config = new SQLiteConfig();
config.setJournalMode(SQLiteConfig.JournalMode.WAL);
config.setSynchronous(SQLiteConfig.SynchronousMode.NORMAL);
config.setCacheSize(4000);
config.setTempStore(SQLiteConfig.TempStore.MEMORY);

Connection conn = DriverManager.getConnection(
    "jdbc:mydb.sqlite",
    config.toProperties()
);
```

---

## 4. C/C++ Integration

### 4.1 Basic API Usage

```c
#include <sqlite3.h>
#include <stdio.h>

int main() {
    sqlite3 *db;
    char *err_msg = 0;
    int rc;
    
    // Aprire database
    rc = sqlite3_open("mydb.sqlite", &db);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "Cannot open database: %s\n", sqlite3_errmsg(db));
        return 1;
    }
    
    // Creare tabella
    const char *sql = "CREATE TABLE IF NOT EXISTS users ("  \
        "id INTEGER PRIMARY KEY AUTOINCREMENT," \
        "name TEXT NOT NULL," \
        "email TEXT" \
    ");";
    
    rc = sqlite3_exec(db, sql, 0, 0, &err_msg);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "SQL error: %s\n", err_msg);
        sqlite3_free(err_msg);
    }
    
    // Inserire dati
    sql = "INSERT INTO users (name, email) VALUES ('John', 'john@example.com');";
    rc = sqlite3_exec(db, sql, 0, 0, &err_msg);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "SQL error: %s\n", err_msg);
        sqlite3_free(err_msg);
    }
    
    // Chiudere
    sqlite3_close(db);
    return 0;
}
```

### 4.2 Prepared Statements

```c
// Prepared statement
sqlite3_stmt *stmt;
const char *sql = "INSERT INTO users (name, email) VALUES (?, ?)";

// Prepare
rc = sqlite3_prepare_v2(db, sql, -1, &stmt, NULL);
if (rc != SQLITE_OK) {
    fprintf(stderr, "Prepare failed: %s\n", sqlite3_errmsg(db));
    return 1;
}

// Bind parameters
sqlite3_bind_text(stmt, 1, "John", -1, SQLITE_TRANSIENT);
sqlite3_bind_text(stmt, 2, "john@example.com", -1, SQLITE_TRANSIENT);

// Execute
rc = sqlite3_step(stmt);
if (rc != SQLITE_DONE) {
    fprintf(stderr, "Execution failed: %s\n", sqlite3_errmsg(db));
}

// Cleanup
sqlite3_finalize(stmt);
```

### 4.3 Query con risultati

```c
// Query con results
sqlite3_stmt *stmt;
const char *sql = "SELECT id, name, email FROM users WHERE id = ?";

rc = sqlite3_prepare_v2(db, sql, -1, &stmt, NULL);
if (rc != SQLITE_OK) {
    // error
}

sqlite3_bind_int(stmt, 1, 1);

while ((rc = sqlite3_step(stmt)) == SQLITE_ROW) {
    int id = sqlite3_column_int(stmt, 0);
    const char *name = (const char*)sqlite3_column_text(stmt, 1);
    const char *email = (const char*)sqlite3_column_text(stmt, 2);
    
    printf("User: %d, %s, %s\n", id, name, email ? email : "NULL");
}

if (rc != SQLITE_DONE) {
    // error
}

sqlite3_finalize(stmt);
```

### 4.4 Custom Functions

```c
// Funzione custom
static void md5_func(sqlite3_context *context, int argc, sqlite3_value **argv) {
    const unsigned char *str = sqlite3_value_text(argv[0]);
    if (str == NULL) {
        sqlite3_result_null(context);
        return;
    }
    
    // Compute MD5 (using external library or custom)
    unsigned char md5[16];
    compute_md5(str, md5);
    
    // Convert to hex
    char hex[33];
    for (int i = 0; i < 16; i++) {
        sprintf(hex + 2*i, "%02x", md5[i]);
    }
    
    sqlite3_result_text(context, hex, -1, SQLITE_TRANSIENT);
}

// Register function
sqlite3_create_function(
    db,
    "md5",
    1,
    SQLITE_UTF8,
    NULL,
    md5_func,
    NULL,
    NULL
);
```

---

## 5. Go Integration

### 5.1 Using go-sqlite3

```go
package main

import (
    "database/sql"
    "fmt"
    _ "github.com/mattn/go-sqlite3"
)

func main() {
    db, err := sql.Open("sqlite3", "./mydb.sqlite")
    if err != nil {
        panic(err)
    }
    defer db.Close()
    
    // Create table
    _, err = db.Exec(`
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE
        )
    `)
    if err != nil {
        panic(err)
    }
    
    // Insert
    result, err := db.Exec(
        "INSERT INTO users (name, email) VALUES (?, ?)",
        "John Doe", "john@example.com",
    )
    if err != nil {
        panic(err)
    }
    
    id, _ := result.LastInsertId()
    fmt.Println("Inserted ID:", id)
    
    // Query
    rows, err := db.Query("SELECT id, name, email FROM users")
    if err != nil {
        panic(err)
    }
    defer rows.Close()
    
    for rows.Next() {
        var id int
        var name, email string
        if err := rows.Scan(&id, &name, &email); err != nil {
            panic(err)
        }
        fmt.Printf("User: %d, %s, %s\n", id, name, email)
    }
}
```

### 5.2 Prepared Statements

```go
// Prepared statement
stmt, err := db.Prepare("SELECT * FROM users WHERE id = ?")
if err != nil {
    panic(err)
}
defer stmt.Close()

var user struct {
    ID    int
    Name  string
    Email string
}

err = stmt.QueryRow(1).Scan(&user.ID, &user.Name, &user.Email)
if err != nil {
    panic(err)
}

// Reuse for multiple queries
for _, id := range []int{1, 2, 3} {
    err = stmt.QueryRow(id).Scan(&user.ID, &user.Name, &user.Email)
    // ...
}
```

### 5.3 Transactions

```go
tx, err := db.Begin()
if err != nil {
    panic(err)
}
defer tx.Rollback()

_, err = tx.Exec("INSERT INTO orders (total) VALUES (?)", 100)
if err != nil {
    panic(err)
}

orderID, err := tx.LastInsertId()
if err != nil {
    panic(err)
}

_, err = tx.Exec(
    "INSERT INTO order_items (order_id, product_id, qty) VALUES (?, ?, ?)",
    orderID, 1, 2,
)
if err != nil {
    panic(err)
}

if err := tx.Commit(); err != nil {
    panic(err)
}
```

---

## 6. Ruby Integration

### 6.1 Using SQLite3 Gem

```ruby
require 'sqlite3'

# Aprire database
db = SQLite3::Database.new('mydb.sqlite')

# Creare tabella
db.execute <<-SQL
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE
  )
SQL

# Inserire dati
db.execute(
    "INSERT INTO users (name, email) VALUES (?, ?)",
    ['John Doe', 'john@example.com']
)

# Query
db.results_as_hash = true
db.execute("SELECT * FROM users") do |row|
  puts "ID: #{row['id']}, Name: #{row['name']}"
end

# Chiudere
db.close
```

### 6.2 Prepared Statements

```ruby
# Prepare statement
stmt = db.prepare("SELECT * FROM users WHERE id = ?")

# Execute with parameters
stmt.execute(1) do |row|
  puts row
end

# Multiple executions
stmt.execute(2) do |row|
  puts row
end

stmt.close

# Insert con placeholder
insert_stmt = db.prepare("INSERT INTO users (name, email) VALUES (?, ?)")
['Alice', 'Bob'].each do |name|
  insert_stmt.execute(name, "#{name.downcase}@example.com")
end
insert_stmt.close
```

### 6.3 Transactions

```ruby
db.transaction do |tx|
  tx.execute("INSERT INTO orders (total) VALUES (?)", 100)
  order_id = tx.get_first_value("SELECT last_insert_rowid()")
  tx.execute(
    "INSERT INTO order_items (order_id, product_id, qty) VALUES (?, ?, ?)",
    [order_id, 1, 2]
  )
end  # Auto-commit on success, rollback on exception
```

---

## 7. PHP Integration

### 7.1 Using PDO

```php
<?php
try {
    // Connessione
    $pdo = new PDO('sqlite:mydb.sqlite');
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    // Creare tabella
    $pdo->exec('
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE
        )
    ');
    
    // Insert con prepare
    $stmt = $pdo->prepare('INSERT INTO users (name, email) VALUES (:name, :email)');
    $stmt->execute(['name' => 'John Doe', 'email' => 'john@example.com']);
    
    // Query
    $stmt = $pdo->prepare('SELECT * FROM users WHERE id = :id');
    $stmt->execute(['id' => 1]);
    $user = $stmt->fetch(PDO::FETCH_ASSOC);
    
    print_r($user);
    
} catch (PDOException $e) {
    echo 'Error: ' . $e->getMessage();
}
?>
```

### 7.2 SQLite3 Class

```php
<?php
$db = new SQLite3('mydb.sqlite');

// Create table
$db->exec('CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT
)');

// Prepare statements
$stmt = $db->prepare('INSERT INTO users (name) VALUES (:name)');
$stmt->bindValue(':name', 'John', SQLITE3_TEXT);
$stmt->execute();

// Query
$result = $db->query('SELECT * FROM users');
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    print_r($row);
}

// Close
$db->close();
?>
```

---

## 8. C#/.NET Integration

### 8.1 Using Microsoft.Data.Sqlite

```csharp
using Microsoft.Data.Sqlite;
using System;

class Program
{
    static void Main()
    {
        using var connection = new SqliteConnection("Data Source=mydb.sqlite");
        connection.Open();
        
        // Create table
        using var command = connection.CreateCommand();
        command.CommandText = @"
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT
            )
        ";
        command.ExecuteNonQuery();
        
        // Insert
        command.CommandText = "INSERT INTO users (name, email) VALUES (@name, @email)";
        command.Parameters.AddWithValue("@name", "John Doe");
        command.Parameters.AddWithValue("@email", "john@example.com");
        command.ExecuteNonQuery();
        
        // Query
        command.CommandText = "SELECT * FROM users";
        using var reader = command.ExecuteReader();
        while (reader.Read())
        {
            Console.WriteLine($"ID: {reader.GetInt32(0)}, Name: {reader.GetString(1)}");
        }
    }
}
```

### 8.2 Dapper Integration

```csharp
using Dapper;
using Microsoft.Data.Sqlite;

var connection = new SqliteConnection("Data Source=mydb.sqlite");
connection.Open();

// Query
var users = connection.Query<User>("SELECT * FROM users");

// Insert
connection.Execute(
    "INSERT INTO users (name, email) VALUES (@Name, @Email)",
    new { Name = "John", Email = "john@example.com" }
);

public class User
{
    public int Id { get; set; }
    public string Name { get; set; }
    public string Email { get; set; }
}
```

---

## 9. Swift Integration

### 9.1 Using SQLite.swift

```swift
import SQLite

// Aprire database
let db = try Connection("mydb.sqlite")

// Definire tabella
let users = Table("users")
let id = Expression<Int64>("id")
let name = Expression<String>("name")
let email = Expression<String?>("email")

// Create
try db.run(users.create(ifNotExists: true) { t in
    t.column(id, primaryKey: .autoincrement)
    t.column(name)
    t.column(email)
})

// Insert
let insert = users.insert(
    name <- "John Doe",
    email <- "john@example.com"
)
let rowId = try db.run(insert)

// Query
for user in try db.prepare(users) {
    print("\(user[id]) - \(user[name])")
}

// Filter
let query = users.filter(email != nil)
for user in try db.prepare(query) {
    print(user[name])
}
```

### 9.2 Raw SQLite with Swift

```swift
import Foundation
import SQLite3

var db: OpaquePointer?

if sqlite3_open("mydb.sqlite", &db) == SQLITE_OK {
    // Create table
    let sql = "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)"
    sqlite3_exec(db, sql, nil, nil, nil)
    
    // Insert
    let insert = "INSERT INTO users (name) VALUES (?)"
    var stmt: OpaquePointer?
    if sqlite3_prepare_v2(db, insert, -1, &stmt, nil) == SQLITE_OK {
        sqlite3_bind_text(stmt, 1, "John", -1, nil)
        sqlite3_step(stmt)
    }
    sqlite3_finalize(stmt)
    
    // Query
    let query = "SELECT * FROM users"
    if sqlite3_prepare_v2(db, query, -1, &stmt, nil) == SQLITE_OK {
        while sqlite3_step(stmt) == SQLITE_ROW {
            let id = sqlite3_column_int(stmt, 0)
            let name = String(cString: sqlite3_column_text(stmt, 1))
            print("\(id): \(name)")
        }
    }
    sqlite3_finalize(stmt)
}

sqlite3_close(db)
```

---

## 10. Cross-Language Considerations

### 10.1 Data Type Mapping

```sql
-- Type mappings tra linguaggi:
-- Python         | JavaScript      | Java         | Go           | C#
-- ---------------+-----------------+--------------+--------------+-------
-- None           | null            | null         | nil          | null
-- int            | number          | int/long     | int          | int
-- float          | number          | double/float | float64      | double
-- str            | string          | String       | string       | string
-- bytes          | Uint8Array      | byte[]       | []byte       | byte[]
-- datetime       | Date            | Date/Instant | time.Time    | DateTime
-- bool            | boolean         | boolean      | bool         | bool
```

### 10.2 Encoding Considerations

```python
# SQLite usa UTF-8
# Assicurarsi che tutti i linguaggi usino UTF-8

# Python 3: default UTF-8
# JavaScript: UTF-8 per default
# Java: specificare UTF-8 nel connection string
new Connection("jdbc:sqlite:mydb.sqlite;charset=UTF-8")

# Go: default UTF-8
# C#: default UTF-8
```

### 10.3 Thread Safety

```python
# Python: non condividere connessioni tra thread
# Java: usa connection pooling
# Go: single connection non è thread-safe
# JavaScript/Node: async, usa callbacks/promises
# C#: async/await, connection pooling
# Swift: connessione per thread o serial queue
```

---

*Questo documento fa parte del modulo 04 "SQLite Portatile" della Data Encyclopedia.*