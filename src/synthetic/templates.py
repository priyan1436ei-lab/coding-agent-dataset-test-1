"""Multi-language and task templates for verified synthetic code generation."""
from typing import List, Dict, Any

# Multi-language Algorithm & Systems Implementation Templates
ALGORITHM_TEMPLATES: List[Dict[str, Any]] = [
    {
        "language": "python",
        "task_type": "code_generation",
        "title": "LRU Cache Implementation",
        "prompt": "Implement an LRU (Least Recently Used) Cache with O(1) time complexity for get and put operations using Python's collections.OrderedDict.",
        "response": '''```python
from collections import OrderedDict
from typing import Any, Optional

class LRUCache:
    """Least Recently Used (LRU) Cache with O(1) get and put."""
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self.capacity = capacity
        self.cache: OrderedDict[Any, Any] = OrderedDict()

    def get(self, key: Any) -> Optional[Any]:
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: Any, value: Any) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
```''',
        "test_code": '''c = LRUCache(2)
c.put(1, 1)
c.put(2, 2)
assert c.get(1) == 1
c.put(3, 3)
assert c.get(2) is None
assert c.get(3) == 3
'''
    },
    {
        "language": "typescript",
        "task_type": "code_generation",
        "title": "Type-safe Event Emitter",
        "prompt": "Write a fully type-safe EventEmitter in TypeScript supporting subscribe, emit, and unsubscribe methods.",
        "response": '''```typescript
type EventCallback<T = any> = (payload: T) => void;

export class TypedEventEmitter<Events extends Record<string, any>> {
  private listeners: { [K in keyof Events]?: Array<EventCallback<Events[K]>> } = {};

  on<K extends keyof Events>(event: K, callback: EventCallback<Events[K]>): () => void {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event]!.push(callback);

    // Return unbind function
    return () => this.off(event, callback);
  }

  off<K extends keyof Events>(event: K, callback: EventCallback<Events[K]>): void {
    const list = this.listeners[event];
    if (!list) return;
    this.listeners[event] = list.filter((cb) => cb !== callback);
  }

  emit<K extends keyof Events>(event: K, payload: Events[K]): void {
    const list = this.listeners[event];
    if (!list) return;
    for (const callback of list) {
      callback(payload);
    }
  }
}
```''',
        "test_code": None
    },
    {
        "language": "rust",
        "task_type": "code_generation",
        "title": "Thread-safe ThreadPool Worker in Rust",
        "prompt": "Write a concurrent Worker ThreadPool pattern in Rust using std::sync::mpsc and Arc<Mutex<Receiver>>.",
        "response": '''```rust
use std::sync::{mpsc, Arc, Mutex};
use std::thread;

type Job = Box<dyn FnOnce() + Send + 'static>;

pub struct ThreadPool {
    workers: Vec<Worker>,
    sender: Option<mpsc::Sender<Job>>,
}

struct Worker {
    id: usize,
    thread: Option<thread::JoinHandle<()>>,
}

impl ThreadPool {
    pub fn new(size: usize) -> ThreadPool {
        assert!(size > 0, "ThreadPool size must be greater than zero");
        let (sender, receiver) = mpsc::channel();
        let receiver = Arc::new(Mutex::new(receiver));
        let mut workers = Vec::with_capacity(size);

        for id in 0..size {
            workers.push(Worker::new(id, Arc::clone(&receiver)));
        }

        ThreadPool {
            workers,
            sender: Some(sender),
        }
    }

    pub fn execute<F>(&self, f: F)
    where
        F: FnOnce() + Send + 'static,
    {
        let job = Box::new(f);
        if let Some(ref sender) = self.sender {
            sender.send(job).expect("Failed to send job to worker thread");
        }
    }
}

impl Worker {
    fn new(id: usize, receiver: Arc<Mutex<mpsc::Receiver<Job>>>) -> Worker {
        let thread = thread::spawn(move || loop {
            let message = receiver.lock().unwrap().recv();
            match message {
                Ok(job) => job(),
                Err(_) => break,
            }
        });
        Worker { id, thread: Some(thread) }
    }
}
```''',
        "test_code": None
    },
    {
        "language": "go",
        "task_type": "code_generation",
        "title": "Token Bucket Rate Limiter in Go",
        "prompt": "Implement a thread-safe Token Bucket rate limiter in Go with automatic refill using goroutines.",
        "response": '''```go
package ratelimit

import (
	"sync"
	"time"
)

type TokenBucket struct {
	capacity   int64
	tokens     float64
	refillRate float64 // tokens per second
	lastRefill time.Time
	mu         sync.Mutex
}

func NewTokenBucket(capacity int64, refillRate float64) *TokenBucket {
	return &TokenBucket{
		capacity:   capacity,
		tokens:     float64(capacity),
		refillRate: refillRate,
		lastRefill: time.Now(),
	}
}

func (tb *TokenBucket) Allow() bool {
	tb.mu.Lock()
	defer tb.mu.Unlock()

	now := time.Now()
	elapsed := now.Sub(tb.lastRefill).Seconds()
	tb.tokens += elapsed * tb.refillRate
	if tb.tokens > float64(tb.capacity) {
		tb.tokens = float64(tb.capacity)
	}
	tb.lastRefill = now

	if tb.tokens >= 1.0 {
		tb.tokens -= 1.0
		return true
	}
	return false
}
```''',
        "test_code": None
    },
    {
        "language": "java",
        "task_type": "code_generation",
        "title": "Generic Binary Search Tree with Inorder Traversal",
        "prompt": "Write a generic Binary Search Tree (BST) in Java with generic Comparable<T> and iterative inorder traversal.",
        "response": '''```java
package com.aethercoder.structures;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

public class BinarySearchTree<T extends Comparable<T>> {
    private static class Node<T> {
        T value;
        Node<T> left;
        Node<T> right;
        Node(T value) { this.value = value; }
    }

    private Node<T> root;

    public void insert(T value) {
        root = insertRecursive(root, value);
    }

    private Node<T> insertRecursive(Node<T> current, T value) {
        if (current == null) return new Node<>(value);
        int cmp = value.compareTo(current.value);
        if (cmp < 0) current.left = insertRecursive(current.left, value);
        else if (cmp > 0) current.right = insertRecursive(current.right, value);
        return current;
    }

    public List<T> inorderTraversal() {
        List<T> result = new ArrayList<>();
        Deque<Node<T>> stack = new ArrayDeque<>();
        Node<T> curr = root;

        while (curr != null || !stack.isEmpty()) {
            while (curr != null) {
                stack.push(curr);
                curr = curr.left;
            }
            curr = stack.pop();
            result.add(curr.value);
            curr = curr.right;
        }
        return result;
    }
}
```''',
        "test_code": None
    },
    {
        "language": "cpp",
        "task_type": "code_generation",
        "title": "Lock-Free SPSC Queue in Modern C++20",
        "prompt": "Write a single-producer single-consumer (SPSC) ring buffer in C++20 using std::atomic with acquire/release memory semantics.",
        "response": '''```cpp
#include <atomic>
#include <vector>
#include <optional>
#include <cstddef>

template <typename T, size_t Capacity>
class SPSCQueue {
    static_assert((Capacity & (Capacity - 1)) == 0, "Capacity must be power of two");
private:
    T buffer_[Capacity];
    alignas(64) std::atomic<size_t> tail_{0};
    alignas(64) std::atomic<size_t> head_{0};

public:
    bool push(const T& item) {
        const size_t current_tail = tail_.load(std::memory_order_relaxed);
        if ((current_tail - head_.load(std::memory_order_acquire)) >= Capacity) {
            return false; // Queue is full
        }
        buffer_[current_tail & (Capacity - 1)] = item;
        tail_.store(current_tail + 1, std::memory_order_release);
        return true;
    }

    std::optional<T> pop() {
        const size_t current_head = head_.load(std::memory_order_relaxed);
        if (current_head == tail_.load(std::memory_order_acquire)) {
            return std::nullopt; // Queue is empty
        }
        T item = buffer_[current_head & (Capacity - 1)];
        head_.store(current_head + 1, std::memory_order_release);
        return item;
    }
};
```''',
        "test_code": None
    },
    {
        "language": "c",
        "task_type": "code_generation",
        "title": "Dynamic String Buffer in C99",
        "prompt": "Implement a dynamic string buffer in C99 with safe memory reallocation, append, and clear operations.",
        "response": '''```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    char *data;
    size_t length;
    size_t capacity;
} StringBuffer;

StringBuffer* string_buffer_create(size_t initial_cap) {
    StringBuffer *sb = (StringBuffer*)malloc(sizeof(StringBuffer));
    if (!sb) return NULL;
    sb->capacity = initial_cap > 16 ? initial_cap : 16;
    sb->data = (char*)malloc(sb->capacity);
    if (!sb->data) {
        free(sb);
        return NULL;
    }
    sb->data[0] = '\\0';
    sb->length = 0;
    return sb;
}

int string_buffer_append(StringBuffer *sb, const char *str) {
    if (!sb || !str) return 0;
    size_t str_len = strlen(str);
    if (sb->length + str_len + 1 > sb->capacity) {
        size_t new_cap = sb->capacity * 2 + str_len;
        char *new_data = (char*)realloc(sb->data, new_cap);
        if (!new_data) return 0;
        sb->data = new_data;
        sb->capacity = new_cap;
    }
    memcpy(sb->data + sb->length, str, str_len);
    sb->length += str_len;
    sb->data[sb->length] = '\\0';
    return 1;
}

void string_buffer_free(StringBuffer *sb) {
    if (!sb) return;
    free(sb->data);
    free(sb);
}
```''',
        "test_code": None
    },
    {
        "language": "sql",
        "task_type": "code_generation",
        "title": "Window Function Ranking & Running Total in SQL",
        "prompt": "Write a PostgreSQL query using CTEs and Window Functions (DENSE_RANK, SUM OVER PARTITION) to calculate employee rankings and running departmental salaries.",
        "response": '''```sql
WITH DepartmentSalaryStats AS (
    SELECT 
        employee_id,
        first_name,
        last_name,
        department_id,
        salary,
        DENSE_RANK() OVER (
            PARTITION BY department_id 
            ORDER BY salary DESC
        ) AS salary_rank_in_dept,
        SUM(salary) OVER (
            PARTITION BY department_id 
            ORDER BY hire_date ASC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS running_dept_salary_total
    FROM employees
    WHERE status = 'ACTIVE'
)
SELECT 
    employee_id,
    first_name || ' ' || last_name AS full_name,
    department_id,
    salary,
    salary_rank_in_dept,
    running_dept_salary_total
FROM DepartmentSalaryStats
ORDER BY department_id, salary_rank_in_dept;
```''',
        "test_code": None
    },
    {
        "language": "html",
        "task_type": "code_generation",
        "title": "Accessible Responsive Modal Dialog",
        "prompt": "Write semantic HTML5 and CSS for an accessible modal dialog adhering to WAI-ARIA guidelines.",
        "response": '''```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Accessible Modal Dialog</title>
  <style>
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.75);
      backdrop-filter: blur(4px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    }
    .modal-card {
      background: #ffffff;
      border-radius: 12px;
      padding: 24px;
      width: min(90vw, 520px);
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    }
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  </style>
</head>
<body>
  <div class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="modal-title">
    <div class="modal-card">
      <header class="modal-header">
        <h2 id="modal-title">Confirm Deployment</h2>
        <button type="button" aria-label="Close dialog">&times;</button>
      </header>
      <main>
        <p>Are you sure you want to deploy AetherCoder to production?</p>
      </main>
    </div>
  </div>
</body>
</html>
```''',
        "test_code": None
    }
]

