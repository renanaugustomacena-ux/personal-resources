# Module 6.3: Mobile & Cross-Platform Engineering

> **Module 06.3** · **Last updated:** 2026-05-22

## Guiding ideas

1. **Flutter state management: Provider, Riverpod, Bloc.**
2. **Kotlin coroutines: structured concurrency for Android.**
3. **React Native + Expo for JS-skill teams.**
4. **Offline-first sync: SQLite + reconciliation.**
5. **Native bridges: the boundary where cross-platform frameworks pay their tax.**
6. **App lifecycle management: foreground, background, terminated states matter.**
7. **Push notifications and deep linking are infrastructure, not features.**

---

## Table of Contents

1. [Native iOS Engineering](#1-native-ios-engineering)
2. [Native Android Engineering](#2-native-android-engineering)
3. [React Native Architecture](#3-react-native-architecture)
4. [Flutter Architecture](#4-flutter-architecture)
5. [Kotlin Multiplatform (KMP)](#5-kotlin-multiplatform-kmp)
6. [Other Cross-Platform Frameworks](#6-other-cross-platform-frameworks)
7. [Native Bridges and Interop](#7-native-bridges-and-interop)
8. [App Lifecycle Management](#8-app-lifecycle-management)
9. [Background Execution](#9-background-execution)
10. [Push Notifications](#10-push-notifications)
11. [Deep Linking and Navigation](#11-deep-linking-and-navigation)
12. [Offline-First Architecture](#12-offline-first-architecture)
13. [State Management Patterns](#13-state-management-patterns)
14. [Performance Optimization](#14-performance-optimization)
15. [App Store Optimization and Distribution](#15-app-store-optimization-and-distribution)
16. [Mobile CI/CD](#16-mobile-cicd)
17. [Mobile Security](#17-mobile-security)
18. [Testing Mobile Applications](#18-testing-mobile-applications)
19. [Framework Selection Guide](#19-framework-selection-guide)
20. [Exercises](#20-exercises)
21. [References](#21-references)

---

## 1. Native iOS Engineering

### 1.1 Language: Swift

Swift is Apple's primary language since 2014. Key characteristics:

- **Value semantics:** `struct` over `class` by default. Structs are stack-allocated,
  copied on assignment (with COW optimization for collections). No shared
  mutable state surprises.
- **Protocol-oriented programming:** Protocols define contracts. Extensions provide
  default implementations. Prefer composition over inheritance.
- **Optionals:** `nil` is a compile-time checked concept. No null pointer exceptions
  at runtime (unless you force-unwrap with `!`).
- **Result type:** `Result<Success, Failure>` for typed error handling.
- **String safety:** `String` is Unicode-correct by default. `String.Index` is
  not an integer — prevents off-by-one errors on multi-byte characters.

```swift
// Value type with protocol conformance
struct User: Identifiable, Codable, Hashable {
    let id: UUID
    var name: String
    var email: String

    // Computed property
    var displayName: String {
        name.isEmpty ? email : name
    }
}

// Protocol with default implementation
protocol DataFetching {
    associatedtype Model: Decodable
    func fetch() async throws -> Model
}

extension DataFetching {
    func fetch() async throws -> Model {
        let (data, _) = try await URLSession.shared.data(from: endpoint)
        return try JSONDecoder().decode(Model.self, from: data)
    }
}
```

### 1.2 SwiftUI (Declarative UI)

```swift
struct ProductListView: View {
    @State private var searchText = ""
    @State private var selectedCategory: Category?

    var body: some View {
        NavigationStack {
            List(filteredProducts) { product in
                NavigationLink(value: product) {
                    ProductRow(product: product)
                }
            }
            .searchable(text: $searchText)
            .navigationTitle("Products")
            .navigationDestination(for: Product.self) { product in
                ProductDetailView(product: product)
            }
        }
    }

    var filteredProducts: [Product] {
        products.filter { product in
            (searchText.isEmpty || product.name.localizedCaseInsensitiveContains(searchText)) &&
            (selectedCategory == nil || product.category == selectedCategory)
        }
    }
}
```

**Property wrappers for state:**

| Wrapper | Ownership | Use case |
|---|---|---|
| `@State` | Owned by this view | Simple local state |
| `@Binding` | Reference to parent's state | Child view modifies parent's data |
| `@Observable` (Swift 5.9+) | Reference type observation | Model objects, replaces ObservableObject |
| `@Environment` | System or app-level values | Color scheme, locale, custom deps |
| `@AppStorage` | UserDefaults-backed | Persistent preferences |

### 1.3 Swift Concurrency

```swift
// Structured concurrency with async/await
func fetchDashboard() async throws -> Dashboard {
    async let user = fetchUser()
    async let orders = fetchOrders()
    async let recommendations = fetchRecommendations()

    // All three requests run concurrently
    return try await Dashboard(
        user: user,
        orders: orders,
        recommendations: recommendations
    )
}

// Actors: thread-safe mutable state
actor ImageCache {
    private var cache: [URL: UIImage] = [:]

    func image(for url: URL) async throws -> UIImage {
        if let cached = cache[url] {
            return cached
        }
        let (data, _) = try await URLSession.shared.data(from: url)
        let image = UIImage(data: data)!
        cache[url] = image
        return image
    }
}

// @MainActor: ensure UI updates on main thread
@MainActor
class ProductViewModel: Observable {
    var products: [Product] = []
    var isLoading = false

    func loadProducts() async {
        isLoading = true
        defer { isLoading = false }

        do {
            products = try await api.fetchProducts()
        } catch {
            // handle error
        }
    }
}
```

**Swift 6 strict concurrency:** Compile-time data race safety. All mutable
shared state must be `Sendable` (safe to pass across concurrency domains).
The compiler rejects code that could race. This is similar to Rust's borrow
checker but for concurrency.

### 1.4 Memory Management (ARC)

Automatic Reference Counting inserts `retain` and `release` calls at compile
time. No garbage collector — deterministic deallocation.

```swift
// Strong reference cycle (memory leak)
class Parent {
    var child: Child?   // strong reference
}
class Child {
    var parent: Parent? // strong reference → cycle!
}

// Fix with weak reference
class Child {
    weak var parent: Parent? // does not increment refcount
}

// Closure capture lists
class ViewModel {
    func loadData() {
        api.fetch { [weak self] result in  // weak self prevents retain cycle
            guard let self else { return }
            self.data = result
        }
    }
}
```

### 1.5 Build and Distribution

```
Source → swiftc → .o files → Linker → .app bundle → codesign → .ipa
                                          │
                               Provisioning Profile
                               (Team ID + App ID + Device UDIDs + Entitlements)
```

**App Store Review** rejects for: private API usage, IDFA without ATT prompt,
payment circumvention (30%/15% IAP rule), guideline 4.3 (spam/clones),
incomplete metadata, crashes on review device.

---

## 2. Native Android Engineering

### 2.1 Kotlin

Kotlin is the official Android language. Key features over Java:

- **Null safety:** `String` vs `String?` at the type level.
- **Data classes:** Auto-generated `equals`, `hashCode`, `toString`, `copy`.
- **Sealed classes:** Exhaustive `when` expressions (like Rust `match`).
- **Extension functions:** Add methods to existing classes without inheritance.
- **Coroutines:** First-class structured concurrency.
- **Flow:** Cold reactive streams, replacement for RxJava.

```kotlin
// Sealed class hierarchy
sealed class UiState<out T> {
    data object Loading : UiState<Nothing>()
    data class Success<T>(val data: T) : UiState<T>()
    data class Error(val message: String) : UiState<Nothing>()
}

// Extension function
fun String.toSlug(): String =
    this.lowercase()
        .replace(Regex("[^a-z0-9\\s-]"), "")
        .replace(Regex("\\s+"), "-")

// Data class with copy
data class User(val name: String, val email: String, val role: Role)
val admin = user.copy(role = Role.ADMIN) // immutable update
```

### 2.2 Jetpack Compose

```kotlin
@Composable
fun ProductListScreen(
    viewModel: ProductViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(title = { Text("Products") })
        }
    ) { padding ->
        when (val state = uiState) {
            is UiState.Loading -> CircularProgressIndicator(
                modifier = Modifier.padding(padding)
            )
            is UiState.Success -> LazyColumn(
                contentPadding = padding
            ) {
                items(state.data, key = { it.id }) { product ->
                    ProductCard(product = product)
                }
            }
            is UiState.Error -> ErrorMessage(
                message = state.message,
                onRetry = viewModel::retry
            )
        }
    }
}

@Composable
fun ProductCard(product: Product) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(product.name, style = MaterialTheme.typography.titleMedium)
            Spacer(modifier = Modifier.height(4.dp))
            Text(product.price.format(), style = MaterialTheme.typography.bodyLarge)
        }
    }
}
```

**Recomposition rules:**
- Composable functions can be called in any order.
- Composable functions can execute in parallel.
- Recomposition skips unchanged composable functions.
- Recomposition is optimistic (may be cancelled).
- Use `remember` to survive recomposition, `rememberSaveable` to survive
  process death.

### 2.3 Coroutines and Flow

```kotlin
@HiltViewModel
class ProductViewModel @Inject constructor(
    private val repository: ProductRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<UiState<List<Product>>>(UiState.Loading)
    val uiState: StateFlow<UiState<List<Product>>> = _uiState.asStateFlow()

    init {
        loadProducts()
    }

    private fun loadProducts() {
        viewModelScope.launch {  // cancelled when ViewModel is cleared
            repository.getProducts()
                .catch { e ->
                    _uiState.value = UiState.Error(e.message ?: "Unknown error")
                }
                .collect { products ->
                    _uiState.value = UiState.Success(products)
                }
        }
    }

    fun retry() = loadProducts()
}

class ProductRepository @Inject constructor(
    private val api: ProductApi,
    private val dao: ProductDao
) {
    fun getProducts(): Flow<List<Product>> = flow {
        // Emit cached data first
        val cached = dao.getAll()
        if (cached.isNotEmpty()) emit(cached)

        // Fetch fresh data
        val fresh = api.fetchProducts()
        dao.insertAll(fresh)
        emit(fresh)
    }
}
```

### 2.4 Dependency Injection (Hilt)

```kotlin
@HiltAndroidApp
class MyApplication : Application()

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides
    @Singleton
    fun provideRetrofit(): Retrofit =
        Retrofit.Builder()
            .baseUrl("https://api.example.com/")
            .addConverterFactory(MoshiConverterFactory.create())
            .build()

    @Provides
    @Singleton
    fun provideProductApi(retrofit: Retrofit): ProductApi =
        retrofit.create(ProductApi::class.java)
}

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {
    @Binds
    @Singleton
    abstract fun bindProductRepository(
        impl: ProductRepositoryImpl
    ): ProductRepository
}
```

### 2.5 Build and Distribution

**Gradle (Kotlin DSL):**
```kotlin
// build.gradle.kts
android {
    namespace = "com.example.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.example.app"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
}
```

**AAB (Android App Bundle):** Mandatory for new Play Store submissions.
Google generates optimized APKs per device configuration (architecture,
screen density, language).

---

## 3. React Native Architecture

### 3.1 Old Architecture (Pre-0.76)

```
 JS Thread                      Native Thread
┌──────────┐    JSON Bridge    ┌──────────┐
│ React    │   (serialized,    │ UIKit /  │
│ Component│   async,          │ Android  │
│ Tree     │   batched)        │ Views    │
│          │ ─────────────────→│          │
│          │ ←─────────────────│          │
└──────────┘                   └──────────┘
```

**Limitations:**
- JSON serialization overhead for every bridge message.
- Async nature meant layout could not be synchronous.
- Animations running through the bridge were janky (~30fps).
- Large list scrolling suffered from bridge bottleneck.

### 3.2 New Architecture (Default since 0.76)

```
 JS Thread                           Native Thread
┌──────────┐    JSI (C++ bindings)   ┌──────────┐
│ React    │   direct function       │ Fabric   │
│ Component│   calls, no JSON        │ Renderer │
│ Tree     │ ────────────────────────→│          │
│          │                         │ Turbo    │
│ Hermes   │   synchronous when      │ Modules  │
│ Engine   │   needed                │          │
└──────────┘                         └──────────┘
```

**Key components:**

**Hermes:** AOT-compiled JavaScript engine built by Meta. Compiles JS to
bytecode at build time (not at runtime like V8). Benefits:
- 50-80% faster startup (no JIT warmup).
- 30-50% lower memory usage.
- Smaller app size (bytecode is smaller than source).

**JSI (JavaScript Interface):** C++ layer that allows JS to directly call
native functions without JSON serialization. Enables synchronous calls when
needed (e.g., layout measurements).

```cpp
// Native module registered via JSI — no JSON bridge
jsi::Value MyModule::multiply(
    jsi::Runtime &rt,
    const jsi::Value &a,
    const jsi::Value &b
) {
    return jsi::Value(a.getNumber() * b.getNumber());
}
```

**Fabric:** New rendering system. Replaces the old asynchronous rendering
pipeline with one that supports:
- Synchronous layout measurements.
- Concurrent React features (Suspense, transitions).
- Priority-based rendering (high-priority touch events pre-empt lower-priority updates).

**TurboModules:** Native modules loaded lazily via JSI. Old architecture loaded
all native modules at startup, even if unused. TurboModules load on first call.

### 3.3 Expo

Expo is the recommended way to build React Native apps:

```bash
# Create new project
npx create-expo-app@latest my-app

# Start development
npx expo start

# Build for production (cloud build)
eas build --platform ios

# Over-the-air update (no App Store review needed)
eas update --branch production --message "Fix typo on home screen"
```

**EAS (Expo Application Services):**
- **EAS Build:** Cloud builds for iOS and Android (eliminates local Xcode/Android Studio setup).
- **EAS Update:** OTA updates that push JS bundle changes without App Store review. Compliant with Apple guidelines (no native code changes).
- **EAS Submit:** Automated submission to App Store and Play Store.

**Expo Config Plugins:** Modify native project configuration without ejecting:

```javascript
// app.config.js
module.exports = {
  expo: {
    plugins: [
      ['expo-camera', { cameraPermission: 'Allow camera access for barcode scanning' }],
      ['expo-location', { locationAlwaysPermission: 'Allow location for delivery tracking' }],
    ],
  },
};
```

### 3.4 React Native Performance

```typescript
// Use FlatList for large lists (virtualized)
<FlatList
  data={products}
  renderItem={({ item }) => <ProductCard product={item} />}
  keyExtractor={(item) => item.id}
  initialNumToRender={10}
  maxToRenderPerBatch={10}
  windowSize={5}  // render 5 screens worth of items
  removeClippedSubviews={true}  // reclaim memory for off-screen items
  getItemLayout={(data, index) => ({
    length: ITEM_HEIGHT,
    offset: ITEM_HEIGHT * index,
    index,
  })}  // skip layout measurement for known-height items
/>

// Memoize expensive renders
const ProductCard = React.memo(({ product }: { product: Product }) => {
  // only re-renders when product changes
  return (
    <View style={styles.card}>
      <Text>{product.name}</Text>
    </View>
  );
});

// Use Reanimated for 60fps animations (runs on UI thread)
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
} from 'react-native-reanimated';

function AnimatedCard() {
  const scale = useSharedValue(1);
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const onPressIn = () => {
    scale.value = withSpring(0.95);
  };

  return (
    <Pressable onPressIn={onPressIn}>
      <Animated.View style={animatedStyle}>
        <Text>Animated Content</Text>
      </Animated.View>
    </Pressable>
  );
}
```

---

## 4. Flutter Architecture

### 4.1 Dart Language

Dart is AOT-compiled to ARM64/x64 for release builds and JIT-compiled for
development (enabling hot reload).

```dart
// Null safety
String? nullableName; // can be null
String nonNullName = 'required'; // cannot be null

// Pattern matching (Dart 3+)
sealed class Shape {}
class Circle extends Shape { final double radius; Circle(this.radius); }
class Rectangle extends Shape { final double w, h; Rectangle(this.w, this.h); }

double area(Shape shape) => switch (shape) {
  Circle(radius: var r) => 3.14159 * r * r,
  Rectangle(w: var w, h: var h) => w * h,
};

// Records (unnamed and named fields)
(String, int) userInfo = ('Alice', 30);
({String name, int age}) namedUser = (name: 'Bob', age: 25);

// Extension methods
extension StringExtension on String {
  String capitalize() => '${this[0].toUpperCase()}${substring(1)}';
}
```

### 4.2 Widget Tree and Rendering

```
Widget Tree (immutable description)
        │
        ▼
Element Tree (mutable, manages lifecycle)
        │
        ▼
RenderObject Tree (layout + paint)
        │
        ▼
Skia / Impeller (GPU rendering)
```

**Key distinction from React Native:** Flutter does NOT use platform UI
controls. It renders every pixel itself via Skia (or Impeller). This means:
- Pixel-identical rendering across iOS and Android.
- Custom rendering is first-class (draw anything).
- Platform look-and-feel requires explicit effort (Material + Cupertino widgets).

**Impeller (replacing Skia):** Pre-compiled shaders, eliminates shader
compilation jank (the notorious first-frame stutter). Default on iOS since
Flutter 3.16, Android since 3.22.

### 4.3 Widget Patterns

```dart
// StatelessWidget: immutable, no internal state
class ProductCard extends StatelessWidget {
  final Product product;
  const ProductCard({super.key, required this.product});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Column(
        children: [
          Image.network(product.imageUrl),
          Text(product.name, style: Theme.of(context).textTheme.titleMedium),
          Text('\$${product.price.toStringAsFixed(2)}'),
        ],
      ),
    );
  }
}

// StatefulWidget: mutable internal state
class CounterWidget extends StatefulWidget {
  const CounterWidget({super.key});

  @override
  State<CounterWidget> createState() => _CounterWidgetState();
}

class _CounterWidgetState extends State<CounterWidget> {
  int _count = 0;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text('Count: $_count'),
        ElevatedButton(
          onPressed: () => setState(() => _count++),
          child: const Text('Increment'),
        ),
      ],
    );
  }
}
```

### 4.4 Isolates (Dart Concurrency)

Dart's concurrency model is actor-based: each isolate has its own heap and
communicates via message passing. No shared mutable state.

```dart
// Simple offload with compute()
Future<List<Product>> parseProducts(String jsonString) async {
  // Runs in a separate isolate — does not block UI thread
  return await compute(_parseJson, jsonString);
}

List<Product> _parseJson(String json) {
  final data = jsonDecode(json) as List;
  return data.map((e) => Product.fromJson(e)).toList();
}

// Long-running isolate with bidirectional communication
void main() async {
  final receivePort = ReceivePort();
  await Isolate.spawn(_workerEntryPoint, receivePort.sendPort);

  final sendPort = await receivePort.first as SendPort;

  // Communicate with the isolate
  final responsePort = ReceivePort();
  sendPort.send(['process', data, responsePort.sendPort]);
  final result = await responsePort.first;
}

void _workerEntryPoint(SendPort mainSendPort) {
  final receivePort = ReceivePort();
  mainSendPort.send(receivePort.sendPort);

  receivePort.listen((message) {
    final [command, data, replyPort] = message;
    if (command == 'process') {
      final result = heavyProcessing(data);
      (replyPort as SendPort).send(result);
    }
  });
}
```

### 4.5 dart:ffi (Foreign Function Interface)

Zero-overhead interop with C libraries:

```dart
// Load a C library and call functions
import 'dart:ffi';
import 'package:ffi/ffi.dart';

typedef NativeAdd = Int32 Function(Int32 a, Int32 b);
typedef DartAdd = int Function(int a, int b);

void main() {
  final dylib = DynamicLibrary.open('libmath.so');
  final add = dylib.lookupFunction<NativeAdd, DartAdd>('add');

  print(add(3, 5)); // 8 — direct C call, no overhead
}
```

Used for SQLite (via `sqflite_ffi`), OpenCV, custom native algorithms.

---

## 5. Kotlin Multiplatform (KMP)

### 5.1 Philosophy

Share business logic, keep UI native. KMP is not "write once, run anywhere" —
it is "write once, integrate natively."

```
┌──────────────────────────────────────────────┐
│                 commonMain                    │
│  Business logic, networking, persistence,    │
│  domain models, validation                   │
│                                              │
│  expect class Platform                       │
│  expect fun createHttpClient(): HttpClient   │
└────────┬─────────────────────┬───────────────┘
         │                     │
    ┌────▼────┐          ┌─────▼─────┐
    │ androidMain│        │  iosMain   │
    │           │        │           │
    │ actual    │        │ actual    │
    │ class     │        │ class     │
    │ Platform  │        │ Platform  │
    │           │        │           │
    │ Jetpack   │        │ SwiftUI   │
    │ Compose   │        │           │
    └───────────┘        └───────────┘
```

### 5.2 expect/actual Mechanism

```kotlin
// commonMain/Platform.kt
expect class Platform {
    val name: String
    fun generateUUID(): String
}

// androidMain/Platform.kt
actual class Platform {
    actual val name: String = "Android ${android.os.Build.VERSION.SDK_INT}"
    actual fun generateUUID(): String = java.util.UUID.randomUUID().toString()
}

// iosMain/Platform.kt
actual class Platform {
    actual val name: String = UIDevice.currentDevice.systemName +
        " " + UIDevice.currentDevice.systemVersion
    actual fun generateUUID(): String = NSUUID().UUIDString
}
```

### 5.3 Shared Networking with Ktor

```kotlin
// commonMain
class ProductRepository(private val client: HttpClient) {
    suspend fun getProducts(): List<Product> {
        return client.get("https://api.example.com/products").body()
    }
}

// commonMain — HttpClient factory
expect fun createHttpClient(): HttpClient

// androidMain
actual fun createHttpClient(): HttpClient = HttpClient(OkHttp) {
    install(ContentNegotiation) { json() }
}

// iosMain
actual fun createHttpClient(): HttpClient = HttpClient(Darwin) {
    install(ContentNegotiation) { json() }
}
```

### 5.4 Compose Multiplatform

Optional UI sharing layer extending KMP to share Compose UI across
Android, Desktop (JVM), iOS (beta), and Web (Wasm, experimental):

```kotlin
// commonMain — shared UI
@Composable
fun App() {
    MaterialTheme {
        var count by remember { mutableIntStateOf(0) }
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.fillMaxSize().padding(16.dp)
        ) {
            Text("Count: $count", style = MaterialTheme.typography.headlineMedium)
            Button(onClick = { count++ }) {
                Text("Increment")
            }
        }
    }
}
```

**iOS integration status:** Beta. Works well for simple UI. Complex
platform-specific interactions (navigation gestures, keyboard handling)
still require native fallbacks.

---

## 6. Other Cross-Platform Frameworks

### 6.1 .NET MAUI

Successor to Xamarin.Forms. Single C# codebase, multi-platform.

```xml
<!-- MainPage.xaml -->
<ContentPage xmlns="http://schemas.microsoft.com/dotnet/2021/maui">
    <VerticalStackLayout>
        <Label Text="{Binding Title}" FontSize="24" />
        <Button Text="Click me" Command="{Binding ClickCommand}" />
        <Label Text="{Binding Count}" />
    </VerticalStackLayout>
</ContentPage>
```

**Strengths:** C# ecosystem, .NET libraries, MVVM pattern, Blazor Hybrid
(embed web UI in native app).
**Weaknesses:** iOS performance lags behind native, community smaller than
RN/Flutter, debugging cross-platform issues is painful.

### 6.2 Capacitor / Ionic

Web app (HTML/CSS/JS) wrapped in a native WebView shell with a plugin layer
for native APIs.

```typescript
// Capacitor plugin usage
import { Camera, CameraResultType } from '@capacitor/camera';
import { Geolocation } from '@capacitor/geolocation';

async function takePhoto() {
  const image = await Camera.getPhoto({
    quality: 90,
    resultType: CameraResultType.Uri,
  });
  return image.webPath;
}

async function getLocation() {
  const position = await Geolocation.getCurrentPosition();
  return { lat: position.coords.latitude, lng: position.coords.longitude };
}
```

**When appropriate:** Content-heavy apps (news readers, documentation),
internal enterprise apps where 60fps animations are not required, rapid
prototyping for teams with web skills.

**When NOT appropriate:** Games, camera-heavy apps, apps requiring smooth
gesture-based interactions, apps where native performance is expected.

### 6.3 Framework Comparison

| Aspect | React Native | Flutter | KMP | MAUI | Capacitor |
|---|---|---|---|---|---|
| **Language** | JavaScript/TS | Dart | Kotlin | C# | Web (JS/TS) |
| **UI rendering** | Platform native | Own canvas (Skia/Impeller) | Platform native | Platform native | WebView |
| **Shared code** | ~90% (UI + logic) | ~95% (UI + logic) | ~70% (logic only) | ~90% (UI + logic) | ~95% (UI + logic) |
| **Performance** | Near-native | Near-native | Native | Variable | Web-tier |
| **Hot reload** | Yes (Fast Refresh) | Yes (sub-second) | Partial | Yes | Yes |
| **Maturity** | 2015, Meta | 2018, Google | 2020, JetBrains | 2022, Microsoft | 2019, Ionic |
| **Ecosystem** | Massive (npm) | Growing (pub.dev) | Kotlin/JVM | NuGet | npm |
| **Learning curve** | Low (JS devs) | Medium (Dart) | High (multiplatform) | Medium (C# devs) | Low (web devs) |

---

## 7. Native Bridges and Interop

### 7.1 React Native: TurboModules

```typescript
// TypeScript spec (codegen input)
import { TurboModuleRegistry, TurboModule } from 'react-native';

export interface Spec extends TurboModule {
  getDeviceId(): string;           // synchronous via JSI
  fetchSecureToken(): Promise<string>;  // async
}

export default TurboModuleRegistry.getEnforcing<Spec>('DeviceModule');
```

```kotlin
// Android implementation (Kotlin)
class DeviceModule(reactContext: ReactApplicationContext)
    : NativeDeviceModuleSpec(reactContext) {

    override fun getDeviceId(): String {
        return Settings.Secure.getString(
            reactApplicationContext.contentResolver,
            Settings.Secure.ANDROID_ID
        )
    }

    override fun fetchSecureToken(): Promise<String> {
        // return encrypted token from Keystore
    }
}
```

### 7.2 Flutter: Platform Channels

```dart
// Dart side
class BatteryLevel {
  static const _channel = MethodChannel('com.example/battery');

  static Future<int> getBatteryLevel() async {
    final int level = await _channel.invokeMethod('getBatteryLevel');
    return level;
  }
}
```

```kotlin
// Android side (Kotlin)
class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "com.example/battery")
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "getBatteryLevel" -> {
                        val batteryManager = getSystemService(BATTERY_SERVICE) as BatteryManager
                        val level = batteryManager.getIntProperty(
                            BatteryManager.BATTERY_PROPERTY_CAPACITY
                        )
                        result.success(level)
                    }
                    else -> result.notImplemented()
                }
            }
    }
}
```

### 7.3 Flutter: Federated Plugins

The preferred architecture for plugins that need platform-specific code:

```
my_plugin/                    # App-facing API
├── lib/
│   └── my_plugin.dart       # Public API (delegates to platform interface)
├── my_plugin_platform_interface/  # Abstract interface
│   └── lib/
│       └── my_plugin_platform_interface.dart
├── my_plugin_android/        # Android implementation
│   └── android/
├── my_plugin_ios/            # iOS implementation
│   └── ios/
└── my_plugin_web/            # Web implementation
    └── lib/
```

---

## 8. App Lifecycle Management

### 8.1 iOS App States

```
                 ┌───────────┐
      Launch ───→│Not Running│
                 └─────┬─────┘
                       │
                 ┌─────▼─────┐
                 │  Inactive  │ ← transitional (between active/background)
                 └─────┬─────┘
                       │
                 ┌─────▼─────┐
          ┌─────→│   Active   │←─────┐
          │      └─────┬─────┘      │
    foreground         │        foreground
          │      ┌─────▼─────┐      │
          └──────│ Background │──────┘
                 └─────┬─────┘
                       │ (system suspends after ~5s)
                 ┌─────▼──────┐
                 │ Suspended   │ ← still in memory, not executing
                 └─────┬──────┘
                       │ (memory pressure)
                 ┌─────▼──────┐
                 │  Terminated │
                 └────────────┘
```

### 8.2 Android Activity Lifecycle

```
                    onCreate()
                        │
                    onStart()
                        │
                    onResume() ← RUNNING (visible + foreground)
                        │
                    onPause()  ← another activity partially covers
                        │
                    onStop()   ← no longer visible
                        │
                    onDestroy() ← activity destroyed
                        │
                   ┌────┘
                   │
              Configuration
               change?
              ┌───┴───┐
              │  Yes   │ → onCreate() with saved state
              │  No    │ → garbage collected
              └────────┘
```

### 8.3 Flutter Lifecycle

```dart
class MyApp extends StatefulWidget {
  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    switch (state) {
      case AppLifecycleState.resumed:
        // App is in foreground — resume network, animations
        break;
      case AppLifecycleState.inactive:
        // Transitional — pause non-critical work
        break;
      case AppLifecycleState.paused:
        // App backgrounded — save state, stop location tracking
        break;
      case AppLifecycleState.detached:
        // App is being terminated
        break;
      case AppLifecycleState.hidden:
        // App is hidden but still running
        break;
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }
}
```

---

## 9. Background Execution

### 9.1 Android WorkManager

```kotlin
// Define the work
class SyncWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        return try {
            val data = repository.fetchPendingSync()
            repository.pushToServer(data)
            Result.success()
        } catch (e: Exception) {
            if (runAttemptCount < 3) Result.retry()
            else Result.failure()
        }
    }
}

// Schedule the work
val syncRequest = PeriodicWorkRequestBuilder<SyncWorker>(
    repeatInterval = 1, TimeUnit.HOURS
)
    .setConstraints(
        Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .setRequiresBatteryNotLow(true)
            .build()
    )
    .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
    .addTag("sync")
    .build()

WorkManager.getInstance(context).enqueueUniquePeriodicWork(
    "periodic-sync",
    ExistingPeriodicWorkPolicy.KEEP,
    syncRequest
)
```

### 9.2 iOS BGTaskScheduler

```swift
// Register in AppDelegate
BGTaskScheduler.shared.register(
    forTaskWithIdentifier: "com.example.app.refresh",
    using: nil
) { task in
    handleAppRefresh(task: task as! BGAppRefreshTask)
}

func handleAppRefresh(task: BGAppRefreshTask) {
    // Schedule the next refresh
    scheduleAppRefresh()

    let syncTask = Task {
        do {
            try await syncData()
            task.setTaskCompleted(success: true)
        } catch {
            task.setTaskCompleted(success: false)
        }
    }

    // Handle expiration (system kills your task)
    task.expirationHandler = {
        syncTask.cancel()
    }
}

func scheduleAppRefresh() {
    let request = BGAppRefreshTaskRequest(identifier: "com.example.app.refresh")
    request.earliestBeginDate = Date(timeIntervalSinceNow: 15 * 60) // 15 min minimum
    try? BGTaskScheduler.shared.submit(request)
}
```

**Limitations:** iOS controls when background tasks actually run. The system
considers battery level, charging state, network availability, and user
behavior patterns. No guarantees on timing.

---

## 10. Push Notifications

### 10.1 Architecture

```
┌─────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────┐
│Your      │───→│ FCM / APNs   │───→│ Device      │───→│ Your App │
│Server    │    │ (Push Service)│    │ (OS level)  │    │          │
└─────────┘    └──────────────┘    └─────────────┘    └──────────┘
    │                                                       │
    │  HTTP/2 request with                      Display notification
    │  device token + payload                   or handle silently
```

### 10.2 FCM (Firebase Cloud Messaging)

```typescript
// Server-side: send notification (Node.js)
import admin from 'firebase-admin';

admin.initializeApp({
  credential: admin.credential.applicationDefault(),
});

await admin.messaging().send({
  token: deviceToken,
  notification: {
    title: 'New order',
    body: 'Order #1234 has shipped',
  },
  data: {
    orderId: '1234',
    type: 'order_shipped',
  },
  android: {
    priority: 'high',
    notification: {
      channelId: 'orders',
      clickAction: 'OPEN_ORDER',
    },
  },
  apns: {
    payload: {
      aps: {
        sound: 'default',
        badge: 1,
        'mutable-content': 1,  // enable Notification Service Extension
      },
    },
  },
});

// Topic-based: send to all subscribers of "deals"
await admin.messaging().send({
  topic: 'deals',
  notification: {
    title: 'Flash sale!',
    body: '50% off for the next 2 hours',
  },
});
```

### 10.3 APNs (Apple Push Notification service)

```swift
// iOS: request permission and register
func requestNotificationPermission() async {
    let center = UNUserNotificationCenter.current()
    let granted = try? await center.requestAuthorization(options: [.alert, .badge, .sound])

    if granted == true {
        await MainActor.run {
            UIApplication.shared.registerForRemoteNotifications()
        }
    }
}

// Handle registration
func application(_ application: UIApplication,
                 didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
    let token = deviceToken.map { String(format: "%02x", $0) }.joined()
    // Send token to your server
    api.registerDeviceToken(token)
}

// Handle notification when app is in foreground
func userNotificationCenter(_ center: UNUserNotificationCenter,
                           willPresent notification: UNNotification) async
    -> UNNotificationPresentationOptions {
    // Decide: show banner or handle silently
    return [.banner, .sound, .badge]
}
```

### 10.4 Notification Channels (Android)

```kotlin
// Create channel (required since Android 8.0 / API 26)
val channel = NotificationChannel(
    "orders",
    "Order Updates",
    NotificationManager.IMPORTANCE_HIGH
).apply {
    description = "Notifications about order status changes"
    enableVibration(true)
    setShowBadge(true)
}

val notificationManager = getSystemService(NotificationManager::class.java)
notificationManager.createNotificationChannel(channel)
```

---

## 11. Deep Linking and Navigation

### 11.1 Universal Links (iOS) and App Links (Android)

Both verify domain ownership to prevent URL hijacking:

**iOS (Universal Links):**
```json
// https://example.com/.well-known/apple-app-site-association
{
  "applinks": {
    "apps": [],
    "details": [
      {
        "appIDs": ["TEAMID.com.example.app"],
        "components": [
          { "/": "/products/*", "comment": "Product pages" },
          { "/": "/orders/*", "comment": "Order pages" }
        ]
      }
    ]
  }
}
```

**Android (App Links):**
```json
// https://example.com/.well-known/assetlinks.json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.example.app",
    "sha256_cert_fingerprints": ["AB:CD:EF:..."]
  }
}]
```

### 11.2 Deep Link Routing

```typescript
// React Native (React Navigation)
const linking = {
  prefixes: ['https://example.com', 'myapp://'],
  config: {
    screens: {
      Home: '',
      Product: 'products/:id',
      Order: 'orders/:id',
      Settings: 'settings',
    },
  },
};

function App() {
  return (
    <NavigationContainer linking={linking}>
      <Stack.Navigator>
        <Stack.Screen name="Home" component={HomeScreen} />
        <Stack.Screen name="Product" component={ProductScreen} />
        <Stack.Screen name="Order" component={OrderScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```

### 11.3 Deferred Deep Links

Handle the case where the app is not installed when the link is tapped:

```
1. User taps link on mobile web
2. App not installed → redirect to App Store / Play Store
3. User installs app
4. App opens → check for deferred deep link
5. Navigate to the intended content
```

Services: Firebase Dynamic Links (deprecated, use alternatives), Branch.io,
Adjust, AppsFlyer.

---

## 12. Offline-First Architecture

### 12.1 Design Principles

1. **Local-first:** Read from local database, sync in background.
2. **Optimistic writes:** Write locally, queue for server sync.
3. **Conflict resolution:** Define strategy before implementation.
4. **Sync indicator:** User always knows their sync status.

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│  UI Layer    │ ←──→│ Local DB    │ ←──→│ Sync Engine  │
│             │     │ (SQLite)    │     │              │
│ reads local │     │ source of   │     │ pushes/pulls │
│ writes local│     │ truth       │     │ to server    │
└─────────────┘     └─────────────┘     └──────┬───────┘
                                                │
                                         ┌──────▼───────┐
                                         │   Server API  │
                                         └──────────────┘
```

### 12.2 Local Storage Options

| Solution | Type | Strengths | Use case |
|---|---|---|---|
| **SQLite (Room/GRDB)** | Relational | ACID, complex queries, mature | Structured data |
| **Realm** | Object DB | Live objects, auto-sync with MongoDB | Mobile-first apps |
| **WatermelonDB** | React Native DB | Lazy loading, fast list rendering | RN with large datasets |
| **MMKV** | Key-value | Fastest KV on mobile (mmap-based) | Preferences, small data |
| **Hive** | Key-value (Dart) | No native deps, pure Dart | Flutter simple storage |

### 12.3 Conflict Resolution

| Strategy | Mechanism | Trade-off |
|---|---|---|
| **Last-write-wins (LWW)** | Timestamp comparison | Simple but lossy |
| **Server-wins** | Server always authoritative | Safe but may lose offline edits |
| **Client-wins** | Client edits override | Dangerous if multiple clients |
| **CRDT** | Mathematically mergeable | Complex but conflict-free |
| **Manual merge** | Show conflicts to user | Best UX for important data |
| **Operational Transform (OT)** | Transform operations against each other | Real-time collab (Google Docs) |

### 12.4 Sync Engines

```
PowerSync (Postgres-backed):
  Server → logical replication → sync rules → PowerSync service → client SDK → SQLite

CouchDB / PouchDB:
  Client writes to PouchDB → continuous replication → CouchDB → replication → other clients

Electric SQL:
  Postgres → Electric service → client SQLite (bidirectional sync via CRDT)
```

---

## 13. State Management Patterns

### 13.1 Flutter: Riverpod

```dart
// Provider definition
final productsProvider = FutureProvider.autoDispose<List<Product>>((ref) async {
  final repository = ref.watch(productRepositoryProvider);
  return repository.getProducts();
});

// Filtered provider (derived)
final filteredProductsProvider = Provider<List<Product>>((ref) {
  final products = ref.watch(productsProvider).valueOrNull ?? [];
  final filter = ref.watch(filterProvider);
  return products.where((p) => p.category == filter).toList();
});

// Usage in widget
class ProductList extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final productsAsync = ref.watch(productsProvider);

    return productsAsync.when(
      loading: () => const CircularProgressIndicator(),
      error: (err, stack) => Text('Error: $err'),
      data: (products) => ListView.builder(
        itemCount: products.length,
        itemBuilder: (ctx, i) => ProductCard(product: products[i]),
      ),
    );
  }
}
```

### 13.2 Flutter: BLoC

```dart
// Events
sealed class ProductEvent {}
class LoadProducts extends ProductEvent {}
class FilterProducts extends ProductEvent {
  final String category;
  FilterProducts(this.category);
}

// States
sealed class ProductState {}
class ProductLoading extends ProductState {}
class ProductLoaded extends ProductState {
  final List<Product> products;
  ProductLoaded(this.products);
}
class ProductError extends ProductState {
  final String message;
  ProductError(this.message);
}

// BLoC
class ProductBloc extends Bloc<ProductEvent, ProductState> {
  final ProductRepository repository;

  ProductBloc(this.repository) : super(ProductLoading()) {
    on<LoadProducts>((event, emit) async {
      emit(ProductLoading());
      try {
        final products = await repository.getProducts();
        emit(ProductLoaded(products));
      } catch (e) {
        emit(ProductError(e.toString()));
      }
    });

    on<FilterProducts>((event, emit) async {
      final currentState = state;
      if (currentState is ProductLoaded) {
        final filtered = currentState.products
            .where((p) => p.category == event.category)
            .toList();
        emit(ProductLoaded(filtered));
      }
    });
  }
}
```

### 13.3 Android: Unidirectional Data Flow

```kotlin
// ViewModel (MVI-like pattern)
@HiltViewModel
class ProductViewModel @Inject constructor(
    private val repository: ProductRepository
) : ViewModel() {

    private val _state = MutableStateFlow(ProductUiState())
    val state: StateFlow<ProductUiState> = _state.asStateFlow()

    fun onEvent(event: ProductEvent) {
        when (event) {
            is ProductEvent.Load -> loadProducts()
            is ProductEvent.Filter -> filterProducts(event.category)
            is ProductEvent.Search -> searchProducts(event.query)
        }
    }

    private fun loadProducts() {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true) }
            repository.getProducts()
                .catch { e -> _state.update { it.copy(error = e.message, isLoading = false) } }
                .collect { products ->
                    _state.update { it.copy(products = products, isLoading = false, error = null) }
                }
        }
    }
}

data class ProductUiState(
    val products: List<Product> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null,
    val selectedCategory: String? = null,
)

sealed class ProductEvent {
    data object Load : ProductEvent()
    data class Filter(val category: String) : ProductEvent()
    data class Search(val query: String) : ProductEvent()
}
```

---

## 14. Performance Optimization

### 14.1 List Performance

**Flutter:**
```dart
// Use ListView.builder for large lists (lazy rendering)
ListView.builder(
  itemCount: 10000,
  itemBuilder: (context, index) => ProductCard(product: products[index]),
  // Only renders visible items + buffer
);

// Use const constructors for static widgets
const SizedBox(height: 8); // compiled as singleton, no rebuild
```

**React Native:**
```typescript
// FlashList (Shopify) — faster than FlatList for complex items
import { FlashList } from '@shopify/flash-list';

<FlashList
  data={products}
  renderItem={({ item }) => <ProductCard product={item} />}
  estimatedItemSize={100}
  drawDistance={250}
/>
```

### 14.2 Image Optimization

- Use platform-appropriate formats (WebP for Android, HEIC for iOS).
- Resize images server-side to match display size (don't send 4000px for a 400px thumbnail).
- Use progressive loading (blur-up, LQIP — Low Quality Image Placeholder).
- Cache aggressively (SDWebImage on iOS, Coil/Glide on Android, FastImage for RN).

### 14.3 Startup Performance

| Phase | Optimization |
|---|---|
| Cold start | Reduce binary size (R8/ProGuard), defer initialization |
| Warm start | Keep activities in memory, use saved instance state |
| Hot start | Already in memory, just bring to foreground |

**Measurement:**
- Android: `adb shell am start -W com.example.app/.MainActivity` (reports TotalTime).
- iOS: Instruments → App Launch template.
- Flutter: `flutter run --trace-startup`.

### 14.4 App Size

| Technique | Platform | Savings |
|---|---|---|
| **R8 / ProGuard** | Android | 30-50% code size, 10-30% total |
| **Resource shrinking** | Android | Remove unused resources |
| **App Thinning** | iOS | Per-device slicing |
| **--split-per-abi** | Flutter Android | ~50% (ship single ABI) |
| **--obfuscate + --split-debug-info** | Flutter | 10-20% |
| **Hermes AOT** | React Native | 20-30% smaller than V8 |

---

## 15. App Store Optimization and Distribution

### 15.1 App Store (iOS) Considerations

- **Review time:** 24-48 hours typical. Expedited review available for critical fixes.
- **Rejection reasons:** Private API usage, IDFA without ATT, payment circumvention,
  guideline 4.3 (spam), crashes on review device, incomplete metadata.
- **IAP commission:** 30% (first year or Small Business Program: 15%).
- **App Clips:** Lightweight (<15 MB), invokable via NFC, QR, Safari banner.

### 15.2 Play Store (Android) Considerations

- **Review time:** Hours to days.
- **AAB mandatory:** Since Aug 2021 for new apps.
- **Play App Signing:** Google manages the signing key. You hold an upload key.
- **Play Integrity API:** Device attestation (replaced SafetyNet).
- **Service fee:** 15% on first $1M, 30% thereafter.

### 15.3 Distribution Alternatives

| Channel | iOS | Android |
|---|---|---|
| **Enterprise** | MDM / Apple Business Manager | Managed Google Play |
| **Testing** | TestFlight (10K external testers) | Internal/Closed/Open testing tracks |
| **Side-loading** | Not officially supported (EU DMA changes pending) | APK install from any source |
| **Alternative stores** | AltStore (third-party, limited) | Amazon, Samsung, Huawei AppGallery |
| **PWA** | Safari (limited APIs) | Chrome (full PWA support, installable) |

---

## 16. Mobile CI/CD

### 16.1 Pipeline Stages

```
Code Push → Lint/Format → Unit Tests → Build → Integration Tests
    → Screenshot Tests → Sign → Deploy to Test Track → QA
    → Promote to Production → Monitor
```

### 16.2 Fastlane

```ruby
# Fastfile
platform :ios do
  lane :beta do
    increment_build_number
    build_app(scheme: "MyApp")
    upload_to_testflight
  end

  lane :release do
    build_app(scheme: "MyApp")
    upload_to_app_store(
      submit_for_review: true,
      automatic_release: false
    )
  end
end

platform :android do
  lane :beta do
    gradle(task: "bundleRelease")
    upload_to_play_store(
      track: "internal",
      aab: "app/build/outputs/bundle/release/app-release.aab"
    )
  end
end
```

### 16.3 EAS Build (Expo)

```json
// eas.json
{
  "cli": { "version": ">= 5.0.0" },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "distribution": "internal",
      "ios": { "simulator": true }
    },
    "production": {
      "autoIncrement": true
    }
  },
  "submit": {
    "production": {
      "ios": {
        "appleId": "your@email.com",
        "ascAppId": "1234567890"
      },
      "android": {
        "serviceAccountKeyPath": "./play-service-account.json",
        "track": "production"
      }
    }
  }
}
```

### 16.4 CI Runners

| Service | iOS support | Android support | Pricing model |
|---|---|---|---|
| **GitHub Actions** | macOS runners | Linux runners | Per-minute |
| **Bitrise** | macOS VMs | Linux VMs | Per-build-minute |
| **Codemagic** | macOS VMs, M1/M2 | Linux | Per-build-minute |
| **CircleCI** | macOS VMs | Linux/Docker | Per-credit |
| **EAS Build** | Cloud (managed) | Cloud (managed) | Per-build |

**iOS builds require macOS:** Xcode, codesigning, and the iOS toolchain only
run on macOS. Linux CI cannot build iOS apps. Budget accordingly.

---

## 17. Mobile Security

### 17.1 Secure Storage

| Platform | Mechanism | Use case |
|---|---|---|
| **iOS Keychain** | Hardware-backed encryption | Tokens, credentials, keys |
| **Android Keystore** | Hardware-backed (TEE/StrongBox) | Crypto keys, biometric-gated |
| **EncryptedSharedPreferences** | AES-256 encrypted SharedPreferences | Sensitive preferences |
| **expo-secure-store** | Cross-platform abstraction | RN token storage |
| **flutter_secure_storage** | Keychain + Keystore wrapper | Flutter token storage |

### 17.2 Certificate Pinning

```kotlin
// OkHttp certificate pinning (Android)
val client = OkHttpClient.Builder()
    .certificatePinner(
        CertificatePinner.Builder()
            .add("api.example.com", "sha256/AAAAAAA...")
            .add("api.example.com", "sha256/BBBBBBB...")  // backup pin
            .build()
    )
    .build()
```

**Caution:** Pin the intermediate CA certificate, not the leaf. Leaf
certificates rotate frequently. Include a backup pin. Have a recovery plan
if all pinned certificates expire (force-update mechanism or remote pin
configuration).

### 17.3 Code Obfuscation

- **Android:** R8 (ProGuard replacement) — renames classes, methods, fields;
  removes unused code; optimizes bytecode.
- **iOS:** Swift compiler does not obfuscate by default. Tools like SwiftShield
  or commercial obfuscators exist but are less common.
- **React Native:** Hermes bytecode provides mild obfuscation. Metro bundler
  can minify JS.
- **Flutter:** `--obfuscate --split-debug-info` flag.

### 17.4 Root/Jailbreak Detection

Use with caution — sophisticated bypass tools exist. Defense in depth:

```kotlin
// Android (basic checks)
fun isRooted(): Boolean {
    val suPaths = arrayOf("/system/bin/su", "/system/xbin/su", "/sbin/su")
    return suPaths.any { File(it).exists() } ||
        Build.TAGS?.contains("test-keys") == true
}
// Better: use Play Integrity API for device attestation
```

### 17.5 Network Security

```xml
<!-- Android: Network Security Config (res/xml/network_security_config.xml) -->
<network-security-config>
    <domain-config cleartextTrafficPermitted="false">
        <domain includeSubdomains="true">api.example.com</domain>
        <pin-set expiration="2027-01-01">
            <pin digest="SHA-256">base64encodedSHA256=</pin>
        </pin-set>
    </domain-config>
    <!-- Block cleartext (HTTP) traffic globally -->
    <base-config cleartextTrafficPermitted="false" />
</network-security-config>
```

---

## 18. Testing Mobile Applications

### 18.1 Test Pyramid

```
        ┌───────────┐
        │   E2E     │  Detox (RN), Maestro, XCUITest, Espresso
        ├───────────┤
        │Integration│  Widget tests (Flutter), component tests (RN)
        ├───────────┤
        │   Unit    │  Jest, Vitest, XCTest, JUnit, dart test
        └───────────┘
```

### 18.2 Flutter Widget Tests

```dart
testWidgets('ProductCard displays name and price', (tester) async {
  final product = Product(id: '1', name: 'Widget', price: 29.99);

  await tester.pumpWidget(
    MaterialApp(home: ProductCard(product: product)),
  );

  expect(find.text('Widget'), findsOneWidget);
  expect(find.text('\$29.99'), findsOneWidget);
});
```

### 18.3 Maestro (Cross-Platform E2E)

```yaml
# maestro/flow.yaml
appId: com.example.app
---
- launchApp
- tapOn: "Products"
- assertVisible: "Widget"
- tapOn: "Widget"
- assertVisible: "Add to Cart"
- tapOn: "Add to Cart"
- assertVisible: "Cart (1)"
```

### 18.4 Screenshot Testing

```kotlin
// Paparazzi (Android — no device needed)
@Test
fun productCard_snapshot() {
    paparazzi.snapshot {
        ProductCard(
            product = Product("Widget", "$29.99"),
        )
    }
}
```

---

## 19. Framework Selection Guide

### 19.1 Decision Tree

```
Do you need native-level performance (games, camera, AR)?
├── Yes → Native (Swift + Kotlin)
└── No
    │
    Does your team know JavaScript/TypeScript?
    ├── Yes
    │   │
    │   Do you need pixel-perfect custom UI?
    │   ├── Yes → Flutter (learn Dart)
    │   └── No → React Native + Expo
    │
    └── No
        │
        Does your team know Kotlin?
        ├── Yes → KMP (shared logic) + Native UI
        └── No
            │
            Does your team know C#?
            ├── Yes → .NET MAUI
            └── No
                │
                Is it a content-heavy app (minimal native features)?
                ├── Yes → Capacitor/PWA
                └── No → React Native (most hirable skill set)
```

### 19.2 When to Go Native

- Camera-first apps (Instagram, Snapchat-style).
- AR/VR (ARKit, ARCore).
- Health/fitness with HealthKit/Google Fit deep integration.
- Apps where 1ms of animation latency matters.
- Tiny teams that only target one platform.
- Enterprise apps mandating platform SDK compliance.

### 19.3 When Cross-Platform Works

- Business/productivity apps.
- E-commerce apps.
- Social/messaging apps.
- Content consumption apps (news, video, reading).
- Internal enterprise tools.
- MVPs and prototypes.

---

## 20. Exercises

### Exercise 1: React Native New Architecture

1. Create a new Expo project.
2. Verify the New Architecture is enabled (default in SDK 52+).
3. Create a TurboModule that returns device information (battery level, device name).
4. Compare bridge overhead: call the module 10,000 times and measure latency
   vs an equivalent old-architecture bridge call.

### Exercise 2: Flutter Offline-First

1. Build a todo app with Flutter and SQLite (sqflite).
2. Implement optimistic writes: add a todo locally, queue for server sync.
3. Implement background sync using WorkManager (Android) or BGTaskScheduler (iOS).
4. Handle conflicts: if the server rejects a write, show a conflict resolution UI.
5. Add a sync status indicator (synced, pending, error).

### Exercise 3: KMP Shared Logic

1. Create a KMP project with shared business logic.
2. Implement a ProductRepository in commonMain with Ktor networking.
3. Implement platform-specific storage (Room on Android, Core Data on iOS).
4. Build Android UI with Jetpack Compose consuming the shared repository.
5. Build iOS UI with SwiftUI consuming the shared repository via exported framework.

### Exercise 4: Push Notification System

1. Set up FCM for a React Native app (or Flutter app).
2. Implement: request permission, register token, send from server.
3. Handle notifications in foreground (show in-app banner).
4. Handle deep links from notification tap (navigate to specific screen).
5. Implement notification channels (Android) for different notification types.

### Exercise 5: Performance Profiling

1. Build a list with 10,000 items in React Native (FlatList vs FlashList).
2. Profile with React DevTools: identify re-renders.
3. Optimize: memoize components, use stable keys, add getItemLayout.
4. Measure: FPS during fast scroll before and after optimization.
5. Compare with Flutter equivalent (ListView.builder).

### Exercise 6: App Security Hardening

1. Implement secure token storage (Keychain/Keystore).
2. Add certificate pinning to all API calls.
3. Enable R8 obfuscation (Android) or `--obfuscate` (Flutter).
4. Implement root/jailbreak detection with graceful degradation.
5. Add Network Security Config blocking cleartext traffic.
6. Test: use a proxy (mitmproxy) to verify certificate pinning prevents MITM.

### Exercise 7: CI/CD Pipeline

1. Set up GitHub Actions for a mobile project.
2. Configure: lint → unit tests → build (Android + iOS) → deploy to test track.
3. Add screenshot testing (Paparazzi for Android or Maestro screenshots).
4. Automate version bumping on merge to main.
5. Deploy to TestFlight and Play Store internal track on tag push.

---

## 21. References

- Apple Developer Documentation. https://developer.apple.com/documentation/
- Android Developer Documentation. https://developer.android.com/
- React Native Architecture. https://reactnative.dev/architecture/overview
- Flutter Engine. https://github.com/flutter/engine
- Kotlin Multiplatform. https://kotlinlang.org/docs/multiplatform.html
- Expo Documentation. https://docs.expo.dev/
- Jetpack Compose. https://developer.android.com/compose
- SwiftUI. https://developer.apple.com/xcode/swiftui/
- Riverpod. https://riverpod.dev/
- Fastlane. https://fastlane.tools/
- Maestro. https://maestro.mobile.dev/
