# SQLite: Sviluppo Mobile

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
1. iOS Development
2. Android Development
3. Cross-Platform Mobile
4. Mobile Database Patterns
5. Sync and Offline
6. Performance on Mobile
7. Security on Mobile
8. Data Migration on Mobile
9. Testing Mobile Apps
10. Best Practices

---

## 1. iOS Development

### 1.1 SQLite on iOS

```swift
import Foundation
import SQLite3

// Database manager singleton
class DatabaseManager {
    static let shared = DatabaseManager()
    private var db: OpaquePointer?
    
    private init() {
        openDatabase()
    }
    
    private func openDatabase() {
        let documentsPath = FileManager.default.urls(
            for: .documentDirectory, 
            in: .userDomainMask
        ).first!
        
        let dbPath = documentsPath.appendingPathComponent("app.db").path
        
        if sqlite3_open(dbPath, &db) != SQLITE_OK {
            print("Error opening database")
        }
    }
    
    // CRUD operations
    func createUser(name: String, email: String) -> Int64 {
        let sql = "INSERT INTO users (name, email) VALUES (?, ?)"
        var stmt: OpaquePointer?
        
        if sqlite3_prepare_v2(db, sql, -1, &stmt, nil) == SQLITE_OK {
            sqlite3_bind_text(stmt, 1, (name as NSString).utf8String, -1, nil)
            sqlite3_bind_text(stmt, 2, (email as NSString).utf8String, -1, nil)
            
            if sqlite3_step(stmt) == SQLITE_DONE {
                return sqlite3_last_insert_rowid(db)
            }
        }
        
        sqlite3_finalize(stmt)
        return -1
    }
    
    func getUsers() -> [(id: Int64, name: String, email: String)] {
        var users: [(id: Int64, name: String, email: String)] = []
        let sql = "SELECT id, name, email FROM users"
        var stmt: OpaquePointer?
        
        if sqlite3_prepare_v2(db, sql, -1, &stmt, nil) == SQLITE_OK {
            while sqlite3_step(stmt) == SQLITE_ROW {
                let id = sqlite3_column_int64(stmt, 0)
                let name = String(cString: sqlite3_column_text(stmt, 1))
                let email = String(cString: sqlite3_column_text(stmt, 2))
                users.append((id: id, name: name, email: email))
            }
        }
        
        sqlite3_finalize(stmt)
        return users
    }
}
```

### 1.2 SQLite.swift Library

```swift
import SQLite

class DatabaseService {
    private var db: Connection?
    
    // Tables
    private let users = Table("users")
    private let id = Expression<Int64>("id")
    private let name = Expression<String>("name")
    private let email = Expression<String?>("email")
    private let createdAt = Expression<Date>("created_at")
    
    init() {
        setupDatabase()
    }
    
    private func setupDatabase() {
        do {
            let path = NSSearchPathForDirectoriesInDomains(
                .documentDirectory, .userDomainMask, true
            ).first!
            
            db = try Connection("\(path)/app.sqlite3")
            
            try db?.run(users.create(ifNotExists: true) { t in
                t.column(id, primaryKey: .autoincrement)
                t.column(name)
                t.column(email)
                t.column(createdAt, defaultValue: Date())
            })
        } catch {
            print("Database setup error: \(error)")
        }
    }
    
    // CRUD
    func insertUser(name: String, email: String?) throws -> Int64 {
        let insert = users.insert(
            self.name <- name,
            self.email <- email
        )
        return try db!.run(insert)
    }
    
    func getAllUsers() throws -> [(id: Int64, name: String, email: String?)] {
        var results: [(id: Int64, name: String, email: String?)] = []
        
        for row in try db!.prepare(users) {
            results.append((
                id: row[id],
                name: row[name],
                email: row[email]
            ))
        }
        
        return results
    }
    
    func updateUser(id: Int64, name: String) throws {
        let user = users.filter(self.id == id)
        try db?.run(user.update(self.name <- name))
    }
    
    func deleteUser(id: Int64) throws {
        let user = users.filter(self.id == id)
        try db?.run(user.delete())
    }
}
```

### 1.3 GRDB.swift