# Debugging and Bug Repair Templates
DEBUGGING_TEMPLATES: List[Dict[str, Any]] = [
    {
        "language": "python",
        "task_type": "debugging_repair",
        "title": "Off-by-one in Binary Search",
        "prompt": '''Debug the following broken Python binary search function:
```python
def binary_search(arr, target):
    low = 0
    high = len(arr) # BUG
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid # BUG
        else:
            high = mid - 1
    return -1
```
Identify the defects and provide the corrected code with explanation.''',
        "response": '''### Defects Identified:
1. **IndexError on `high` initialization**: `high` was initialized to `len(arr)` instead of `len(arr) - 1`, causing an `IndexError` when `target` is greater than or equal to elements near the end.
2. **Infinite Loop on `low` update**: Setting `low = mid` can trap the loop when `low == mid`. It must be incremented to `low = mid + 1`.

### Corrected Code:
```python
def binary_search(arr, target):
    low = 0
    high = len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
```''',
        "test_code": '''arr = [1, 3, 5, 7, 9]
assert binary_search(arr, 1) == 0
assert binary_search(arr, 9) == 4
assert binary_search(arr, 4) == -1
'''
    },
    {
        "language": "javascript",
        "task_type": "debugging_repair",
        "title": "Asynchronous Array Iteration Bug",
        "prompt": '''Fix this broken JavaScript code that uses `forEach` with an asynchronous callback:
```javascript
async function fetchAllUserData(userIds) {
  const results = [];
  userIds.forEach(async (id) => {
    const data = await api.getUser(id);
    results.push(data);
  });
  return results; // Returns empty array!
}
```''',
        "response": '''### Root Cause:
`Array.prototype.forEach` does not await promises returned by asynchronous callbacks. Execution proceeds synchronously to `return results` before any `api.getUser(id)` call completes.

### Fixed Implementation:
Use `Promise.all` with `map` for concurrent execution:
```javascript
async function fetchAllUserData(userIds) {
  const promises = userIds.map(async (id) => {
    return await api.getUser(id);
  });
  return await Promise.all(promises);
}
```''',
        "test_code": None
    }
]

