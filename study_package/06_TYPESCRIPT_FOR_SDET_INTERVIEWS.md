# 📘 TYPESCRIPT FOR SDET INTERVIEWS (THEORETICAL REFRESHER & CHEATSHEET)
**Target**: Senior SDET Technical Interview Preparation (Theoretical Mastery)  
**Candidate**: Lokender Singh  
*Purpose: You will answer TypeScript interview questions verbally while live coding in Python/SQL. This guide gives you the precise terminology, mental models, and architectural patterns needed to sound authoritative and experienced in your interview.*

---

## 1. What TypeScript Is & Why Modern Automation Frameworks Use It

### The Architectural Elevator Pitch
> *"TypeScript is a statically typed superset of JavaScript that compiles down to clean, plain JavaScript. In automation frameworks (like Playwright), TypeScript brings compile-time type safety, intelligent autocompletion for DOM locators and API payloads, and catches 80% of runtime errors (like spelling mistakes in payload keys or accessing undefined properties) before the browser even launches."*

### Key Compilation Principle: Type Erasure
- **TypeScript exists ONLY at compile time**.
- When `tsc` compiles TypeScript into JavaScript, **all types, interfaces, generics, and type annotations are completely stripped away (erased)**.
- At runtime in Node.js or the browser, only plain JavaScript executes. Types have zero runtime performance cost.

---

## 2. Types vs. Interfaces (The #1 Most Common TS Interview Question)

Interviewers frequently ask: *"What is the difference between `type` and `interface` in TypeScript, and which do you use in an automation framework?"*

| Feature | `interface` | `type` (Type Alias) |
| :--- | :--- | :--- |
| **Primary Purpose** | Defining the shape of objects, classes, and Page Objects. | Defining any type: primitives, unions, tuples, intersections, or primitives. |
| **Extensibility** | Extends via the `extends` keyword (`interface AdminUser extends User`). | Extends via intersection `&` (`type AdminUser = User & { role: string }`). |
| **Declaration Merging** | **Yes**: Defining the same interface twice merges them into one. | **No**: Defining duplicate type names throws a compile error. |
| **Unions & Primitives** | Cannot directly represent a union (`type Status = 'A' \| 'B'`). | Can represent unions, mapped types, conditional types. |
| **SDET Best Practice** | **Use `interface` for Page Objects, API DTO payloads, and custom fixtures (`test.extend<CustomFixtures>`).** | **Use `type` for status unions, string literals, and utility transformations.** |

### Practical SDET Code Example:
```typescript
// Union Type for Status
type ClaimStatus = 'PAID' | 'DENIED' | 'PENDING' | 'IN_REVIEW';

// Interface for API Request Payload
interface CreateClaimDTO {
  patientId: string;
  providerId: string;
  billedAmount: number;
  status: ClaimStatus; // using union type inside interface
}

// Interface for Custom Playwright Fixtures
interface FrameworkFixtures {
  authenticatedPage: Page;
  claimApi: ClaimApiClient;
}
```

---

## 3. The Special Types: `any` vs `unknown` vs `never` vs `void`

Enterprise interviewers use these 4 types to separate junior testers from senior automation engineers:

### 1. `any` (The "Escape Hatch" - Anti-Pattern)
- Disables all compile-time type checking for that variable.
- Calling `foo.bar.baz()` on an `any` compiles without error, but crashes at runtime with `TypeError: Cannot read properties of undefined`.
- **Senior SDET Rule**: Avoid `any` in test frameworks. If data is dynamic, use `unknown` or generics.

### 2. `unknown` (The Type-Safe Alternative to `any`)
- Represents a value whose type is not yet known (e.g. raw JSON from `fetch()` or dynamic API response).
- **The Rule**: TypeScript will **NOT** allow you to access properties or call methods on an `unknown` variable until you perform **Type Narrowing** (using `typeof`, `instanceof`, or a custom type guard).
```typescript
const response: unknown = await fetchApi('/data');

// ❌ Error: Property 'id' does not exist on type 'unknown'
// console.log(response.id);

// ✅ Correct (Type Narrowing):
if (typeof response === 'object' && response !== null && 'id' in response) {
  console.log((response as { id: string }).id);
}
```

