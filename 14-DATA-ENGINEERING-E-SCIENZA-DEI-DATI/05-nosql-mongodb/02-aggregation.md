# MongoDB Aggregation: Pipeline, Pattern e Ottimizzazione

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-04  
> Versione: 2.0.0  
> Stato: expanded

## Skip list
- [x] Bozza iniziale
- [ ] Review tecnica
- [ ] Formattazione
- [ ] Pubblicazione

## Indice
1. Aggregation Pipeline Basics
2. Stage Operators
3. Expression Operators
4. Array Operations
5. Date Operations
6. Aggregation Optimization
7. Common Patterns
8. Advanced Transformations
9. Time Series Patterns
10. Performance Patterns
11. Anti-Patterns

---

## 1. Aggregation Pipeline Basics

### 1.1 Pipeline Structure

L'Aggregation Pipeline è una serie di stage che trasformano i documenti:

```javascript
// Basic pipeline: match -> project -> sort
db.collection.aggregate([
  { $match: { status: "active" } },
  { $project: { name: 1, total: 1 } },
  { $sort: { total: -1 } }
])

// Pipeline equivalent in SQL
SELECT name, total 
FROM collection 
WHERE status = 'active' 
ORDER BY total DESC
```

### 1.2 Pipeline Options

```javascript
// Allow disk use for large pipelines
db.orders.aggregate([
  { $group: { _id: "$customer", total: { $sum: "$amount" } } }
], { allowDiskUse: true })

// Cursor for large results (memory efficient)
db.orders.aggregate(pipeline, { cursor: { batchSize: 1000 } })

// Explain pipeline
db.orders.explain().aggregate([...])

// Collation for locale-aware operations
db.users.aggregate([
  { $match: { name: "john" } }
], { collation: { locale: "en", strength: 2 } })

// Hints (force index usage)
db.orders.aggregate([
  { $match: { status: "completed" } }
], { hint: { status: 1, date: -1 } })
```

### 1.3 Pipeline Flow

```
┌────────────┐    ┌────────────┐    ┌────────────┐
│  $match    │ -> │ $project   │ -> │   $sort   │
│  (filter)  │    │ (reshape)  │    │ (ordering)│
└────────────┘    └────────────┘    └────────────┘
     ↓                ↓                  ↓
  Reduced           Less             Sorted
  documents         fields           output
```

**Stage ordering best practices:**
1. `$match` early - reduce document count
2. `$project` after - remove unnecessary fields
3. `$sort` late - sort only final results
4. `$limit` as early as possible

---

## 2. Stage Operators

### 2.1 $match - Filtering

```javascript
// Basic filter
{ $match: { status: "completed", amount: { $gt: 100 } } }

// Multiple conditions
{ $match: {
  $and: [
    { status: "active" },
    { amount: { $gte: 100, $lt: 1000 } }
  ]
}}

// Regex matching
{ $match: { name: { $regex: "^John", $options: "i" } } }

// Element matchers
{ $match: { "profile.active": true } }
{ $match: { tags: { $exists: true } } }
{ $match: { age: { $type: "number" } } }

// Array matchers
{ $match: { "items.sku": "WIDGET-001" } }  // any item
{ $match: { items: { $elemMatch: { sku: "W001", qty: { $gt: 0 } } } } }

// Type-based filtering (MongoDB 5.0+)
{ $match: { $expr: { $eq: [{ $type: "$field" }, "string"] } } }
```

### 2.2 $project - Reshaping

```javascript
// Include specific fields
{ $project: { "customer.name": 1, "total": 1, "_id": 0 } }

// Exclude specific fields
{ $project: { "internal_data": 0, "password": 0 } }

// Add computed fields
{ $project: {
  name: 1,
  total: 1,
  discount: { $multiply: ["$total", 0.1] },
  final_price: { $subtract: ["$total", { $multiply: ["$total", 0.1] }] }
}}

// Rename fields
{ $project: { order_total: "$total", customer_name: "$customer.name" } }

// Create nested structures
{ $project: {
  order: {
    id: "$_id",
    total: "$total",
    customer: "$customer.name"
  }
}}

// Conditional fields
{ $project: {
  status_label: {
    $switch: {
      branches: [
        { case: { $eq: ["$status", 1] }, then: "Active" },
        { case: { $eq: ["$status", 0] }, then: "Inactive" }
      ],
      default: "Unknown"
    }
  }
}}

// Exclude _id
{ $project: { _id: 0 } }
```