```swift
import GRDB

// Model
struct User: Codable, FetchableRecord, PersistableRecord {
    var id: Int64?
    var name: String
    var email: String?
    var createdAt: Date
    
    static let databaseTableName = "users"
    
    mutating func didInsert(_ inserted: InsertionSuccess) {
        id = inserted.rowID
    }
}

// Database queue
var dbQueue: DatabaseQueue!

func setupDatabase() throws {
    let databaseURL = try FileManager.default
        .url(for: .documentDirectory, in: .userDomainMask, appropriateFor: nil, create: true)
        .appendingPathComponent("db.sqlite")
    
    var config = Configuration()
    config.foreignKeysEnabled = true
    
    dbQueue = try DatabaseQueue(path: databaseURL.path, configuration: config)
    
    // Migration
    var migrator = DatabaseMigrator()
    
    migrator.registerMigration("v1") { db in
        try db.create(table: "users") { t in
            t.autoIncrementedPrimaryKey("id")
            t.column("name", .text).notNull()
            t.column("email", .text)
            t.column("createdAt", .datetime).notNull()
        }
    }
    
    try migrator.migrate(dbQueue)
}

// Usage
func insertUser(_ user: User) throws -> User {
    try dbQueue.write { db in
        var user = user
        try user.insert(db)
        return user
    }
}

func fetchUsers() throws -> [User] {
    try dbQueue.read { db in
        try User.fetchAll(db)
    }
}
```

### 1.4 FMDB Wrapper

```objc
// Objective-C con FMDB
#import "FMDatabase.h"

FMDatabase *db = [FMDatabase databaseWithPath:path];

if ([db open]) {
    [db executeUpdate:@"CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)"];
    
    // Insert
    [db executeUpdate:@"INSERT INTO users (name, email) VALUES (?, ?)", @"John", @"john@example.com"];
    
    // Query
    FMResultSet *results = [db executeQuery:@"SELECT * FROM users"];
    while ([results next]) {
        NSLog(@"User: %@ - %@", [results stringForColumn:@"name"], [results stringForColumn:@"email"]);
    }
    
    [db close];
}
```

---

## 2. Android Development

### 2.1 SQLiteOpenHelper

```java
public class DatabaseHelper extends SQLiteOpenHelper {
    private static final String DATABASE_NAME = "app.db";
    private static final int DATABASE_VERSION = 1;
    
    public DatabaseHelper(Context context) {
        super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }
    
    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE users (" +
            "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
            "name TEXT NOT NULL, " +
            "email TEXT, " +
            "created_at DATETIME DEFAULT CURRENT_TIMESTAMP" +
        ")");
        
        db.execSQL("CREATE TABLE posts (" +
            "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
            "user_id INTEGER NOT NULL, " +
            "title TEXT NOT NULL, " +
            "content TEXT, " +
            "FOREIGN KEY(user_id) REFERENCES users(id)" +
        ")");
    }
    
    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        // Handle migrations
        if (oldVersion < 2) {
            // Add new column
            db.execSQL("ALTER TABLE users ADD COLUMN phone TEXT");
        }
    }
}
```

### 2.2 Repository Pattern