### 3. `void` (Nothing Returned)
- Used as the return type of functions that do not return a value (e.g., an action method in a Page Object):
```typescript
async clickSubmit(): Promise<void> {
  await this.submitBtn.click();
}
```

### 4. `never` (Values That Never Occur)
- Represents values that can never happen.
- Used as the return type of functions that **always throw an exception** or enter an infinite loop.
- Used in **Exhaustive Type Checking** to ensure all branches of a union type are handled.

---

## 4. Type Narrowing & Custom Type Guards

Type narrowing is the process of moving an expression from a broader type (like `string | number` or `unknown`) to a more specific type.

### Techniques for Narrowing:
1. **`typeof`**: Used for primitives (`typeof x === 'string'`, `'number'`, `'boolean'`).
2. **`instanceof`**: Used for class instances (`if (err instanceof ApiError)`).
3. **`in` operator**: Checks if a property exists in an object (`if ('claimId' in payload)`).
4. **Custom Type Guard (`is` keyword)**:
   A function whose return type is `param is TargetType`:
   ```typescript
   interface HealthcareClaim {
     claimId: string;
     amount: number;
   }

   function isHealthcareClaim(obj: any): obj is HealthcareClaim {
     return obj && typeof obj.claimId === 'string' && typeof obj.amount === 'number';
   }

   // In test assertions:
   if (isHealthcareClaim(responsePayload)) {
     // TypeScript now treats responsePayload strictly as HealthcareClaim!
     expect(responsePayload.amount).toBeGreaterThan(0);
   }
   ```

---

## 5. Generics in Test Automation (`<T>`)

Generics allow you to write reusable code that works with a variety of types while maintaining strict type safety.

### Why Generics Matter in SDET Frameworks:
Playwright and API test runners rely heavily on generics:

1. **Custom Fixtures**: `base.extend<CustomFixtures>({ ... })`
2. **API Client Wrapper**:
   ```typescript
   export class ApiClient {
     // Generic method: caller specifies the return DTO type T
     async get<T>(url: string): Promise<T> {
       const res = await this.request.get(url);
       return (await res.json()) as T;
     }
   }

   // Usage in test:
   const user = await api.get<UserDTO>('/api/user/1');
   // user.email has full type completion!
   ```

---

## 6. TypeScript Utility Types (Must-Know for Interviews)

TypeScript provides built-in transformations for existing types. In interview questions regarding payload validation, mentioning these marks you as a senior engineer:

### 1. `Partial<T>`
Makes all properties of `T` **optional** (`?`).
- **SDET Use Case**: Writing PATCH API requests or test data factories where you only want to override 1 or 2 fields:
```typescript
function createTestUser(overrides: Partial<UserDTO> = {}): UserDTO {
  return {
    id: 'usr-default',
    email: 'test@optum.com',
    role: 'QA',
    ...overrides
  };
}
```

### 2. `Required<T>`
Makes all properties in `T` mandatory (opposite of `Partial`).

### 3. `Readonly<T>`
Makes all properties immutable. Modifying a property causes a compile-time error.
- **SDET Use Case**: Framework environment configs (`Readonly<EnvironmentConfig>`).

### 4. `Pick<T, Keys>`
Creates a new type by selecting a specific subset of keys from `T`.
```typescript
type UserCredentials = Pick<UserDTO, 'email' | 'password'>;
```

### 5. `Omit<T, Keys>`
Creates a new type by dropping specific keys from `T`.
- **SDET Use Case**: Creating a POST payload from a DB model by omitting the auto-generated `id` and `createdAt` fields:
```typescript
type NewClaimPayload = Omit<ClaimModel, 'id' | 'createdAt'>;
```

### 6. `Record<Keys, Type>`
Constructs an object type whose property keys are `Keys` and values are `Type`.
```typescript
type CategoryColorMap = Record<string, string>;
type EndpointStatusMap = Record<string, number>;
```

---

## 7. Enums vs. Union Types

In older TypeScript codebases, developers used `enum`:
```typescript
enum TestStatus {
  PASS = 'PASS',
  FAIL = 'FAIL'
}
```
**Why Modern SDETs Prefer Union String Literals over `enum`**:
1. Enums generate extra runtime JavaScript boilerplate code.
2. Union types (`type TestStatus = 'PASS' | 'FAIL'`) are completely erased at compile time (zero runtime overhead).
3. Union types work seamlessly with pure JSON payloads received from REST APIs without needing custom deserializers.