### 2.3 $group - Aggregation

```javascript
// Basic grouping
{ $group: { _id: "$customer_id", total: { $sum: "$total" } } }

// Group by multiple fields
{ $group: {
  _id: { 
    month: { $month: "$created" }, 
    status: "$status" 
  },
  count: { $sum: 1 },
  total: { $sum: "$total" },
  avg_amount: { $avg: "$total" },
  min_amount: { $min: "$total" },
  max_amount: { $max: "$total" }
}}

// Group with array accumulation
{ $group: {
  _id: "$customer_id",
  orders: { $push: "$_id" },
  unique_items: { $addToSet: "$product_id" },
  first_order: { $first: "$created" },
  last_order: { $last: "$created" }
}}

// Group all documents
{ $group: {
  _id: null,
  total_revenue: { $sum: "$total" },
  total_orders: { $sum: 1 },
  average_order: { $avg: "$total" }
}}

// Group with $count
{ $group: { _id: "$status", count: { $sum: 1 } } }

// Count all (equivalent to COUNT(*))
{ $count: "total" }
```

### 2.4 $lookup - Joins

```javascript
// Basic lookup (LEFT OUTER JOIN equivalent)
{ $lookup: {
  from: "customers",
  localField: "customer_id",
  foreignField: "_id",
  as: "customer_info"
}}

// Lookup with pipeline (more control)
{ $lookup: {
  from: "products",
  let: { product_id: "$product_id" },
  pipeline: [
    { $match: { $expr: { $eq: ["$_id", "$$product_id"] } } },
    { $project: { name: 1, price: 1 } }
  ],
  as: "product_details"
}}

// Lookup with array localField
{ $lookup: {
  from: "products",
  localField: "item_ids",
  foreignField: "_id",
  as: "items"
}}

// Self-referential lookup
{ $lookup: {
  from: "employees",
  localField: "manager_id",
  foreignField: "_id",
  as: "manager"
}}

// Uncorrelated subquery (static from)
{ $lookup: {
  from: "settings",
  pipeline: [
    { $match: { type: "global" } }
  ],
  as: "global_settings"
}}
```

### 2.5 $unwind - Array Deconstruction

```javascript
// Basic unwind
{ $unwind: "$items" }

// Preserve null and empty arrays
{ $unwind: { 
  path: "$items", 
  preserveNullAndEmptyArrays: true 
}}

// Unwind with include array index
{ $unwind: {
  path: "$items",
  includeArrayIndex: "item_index"
}}

// Multiple unwinds (order matters!)
// This creates cartesian product - be careful
{ $unwind: "$items" },
{ $unwind: "$tags" }

// Correct approach for nested arrays
// First group to nest, then unwind once
```

### 2.6 $facet - Multiple Pipelines

```javascript
// Multiple parallel pipelines on same data
db.products.aggregate([
  { $facet: {
    // Pipeline 1: Group by category
    byCategory: [
      { $group: { _id: "$category", count: { $sum: 1 } } }
    ],
    
    // Pipeline 2: Price ranges
    byPrice: [
      { $bucket: {
        groupBy: "$price",
        boundaries: [0, 50, 100, 200, Infinity],
        default: "Other"
      }}
    ],
    
    // Pipeline 3: Top tags
    topTags: [
      { $unwind: "$tags" },
      { $group: { _id: "$tags", count: { $sum: 1 } } },
      { $sort: { count: -1 } },
      { $limit: 10 }
    ]
  }}
])
```

### 2.7 Other Stage Operators

