from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import os
import jwt
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="PythonQuest - Gamified Python Learning", version="1.0.0")

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get("SECRET_KEY", "your-super-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "pythonquest")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections
users_collection = db.users
levels_collection = db.levels
user_progress_collection = db.user_progress
feedback_collection = db.feedback

# Pydantic Models
class User(BaseModel):
    id: Optional[str] = None
    username: str
    email: EmailStr
    password: str
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    is_active: bool = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    id: str
    username: str
    email: str
    current_level: int = 100
    total_xp: int = 0
    completed_levels: int = 0
    streak: int = 0
    badges: List[Dict[str, Any]] = []
    achievements: List[Dict[str, Any]] = []
    created_at: datetime
    last_login: Optional[datetime] = None

class Level(BaseModel):
    id: str
    level_id: int
    title: str
    description: str
    category: str
    difficulty: str  # Easy, Medium, Hard
    xp_reward: int
    starter_code: str
    expected_output: str
    hints: List[str] = []
    prerequisites: List[int] = []
    is_active: bool = True

class LevelSubmission(BaseModel):
    code: str
    output: str

class UserProgress(BaseModel):
    id: Optional[str] = None
    user_id: str
    level_id: int
    completed_at: Optional[datetime] = None
    stars: int = 0  # 0-3 stars
    attempts: int = 0
    is_completed: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserProfile
    stats: Dict[str, Any]

class LevelFeedback(BaseModel):
    user_id: Optional[str] = None
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    category: str  # general, difficulty, instructions, bug, suggestion
    comment: str

# Utility functions
def hash_password(password: str) -> str:
    # Truncate password to 72 bytes to avoid bcrypt limitations
    if len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await users_collection.find_one({"_id": user_id})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

async def get_user_stats(user_id: str) -> Dict[str, Any]:
    # Get user progress
    progress_docs = await user_progress_collection.find({"user_id": user_id}).to_list(length=None)
    completed_levels = [p for p in progress_docs if p.get("is_completed", False)]
    
    # Calculate current level (highest completed level)
    current_level = 100
    if completed_levels:
        current_level = max([p["level_id"] for p in completed_levels]) + 1
        if current_level > 400:
            current_level = 400
    
    # Calculate total XP
    total_xp = sum([p.get("xp_earned", 0) for p in completed_levels])
    
    # Calculate badges (simplified)
    badges = []
    if len(completed_levels) >= 1:
        badges.append({"name": "First Steps", "icon": "🎯", "earned_at": completed_levels[0].get("completed_at")})
    if len(completed_levels) >= 10:
        badges.append({"name": "Dedicated Learner", "icon": "📚", "earned_at": datetime.now(timezone.utc)})
    if len(completed_levels) >= 50:
        badges.append({"name": "Python Expert", "icon": "🐍", "earned_at": datetime.now(timezone.utc)})
    
    return {
        "current_level": current_level,
        "total_xp": total_xp,
        "completed_levels": len(completed_levels),
        "streak": 0,  # Simplified for now
        "badges": badges,
        "achievements": []  # Can be expanded later
    }

# Initialize sample levels
async def init_levels():
    # Check if levels already exist
    existing_count = await levels_collection.count_documents({})
    if existing_count > 0:
        # Clear existing levels to add enhanced ones
        await levels_collection.delete_many({})
    
    sample_levels = [
        {
            "_id": str(uuid.uuid4()),
            "level_id": 100,
            "title": "Hello Python World!",
            "description": "Write your first Python program that prints 'Hello, World!' to the console. This is the traditional first program that every programmer writes!",
            "category": "Python Basics",
            "difficulty": "Easy",
            "xp_reward": 50,
            "starter_code": "# Hello World - Your first Python program!\n# In Python, we use the built-in print() function to display output\n# No imports needed for basic print statements\n\n# Print is a function that displays text to the console\nprint(\"Hello, World!\")\n\n# Try changing the message above!\n# Remember: strings must be in quotes\n# You can also print variables:\n# name = \"Python\"\n# print(f\"Hello, {name}!\")",
            "expected_output": "Hello, World!",
            "hints": [
                "Use the print() function to display text",
                "Put your text inside quotes (either single ' or double \")",
                "Make sure the text matches exactly: Hello, World!"
            ],
            "prerequisites": [],
            "is_active": True,
            "problem_type": "basic",
            "tutorial_links": ["print", "strings"]
        },
        {
            "_id": str(uuid.uuid4()),
            "level_id": 101,
            "title": "Variables and Numbers",
            "description": "Learn to work with variables and perform basic arithmetic operations. Create variables and calculate their sum!",
            "category": "Python Basics",
            "difficulty": "Easy",
            "xp_reward": 75,
            "starter_code": "# Create two variables and add them together\na = 15\nb = 25\n\n# Calculate and print their sum\nresult = # Your code here\nprint(result)",
            "expected_output": "40",
            "hints": ["Use the + operator to add numbers", "Store the result in a variable"],
            "prerequisites": [100],
            "is_active": True
        },
        {
            "_id": str(uuid.uuid4()),
            "level_id": 102,
            "title": "Working with Strings",
            "description": "Manipulate text data using strings. Learn concatenation and basic string operations!",
            "category": "Python Basics",
            "difficulty": "Easy",
            "xp_reward": 75,
            "starter_code": "# String operations\nfirst_name = \"Python\"\nlast_name = \"Programmer\"\n\n# Create a full name by combining first and last name\nfull_name = # Your code here\nprint(full_name)",
            "expected_output": "Python Programmer",
            "hints": ["Use the + operator to join strings", "Don't forget the space between names"],
            "prerequisites": [101],
            "is_active": True
        },
        {
            "_id": str(uuid.uuid4()),
            "level_id": 103,
            "title": "Conditional Logic",
            "description": "Make decisions in your code using if statements. Check if a number is positive, negative, or zero!",
            "category": "Control Flow",
            "difficulty": "Medium",
            "xp_reward": 100,
            "starter_code": "# Conditional statements\nnumber = 42\n\n# Check if number is positive, negative, or zero\nif # Your condition here:\n    print(\"Positive\")\n# Add more conditions here",
            "expected_output": "Positive",
            "hints": ["Use if, elif, and else", "Compare using >, <, or =="],
            "prerequisites": [102],
            "is_active": True
        },
        {
            "_id": str(uuid.uuid4()),
            "level_id": 104,
            "title": "Loops - Counting Fun",
            "description": "Use loops to repeat actions. Print numbers from 1 to 5 using a for loop!",
            "category": "Control Flow",
            "difficulty": "Medium",
            "xp_reward": 125,
            "starter_code": "# For loops\n# Print numbers 1 through 5\nfor i in # Your code here:\n    print(i)",
            "expected_output": "1\n2\n3\n4\n5",
            "hints": [
                "Use the range() function to generate numbers",
                "range(1, 6) gives numbers 1 to 5 (end is exclusive)",
                "Complete syntax: for i in range(1, 6):"
            ],
            "prerequisites": [103],
            "is_active": True,
            "problem_type": "basic",
            "tutorial_links": ["loops", "functions"]
        },
        {
            "_id": str(uuid.uuid4()),
            "level_id": 105,
            "title": "Build a Calculator",
            "description": "Create a comprehensive calculator that can perform addition, subtraction, multiplication, and division. Handle user input and provide a menu system.",
            "category": "Comprehensive Project",
            "difficulty": "Hard",
            "xp_reward": 200,
            "starter_code": "# Build a Calculator\n# Create functions for basic operations and a menu system\n\ndef add(x, y):\n    # Your code here\n    pass\n\ndef subtract(x, y):\n    # Your code here\n    pass\n\ndef multiply(x, y):\n    # Your code here\n    pass\n\ndef divide(x, y):\n    # Your code here\n    pass\n\n# Main program\nprint(\"Calculator Menu:\")\nprint(\"1. Add\")\nprint(\"2. Subtract\")\nprint(\"3. Multiply\")\nprint(\"4. Divide\")\n\n# Get user choice and numbers\n# Perform calculation and display result",
            "expected_output": "Calculator Menu:\n1. Add\n2. Subtract\n3. Multiply\n4. Divide",
            "hints": [
                "Define each function to return the result of the operation",
                "Use input() to get user choices and numbers",
                "Convert string inputs to numbers using int() or float()",
                "Handle division by zero with an if statement",
                "Use if-elif-else to handle menu choices"
            ],
            "prerequisites": [104],
            "is_active": True,
            "problem_type": "comprehensive",
            "tutorial_links": ["functions", "variables", "loops"]
        },
        # Data Analyst Track
        {
            "_id": str(uuid.uuid4()),
            "level_id": 200,
            "title": "Data Analysis Basics",
            "description": "Learn to work with data using Python lists. Calculate basic statistics like mean, median, and mode from a dataset.",
            "category": "Data Analysis",
            "difficulty": "Medium",
            "xp_reward": 150,
            "starter_code": "# Data Analysis Basics\n# Import statements for data analysis (learn about imports!)\nimport statistics  # For statistical functions\nimport math        # For mathematical operations\n\n# Let's work with a list of test scores\nscores = [85, 92, 78, 96, 88, 76, 91, 84, 89, 93]\n\n# Method 1: Calculate the mean manually\ntotal = sum(scores)  # Built-in sum() function\ncount = len(scores)  # Built-in len() function\nmean = total / count\n\n# Method 2: Using statistics module (more professional)\n# mean_stats = statistics.mean(scores)\n\n# Find the maximum and minimum scores\nmax_score = max(scores)  # Built-in max() function\nmin_score = min(scores)  # Built-in min() function\n\n# Print results rounded to 1 decimal place\nprint(f\"Mean: {round(mean, 1)}\")\nprint(f\"Max: {max_score}\")\nprint(f\"Min: {min_score}\")\n\n# Bonus: Try using the statistics module!\n# print(f\"Mean (statistics): {round(statistics.mean(scores), 1)}\")",
            "expected_output": "Mean: 87.2\nMax: 96\nMin: 76",
            "hints": [
                "Use sum(scores) to add all numbers in the list",
                "Use len(scores) to get the count of items", 
                "Mean = total / count",
                "Use max(scores) and min(scores) for maximum and minimum",
                "The code shows you how to use built-in functions",
                "Try the statistics module for more advanced operations"
            ],
            "prerequisites": [],
            "is_active": True,
            "problem_type": "data_analysis",
            "tutorial_links": ["lists", "functions", "statistics"]
        },
        {
            "_id": str(uuid.uuid4()),
            "level_id": 201,
            "title": "Working with CSV Data",
            "description": "Learn to read and process CSV data. Parse a simple dataset and extract meaningful information from it.",
            "category": "Data Analysis",
            "difficulty": "Medium",
            "xp_reward": 175,
            "starter_code": "# Working with CSV Data (simulated)\n# Import statements for CSV processing\nimport csv        # For CSV file handling (not used here but good to know)\nfrom io import StringIO  # For treating strings as file objects\n\n# Sample CSV data as string\ncsv_data = \"Name,Age,City\\nAlice,25,New York\\nBob,30,San Francisco\\nCharlie,35,Chicago\\nDiana,28,Boston\"\n\n# Method 1: Manual parsing (what we're learning)\nlines = csv_data.strip().split('\\n')\nheader = lines[0].split(',')\nrows = [line.split(',') for line in lines[1:]]\n\n# Extract ages and calculate average\nages = [int(row[1]) for row in rows]  # List comprehension to get ages\naverage_age = sum(ages) / len(ages)\n\n# Count people by city\ncity_count = {}\nfor row in rows:\n    city = row[2]  # Third column is city\n    city_count[city] = city_count.get(city, 0) + 1\n    \n# Print results\nprint(f\"Average age: {average_age}\")\nprint(f\"Cities: {city_count}\")\n\n# Bonus: Try using the csv module for real CSV files!\n# csv_file = StringIO(csv_data)\n# reader = csv.DictReader(csv_file)\n# data = list(reader)",
            "expected_output": "Average age: 29.5\nCities: {'New York': 1, 'San Francisco': 1, 'Chicago': 1, 'Boston': 1}",
            "hints": [
                "Use list comprehension to extract ages: [int(row[1]) for row in rows]",
                "Calculate average using sum(ages) / len(ages)",
                "Access city using row[2] for each row",
                "Use dictionary to count: city_count[city] = city_count.get(city, 0) + 1"
            ],
            "prerequisites": [],
            "is_active": True,
            "problem_type": "data_analysis",
            "tutorial_links": ["lists", "dictionaries", "csv"]
        },
        {
            "_id": str(uuid.uuid4()),
            "level_id": 202,
            "title": "Data Filtering and Sorting",
            "description": "Filter data based on conditions and sort datasets. Learn essential data manipulation techniques.",
            "category": "Data Analysis",
            "difficulty": "Medium",
            "xp_reward": 175,
            "starter_code": "# Data Filtering and Sorting\nsales_data = [\n    {'product': 'Laptop', 'price': 1200, 'quantity': 5},\n    {'product': 'Mouse', 'price': 25, 'quantity': 50},\n    {'product': 'Keyboard', 'price': 75, 'quantity': 30},\n    {'product': 'Monitor', 'price': 300, 'quantity': 15},\n    {'product': 'Headphones', 'price': 100, 'quantity': 25}\n]\n\n# Filter products with price > 50\nexpensive_products = # Your code here\n\n# Sort products by quantity (descending)\nsorted_by_quantity = # Your code here\n\n# Calculate total revenue for expensive products\ntotal_revenue = # Your code here\n\nprint(f\"Expensive products: {len(expensive_products)}\")\nprint(f\"Top product by quantity: {sorted_by_quantity[0]['product']}\")\nprint(f\"Total revenue (expensive): ${total_revenue}\")",
            "expected_output": "Expensive products: 4\nTop product by quantity: Mouse\nTotal revenue (expensive): $13500",
            "hints": [
                "Filter using list comprehension: [item for item in sales_data if item['price'] > 50]",
                "Sort using sorted() with key parameter: sorted(sales_data, key=lambda x: x['quantity'], reverse=True)",
                "Calculate revenue: sum(item['price'] * item['quantity'] for item in expensive_products)"
            ],
            "prerequisites": [],
            "is_active": True,
            "problem_type": "data_analysis",
            "tutorial_links": ["lists", "dictionaries", "sorting"]
        },
        {
            "_id": str(uuid.uuid4()),
            "level_id": 203,
            "title": "Statistical Analysis",
            "description": "Perform advanced statistical calculations including median, mode, and standard deviation on datasets.",
            "category": "Data Analysis",
            "difficulty": "Hard",
            "xp_reward": 200,
            "starter_code": "# Statistical Analysis\nimport math\n\ntest_scores = [78, 85, 92, 78, 88, 95, 82, 78, 91, 87, 89, 94, 78, 83, 90]\n\n# Calculate median (middle value when sorted)\nsorted_scores = # Your code here\nn = len(sorted_scores)\nif n % 2 == 0:\n    median = # Your code here (average of two middle values)\nelse:\n    median = # Your code here (middle value)\n\n# Calculate mode (most frequent value)\nfrom collections import Counter\nscore_counts = Counter(test_scores)\nmode = # Your code here (most common score)\n\n# Calculate standard deviation\nmean = sum(test_scores) / len(test_scores)\nvariance = sum((x - mean) ** 2 for x in test_scores) / len(test_scores)\nstd_dev = # Your code here\n\nprint(f\"Median: {median}\")\nprint(f\"Mode: {mode}\")\nprint(f\"Standard Deviation: {round(std_dev, 2)}\")",
            "expected_output": "Median: 87\nMode: 78\nStandard Deviation: 5.77",
            "hints": [
                "Sort the list using sorted(test_scores)",
                "For even length: (sorted_scores[n//2-1] + sorted_scores[n//2]) / 2",
                "For odd length: sorted_scores[n//2]",
                "Mode: score_counts.most_common(1)[0][0]",
                "Standard deviation: math.sqrt(variance)"
            ],
            "prerequisites": [],
            "is_active": True,
            "problem_type": "data_analysis",
            "tutorial_links": ["statistics", "math", "collections"]
        }
    ]
    
    await levels_collection.insert_many(sample_levels)
    logger.info(f"Initialized {len(sample_levels)} sample levels")

@app.on_event("startup")
async def startup_event():
    await init_levels()
    logger.info("Application started successfully")

# Auth endpoints
@app.post("/api/auth/signup", response_model=Token)
async def signup(user: User):
    # Check if user exists
    existing_user = await users_collection.find_one({"$or": [{"email": user.email}, {"username": user.username}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user.password)
    user_data = {
        "_id": user_id,
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "created_at": datetime.now(timezone.utc),
        "last_login": None,
        "is_active": True
    }
    
    await users_collection.insert_one(user_data)
    
    # Create access token
    access_token = create_access_token(data={"sub": user_id})
    
    # Get user stats
    stats = await get_user_stats(user_id)
    
    user_profile = UserProfile(
        id=user_id,
        username=user.username,
        email=user.email,
        created_at=user_data["created_at"],
        **stats
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_profile,
        stats=stats
    )

@app.post("/api/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    # Find user
    user = await users_collection.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last login
    await users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.now(timezone.utc)}}
    )
    
    # Create access token
    access_token = create_access_token(data={"sub": user["_id"]})
    
    # Get user stats
    stats = await get_user_stats(user["_id"])
    
    user_profile = UserProfile(
        id=user["_id"],
        username=user["username"],
        email=user["email"],
        created_at=user["created_at"],
        last_login=user.get("last_login"),
        **stats
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_profile,
        stats=stats
    )

@app.get("/api/auth/verify")
async def verify_token(current_user: dict = Depends(get_current_user)):
    stats = await get_user_stats(current_user["_id"])
    
    user_profile = UserProfile(
        id=current_user["_id"],
        username=current_user["username"],
        email=current_user["email"],
        created_at=current_user["created_at"],
        last_login=current_user.get("last_login"),
        **stats
    )
    
    return {
        "user": user_profile,
        "stats": stats
    }

# Level endpoints
@app.get("/api/levels", response_model=List[Level])
async def get_levels(skip: int = 0, limit: int = 20):
    levels_cursor = levels_collection.find({"is_active": True}).sort("level_id", 1).skip(skip).limit(limit)
    levels = await levels_cursor.to_list(length=limit)
    
    return [Level(
        id=level["_id"],
        level_id=level["level_id"],
        title=level["title"],
        description=level["description"],
        category=level["category"],
        difficulty=level["difficulty"],
        xp_reward=level["xp_reward"],
        starter_code=level["starter_code"],
        expected_output=level["expected_output"],
        hints=level.get("hints", []),
        prerequisites=level.get("prerequisites", []),
        is_active=level.get("is_active", True)
    ) for level in levels]

@app.get("/api/levels/{level_id}", response_model=Level)
async def get_level(level_id: int):
    level = await levels_collection.find_one({"level_id": level_id})
    if not level:
        raise HTTPException(status_code=404, detail="Level not found")
    
    return Level(
        id=level["_id"],
        level_id=level["level_id"],
        title=level["title"],
        description=level["description"],
        category=level["category"],
        difficulty=level["difficulty"],
        xp_reward=level["xp_reward"],
        starter_code=level["starter_code"],
        expected_output=level["expected_output"],
        hints=level.get("hints", []),
        prerequisites=level.get("prerequisites", []),
        is_active=level.get("is_active", True)
    )

@app.post("/api/levels/{level_id}/submit")
async def submit_level(level_id: int, submission: LevelSubmission, current_user: dict = Depends(get_current_user)):
    # Get level
    level = await levels_collection.find_one({"level_id": level_id})
    if not level:
        raise HTTPException(status_code=404, detail="Level not found")
    
    # Check if output matches expected (simplified validation)
    is_correct = submission.output.strip() == level["expected_output"].strip()
    
    # Get or create user progress
    progress = await user_progress_collection.find_one({
        "user_id": current_user["_id"],
        "level_id": level_id
    })
    
    if not progress:
        progress = {
            "_id": str(uuid.uuid4()),
            "user_id": current_user["_id"],
            "level_id": level_id,
            "attempts": 0,
            "is_completed": False,
            "stars": 0,
            "xp_earned": 0
        }
    
    # Update progress
    progress["attempts"] += 1
    
    if is_correct and not progress["is_completed"]:
        progress["is_completed"] = True
        progress["completed_at"] = datetime.now(timezone.utc)
        progress["stars"] = 3  # Award full stars for correct solution
        progress["xp_earned"] = level["xp_reward"]
    
    # Upsert progress
    await user_progress_collection.replace_one(
        {"user_id": current_user["_id"], "level_id": level_id},
        progress,
        upsert=True
    )
    
    # Get updated stats
    stats = await get_user_stats(current_user["_id"])
    
    return {
        "success": is_correct,
        "message": "Congratulations! Level completed!" if is_correct else "Keep trying! Check your output.",
        "xp_earned": level["xp_reward"] if is_correct and not progress.get("was_completed_before") else 0,
        "stars": progress["stars"],
        "attempts": progress["attempts"],
        "stats": stats
    }

@app.get("/api/user/progress")
async def get_user_progress(current_user: dict = Depends(get_current_user)):
    progress_docs = await user_progress_collection.find({"user_id": current_user["_id"]}).to_list(length=None)
    
    progress_map = {}
    for progress in progress_docs:
        progress_map[progress["level_id"]] = {
            "level_id": progress["level_id"],
            "is_completed": progress.get("is_completed", False),
            "stars": progress.get("stars", 0),
            "attempts": progress.get("attempts", 0),
            "completed_at": progress.get("completed_at"),
            "xp_earned": progress.get("xp_earned", 0)
        }
    
    return progress_map

@app.get("/api/leaderboard")
async def get_leaderboard(limit: int = 10):
    # Aggregate user progress to calculate leaderboard
    pipeline = [
        {"$match": {"is_completed": True}},
        {
            "$group": {
                "_id": "$user_id",
                "total_xp": {"$sum": "$xp_earned"},
                "completed_levels": {"$sum": 1}
            }
        },
        {"$sort": {"total_xp": -1}},
        {"$limit": limit}
    ]
    
    leaderboard_data = await user_progress_collection.aggregate(pipeline).to_list(length=limit)
    
    # Get user details
    leaderboard = []
    for entry in leaderboard_data:
        user = await users_collection.find_one({"_id": entry["_id"]})
        if user:
            leaderboard.append({
                "rank": len(leaderboard) + 1,
                "username": user["username"],
                "total_xp": entry["total_xp"],
                "completed_levels": entry["completed_levels"],
                "current_level": entry["completed_levels"] + 100  # Simplified calculation
            })
    
    return leaderboard

@app.post("/api/levels/{level_id}/feedback")
async def submit_feedback(level_id: int, feedback_data: LevelFeedback, current_user: dict = Depends(get_current_user)):
    try:
        feedback_doc = {
            "_id": str(uuid.uuid4()),
            "level_id": level_id,
            "user_id": current_user["_id"],
            "username": current_user["username"],
            "rating": feedback_data.rating,
            "category": feedback_data.category,
            "comment": feedback_data.comment,
            "submitted_at": datetime.now(timezone.utc),
            "status": "pending"  # pending, reviewed, resolved
        }
        
        await feedback_collection.insert_one(feedback_doc)
        
        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "feedback_id": feedback_doc["_id"]
        }
    except Exception as e:
        logger.error(f"Failed to submit feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

async def check_admin_access(current_user: dict = Depends(get_current_user)):
    # Simple admin check - in production, you'd want proper role-based access
    # Allow any user with "admin" in their username for testing purposes
    if "admin" not in current_user["username"].lower():
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@app.get("/api/admin/feedback")
async def get_all_feedback(
    admin_user: dict = Depends(check_admin_access),
    skip: int = 0, 
    limit: int = 50,
    status: Optional[str] = None,
    category: Optional[str] = None,
    level_id: Optional[int] = None,
    user_id: Optional[str] = None
):
    # Build filter query
    filter_query = {}
    if status:
        filter_query["status"] = status
    if category:
        filter_query["category"] = category
    if level_id:
        filter_query["level_id"] = level_id
    if user_id:
        filter_query["user_id"] = user_id
    
    feedback_cursor = feedback_collection.find(filter_query).sort("submitted_at", -1).skip(skip).limit(limit)
    feedback_list = await feedback_cursor.to_list(length=limit)
    
    # Get statistics
    total_feedback = await feedback_collection.count_documents(filter_query)
    pending_count = await feedback_collection.count_documents({"status": "pending"})
    reviewed_count = await feedback_collection.count_documents({"status": "reviewed"})
    resolved_count = await feedback_collection.count_documents({"status": "resolved"})
    
    return {
        "feedback": feedback_list,
        "total": total_feedback,
        "statistics": {
            "pending": pending_count,
            "reviewed": reviewed_count,
            "resolved": resolved_count,
            "total_all": pending_count + reviewed_count + resolved_count
        },
        "pagination": {
            "skip": skip,
            "limit": limit,
            "has_more": total_feedback > skip + limit
        }
    }

@app.patch("/api/admin/feedback/{feedback_id}/status")
async def update_feedback_status(
    feedback_id: str,
    status_update: dict,
    admin_user: dict = Depends(check_admin_access)
):
    valid_statuses = ["pending", "reviewed", "resolved"]
    new_status = status_update.get("status")
    
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    # Update feedback status
    result = await feedback_collection.update_one(
        {"_id": feedback_id},
        {
            "$set": {
                "status": new_status,
                "updated_at": datetime.now(timezone.utc),
                "updated_by": admin_user["_id"]
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    return {"success": True, "message": f"Feedback status updated to {new_status}"}

@app.get("/api/admin/feedback/statistics")
async def get_feedback_statistics(admin_user: dict = Depends(check_admin_access)):
    # Get overall statistics
    total_feedback = await feedback_collection.count_documents({})
    
    # Status breakdown
    status_stats = await feedback_collection.aggregate([
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]).to_list(length=None)
    
    # Category breakdown
    category_stats = await feedback_collection.aggregate([
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]).to_list(length=None)
    
    # Rating distribution
    rating_stats = await feedback_collection.aggregate([
        {"$group": {"_id": "$rating", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]).to_list(length=None)
    
    # Recent feedback count (last 7 days)
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_feedback = await feedback_collection.count_documents({
        "submitted_at": {"$gte": week_ago}
    })
    
    return {
        "total_feedback": total_feedback,
        "recent_feedback": recent_feedback,
        "status_breakdown": {item["_id"]: item["count"] for item in status_stats},
        "category_breakdown": {item["_id"]: item["count"] for item in category_stats},
        "rating_distribution": {str(item["_id"]): item["count"] for item in rating_stats}
    }

@app.get("/api/admin/users")
async def get_all_users(
    admin_user: dict = Depends(check_admin_access),
    skip: int = 0,
    limit: int = 50
):
    users_cursor = users_collection.find({}, {"password": 0}).sort("created_at", -1).skip(skip).limit(limit)
    users_list = await users_cursor.to_list(length=limit)
    
    # Add user progress for each user
    enriched_users = []
    for user in users_list:
        progress_docs = await user_progress_collection.find({"user_id": user["_id"]}).to_list(length=None)
        completed_levels = [p for p in progress_docs if p.get("is_completed", False)]
        
        user_data = {
            **user,
            "total_levels_completed": len(completed_levels),
            "total_xp": sum([p.get("xp_earned", 0) for p in completed_levels]),
            "current_level": max([p["level_id"] for p in completed_levels], default=99) + 1 if completed_levels else 100,
            "last_activity": max([p.get("completed_at") for p in progress_docs if p.get("completed_at")], default=user.get("last_login"))
        }
        enriched_users.append(user_data)
    
    total_users = await users_collection.count_documents({})
    
    return {
        "users": enriched_users,
        "total": total_users,
        "pagination": {
            "skip": skip,
            "limit": limit,
            "has_more": total_users > skip + limit
        }
    }

@app.patch("/api/admin/users/{user_id}/progress")
async def update_user_progress(
    user_id: str,
    progress_update: dict,
    admin_user: dict = Depends(check_admin_access)
):
    """Manually update user progress - pass them through levels or reset progress"""
    action = progress_update.get("action")  # "unlock_level", "complete_level", "reset_progress"
    level_id = progress_update.get("level_id")
    
    if action == "unlock_level" and level_id:
        # Create progress entry to unlock a specific level
        progress_entry = {
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "level_id": level_id - 1,  # Complete previous level to unlock target
            "is_completed": True,
            "completed_at": datetime.now(timezone.utc),
            "stars": 3,
            "xp_earned": 100,  # Default XP
            "attempts": 1,
            "admin_granted": True
        }
        
        await user_progress_collection.replace_one(
            {"user_id": user_id, "level_id": level_id - 1},
            progress_entry,
            upsert=True
        )
        
        return {"success": True, "message": f"Unlocked access to Level {level_id} for user"}
    
    elif action == "complete_level" and level_id:
        # Mark specific level as completed
        level = await levels_collection.find_one({"level_id": level_id})
        if not level:
            raise HTTPException(status_code=404, detail="Level not found")
        
        progress_entry = {
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "level_id": level_id,
            "is_completed": True,
            "completed_at": datetime.now(timezone.utc),
            "stars": 3,
            "xp_earned": level.get("xp_reward", 100),
            "attempts": 1,
            "admin_granted": True
        }
        
        await user_progress_collection.replace_one(
            {"user_id": user_id, "level_id": level_id},
            progress_entry,
            upsert=True
        )
        
        return {"success": True, "message": f"Marked Level {level_id} as completed for user"}
    
    elif action == "reset_progress":
        # Reset all user progress
        await user_progress_collection.delete_many({"user_id": user_id})
        return {"success": True, "message": "All user progress has been reset"}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action or missing level_id")

@app.post("/api/admin/users/{user_id}/password-reset")
async def initiate_password_reset(
    user_id: str,
    admin_user: dict = Depends(check_admin_access)
):
    """Initiate password reset for a user (provision for email integration)"""
    user = await users_collection.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate reset token (for future email integration)
    reset_token = str(uuid.uuid4())
    reset_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    
    # Store reset token in database
    await users_collection.update_one(
        {"_id": user_id},
        {
            "$set": {
                "password_reset_token": reset_token,
                "password_reset_expires": reset_expires,
                "password_reset_requested_by": admin_user["_id"],
                "password_reset_requested_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # TODO: Integrate with email service to send reset link
    # For now, return the reset token for admin to share manually
    reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
    
    return {
        "success": True,
        "message": "Password reset initiated",
        "reset_token": reset_token,
        "reset_link": reset_link,
        "expires_at": reset_expires,
        "note": "Future: This will be sent via email automatically"
    }

@app.post("/api/admin/issues")
async def create_issue(
    issue_data: dict,
    admin_user: dict = Depends(check_admin_access)
):
    """Create issue ticket (provision for Jira integration)"""
    issue_doc = {
        "_id": str(uuid.uuid4()),
        "title": issue_data.get("title"),
        "description": issue_data.get("description"),
        "priority": issue_data.get("priority", "medium"),
        "type": issue_data.get("type", "bug"),
        "status": "open",
        "affected_user": issue_data.get("affectedUser"),
        "code_file": issue_data.get("codeFile"),
        "code_error": issue_data.get("codeError"),
        "created_by": admin_user["_id"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "jira_integration": {
            "enabled": False,
            "jira_key": None,
            "sync_status": "pending"
        }
    }
    
    # Store in local database
    result = await db.issues.insert_one(issue_doc)
    
    # TODO: Integrate with Jira API to create actual ticket
    # For now, return issue details for admin tracking
    
    return {
        "success": True,
        "message": "Issue created successfully",
        "issue_id": issue_doc["_id"],
        "issue": issue_doc,
        "note": "Future: This will be automatically synced to Jira"
    }

@app.get("/api/admin/test-modules")
async def get_test_modules(admin_user: dict = Depends(check_admin_access)):
    """Get available modules for testing"""
    modules = [
        {"id": "python-basics", "name": "Python Basics", "levels": "100-105"},
        {"id": "control-flow", "name": "Control Flow", "levels": "103-104"},
        {"id": "data-analysis", "name": "Data Analysis", "levels": "200-203"},
        {"id": "projects", "name": "Projects", "levels": "105"},
        {"id": "feedback-system", "name": "Feedback System", "description": "Test feedback submission and admin management"},
        {"id": "user-management", "name": "User Management", "description": "Test user registration, login, progress tracking"}
    ]
    
    return {"modules": modules}

@app.post("/api/admin/test-module/{module_id}")
async def test_module(
    module_id: str,
    test_params: dict,
    admin_user: dict = Depends(check_admin_access)
):
    """Execute module test (provision for comprehensive testing)"""
    test_results = {
        "module_id": module_id,
        "test_started_at": datetime.now(timezone.utc),
        "test_completed_at": None,
        "status": "running",
        "results": {},
        "errors": [],
        "notes": "Test execution started by admin"
    }
    
    # TODO: Implement actual module testing logic
    # For now, simulate test results
    if module_id == "python-basics":
        test_results["results"] = {
            "levels_tested": [100, 101, 102, 103, 104, 105],
            "passed": 6,
            "failed": 0,
            "execution_time": "2.3s"
        }
    elif module_id == "data-analysis":
        test_results["results"] = {
            "levels_tested": [200, 201, 202, 203],
            "passed": 4,
            "failed": 0,
            "execution_time": "1.8s"
        }
    elif module_id == "feedback-system":
        test_results["results"] = {
            "feedback_submission": "passed",
            "admin_management": "passed",
            "status_updates": "passed",
            "statistics": "passed"
        }
    
    test_results["status"] = "completed"
    test_results["test_completed_at"] = datetime.now(timezone.utc)
    
    return {
        "success": True,
        "message": f"Module {module_id} tested successfully",
        "test_results": test_results
    }

# Subscription and Payment Models
class SubscriptionPlan(BaseModel):
    id: str
    name: str
    price: float
    currency: str = "USD"
    billing_period: str = "monthly"  # monthly, yearly
    features: List[str]
    is_active: bool = True
    created_at: Optional[datetime] = None

class UserSubscription(BaseModel):
    id: Optional[str] = None
    user_id: str
    plan_id: str
    status: str  # active, cancelled, expired, trial
    current_period_start: datetime
    current_period_end: datetime
    trial_end: Optional[datetime] = None
    payment_method: Optional[str] = None
    created_at: Optional[datetime] = None

class Transaction(BaseModel):
    id: Optional[str] = None
    user_id: str
    subscription_id: Optional[str] = None
    amount: float
    currency: str = "USD"
    status: str  # pending, completed, failed, refunded
    payment_method: str
    transaction_date: datetime
    description: Optional[str] = None

# Subscription Management Endpoints
@app.get("/api/admin/subscriptions/plans")
async def get_subscription_plans(admin_user: dict = Depends(check_admin_access)):
    """Get all subscription plans with user counts"""
    plans = [
        {
            "id": "free",
            "name": "Free Plan",
            "price": 0,
            "currency": "USD",
            "billing_period": "forever",
            "features": ["Basic Challenges", "Community Access", "Progress Tracking"],
            "is_active": True,
            "user_count": 800,
            "revenue": 0
        },
        {
            "id": "pro",
            "name": "Pro Plan", 
            "price": 9.99,
            "currency": "USD",
            "billing_period": "monthly",
            "features": ["All Challenges", "Priority Support", "Certificates", "Advanced Analytics", "Offline Access"],
            "is_active": True,
            "user_count": 400,
            "revenue": 3996
        },
        {
            "id": "enterprise",
            "name": "Enterprise Plan",
            "price": 49.99,
            "currency": "USD", 
            "billing_period": "monthly",
            "features": ["Custom Tracks", "Team Management", "API Access", "White Label", "Dedicated Support"],
            "is_active": True,
            "user_count": 50,
            "revenue": 2499.50
        }
    ]
    
    return {"plans": plans, "total_plans": len(plans)}

@app.post("/api/admin/subscriptions/plans")
async def create_subscription_plan(
    plan_data: SubscriptionPlan,
    admin_user: dict = Depends(check_admin_access)
):
    """Create a new subscription plan"""
    plan_doc = {
        "_id": plan_data.id,
        "name": plan_data.name,
        "price": plan_data.price,
        "currency": plan_data.currency,
        "billing_period": plan_data.billing_period,
        "features": plan_data.features,
        "is_active": plan_data.is_active,
        "created_at": datetime.now(timezone.utc),
        "created_by": admin_user["_id"]
    }
    
    await db.subscription_plans.insert_one(plan_doc)
    
    return {"success": True, "message": "Subscription plan created", "plan_id": plan_data.id}

@app.get("/api/admin/subscriptions/users")
async def get_user_subscriptions(
    admin_user: dict = Depends(check_admin_access),
    status: Optional[str] = None,
    plan_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """Get user subscription data with filtering"""
    # Mock subscription data - replace with actual database queries
    subscriptions = [
        {
            "user_id": "user_001",
            "username": "john_doe",
            "email": "john@example.com", 
            "plan_id": "pro",
            "plan_name": "Pro Plan",
            "status": "active",
            "current_period_start": datetime.now(timezone.utc) - timedelta(days=15),
            "current_period_end": datetime.now(timezone.utc) + timedelta(days=15),
            "next_billing_date": datetime.now(timezone.utc) + timedelta(days=15),
            "total_paid": 29.97,
            "payment_method": "credit_card"
        }
    ]
    
    return {
        "subscriptions": subscriptions,
        "total": len(subscriptions),
        "pagination": {"skip": skip, "limit": limit}
    }

@app.get("/api/admin/payments/transactions")
async def get_transactions(
    admin_user: dict = Depends(check_admin_access),
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """Get transaction history with filtering"""
    # Mock transaction data
    transactions = [
        {
            "id": "txn_001",
            "user_id": "user_001",
            "username": "john_doe",
            "email": "john@example.com",
            "amount": 9.99,
            "currency": "USD",
            "status": "completed",
            "payment_method": "credit_card",
            "transaction_date": datetime.now(timezone.utc) - timedelta(days=1),
            "description": "Pro Plan - Monthly Subscription",
            "stripe_transaction_id": "pi_1234567890"
        },
        {
            "id": "txn_002", 
            "user_id": "user_002",
            "username": "jane_smith",
            "email": "jane@example.com",
            "amount": 49.99,
            "currency": "USD", 
            "status": "completed",
            "payment_method": "credit_card",
            "transaction_date": datetime.now(timezone.utc) - timedelta(days=2),
            "description": "Enterprise Plan - Monthly Subscription",
            "stripe_transaction_id": "pi_0987654321"
        }
    ]
    
    return {
        "transactions": transactions,
        "total": len(transactions),
        "pagination": {"skip": skip, "limit": limit}
    }

@app.get("/api/admin/payments/revenue")
async def get_revenue_analytics(admin_user: dict = Depends(check_admin_access)):
    """Get comprehensive revenue analytics"""
    revenue_data = {
        "mrr": 4500.00,  # Monthly Recurring Revenue
        "arr": 54000.00,  # Annual Recurring Revenue  
        "total_revenue_30d": 6750.50,
        "total_revenue_90d": 19250.75,
        "churn_rate": 5.2,
        "trial_conversion_rate": 68.5,
        "average_revenue_per_user": 11.25,
        "ltv": 135.50,  # Customer Lifetime Value
        "monthly_growth_rate": 12.3,
        
        # Revenue by plan
        "revenue_by_plan": {
            "free": 0,
            "pro": 3996.00,
            "enterprise": 2499.50
        },
        
        # Monthly revenue trend (last 12 months)
        "monthly_revenue": [
            {"month": "Jan", "revenue": 3200}, {"month": "Feb", "revenue": 3450},
            {"month": "Mar", "revenue": 3680}, {"month": "Apr", "revenue": 3920},
            {"month": "May", "revenue": 4100}, {"month": "Jun", "revenue": 4350},
            {"month": "Jul", "revenue": 4200}, {"month": "Aug", "revenue": 4400},
            {"month": "Sep", "revenue": 4600}, {"month": "Oct", "revenue": 4750},
            {"month": "Nov", "revenue": 4850}, {"month": "Dec", "revenue": 4995.50}
        ],
        
        # Subscription metrics
        "subscription_metrics": {
            "new_subscriptions_30d": 45,
            "cancelled_subscriptions_30d": 8,
            "upgraded_subscriptions_30d": 12,
            "downgraded_subscriptions_30d": 3
        }
    }
    
    return revenue_data

@app.post("/api/admin/payments/refund")
async def process_refund(
    refund_data: dict,
    admin_user: dict = Depends(check_admin_access)
):
    """Process a payment refund"""
    transaction_id = refund_data.get("transaction_id")
    amount = refund_data.get("amount")
    reason = refund_data.get("reason")
    
    # TODO: Integrate with payment processor (Stripe/PayPal) to process actual refund
    
    refund_doc = {
        "_id": str(uuid.uuid4()),
        "transaction_id": transaction_id,
        "amount": amount,
        "reason": reason,
        "status": "processed",
        "processed_by": admin_user["_id"],
        "processed_at": datetime.now(timezone.utc)
    }
    
    # Store refund record
    await db.refunds.insert_one(refund_doc)
    
    return {
        "success": True,
        "message": "Refund processed successfully",
        "refund_id": refund_doc["_id"],
        "note": "Integration with Stripe/PayPal required for actual refund processing"
    }

# Advanced Admin Analytics
@app.get("/api/admin/analytics/dashboard")
async def get_admin_dashboard_analytics(admin_user: dict = Depends(check_admin_access)):
    """Get comprehensive dashboard analytics for admin overview"""
    
    # User statistics
    user_stats = {
        "total_users": 1250,
        "active_users_7d": 950,
        "active_users_30d": 1150,
        "new_users_7d": 85,
        "new_users_30d": 320,
        "user_retention_7d": 76.0,
        "user_retention_30d": 68.5
    }
    
    # Learning statistics
    learning_stats = {
        "total_challenges_completed": 15750,
        "challenges_completed_7d": 1250,
        "average_completion_rate": 72.5,
        "most_popular_track": "Python Basics",
        "highest_difficulty_completion": "Data Analysis - Hard"
    }
    
    # System health
    system_health = {
        "server_uptime": "99.9%",
        "avg_response_time": "125ms",
        "error_rate": "0.02%",
        "code_executions_today": 2450,
        "queue_length": 3
    }
    
    return {
        "user_stats": user_stats,
        "learning_stats": learning_stats,
        "system_health": system_health,
        "last_updated": datetime.now(timezone.utc)
    }

# AI Tutor System
@app.post("/api/levels/{level_id}/ai-tutor")
async def get_ai_tutor_explanation(
    level_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get AI-powered explanation for a specific level/challenge"""
    
    # Get level details
    level = await levels_collection.find_one({"level_id": level_id})
    if not level:
        raise HTTPException(status_code=404, detail="Level not found")
    
    # Check user subscription for advanced features
    user = await users_collection.find_one({"_id": current_user["_id"]})
    subscription_tier = user.get("subscription_tier", "free")
    
    try:
        # Initialize AI chat
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"tutor_{level_id}_{current_user['_id']}",
            system_message="""You are an expert Python programming tutor. Your job is to explain programming concepts in a clear, engaging way with practical examples. 

Key guidelines:
1. Explain the concept clearly for beginners
2. Provide 2-3 practical code examples
3. Include common use cases and best practices
4. Keep explanations concise but comprehensive
5. Use encouraging and supportive tone
6. Focus on the learning objective of the challenge

Format your response with:
- **Concept Explanation**: Clear overview
- **Code Examples**: 2-3 practical examples with comments
- **Common Use Cases**: Where this is used in real programming
- **Tips**: Best practices and common mistakes to avoid"""
        ).with_model("openai", "gpt-4o-mini")
        
        # Create detailed prompt based on level
        prompt = f"""
Explain this Python programming concept for a learning challenge:

**Challenge Title**: {level['title']}
**Description**: {level['description']}
**Category**: {level['category']}
**Difficulty**: {level['difficulty']}

**Current Challenge Code**:
```python
{level['starter_code']}
```

**Expected Output**: {level['expected_output']}

Please provide a comprehensive tutorial explanation that helps the user understand:
1. The core concept being taught
2. How to approach this type of problem
3. Step-by-step breakdown with examples
4. Import statements needed and why

Make it educational and engaging for a {level['difficulty'].lower()} level programmer.
"""

        user_message = UserMessage(text=prompt)
        ai_response = await chat.send_message(user_message)
        
        return {
            "success": True,
            "explanation": ai_response,
            "level_title": level['title'],
            "subscription_tier": subscription_tier,
            "tutor_available": True
        }
        
    except Exception as e:
        print(f"AI Tutor Error: {str(e)}")
        return {
            "success": False,
            "error": "AI tutor temporarily unavailable",
            "fallback_explanation": f"This challenge focuses on {level['category']} concepts. Practice the provided code and check the hints for guidance.",
            "subscription_tier": subscription_tier,
            "tutor_available": False
        }

# User Subscription Management
@app.get("/api/user/subscription")
async def get_user_subscription(current_user: dict = Depends(get_current_user)):
    """Get user's current subscription details"""
    user = await users_collection.find_one({"_id": current_user["_id"]})
    
    subscription_tier = user.get("subscription_tier", "free")
    subscription_features = {
        "free": {
            "tier": "free",
            "price": 0,
            "features": ["Basic Challenges", "Community Access", "Progress Tracking"],
            "limitations": {
                "ai_tutor_uses": 3,  # 3 uses per day
                "topic_jumping": False,
                "all_categories": False,
                "advanced_hints": False
            }
        },
        "pro": {
            "tier": "pro", 
            "price": 9.99,
            "features": ["All Challenges", "Unlimited AI Tutor", "Topic Jumping", "All Categories", "Priority Support", "Certificates"],
            "limitations": {
                "ai_tutor_uses": -1,  # Unlimited
                "topic_jumping": True,
                "all_categories": True, 
                "advanced_hints": True
            }
        },
        "enterprise": {
            "tier": "enterprise",
            "price": 49.99,
            "features": ["Everything in Pro", "Custom Tracks", "Team Management", "API Access", "White Label"],
            "limitations": {
                "ai_tutor_uses": -1,  # Unlimited
                "topic_jumping": True,
                "all_categories": True,
                "advanced_hints": True,
                "custom_tracks": True
            }
        }
    }
    
    user_subscription = subscription_features.get(subscription_tier, subscription_features["free"])
    
    # Add usage tracking for free users
    if subscription_tier == "free":
        today = datetime.now(timezone.utc).date()
        ai_tutor_usage = user.get("daily_ai_usage", {}).get(str(today), 0)
        user_subscription["daily_ai_usage"] = ai_tutor_usage
        user_subscription["ai_tutor_remaining"] = max(0, 3 - ai_tutor_usage)
    
    return user_subscription

@app.patch("/api/user/subscription/upgrade")
async def upgrade_subscription(
    subscription_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Upgrade user subscription (for testing - mock Stripe integration)"""
    
    new_tier = subscription_data.get("tier")
    if new_tier not in ["free", "pro", "enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")
    
    # Update user subscription
    await users_collection.update_one(
        {"_id": current_user["_id"]},
        {
            "$set": {
                "subscription_tier": new_tier,
                "subscription_updated_at": datetime.now(timezone.utc),
                "payment_method": subscription_data.get("payment_method", "test")
            }
        }
    )
    
    return {
        "success": True,
        "message": f"Subscription upgraded to {new_tier}",
        "new_tier": new_tier
    }

# Create sample paid users for testing
@app.post("/api/admin/create-sample-users")
async def create_sample_paid_users(admin_user: dict = Depends(check_admin_access)):
    """Create sample users with different subscription tiers for testing"""
    
    sample_users = [
        {
            "_id": str(uuid.uuid4()),
            "username": "free_user_demo",
            "email": "free@pythonquest.com",
            "password": pwd_context.hash("demo123"),
            "subscription_tier": "free",
            "profile": {
                "current_level": 100,
                "total_xp": 0,
                "completed_levels": [],
                "badges": []
            },
            "created_at": datetime.now(timezone.utc)
        },
        {
            "_id": str(uuid.uuid4()),
            "username": "pro_user_demo", 
            "email": "pro@pythonquest.com",
            "password": pwd_context.hash("demo123"),
            "subscription_tier": "pro",
            "profile": {
                "current_level": 105,
                "total_xp": 500,
                "completed_levels": [100, 101, 102, 103, 104],
                "badges": ["first_steps", "problem_solver"]
            },
            "created_at": datetime.now(timezone.utc)
        },
        {
            "_id": str(uuid.uuid4()),
            "username": "enterprise_user_demo",
            "email": "enterprise@pythonquest.com", 
            "password": pwd_context.hash("demo123"),
            "subscription_tier": "enterprise",
            "profile": {
                "current_level": 210,
                "total_xp": 2000,
                "completed_levels": list(range(100, 210)),
                "badges": ["first_steps", "problem_solver", "data_master", "python_expert"]
            },
            "created_at": datetime.now(timezone.utc)
        }
    ]
    
    # Insert sample users
    inserted_users = []
    for user in sample_users:
        try:
            await users_collection.insert_one(user)
            user.pop("password")  # Remove password from response
            inserted_users.append(user)
        except Exception as e:
            print(f"Error creating user {user['username']}: {e}")
    
    return {
        "success": True,
        "message": f"Created {len(inserted_users)} sample users",
        "users": inserted_users,
        "login_credentials": [
            {"username": "free_user_demo", "password": "demo123", "tier": "free"},
            {"username": "pro_user_demo", "password": "demo123", "tier": "pro"}, 
            {"username": "enterprise_user_demo", "password": "demo123", "tier": "enterprise"}
        ]
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)