```java
public class UserRepository {
    private final DatabaseHelper dbHelper;
    
    public UserRepository(Context context) {
        this.dbHelper = new DatabaseHelper(context);
    }
    
    public long insert(User user) {
        SQLiteDatabase db = dbHelper.getWritableDatabase();
        ContentValues values = new ContentValues();
        values.put("name", user.getName());
        values.put("email", user.getEmail());
        
        long id = db.insert("users", null, values);
        db.close();
        return id;
    }
    
    public User getById(long id) {
        SQLiteDatabase db = dbHelper.getReadableDatabase();
        Cursor cursor = db.query(
            "users",
            null,
            "id = ?",
            new String[]{String.valueOf(id)},
            null, null, null
        );
        
        User user = null;
        if (cursor.moveToFirst()) {
            user = new User();
            user.setId(cursor.getLong(0));
            user.setName(cursor.getString(1));
            user.setEmail(cursor.getString(2));
        }
        
        cursor.close();
        db.close();
        return user;
    }
    
    public List<User> getAll() {
        List<User> users = new ArrayList<>();
        SQLiteDatabase db = dbHelper.getReadableDatabase();
        
        Cursor cursor = db.rawQuery("SELECT * FROM users ORDER BY name", null);
        
        while (cursor.moveToNext()) {
            User user = new User();
            user.setId(cursor.getLong(0));
            user.setName(cursor.getString(1));
            user.setEmail(cursor.getString(2));
            users.add(user);
        }
        
        cursor.close();
        db.close();
        return users;
    }
    
    public int update(User user) {
        SQLiteDatabase db = dbHelper.getWritableDatabase();
        ContentValues values = new ContentValues();
        values.put("name", user.getName());
        values.put("email", user.getEmail());
        
        int count = db.update("users", values, "id = ?", 
            new String[]{String.valueOf(user.getId())});
        db.close();
        return count;
    }
    
    public int delete(long id) {
        SQLiteDatabase db = dbHelper.getWritableDatabase();
        int count = db.delete("users", "id = ?", new String[]{String.valueOf(id)});
        db.close();
        return count;
    }
}
```

### 2.3 Room Database

```java
// Entity
@Entity(tableName = "users")
public class User {
    @PrimaryKey(autoGenerate = true)
    private long id;
    
    @ColumnInfo(name = "name")
    private String name;
    
    @ColumnInfo(name = "email")
    private String email;
    
    // getters and setters
}

// DAO
@Dao
public interface UserDao {
    @Insert
    long insert(User user);
    
    @Update
    void update(User user);
    
    @Delete
    void delete(User user);
    
    @Query("SELECT * FROM users")
    List<User> getAll();
    
    @Query("SELECT * FROM users WHERE id = :id")
    User getById(long id);
    
    @Query("SELECT * FROM users WHERE name LIKE '%' || :query || '%'")
    List<User> search(String query);
}

// Database
@Database(entities = {User.class}, version = 1)
public abstract class AppDatabase extends RoomDatabase {
    public abstract UserDao userDao();
}

// Usage
AppDatabase db = Room.databaseBuilder(
    getApplicationContext(),
    AppDatabase.class,
    "app_database"
).build();

UserDao userDao = db.userDao();
```

### 2.4 Kotlin Coroutines with Room

```kotlin
// suspend functions for async
@Dao
interface UserDao {
    @Insert(suspend = true)
    suspend fun insert(user: User): Long
    
    @Query("SELECT * FROM users")
    suspend fun getAll(): List<User>
    
    @Query("SELECT * FROM users")
    fun getAllFlow(): Flow<List<User>>  // reactive
}

// ViewModel
class UserViewModel(private val userDao: UserDao) : ViewModel() {
    
    val users: LiveData<List<User>> = userDao.getAll().asLiveData()
    
    fun insert(name: String, email: String) {
        viewModelScope.launch(Dispatchers.IO) {
            userDao.insert(User(name = name, email = email))
        }
    }
    
    suspend fun getUserById(id: Long): User? {
        return withContext(Dispatchers.IO) {
            userDao.getById(id)
        }
    }
}
```

---

## 3. Cross-Platform Mobile

### 3.1 Flutter with sqflite

```dart
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class DatabaseHelper {
  static Database _database;
  
  static Future<Database> get database async {
    if (_database != null) return _database;
    _database = await _initDatabase();
    return _database;
  }
  
  static Future<Database> _initDatabase() async {
    String path = join(await getDatabasesPath(), 'app.db');
    
    return await openDatabase(
      path,
      version: 1,
      onCreate: _onCreate,
    );
  }
  
  static Future<void> _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT
      )
    ''');
  }
  
  // CRUD operations
  static Future<int> insert(String table, Map<String, dynamic> data) async {
    final db = await database;
    return await db.insert(table, data);
  }
  
  static Future<List<Map<String, dynamic>>> query(
    String table, {
    String where,
    List<dynamic> whereArgs,
    String orderBy,
  }) async {
    final db = await database;
    return await db.query(
      table,
      where: where,
      whereArgs: whereArgs,
      orderBy: orderBy,
    );
  }
  
  static Future<int> update(
    String table,
    Map<String, dynamic> data, {
    String where,
    List<dynamic> whereArgs,
  }) async {
    final db = await database;
    return await db.update(
      table,
      data,
      where: where,
      whereArgs: whereArgs,
    );
  }
  
  static Future<int> delete(
    String table, {
    String where,
    List<dynamic> whereArgs,
  }) async {
    final db = await database;
    return await db.delete(
      table,
      where: where,
      whereArgs: whereArgs,
    );
  }
}
```