# Agent Tool-Use Trajectories Templates
AGENT_TOOL_TEMPLATES: List[Dict[str, Any]] = [
    {
        "language": "python",
        "task_type": "agent_tool_use",
        "title": "Fix Unit Test Failure via Terminal & File Patching",
        "prompt": "Unit test `test_order_total` in `tests/test_cart.py` is failing with `AssertionError: 110 != 100`. Inspect the codebase, locate the discount calculation bug in `cart.py`, and apply a fix.",
        "response": '''Step 1: Inspect the failing test file.
Action: `read_file(path="tests/test_cart.py")`
Observation:
```python
def test_order_total():
    cart = ShoppingCart()
    cart.add_item("Widget", price=100)
    cart.apply_discount(percent=10)
    assert cart.calculate_total() == 90
```

Step 2: Inspect `cart.py` implementation.
Action: `read_file(path="cart.py")`
Observation:
```python
class ShoppingCart:
    def __init__(self):
        self.items = []
        self.discount_percent = 0

    def add_item(self, name, price):
        self.items.append(price)

    def apply_discount(self, percent):
        self.discount_percent = percent

    def calculate_total(self):
        subtotal = sum(self.items)
        # Bug: adding discount instead of subtracting
        return subtotal + (subtotal * (self.discount_percent / 100.0))
```

Step 3: Modify `cart.py` to correctly deduct discount.
Action: `replace_file_content(path="cart.py", target="return subtotal + (subtotal * (self.discount_percent / 100.0))", replacement="return subtotal - (subtotal * (self.discount_percent / 100.0))")`
Observation: `cart.py modified successfully.`

Step 4: Rerun unit tests.
Action: `run_terminal_command(command="pytest tests/test_cart.py")`
Observation:
`================ 1 passed in 0.04s ================`

Resolution:
The discount logic previously added the percentage to the subtotal. Replacing addition with subtraction fixed `test_order_total` cleanly.
''',
        "test_code": None
    }
]
