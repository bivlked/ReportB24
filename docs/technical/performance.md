# ⚡ Performance Guide

Оптимизация производительности ReportB24 - метрики, профилирование и best practices.

---

## 📊 Performance Metrics

**Current Benchmarks** (v2.4.1):

| Operation | Metric | Target |
|-----------|--------|--------|
| API Call | ~500ms | <1s |
| 100 Invoices Processing | 2-3 min | <5 min |
| 1000 Products Processing | 0.02s | <1s |
| Excel Generation (100 inv) | 5-10s | <30s |
| Batch API vs Sequential | 5-10x faster | >3x |
| Product Processing Rate | 49,884/sec | >10,000/sec |
| Memory Usage (100 inv) | ~50-100 MB | <200 MB |

---

## 🎯 Optimization Levels

### Level 1: Configuration Tuning (Easy)

**config.ini optimizations**:

```ini
[Performance]
# Увеличьте batch size
batch_size = 100  # Default: 50

# Больше параллельных запросов
max_concurrent_requests = 5  # Default: 2

# Увеличьте кэш
company_cache_size = 5000  # Default: 1000

# Multiprocessing для CPU-bound задач
use_multiprocessing = true  # Default: false
max_workers = 8  # Cores

# Увеличьте timeout для медленных сетей
api_timeout = 120  # Default: 30
```

**Impact**: 2-3x improvement

---

### Level 2: Code Optimization (Medium)

**1. Batch Processing**:

```python
# ❌ Slow: Sequential API calls (N+1 problem)
products = []
for invoice_id in invoice_ids:
    products.extend(client.get_products_by_invoice(invoice_id))

# ✅ Fast: Batch API call
products_by_invoice = client.get_products_by_invoices_batch(invoice_ids)
```

**Impact**: 5-10x improvement

**2. Lazy Loading**:

```python
# ❌ Slow: Load everything upfront
class DataProcessor:
    def __init__(self):
        self.all_data = load_huge_dataset()  # Expensive!

# ✅ Fast: Load on demand
class DataProcessor:
    def __init__(self):
        self._data = None
    
    @property
    def data(self):
        if self._data is None:
            self._data = self._load_data()
        return self._data
```

**3. Caching**:

```python
from functools import lru_cache

# Cache expensive computations
@lru_cache(maxsize=1000)
def validate_inn(inn: str) -> bool:
    """Cached INN validation"""
    return _perform_validation(inn)
```

---

### Level 3: Algorithm Optimization (Hard)

**1. Data Structure Selection**:

```python
# ❌ Slow: O(n) lookup in list
invoice_ids = [inv['id'] for inv in invoices]
if invoice_id in invoice_ids:  # O(n) each time
    ...

# ✅ Fast: O(1) lookup in set
invoice_ids = {inv['id'] for inv in invoices}
if invoice_id in invoice_ids:  # O(1)
    ...
```

**2. Bulk Operations**:

```python
# ❌ Slow: Row-by-row Excel writing
for row_idx, data in enumerate(dataset):
    for col_idx, value in enumerate(data):
        worksheet.cell(row_idx, col_idx).value = value

# ✅ Fast: Bulk append
for data in dataset:
    worksheet.append(data)
```

---

## 🔍 Profiling

### CPU Profiling

```python
import cProfile
import pstats

# Profile report generation
cProfile.run('app.generate_report("test.xlsx")', 'profile_stats')

# Analyze results
p = pstats.Stats('profile_stats')
p.sort_stats('cumulative')  # Sort by cumulative time
p.print_stats(20)  # Top 20 functions
```

**Example Output**:
```
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
      100    0.150    0.002   45.230    0.452 client.py:45(get_invoices)
     1000    2.340    0.002   12.580    0.013 processor.py:123(validate_inn)
        1    8.450    8.450    8.450    8.450 generator.py:234(create_excel)
```

---

### Memory Profiling

```bash
# Install memory_profiler
pip install memory_profiler

# Profile script
python -m memory_profiler scripts/run_report.py
```

**Example Output**:
```
Line #    Mem usage    Increment   Line Contents
================================================
    45     50.2 MiB     50.2 MiB   @profile
    46                             def generate_report():
    47     75.3 MiB     25.1 MiB       invoices = client.get_invoices()
    48     95.8 MiB     20.5 MiB       products = client.get_products()
    49     98.2 MiB      2.4 MiB       workbook = generator.create(data)
```

---

### Line Profiling

```python
# Install line_profiler
pip install line_profiler

# Add @profile decorator
@profile
def process_invoices(invoices):
    for invoice in invoices:
        validate_inn(invoice['inn'])
        calculate_vat(invoice['amount'])

# Run
kernprof -l -v script.py
```