### 3.2 React Native with react-native-sqlite-storage

```javascript
import SQLite from 'react-native-sqlite-storage';

SQLite.enablePromise(true);

class DatabaseService {
  database = null;
  
  async init() {
    this.database = await SQLite.openDatabase({
      name: 'app.db',
      location: 'default'
    });
    
    await this.createTables();
  }
  
  async createTables() {
    await this.database.executeSql(`
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT
      )
    `);
  }
  
  async insertUser(name, email) {
    const [result] = await this.database.executeSql(
      'INSERT INTO users (name, email) VALUES (?, ?)',
      [name, email]
    );
    return result.insertId;
  }
  
  async getUsers() {
    const [results] = await this.database.executeSql(
      'SELECT * FROM users'
    );
    
    const users = [];
    for (let i = 0; i < results.rows.length; i++) {
      users.push(results.rows.item(i));
    }
    return users;
  }
  
  async updateUser(id, name, email) {
    await this.database.executeSql(
      'UPDATE users SET name = ?, email = ? WHERE id = ?',
      [name, email, id]
    );
  }
  
  async deleteUser(id) {
    await this.database.executeSql(
      'DELETE FROM users WHERE id = ?',
      [id]
    );
  }
}

export default new DatabaseService();
```

### 3.3 Xamarin with SQLite.NET

```csharp
// Portable Class Library
public class User {
    [PrimaryKey, AutoIncrement]
    public int Id { get; set; }
    
    public string Name { get; set; }
    public string Email { get; set; }
}

public class DatabaseService {
    SQLiteAsyncConnection db;
    
    public async Task Init() {
        if (db != null) return;
        
        db = new SQLiteAsyncConnection("app.db");
        
        await db.CreateTableAsync<User>();
    }
    
    public Task<int> Insert(User user) {
        return db.InsertAsync(user);
    }
    
    public Task<List<User>> GetAll() {
        return db.Table<User>().ToListAsync();
    }
    
    public Task<int> Update(User user) {
        return db.UpdateAsync(user);
    }
    
    public Task<int> Delete(User user) {
        return db.DeleteAsync(user);
    }
}
```

---

## 4. Mobile Database Patterns

### 4.1 Repository Pattern

```kotlin
// Kotlin - Repository per astrazione
interface UserRepository {
    suspend fun getAll(): List<User>
    suspend fun getById(id: Long): User?
    suspend fun insert(user: User): Long
    suspend fun update(user: User)
    suspend fun delete(user: User)
}

class SQLiteUserRepository(context: Context): UserRepository {
    private val dbHelper = DatabaseHelper(context)
    
    override suspend fun getAll(): List<User> = withContext(Dispatchers.IO) {
        dbHelper.getAll()
    }
    
    override suspend fun getById(id: Long): User? = withContext(Dispatchers.IO) {
        dbHelper.getById(id)
    }
    
    override suspend fun insert(user: User): Long = withContext(Dispatchers.IO) {
        dbHelper.insert(user)
    }
    
    override suspend fun update(user: User) = withContext(Dispatchers.IO) {
        dbHelper.update(user)
    }
    
    override suspend fun delete(user: User) = withContext(Dispatchers.IO) {
        dbHelper.delete(user.id)
    }
}
```

### 4.2 Dependency Injection

```swift
// Swift - Protocol + DI
protocol DatabaseServiceProtocol {
    func insert(_ user: User) throws -> Int64
    func fetchAll() throws -> [User]
    func delete(_ user: User) throws
}

class SQLiteDatabaseService: DatabaseServiceProtocol {
    private let db: Connection
    
    init(path: String) throws {
        db = try Connection(path)
        try createTables()
    }
    
    func insert(_ user: User) throws -> Int64 {
        try db.run(users.insert(
            name <- user.name,
            email <- user.email
        ))
    }
    
    // ...
}

// In ViewModel/UseCase
class UserViewModel {
    private let database: DatabaseServiceProtocol
    
    init(database: DatabaseServiceProtocol) {
        self.database = database
    }
}
```