```javascript
// $sort
{ $sort: { total: -1, date: 1 } }

// $limit
{ $limit: 10 }

// $skip
{ $skip: 100 }

// $count (terminal stage)
{ $count: "total" }

// $out (write to collection)
{ $out: "aggregated_results" }

// $merge (write with merge options)
{ $merge: {
  into: "results",
  on: "_id",
  whenMatched: "replace",
  whenNotMatched: "insert"
}}

// $sample (random sampling)
{ $sample: { size: 100 } }

// $bucket (categorize into buckets)
{ $bucket: {
  groupBy: "$price",
  boundaries: [0, 25, 50, 100, 200, Infinity],
  default: "Other",
  output: {
    count: { $sum: 1 },
    products: { $push: "$name" }
  }
}}

// $bucketAuto (automatic boundaries)
{ $bucketAuto: {
  groupBy: "$price",
  buckets: 5,
  output: {
    count: { $sum: 1 },
    avgPrice: { $avg: "$price" }
  }
}}

// $setWindowFields (window functions)
db.sales.aggregate([
  { $setWindowFields: {
    sortBy: { date: 1 },
    output: {
      runningTotal: {
        $sum: "$amount",
        window: { documents: ["unbounded", "current"] }
      }
    }
  }}
])
```

---

## 3. Expression Operators

### 3.1 Arithmetic Operators

```javascript
// Basic arithmetic
{ $add: ["$price", "$tax"] }
{ $subtract: ["$total", "$discount"] }
{ $multiply: ["$quantity", "$price"] }
{ $divide: ["$total", "$quantity"] }
{ $mod: ["$total", 100] }

// Nested arithmetic
{ $add: [
  "$price",
  { $multiply: ["$price", "$tax_rate"] },
  "$shipping"
]}

// Round results
{ $round: ["$price", 2] }  // 2 decimal places

// Floor/Ceiling
{ $floor: "$price" }
{ $ceil: "$price" }

// Exponential/Logarithmic
{ $exp: "$value" }
{ $ln: "$value" }
{ $log10: "$value" }
{ $pow: ["$base", "$exponent"] }
{ $sqrt: "$value" }
```

### 3.2 String Operators

```javascript
// Case conversion
{ $toUpper: "$name" }
{ $toLower: "$email" }

// Substring (byte-based, deprecated)
{ $substr: ["$name", 0, 5] }

// Substring (byte-based, MongoDB 4.4+)
{ $substrBytes: ["$name", 0, 5] }

// Substring (UTF-8 safe, MongoDB 4.4+)
{ $substrCP: ["$name", 0, 5] }

// String concatenation
{ $concat: ["$first_name", " ", "$last_name"] }

// Trim
{ $trim: { input: "  hello  ", chars: " " } }
{ $ltrim: { input: "  hello", chars: " " } }
{ $rtrim: { input: "hello  ", chars: " " } }

// Replace
{ $replaceOne: { input: "$text", find: "old", replacement: "new" } }
{ $replaceAll: { input: "$text", find: "old", replacement: "new" } }

// Split
{ $split: { string: "a,b,c", separator: "," } }

// Find position
{ $indexOfBytes: ["$text", "pattern"] }
{ $indexOfCP: ["$text", "pattern"] }

// Length
{ $strLenBytes: "$text" }  // bytes
{ $strLenCP: "$text" }     // code points

// Regex (MongoDB 5.0+)
{ $regexFind: { input: "$text", regex: "\\d+" } }
{ $regexFindAll: { input: "$text", regex: "\\d+" } }
{ $regexMatch: { input: "$text", regex: "^test" } }
```

### 3.3 Comparison Operators

```javascript
// In aggregation expressions
{ $eq: ["$status", "active"] }
{ $ne: ["$amount", 0] }
{ $gt: ["$price", 100] }
{ $gte: ["$qty", 10] }
{ $lt: ["$total", 1000] }
{ $lte: ["$age", 65] }

// Set membership
{ $in: ["$status", ["active", "pending"]] }
{ $nin: ["$category", ["archived", "deleted"]] }

// In $match stage (shorthand)
{ $match: { status: "active" } }
{ $match: { amount: { $gt: 100 } } }
```