---

## 8. Async / Await & The JavaScript Event Loop

Since Playwright is entirely asynchronous, interviewers love probing the Event Loop:

### Key Concepts:
- **Call Stack**: Executes synchronous JavaScript code one frame at a time.
- **Microtask Queue**: High priority queue where resolved `Promise` callbacks (`then`, `await` continuations) are queued.
- **Macrotask Queue**: Lower priority queue for `setTimeout`, `setInterval`, network I/O events.
- **Event Loop**: Checks if the Call Stack is empty. If empty, processes **ALL** Microtasks first before taking a Macrotask.

### `Promise.all()` vs `Promise.allSettled()` in Test Frameworks:
- **`Promise.all([p1, p2, p3])`**: Executes promises concurrently. **Fails fast**: if any single promise rejects, the entire `Promise.all` immediately rejects.
  - *SDET Use Case*: Submitting concurrent API health checks where all must pass.
- **`Promise.allSettled([p1, p2, p3])`**: Waits for **all** promises to either fulfill or reject. Never rejects. Returns an array of `{ status: 'fulfilled' | 'rejected', value/reason }`.
  - *SDET Use Case*: Running test teardown actions where you want every cleanup step to execute even if one fails.

---

## 9. Top 10 High-Frequency TypeScript Interview Questions & Answers

### Q1: What is the purpose of `tsconfig.json`?
*Answer*: It is the root configuration file for the TypeScript compiler (`tsc`). It specifies compiler options (e.g. `target: "ES2022"`, `module: "CommonJS"` or `"ESNext"`, `strict: true`, `moduleResolution: "Node"`, and `outDir`) and defines which files should be included or excluded from compilation.

### Q2: What does `"strict": true` do in `tsconfig.json`?
*Answer*: It enables a suite of strict type-checking behaviors, including `noImplicitAny` (flags variables without types that default to `any`), `strictNullChecks` (prevents `null`/`undefined` from being assigned to other types unless explicitly unioned), and `strictFunctionTypes`.

### Q3: What is the difference between `null` and `undefined` in TypeScript?
*Answer*: `undefined` means a variable has been declared but has not yet been assigned a value (or a function parameter was not provided). `null` is an intentional assignment representing the explicit absence of any object value (often returned by databases or DOM APIs when an element is not found).

### Q4: What is optional chaining (`?.`) and nullish coalescing (`??`)?
*Answer*:
- Optional chaining (`a?.b?.c`) short-circuits and returns `undefined` if `a` or `b` is `null` or `undefined`, preventing `TypeError`.
- Nullish coalescing (`a ?? 'default'`) returns the right-hand operand **ONLY** if the left-hand operand is `null` or `undefined`. Unlike logical OR (`||`), it does not treat `0`, `""`, or `false` as empty.

### Q5: What is Type Assertion (`as`) and is it safe?
*Answer*: Type assertion (`const x = data as UserDTO`) tells the compiler to treat `data` as `UserDTO`, bypassing compile-time checks. It is a compile-time instruction only and does not perform runtime validation. If the underlying data structure does not match, runtime errors will occur.

### Q6: How do you make a property optional in an interface?
*Answer*: By appending a question mark `?` after the property name (`middleName?: string;`).

### Q7: What are Tuples in TypeScript?
*Answer*: A tuple is a typed array with a fixed number of elements where each position has a specific type. Example: `type Coordinates = [number, number];` or `type TestResult = [string, boolean, number];`.

### Q8: What is Declaration Merging?
*Answer*: A TypeScript feature where the compiler automatically combines two or more separate interface declarations with the same name into a single interface definition.

### Q9: Can an interface implement a class in TypeScript?
*Answer*: A class can `implement` an interface to enforce structure (`class LoginPage implements IPage`). Conversely, a TypeScript interface can also extend a class, inheriting its members but not their implementation.

### Q10: How does TypeScript support Page Object Model design?
*Answer*: TypeScript enables typing for Playwright locators (`readonly submitButton: Locator;`), enforces strict constructor arguments (`constructor(readonly page: Page)`), and ensures action methods return strongly-typed promises (`Promise<DashboardPage>`), providing compile-time assurance that page transitions and selectors are valid.

