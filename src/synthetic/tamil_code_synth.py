"""Tamil-English bilingual programming explanations and code generation templates."""
from typing import List, Dict, Any

TAMIL_ENGLISH_TEMPLATES: List[Dict[str, Any]] = [
    {
        "language": "python",
        "task_type": "bilingual_explanation",
        "title": "Binary Search Algorithm Explanation in Tamil",
        "prompt": "பைத்தானில் இரும தேடல் (Binary Search) வழிமுறையை எளிய தமிழில் விளக்கி, அதற்கான நிரலையும் (code) நேர சிக்கலையும் (time complexity) விளக்குங்கள்.",
        "response": '''### இரும தேடல் (Binary Search) விளக்கம்

**Binary Search** என்பது வரிசைப்படுத்தப்பட்ட பட்டியலில் (sorted list) ஒரு குறிப்பிட்ட மதிப்பை மிக வேகமாக தேடும் ஒரு திறமையான வழிமுறை (efficient searching algorithm) ஆகும்.

#### இது எவ்வாறு செயல்படுகிறது?
1. பட்டியலின் தொடக்கத்தை `low` என்றும், முடிவை `high` என்றும் குறிக்கிறோம்.
2. நடு மதிப்பை (`mid = (low + high) // 2`) கணக்கிடுகிறோம்.
3. நடு மதிப்பு நாம் தேடும் இலக்குடன் (`target`) சமமாக இருந்தால், அந்த குறியீட்டை (`index`) திருப்பி அனுப்புகிறோம்.
4. இலக்கு நடு மதிப்பை விட சிறியதாக இருந்தால், பட்டியலின் இடது பாதியை மட்டும் தேடுகிறோம் (`high = mid - 1`).
5. இலக்கு பெரியதாக இருந்தால், வலது பாதியை தேடுகிறோம் (`low = mid + 1`).

#### Python Implementation:
```python
def binary_search(arr: list[int], target: int) -> int:
    """வரிசைப்படுத்தப்பட்ட பட்டியலில் இரும தேடல் வழிமுறை."""
    low = 0
    high = len(arr) - 1

    while low <= high:
        mid = (low + high) // 2
        
        # இலக்கு கிடைத்துவிட்டது
        if arr[mid] == target:
            return mid
        # இலக்கு சிறியதாக இருந்தால் இடதுபுறம் செல்லவும்
        elif arr[mid] > target:
            high = mid - 1
        # இலக்கு பெரியதாக இருந்தால் வலதுபுறம் செல்லவும்
        else:
            low = mid + 1

    # இலக்கு பட்டியலில் இல்லை
    return -1
```

#### நேர மற்றும் இட சிக்கல் (Complexity Analysis):
- **Time Complexity**: **O(log N)** — ஒவ்வொரு சுற்றிலும் தேடல் பரப்பு பாதியாக குறைகிறது.
- **Space Complexity**: **O(1)** — கூடுதல் நினைவகம் தேவையில்லை.
''',
        "test_code": '''arr = [10, 20, 30, 40, 50]
assert binary_search(arr, 30) == 2
assert binary_search(arr, 10) == 0
assert binary_search(arr, 99) == -1
'''
    },
    {
        "language": "sql",
        "task_type": "bilingual_explanation",
        "title": "SQL JOIN Operations in Tamil",
        "prompt": "SQL தரவுத்தளத்தில் INNER JOIN மற்றும் LEFT JOIN ஆகியவற்றுக்கு இடையேயான வித்தியாசத்தை எளிய தமிழில் எடுத்துக்காட்டுடன் விளக்குங்கள்.",
        "response": '''### SQL இல் INNER JOIN vs LEFT JOIN

SQL-இல் இரண்டு அல்லது அதற்கு மேற்பட்ட அட்டவணைகளை (tables) இணைக்க **JOIN** பயன்படுகிறது.

---

### 1. INNER JOIN (பொருந்தும் பதிவுகள் மட்டும்)
இரண்டு அட்டவணைகளிலும் பொதுவாக பொருந்தும் (matching rows) பதிவுகளை மட்டுமே இது தரும்.

```sql
-- ஊழியர்கள் மற்றும் அவர்களின் துறை விவரங்கள்
SELECT 
    e.employee_id,
    e.name AS employee_name,
    d.department_name
FROM employees e
INNER JOIN departments d 
    ON e.department_id = d.department_id;
```

---

### 2. LEFT JOIN (இடது அட்டவணையின் அனைத்து பதிவுகளும்)
இடது அட்டவணையில் உள்ள **அனைத்து பதிவுகளையும்** மற்றும் வலது அட்டவணையில் பொருந்தும் பதிவுகளையும் தரும். வலதுபுறம் பொருத்தம் இல்லை என்றால் `NULL` என்று வரும்.

```sql
-- அனைத்து ஊழியர்கள் (துறை ஒதுக்கப்படாத ஊழியர்கள் உட்பட)
SELECT 
    e.employee_id,
    e.name AS employee_name,
    COALESCE(d.department_name, 'No Department Assigned') AS department_name
FROM employees e
LEFT JOIN departments d 
    ON e.department_id = d.department_id;
```

#### சுருக்கம் (Summary):
- **INNER JOIN**: இரு பக்கமும் தகவல்கள் பொருந்தியிருக்க வேண்டும்.
- **LEFT JOIN**: இடதுபுற அட்டவணை முழுமையாகவும், வலதுபுறம் பொருந்தினால் மட்டுமே தகவலும் வரும்.
''',
        "test_code": None
    },
    {
        "language": "javascript",
        "task_type": "bilingual_explanation",
        "title": "JavaScript Promises & Async/Await in Tamil",
        "prompt": "JavaScript-ல் Promises மற்றும் Async/Await எதற்காக பயன்படுகின்றன? எளிய உதாரணத்துடன் தமிழில் விளக்கவும்.",
        "response": '''### JavaScript-ல் Asynchronous Programming (Promises & Async/Await)

ஜாவாஸ்கிரிப்ட் ஒரு **Single-threaded language**. அதாவது ஒரே நேரத்தில் ஒரு வேலையை மட்டுமே செய்யும். ஆனால் சர்வரில் இருந்து API தரவை பதிவிறக்குவது போன்ற அதிக நேரம் எடுக்கும் பணிகளுக்கு மற்ற பணிகளை முடக்காமல் (non-blocking) செய்ய **Promises** மற்றும் **Async/Await** பயன்படுகின்றன.

#### 1. Promise என்றால் என்ன?
Promise என்பது எதிர்காலத்தில் கிடைக்கப்போகும் ஒரு முடிவைக் குறிக்கும் பொருள் (Object). இது மூன்று நிலைகளைக் கொண்டுள்ளது:
- `Pending` (செயலில் உள்ளது)
- `Fulfilled` (வெற்றிகரமாக முடிந்தது)
- `Rejected` (தோல்வி அடைந்தது)

#### 2. Async / Await உதாரணம் (Modern Best Practice):
```javascript
// பயனரின் விவரங்களை இணைய சேவையகத்திலிருந்து பெறும் செயற்கூறு
async function fetchUserProfile(userId) {
  try {
    console.log("பயனர் விவரங்கள் பெறப்படுகின்றன...");
    
    const response = await fetch(`https://api.example.com/users/${userId}`);
    if (!response.ok) {
      throw new Error(`HTTP Error! Status: ${response.status}`);
    }
    
    const userData = await response.json();
    console.log("வெற்றிகரமாக பெறப்பட்டது:", userData.name);
    return userData;
  } catch (error) {
    console.error("தரவு பெறுவதில் பிழை ஏற்பட்டது:", error.message);
    throw error;
  }
}
```

#### பயன்கள்:
1. **Callback Hell** தவிர்க்கப்படுகிறது.
2. நிரல் பார்ப்பதற்கு நேர்த்தியாகவும் (clean code), பிழை திருத்தம் செய்ய சுலபமாகவும் (easy error handling with try/catch) இருக்கும்.
''',
        "test_code": None
    },
    {
        "language": "python",
        "task_type": "bilingual_explanation",
        "title": "Python Generator vs List Comprehension in Tamil",
        "prompt": "Python-ல் List Comprehension மற்றும் Generator Expression இடையே உள்ள நினைவக (Memory) வேறுபாட்டை விளக்குங்கள்.",
        "response": '''### Python-ல் List Comprehension vs Generator Expression

பெரிய அளவிலான தரவுகளை கையாளும் போது நினைவக மேலாண்மை (Memory Efficiency) மிகவும் முக்கியமானது.

#### 1. List Comprehension:
இது முழு பட்டியலையும் ஒரே நேரத்தில் நினைவகத்தில் (RAM) உருவாக்கி சேமிக்கிறது.
```python
# 10 லட்சம் எண்களின் வர்க்கங்களை உருவாக்குகிறது
numbers_list = [x * x for x in range(1_000_000)]
```
- **நினைவகம்**: அதிக RAM தேவைப்படும் (~8 MB).

#### 2. Generator Expression:
இது அடைப்புக்குறிகளுடன் `()` எழுதப்படுகிறது. இது தேவைப்படும்போது மட்டுமே அடுத்த மதிப்பை கணக்கிடும் (**Lazy Evaluation**).
```python
# மதிப்பை தேவையான போது மட்டுமே தரும் Generator
numbers_gen = (x * x for x in range(1_000_000))

# முதல் மதிப்பை மட்டும் எடுக்க:
first_val = next(numbers_gen)
```
- **நினைவகம்**: மிகக் குறைவான நிலையான RAM (~120 bytes) மட்டுமே தேவைப்படும்.

#### முடிவு:
நூறாயிரக்கணக்கான பதிவுகளை வரிசையாக செயலாக்க (Stream processing) எப்போதும் **Generators** பயன்படுத்துவது சிறந்தது.
''',
        "test_code": '''gen = (x * 2 for x in range(5))
assert next(gen) == 0
assert next(gen) == 2
assert next(gen) == 4
'''
    }
]