### 3.4 Logical Operators

```javascript
// And
{ $and: [
  { status: "active" },
  { amount: { $gt: 100 } }
]}

// Or
{ $or: [
  { status: "completed" },
  { status: "cancelled" }
]}

// Not
{ $not: { status: "deleted" } }

// Nor (not any of)
{ $nor: [
  { status: "deleted" },
  { status: "archived" }
]}

// Conditional
{ $cond: { if: "$is_active", then: "Active", else: "Inactive" } }
{ $cond: { if: { $gte: ["$amount", 1000] }, then: "Premium", else: "Regular" } }

// Switch
{ $switch: {
  branches: [
    { case: { $eq: ["$status", "new"] }, then: "New Order" },
    { case: { $eq: ["$status", "pending"] }, then: "Pending Review" },
    { case: { $eq: ["$status", "completed"] }, then: "Completed" }
  ],
  default: "Unknown"
}}

// IfNull
{ $ifNull: ["$field", "default_value"] }
```

### 3.5 Type Operators

```javascript
// Convert types
{ $toDouble: "$string_number" }
{ $toInt: "$string_int" }
{ $toString: "$number" }
{ $toDate: "$date_string" }
{ $toObjectId: "$hex_string" }

// Type checking
{ $type: "$field" }

// Convert from
{ $convert: {
  input: "$value",
  to: "int",
  onError: 0,
  onNull: 0
}}
```

---

## 4. Array Operations

### 4.1 Array Field Operations

```javascript
// $filter - Filter array elements
{ $filter: {
  input: "$items",
  as: "item",
  cond: { $gte: ["$$item.price", 10] }
}}

// $map - Transform array elements
{ $map: {
  input: "$items",
  as: "item",
  in: { 
    name: "$$item.name",
    total: { $multiply: ["$$item.price", "$$item.qty"] }
  }
}}

// $reduce - Accumulate array
{ $reduce: {
  input: "$prices",
  initialValue: 0,
  in: { $add: ["$$value", "$$this"] }
}}

// $reduce for complex objects
{ $reduce: {
  input: "$transactions",
  initialValue: { balance: 0, count: 0 },
  in: {
    balance: { $add: ["$$value.balance", "$$this.amount"] },
    count: { $add: ["$$value.count", 1] }
  }
}}
```

### 4.2 Array Element Access

```javascript
// Access specific element
{ $arrayElemAt: ["$items", 0] }   // First
{ $arrayElemAt: ["$items", -1] }  // Last

// First and last
{ $first: "$items" }
{ $last: "$items" }

// Array size
{ $size: "$items" }

// Slice array
{ $slice: ["$items", 0, 5] }       // First 5
{ $slice: ["$items", -5] }        // Last 5

// Range array (generate array of numbers)
{ $range: [0, 10, 2] }  // [0, 2, 4, 6, 8]
```

### 4.3 Array Search Operations

```javascript
// Check if element in array
{ $in: ["$tag", ["new", "featured", "sale"]] }

// Check if any element matches
{ $anyElementTrue: {
  $map: {
    input: "$items",
    as: "item",
    in: { $eq: ["$$item.out_of_stock", true] }
  }
}}

// Check if all elements match
{ $allElementsTrue: {
  $map: {
    input: "$items",
    as: "item",
    in: { $eq: ["$$item.in_stock", true] }
  }
}}

// Object to array conversion
{ $objectToArray: "$specs" }

// Array to object conversion
{ $arrayToObject: "$pairs" }

// Zip two arrays together
{ $zip: {
  inputs: ["$names", "$values"],
  useLongestLength: false
}}
```

### 4.4 Set Operations

```javascript
// $setUnion
{ $setUnion: [["a", "b"], ["b", "c"]] }  // ["a", "b", "c"]

// $setIntersection
{ $setIntersection: [["a", "b"], ["b", "c"]] }  // ["b"]

// $setDifference
{ $setDifference: [["a", "b"], ["b", "c"]] }  // ["a"]
```

---

## 5. Date Operations