### 4.3 Offline-First Architecture

```kotlin
// Android - Offline-first con Repository
class OfflineFirstUserRepository(
    private val localDb: UserDao,
    private val remoteApi: UserApi
): UserRepository {
    
    override suspend fun getAll(): List<User> {
        // Try local first
        val localUsers = localDb.getAll()
        if (localUsers.isNotEmpty()) {
            return localUsers
        }
        
        // Fallback to remote
        return try {
            val remoteUsers = remoteApi.getUsers()
            localDb.insertAll(remoteUsers)
            remoteUsers
        } catch (e: Exception) {
            emptyList()
        }
    }
    
    suspend fun sync() {
        try {
            val remoteUsers = remoteApi.getUsers()
            localDb.insertAll(remoteUsers)
        } catch (e: Exception) {
            // Handle sync failure
        }
    }
}
```

---

## 5. Sync and Offline

### 5.1 Conflict Resolution

```kotlin
// Strategy per conflitti
enum class ConflictResolution {
    SERVER_WINS,
    CLIENT_WINS,
    MERGE,
    MANUAL
}

class SyncManager(
    private val localDb: Database,
    private val remoteApi: RemoteApi
) {
    suspend fun syncTable(table: String, resolution: ConflictResolution) {
        val localChanges = localDb.getUnsyncedChanges(table)
        val remoteChanges = remoteApi.getChanges(table)
        
        when (resolution) {
            ConflictResolution.SERVER_WINS -> applyRemoteChanges(remoteChanges)
            ConflictResolution.CLIENT_WINS -> pushLocalChanges(localChanges)
            ConflictResolution.MERGE -> mergeChanges(localChanges, remoteChanges)
            ConflictResolution.MANUAL -> queueForReview(localChanges, remoteChanges)
        }
    }
}
```

### 5.2 Change Tracking

```kotlin
// Tabella per tracciare modifiche
@Entity(tableName = "sync_log")
data class SyncLog(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val tableName: String,
    val recordId: Long,
    val operation: String, // INSERT, UPDATE, DELETE
    val timestamp: Long = System.currentTimeMillis(),
    val synced: Boolean = false
)

// Trigger-style tracking in Room
class SyncTrackingDao {
    @Insert
    suspend fun logChange(change: SyncLog)
    
    @Query("SELECT * FROM sync_log WHERE synced = 0")
    suspend fun getPendingChanges(): List<SyncLog>
    
    @Query("UPDATE sync_log SET synced = 1 WHERE id IN (:ids)")
    suspend fun markSynced(ids: List<Long>)
}
```

### 5.3 Background Sync

```swift
// iOS - Background fetch
class AppDelegate: UIResponder, UIApplicationDelegate {
    
    func application(
        _ application: UIApplication, 
        performFetchWithCompletionHandler completionHandler: @escaping (UIBackgroundFetchResult) -> Void
    ) {
        Task {
            do {
                try await SyncManager.shared.syncAll()
                completionHandler(.newData)
            } catch {
                completionHandler(.failed)
            }
        }
    }
}
```

```java
// Android - WorkManager
public class SyncWorker extends Worker {
    @Override
    public Result doWork() {
        try {
            syncRepository.syncWithServer();
            return Result.success();
        } catch (Exception e) {
            return Result.retry();
        }
    }
}

// Schedule
WorkManager.getInstance().enqueueUniquePeriodicWork(
    "sync_work",
    ExistingPeriodicWorkPolicy.KEEP,
    PeriodicWorkRequestBuilder<SyncWorker>()
        .setConstraints(Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build())
        .setInterval(15, TimeUnit.MINUTES)
        .build()
);
```

---

## 6. Performance on Mobile

### 6.1 Database Optimization