---

## ⚙️ Performance Tips

### 1. Database-Like Operations

```python
# Use pandas for complex data manipulation
import pandas as pd

# Convert to DataFrame
df = pd.DataFrame(invoices)

# Fast filtering
filtered = df[df['amount'] > 10000]

# Fast grouping
by_company = df.groupby('company_id').agg({
    'amount': 'sum',
    'count': 'count'
})
```

---

### 2. Multiprocessing для CPU-Bound

```python
from concurrent.futures import ProcessPoolExecutor

def process_chunk(invoices_chunk):
    """Process chunk of invoices"""
    return [process_single(inv) for inv in invoices_chunk]

def process_parallel(invoices, n_workers=4):
    """Process invoices in parallel"""
    chunk_size = len(invoices) // n_workers
    chunks = [invoices[i:i+chunk_size] 
              for i in range(0, len(invoices), chunk_size)]
    
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        results = list(executor.map(process_chunk, chunks))
    
    return [item for sublist in results for item in sublist]
```

---

### 3. Асинхронное I/O для API

```python
import asyncio
import aiohttp

async def fetch_invoice(session, invoice_id):
    """Async API call"""
    async with session.get(f'{API_URL}/{invoice_id}') as response:
        return await response.json()

async def fetch_all_invoices(invoice_ids):
    """Fetch multiple invoices concurrently"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_invoice(session, inv_id) for inv_id in invoice_ids]
        return await asyncio.gather(*tasks)

# Usage
invoices = asyncio.run(fetch_all_invoices(invoice_ids))
```

---

### 4. Generator Expressions

```python
# ❌ Memory-intensive: List comprehension
processed = [process_invoice(inv) for inv in huge_invoice_list]
total = sum(processed)

# ✅ Memory-efficient: Generator expression
processed = (process_invoice(inv) for inv in huge_invoice_list)
total = sum(processed)  # Processes on-the-fly
```

---

## 📈 Scaling Strategies

### Horizontal Scaling

**Split by Time Period**:

```python
def generate_quarterly_reports(year):
    """Generate 4 reports in parallel"""
    quarters = [
        (f'01.01.{year}', f'31.03.{year}'),  # Q1
        (f'01.04.{year}', f'30.06.{year}'),  # Q2
        (f'01.07.{year}', f'30.09.{year}'),  # Q3
        (f'01.10.{year}', f'31.12.{year}'),  # Q4
    ]
    
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(generate_report, start, end)
            for start, end in quarters
        ]
        results = [f.result() for f in futures]
    
    return results
```

---

### Vertical Scaling

**Resource Optimization**:

```ini
[Performance]
# For high-end servers
batch_size = 200
max_concurrent_requests = 20
use_multiprocessing = true
max_workers = 32  # All cores
company_cache_size = 50000
api_timeout = 300
```

---

## 🎛️ Monitoring

### Runtime Metrics Collection

```python
import time
from functools import wraps

def timeit(func):
    """Measure function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__} took {elapsed:.2f}s")
        return result
    return wrapper

@timeit
def generate_report(filename):
    # ... implementation ...
    pass
```

---

### Logging Performance Metrics

```python
import logging

logger = logging.getLogger(__name__)

def log_performance(operation, duration, count=None):
    """Log performance metrics"""
    msg = f"{operation} completed in {duration:.2f}s"
    if count:
        rate = count / duration
        msg += f" ({count} items, {rate:.0f} items/sec)"
    logger.info(msg)

# Usage
start = time.time()
processed = process_invoices(invoices)
log_performance("Invoice processing", time.time() - start, len(processed))
```

---

## 🚀 Quick Wins

### Immediate Improvements

1. **Enable batch API** (если еще не включено):
   ```python
   # Use get_products_by_invoices_batch instead of loop
   products = client.get_products_by_invoices_batch(invoice_ids)
   ```

2. **Increase batch size**:
   ```ini
   [Performance]
   batch_size = 100  # From default 50
   ```

3. **Add caching**:
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=2000)
   def get_company_details(company_id):
       return client.call('crm.company.get', {'id': company_id})
   ```

4. **Use bulk Excel operations**:
   ```python
   # Append rows in bulk
   worksheet.append(row_data)  # Not cell-by-cell
   ```

---

## 📚 Resources

- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
- [cProfile Documentation](https://docs.python.org/3/library/profile.html)
- [memory_profiler](https://pypi.org/project/memory-profiler/)
- [line_profiler](https://github.com/pyutils/line_profiler)

---

<div align="center">

[← Testing](testing.md) • [Security →](security-deep-dive.md)

**Performance issues?** [Create Issue](https://github.com/bivlked/ReportB24/issues)

</div>