### 5.1 Date Extractors

```javascript
// Basic extractors
{ $year: "$created_at" }
{ $month: "$created_at" }
{ $dayOfMonth: "$created_at" }
{ $dayOfWeek: "$created_at" }    // 1 (Sunday) - 7 (Saturday)
{ $dayOfYear: "$created_at" }
{ $week: "$created_at" }          // 0-53

// Time extractors
{ $hour: "$created_at" }
{ $minute: "$created_at" }
{ $second: "$created_at" }
{ $millisecond: "$created_at" }

// Combined date parts
{ $dateToParts: {
  date: "$created_at",
  timezone: "America/New_York"
}}
// Returns: { year, month, day, hour, minute, second, millisecond }
```

### 5.2 Date Creation

```javascript
// Date from string
{ $dateFromString: {
  dateString: "2024-01-15T10:30:00Z",
  timezone: "America/New_York"
}}

// Date from parts
{ $dateFromParts: {
  year: 2024,
  month: 1,
  day: 15,
  hour: 10,
  minute: 30
}}

// Date from millis
{ $dateFromString: {
  dateString: { $toString: "$timestamp_ms" }
}}
```

### 5.3 Date Arithmetic

```javascript
// Add to date (MongoDB 5.0+)
{ $dateAdd: {
  startDate: "$created",
  unit: "month",
  amount: 1
}}
// Units: year, month, day, hour, minute, second, week, quarter

// Difference between dates
{ $dateDiff: {
  startDate: "$created",
  endDate: "$$NOW",
  unit: "day"
}}
// Units: year, month, day, hour, minute, second, millisecond

// Truncate date (MongoDB 5.0+)
{ $dateTrunc: {
  date: "$created",
  unit: "day",
  timezone: "America/New_York"
}}
// Truncates to: day, week, month, quarter, year

// Date to string
{ $dateToString: {
  format: "%Y-%m-%d %H:%M",
  date: "$created_at",
  timezone: "America/New_York"
}}

// Date parts from string
{ $dateToParts: { date: "$created_at" }}
```

---

## 6. Aggregation Optimization

### 6.1 Pipeline Optimization

```javascript
// ❌ BAD: Unnecessary full collection scan
db.orders.aggregate([
  { $sort: { date: -1 } },
  { $limit: 100 },
  { $match: { status: "completed" } }
])

// ✅ GOOD: $match early to filter
db.orders.aggregate([
  { $match: { status: "completed" } },
  { $sort: { date: -1 } },
  { $limit: 100 }
])

// ✅ GOOD: $project after $match reduces data
db.orders.aggregate([
  { $match: { status: "completed", date: { $gte: "2024-01-01" } } },
  { $project: { order_id: 1, total: 1, customer: 1 } },
  { $sort: { date: -1 } }
])
```

### 6.2 Index Usage

```javascript
// Ensure $match uses indexes
// Create indexes for filter fields
db.orders.createIndex({ status: 1, date: -1 })

// Verify index usage
db.orders.explain().aggregate([
  { $match: { status: "completed" } }
])

// Use hint to force specific index
db.orders.aggregate([
  { $match: { status: "completed" } }
], { hint: { status: 1, date: -1 } })
```

### 6.3 Memory Management

```javascript
// Default memory limit: 100MB per stage
// Use allowDiskUse for large aggregations
db.orders.aggregate([
  { $group: { _id: "$customer", total: { $sum: "$total" } } }
], { allowDiskUse: true })

// For large group operations, use $bucketAuto
// instead of $group with $push for large arrays

// $bucketAuto automatically distributes into buckets
// reducing memory usage for histogram-style queries
```

### 6.4 Performance Tips

```javascript
// 1. Place $match early
// 2. Use $limit when possible
// 3. Reduce fields with $project
// 4. Use indexed fields in $match
// 5. Avoid $unwind on large arrays - use $filter instead
// 6. Use $lookup with pipeline instead of uncorrelated
// 7. Consider $count instead of $group with $sum: 1 for counting
// 8. Use explain() to diagnose issues
```