```sql
-- Indici per query frequenti
CREATE INDEX idx_posts_user ON posts(user_id);
CREATE INDEX idx_posts_created ON posts(created_at DESC);

-- WAL mode per migliori performance
PRAGMA journal_mode = WAL;

-- Cache size
PRAGMA cache_size = -2000;  -- 2MB

-- Synchronous per balance
PRAGMA synchronous = NORMAL;
```

### 6.2 Lazy Loading

```kotlin
// Android - Paging library con Room
@Entity
data class User(@PrimaryKey val id: Long, val name: String, val email: String)

class UserDao {
    @Query("SELECT * FROM users ORDER BY name")
    fun getUsersPaged(): DataSource.Factory<Int, User> {
        return RemoteKeyDao.getUsersPaged()
    }
}

// In Repository
fun getUsersPaged(): LiveData<PagedList<User>> {
    return LivePagedListBuilder(dao.getUsersPaged(), 
        PagedList.Config.Builder()
            .setPageSize(20)
            .setEnablePlaceholders(false)
            .build()
    ).build()
}
```

### 6.3 Connection Pooling

```kotlin
// Avoid creating many connections
// Use singleton or dependency injection
class DatabaseManager private constructor(context: Context) {
    
    private val db: SQLiteDatabase = context.openOrCreateDatabase(
        DATABASE_NAME, 
        Context.MODE_PRIVATE, 
        null
    )
    
    companion object {
        @Volatile
        private var INSTANCE: DatabaseManager? = null
        
        fun getInstance(context: Context): DatabaseManager {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: DatabaseManager(context.applicationContext).also {
                    INSTANCE = it
                }
            }
        }
    }
}
```

### 6.4 Batch Operations

```kotlin
// Batch insert for performance
fun insertAll(users: List<User>) {
    db.beginTransaction()
    try {
        val stmt = db.compileStatement(
            "INSERT INTO users (name, email) VALUES (?, ?)"
        )
        
        users.forEach { user ->
            stmt.bindString(1, user.name)
            stmt.bindString(2, user.email)
            stmt.executeInsert()
            stmt.clearBindings()
        }
        
        db.setTransactionSuccessful()
    } finally {
        db.endTransaction()
    }
}
```

---

## 7. Security on Mobile

### 7.1 Encryption

```kotlin
// Android - SQLCipher
class EncryptedDatabaseHelper(context: Context) {
    
    private val factory = SQLiteDatabaseFactory()
    
    fun getEncryptedDb(): SQLiteDatabase {
        val passphrase = getSecureKey(context)
        return factory.openDatabase(
            DatabaseBuilder()
                .setName("encrypted.db")
                .setKey(passphrase)
                .build()
        )
    }
    
    private fun getSecureKey(context: Context): ByteArray {
        // Derive key from secure storage
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        
        return masterKey.encoded
    }
}
```

```swift
// iOS - Encryption with SQLCipher
// Use encrypted database with keychain
func openEncryptedDatabase() -> OpaquePointer? {
    let key = getKeyFromKeychain()
    sqlite3_key(db, key, Int32(key.count))
}
```

### 7.2 Secure Storage

```swift
// iOS - Store key in Keychain
import Security

func saveKey(_ key: String, for identifier: String) {
    let data = key.data(using: .utf8)!
    
    let query: [String: Any] = [
        kSecClass as String: kSecClassGenericPassword,
        kSecAttrAccount as String: identifier,
        kSecValueData as String: data,
        kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
    ]
    
    SecItemAdd(query as CFDictionary, nil)
}

func getKey(for identifier: String) -> String? {
    let query: [String: Any] = [
        kSecClass as String: kSecClassGenericPassword,
        kSecAttrAccount as String: identifier,
        kSecReturnData as String: true
    ]
    
    var result: AnyObject?
    let status = SecItemCopyMatching(query as CFDictionary, &result)
    
    if status == errSecSuccess {
        return String(data: result as! Data, encoding: .utf8)
    }
    return nil
}
```

```kotlin
// Android - EncryptedSharedPreferences + SQLCipher
val masterKey = MasterKey.Builder(context)
    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
    .build()

val sharedPrefs = EncryptedSharedPreferences.create(
    context,
    "secure_prefs",
    masterKey,
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
)
```

### 7.3 Input Validation