---

## 7. Common Patterns

### 7.1 Running Totals and Windows

```javascript
// Running total with window
db.sales.aggregate([
  { $setWindowFields: {
    sortBy: { date: 1 },
    output: {
      runningTotal: {
        $sum: "$amount",
        window: { documents: ["unbounded", "current"] }
      },
      runningCount: {
        $sum: 1,
        window: { documents: ["unbounded", "current"] }
      }
    }
  }}
])

// Moving average
db.sales.aggregate([
  { $setWindowFields: {
    sortBy: { date: 1 },
    output: {
      avg_7day: {
        $avg: "$amount",
        window: { documents: [-3, 3] }
      }
    }
  }}
])

// Lag/Lead
db.sales.aggregate([
  { $setWindowFields: {
    sortBy: { date: 1 },
    output: {
      prev_amount: {
        $shift: {
          output: "$amount",
          by: -1,
          default: 0
        }
      },
      next_amount: {
        $shift: {
          output: "$amount",
          by: 1,
          default: 0
        }
      }
    }
  }}
])
```

### 7.2 Top N per Group

```javascript
// Method 1: Sort + group + slice
db.orders.aggregate([
  { $sort: { customer_id: 1, total: -1 } },
  { $group: {
    _id: "$customer_id",
    orders: { $push: "$$ROOT" }
  }},
  { $project: {
    orders: { $slice: ["$orders", 3] }
  }},
  { $unwind: "$orders" },
  { $replaceRoot: { newRoot: "$orders" } }
])

// Method 2: Using $group with $first
db.orders.aggregate([
  { $sort: { customer_id: 1, total: -1 } },
  { $group: {
    _id: "$customer_id",
    top_orders: {
      $push: {
        order_id: "$_id",
        total: "$total"
      }
    }
  }},
  { $project: {
    top_orders: { $slice: ["$top_orders", 3] }
  }}
])
```

### 7.3 Percentiles and Distribution

```javascript
// Percentile using $bucketAuto
db.orders.aggregate([
  { $bucketAuto: {
    groupBy: "$total",
    buckets: 4,
    output: {
      count: { $sum: 1 },
      min: { $min: "$total" },
      max: { $max: "$total" }
    }
  }}
])

// Median calculation
db.orders.aggregate([
  { $sort: { total: 1 } },
  { $group: {
    _id: null,
    sorted: { $push: "$total" }
  }},
  { $project: {
    median: {
      $arrayElemAt: [
        "$sorted",
        { $floor: { $divide: [{ $size: "$sorted" }, 2] } }
      ]
    }
  }}
])
```

### 7.4 Cumulative Calculations

```javascript
// Running count
db.orders.aggregate([
  { $sort: { created: 1 } },
  { $group: {
    _id: "$customer",
    orders: { $push: { id: "$_id", total: "$total" } }
  }},
  { $unwind: "$orders" },
  { $setWindowFields: {
    sortBy: { "orders.id": 1 },
    output: {
      order_number: {
        $sum: 1,
        window: { documents: ["unbounded", "current"] }
      }
    }
  }}
])
```

---

## 8. Advanced Transformations

### 8.1 Pivot/Unpivot

```javascript
// Pivot: Rows to Columns
db.sales.aggregate([
  { $group: {
    _id: "$product",
    months: {
      $push: { month: "$month", sales: "$sales" }
    }
  }},
  { $project: {
    product: "$_id",
    jan: { $arrayElemAt: [{ $filter: { input: "$months", as: "m", cond: { $eq: ["$$m.month", 1] } } }, 0] },
    feb: { $arrayElemAt: [{ $filter: { input: "$months", as: "m", cond: { $eq: ["$$m.month", 2] } } }, 0] }
  }}
])

// Unpivot: Columns to Rows
// Use $objectToArray + $unwind
```

### 8.2 Hierarchical Data

```javascript
// Flatten nested hierarchy
db.organization.aggregate([
  { $project: {
    name: 1,
    level1: "$department",
    level2: "$department.team",
    level3: "$department.team.group"
  }},
  { $unwind: { path: "$level3", preserveNullAndEmptyArrays: true } },
  { $group: {
    _id: "$level3",
    name: { $first: "$name" },
    parent: { $first: "$level2" }
  }}
])
```

### 8.3 Text Search Aggregation

```javascript
// Text search with scoring
db.articles.aggregate([
  { $match: { $text: { $search: "mongodb tutorial" } } },
  { $project: {
    title: 1,
    score: { $meta: "textScore" }
  }},
  { $sort: { score: -1 } }
])

// Search with highlighting
{
  $search: {
    text: {
      query: "database",
      path: ["title", "content"],
      fuzzy: { maxEdits: 1 }
    }
  }
}
```

---

## 9. Time Series Patterns

### 9.1 Time Grouping

```javascript
// Group by hour
db.events.aggregate([
  { $group: {
    _id: {
      $dateToString: { format: "%Y-%m-%d %H:00", date: "$timestamp" }
    },
    count: { $sum: 1 }
  }},
  { $sort: { _id: 1 } }
])

// Group by day of week
db.orders.aggregate([
  { $group: {
    _id: { $dayOfWeek: "$created" },
    count: { $sum: 1 }
  }},
  { $sort: { _id: 1 } }
])
```

### 9.2 Moving Window Analytics

```javascript
// 7-day rolling average
db.metrics.aggregate([
  { $setWindowFields: {
    sortBy: { timestamp: 1 },
    output: {
      rolling_avg: {
        $avg: "$value",
        window: { documents: [-3, 3] }
      },
      trend: {
        $linearRegression: {
          input: [{ x: { $indexOfArray: ["$timestamp"] } }, "y" }],
          output: "slope"
        }
      }
    }
  }}
])
```

---

## 10. Performance Patterns

### 10.1 Covered Queries in Aggregation

```javascript
// Make aggregation use covering index
db.orders.aggregate([
  { $match: { status: "completed" } },
  { $project: { _id: 1, total: 1, status: 1 } }
])  // All in index

// Verify with explain
db.orders.explain("executionStats").aggregate([
  { $match: { status: "completed" } },
  { $project: { _id: 1, total: 1 } }
])
```

### 10.2 Large Result Handling

```javascript
// Cursor with batch size
const cursor = db.orders.aggregate(pipeline, { cursor: { batchSize: 1000 } })
while (cursor.hasNext()) {
  process(cursor.next())
}

// Output to collection for large results
db.orders.aggregate([
  { $match: { date: { $gte: "2024-01-01" } } },
  { $group: { _id: "$product", total: { $sum: "$amount" } } },
  { $out: "product_summaries" }  // Write to new collection
})
```

---

## 11. Anti-Patterns

### 11.1 Common Mistakes

```javascript
// ❌ $match after $sort on large collection
db.orders.aggregate([
  { $sort: { date: -1 } },    // Sorts entire collection
  { $limit: 100 },
  { $match: { status: "x" } } // Filters only 100 docs
])

// ✅ Use $match first
db.orders.aggregate([
  { $match: { status: "x" } },
  { $sort: { date: -1 } },
  { $limit: 100 }
])

// ❌ Large $push in $group
db.orders.aggregate([
  { $group: {
    _id: "$customer",
    all_orders: { $push: "$$ROOT" }  // Could be huge!
  }}
])

// ✅ Use $limit or $project
db.orders.aggregate([
  { $sort: { date: -1 } },
  { $group: {
    _id: "$customer",
    recent_orders: { $push: { $slice: ["$items", 5] } }
  }}
])

// ❌ Unwinding large arrays without limit
db.orders.aggregate([
  { $unwind: "$items" }  // Could multiply docs significantly
])

// ✅ Filter before unwinding
db.orders.aggregate([
  { $match: { "items.price": { $gt: 100 } } },
  { $unwind: "$items" },
  { $match: { "items.price": { $gt: 100 } } }
])
```

---

*Questo documento fa parte del modulo 05 "NoSQL MongoDB" della Data Encyclopedia.*