```sql
-- Parameterized queries always!
-- In Android/Kotlin
fun getUser(id: Long): User? {
    val db = readableDatabase
    val cursor = db.rawQuery(
        "SELECT * FROM users WHERE id = ?",
        arrayOf(id.toString())
    )
    // ...
}

// NOT string concatenation!
```

---

## 8. Data Migration on Mobile

### 8.1 Schema Migration

```kotlin
// Android Room - Migration
val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(database: SupportSQLiteDatabase) {
        database.execSQL("ALTER TABLE users ADD COLUMN phone TEXT")
    }
}

val MIGRATION_2_3 = object : Migration(2, 3) {
    override fun migrate(database: SupportSQLiteDatabase) {
        database.execSQL("CREATE TABLE posts (id INTEGER PRIMARY KEY, user_id INTEGER)")
    }
}

val db = Room.databaseBuilder(
    context,
    AppDatabase::class.java,
    "database"
)
    .addMigrations(MIGRATION_1_2, MIGRATION_2_3)
    .build()
```

### 8.2 Data Migration

```kotlin
// Migrate data during schema change
val MIGRATION_3_4 = object : Migration(3, 4) {
    override fun migrate(database: SupportSQLiteDatabase) {
        // Create new table
        database.execSQL("CREATE TABLE users_new (id INTEGER PRIMARY KEY, name TEXT, email TEXT, created_at INTEGER)")
        
        // Copy data with transformation
        database.execSQL("""
            INSERT INTO users_new (id, name, email, created_at)
            SELECT id, name, email, 
                COALESCE(created_at, (strftime('%s', 'now') * 1000))
            FROM users
        """)
        
        // Drop old table
        database.execSQL("DROP TABLE users")
        
        // Rename
        database.execSQL("ALTER TABLE users_new RENAME TO users")
    }
}
```

---

## 9. Testing Mobile Apps

### 9.1 Unit Testing

```kotlin
// Test repository with in-memory database
@Test
fun testGetAllUsers() {
    // Setup in-memory database
    val db = Room.inMemoryDatabaseBuilder(
        ApplicationProvider.getApplicationContext(),
        AppDatabase::class.java
    ).build()
    
    // Insert test data
    db.userDao().insert(User(name = "Test"))
    
    // Verify
    val users = db.userDao().getAll().first()
    assertEquals(1, users.size)
    assertEquals("Test", users[0].name)
}
```

```swift
// iOS test
func testInsertUser() {
    let db = try! Database(path: ":memory:")
    
    try! db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    
    try db.run("INSERT INTO users (name) VALUES (?)", "Test")
    
    let count = try! db.scalar("SELECT COUNT(*) FROM users")
    XCTAssertEqual(count, 1)
}
```

### 9.2 Integration Testing

```kotlin
// Test full flow
@Test
fun testUserRegistration() {
    // Create user
    val user = User(name = "John", email = "john@test.com")
    val id = userRepository.insert(user)
    
    // Verify in database
    val retrieved = userRepository.getById(id)
    assertEquals("John", retrieved?.name)
    
    // Verify sync status
    assertFalse(retrieved?.synced)
}
```

---

## 10. Best Practices

### 10.1 Architecture Best Practices

```kotlin
// 1. Single source of truth
// 2. Repository pattern
// 3. Dependency injection
// 4. Offline-first
// 5. Proper error handling

// Core principles:
// - Database is an implementation detail
// - Expose only use cases
// - Test at each layer
```

### 10.2 Performance Best Practices

```sql
-- Index foreign keys
CREATE INDEX idx_user_posts ON posts(user_id);

-- Use WAL mode
PRAGMA journal_mode = WAL;

-- Don't store large blobs in SQLite
-- Use file system for images/videos
-- Store only file paths in DB
```

### 10.3 Security Best Practices

```kotlin
// 1. Encrypt database with SQLCipher
// 2. Store encryption key securely (Keychain/EncryptedSharedPreferences)
// 3. Use parameterized queries
// 4. Validate all input
// 5. Don't log sensitive data
```

---

*Questo documento fa parte del modulo 04 "SQLite Portatile" della Data Encyclopedia.*