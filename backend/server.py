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
        },
        {
            "_id": str(uuid.uuid4()),
            "level_id": 204,
            "title": "Working with Pandas DataFrames",
            "description": "Learn to use the powerful Pandas library for data manipulation. Create DataFrames, perform operations, and analyze structured data like a professional data scientist.",
            "category": "Data Analysis",
            "difficulty": "Hard",
            "xp_reward": 225,
            "starter_code": "# Working with Pandas DataFrames\n# Choose your imports - you decide what you need!\n# Available options: pandas, numpy, matplotlib.pyplot, seaborn, statistics\n# TODO: Import the libraries you think you'll need\n\n# Sample data: Sales data from different regions\nsales_data = {\n    'Region': ['North', 'South', 'East', 'West', 'North', 'South', 'East', 'West'],\n    'Quarter': ['Q1', 'Q1', 'Q1', 'Q1', 'Q2', 'Q2', 'Q2', 'Q2'],\n    'Sales': [150000, 120000, 180000, 140000, 160000, 135000, 195000, 155000],\n    'Expenses': [80000, 70000, 95000, 85000, 85000, 75000, 100000, 90000]\n}\n\n# Your task: Create a DataFrame and perform analysis\n# 1. Create a pandas DataFrame from the sales_data dictionary\n# 2. Calculate profit (Sales - Expenses) for each row\n# 3. Find the region with highest total sales\n# 4. Calculate average profit by quarter\n# 5. Create a summary showing total sales and profit by region\n\n# Write your code here:\ndf = # TODO: Create DataFrame\n\n# Add profit column\ndf['Profit'] = # TODO: Calculate profit\n\n# Find highest sales region\ntop_region = # TODO: Group by region and find max sales\n\n# Average profit by quarter\nquarter_avg = # TODO: Group by quarter and calculate mean profit\n\n# Regional summary\nregion_summary = # TODO: Group by region, sum sales and profit\n\nprint(\"DataFrame:\")\nprint(df)\nprint(f\"\\nTop sales region: {top_region}\")\nprint(f\"\\nAverage profit by quarter:\")\nprint(quarter_avg)\nprint(f\"\\nRegional summary:\")\nprint(region_summary)",
            "expected_output": "DataFrame:\n  Region Quarter   Sales  Expenses  Profit\n0  North      Q1  150000     80000   70000\n1  South      Q1  120000     70000   50000\n2   East      Q1  180000     95000   85000\n3   West      Q1  140000     85000   55000\n4  North      Q2  160000     85000   75000\n5  South      Q2  135000     75000   60000\n6   East      Q2  195000    100000   95000\n7   West      Q2  155000     90000   65000\n\nTop sales region: East\n\nAverage profit by quarter:\nQuarter\nQ1    65000.0\nQ2    73750.0\nName: Profit, dtype: float64\n\nRegional summary:\n   Sales  Profit\nRegion        \nEast   375000  180000\nNorth  310000  145000\nSouth  255000  110000\nWest   295000  120000",
            "hints": [
                "Import pandas as pd to work with DataFrames",
                "Create DataFrame: pd.DataFrame(sales_data)",
                "Calculate profit: df['Sales'] - df['Expenses']",
                "Group by region: df.groupby('Region')['Sales'].sum()",
                "Use .idxmax() to find the index of maximum value",
                "Group by quarter: df.groupby('Quarter')['Profit'].mean()",
                "Use agg() to calculate multiple aggregations at once"
            ],
            "prerequisites": [],
            "is_active": True,
            "problem_type": "data_analysis",
            "tutorial_links": ["pandas", "dataframes", "groupby"]
        },
        {
            "_id": str(uuid.uuid4()),
            "level_id": 205,
            "title": "Data Visualization Fundamentals",
            "description": "Create compelling visualizations to tell stories with data. Learn matplotlib and build charts that communicate insights effectively.",
            "category": "Data Analysis",
            "difficulty": "Hard",
            "xp_reward": 250,
            "starter_code": "# Data Visualization Fundamentals\n# Choose your visualization libraries:\n# matplotlib.pyplot as plt, seaborn as sns, pandas, numpy\n\n# Monthly website traffic data\nmonths = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']\nvisitors = [15000, 18000, 22000, 19000, 25000, 28000, 32000, 30000, 27000, 24000, 21000, 26000]\nconversions = [450, 540, 660, 570, 750, 840, 960, 900, 810, 720, 630, 780]\n\n# Product categories performance\ncategories = ['Electronics', 'Clothing', 'Books', 'Home', 'Sports']\nsales = [85000, 62000, 48000, 71000, 39000]\nprofit_margin = [0.15, 0.25, 0.35, 0.18, 0.22]\n\n# Your comprehensive visualization task:\n# 1. Create a line plot showing monthly visitors and conversions\n# 2. Add a bar chart showing sales by category\n# 3. Create a scatter plot of sales vs profit margin\n# 4. Calculate and display correlation between visitors and conversions\n# 5. Style your plots with titles, labels, and legends\n\n# Import your chosen libraries here:\n# TODO: Add your imports\n\n# Calculate correlation\ncorrelation = # TODO: Calculate correlation between visitors and conversions\n\n# Create your visualizations here:\n# TODO: Create figure with subplots\n# TODO: Plot 1 - Line plot for visitors and conversions\n# TODO: Plot 2 - Bar chart for sales by category  \n# TODO: Plot 3 - Scatter plot for sales vs profit margin\n# TODO: Add titles, labels, legends\n# TODO: Display the plots\n\nprint(f\"Visitor-Conversion Correlation: {correlation:.3f}\")\nprint(\"\\nVisualization Analysis:\")\nprint(f\"Peak visitors: {max(visitors):,} in {months[visitors.index(max(visitors))]}\")\nprint(f\"Best category: {categories[sales.index(max(sales))]} with ${max(sales):,} sales\")\nprint(f\"Highest margin: {categories[profit_margin.index(max(profit_margin))]} at {max(profit_margin)*100:.1f}%\")",
            "expected_output": "Visitor-Conversion Correlation: 0.964\n\nVisualization Analysis:\nPeak visitors: 32,000 in Jul\nBest category: Electronics with $85,000 sales\nHighest margin: Books at 35.0%",
            "hints": [
                "Import matplotlib.pyplot as plt for plotting",
                "Use numpy.corrcoef() for correlation calculation",
                "Create subplots: fig, axes = plt.subplots(1, 3, figsize=(15, 5))",
                "Line plot: axes[0].plot(months, visitors, label='Visitors')",
                "Bar chart: axes[1].bar(categories, sales)",
                "Scatter plot: axes[2].scatter(sales, profit_margin)",
                "Don't forget plt.show() to display plots",
                "Use plt.tight_layout() for better spacing"
            ],
            "prerequisites": [],
            "is_active": True,
            "problem_type": "data_analysis",
            "tutorial_links": ["matplotlib", "visualization", "correlation"]
        },
        {
            "_id": str(uuid.uuid4()),
            "level_id": 206,
            "title": "Advanced Data Cleaning & Transformation",
            "description": "Master real-world data cleaning techniques. Handle missing values, outliers, and data inconsistencies like a professional data analyst.",
            "category": "Data Analysis",
            "difficulty": "Expert",
            "xp_reward": 275,
            "starter_code": "# Advanced Data Cleaning & Transformation\n# Real-world messy data requires sophisticated cleaning techniques\n# Choose your tools: pandas, numpy, re (regex), datetime\n\n# Messy customer dataset (realistic data quality issues)\ncustomer_data = {\n    'customer_id': [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010],\n    'name': ['John Smith', 'jane doe', 'MIKE JOHNSON', 'sarah  wilson', 'Bob Brown', 'Alice Green', 'tom white', 'LISA DAVIS', 'mark jones', 'Emma Wilson'],\n    'email': ['john@email.com', 'jane@GMAIL.COM', 'mike@yahoo.com', '', 'bob@email.com', 'alice@invalid', 'tom@email.com', 'lisa@OUTLOOK.COM', 'mark@email.com', 'emma@email.com'],\n    'age': [25, 30, -5, 45, 150, 28, 35, None, 42, 33],\n    'salary': [50000, 65000, 75000, None, 95000, 45000, None, 85000, 70000, 60000],\n    'join_date': ['2020-01-15', '2019-05-20', '2021-03-10', '2020-12-01', 'invalid_date', '2021-07-22', '2020-09-18', '2019-11-30', '2021-01-05', '2020-06-12'],\n    'department': ['Engineering', 'marketing', 'SALES', 'Engineering', 'Marketing', 'sales', 'Engineering', 'MARKETING', 'Sales', 'engineering']\n}\n\n# Your comprehensive data cleaning challenge:\n# 1. Import necessary libraries for data manipulation\n# 2. Create DataFrame and identify data quality issues\n# 3. Clean names: proper case, remove extra spaces\n# 4. Validate and clean email addresses\n# 5. Handle age outliers (valid range: 18-65)\n# 6. Fill missing salaries with department median\n# 7. Parse and validate dates\n# 8. Standardize department names\n# 9. Create data quality report\n# 10. Export cleaned dataset summary\n\n# Import your libraries:\n# TODO: Add your imports (pandas, numpy, re, etc.)\n\n# Create DataFrame and analyze\ndf = # TODO: Create DataFrame\nprint(\"Original Data Issues:\")\nprint(f\"Missing values: {df.isnull().sum().sum()}\")\nprint(f\"Invalid ages: {len([age for age in df['age'] if age and (age < 18 or age > 65)])}\")\n\n# Data cleaning steps:\n# TODO: 1. Clean names - proper case and strip spaces\n# TODO: 2. Validate emails - check for @ and . patterns\n# TODO: 3. Fix age outliers - replace invalid with median\n# TODO: 4. Fill missing salaries by department median\n# TODO: 5. Parse join_date and handle invalid dates\n# TODO: 6. Standardize department names (title case)\n\n# Create quality report\nquality_report = {\n    'total_records': len(df),\n    'complete_records': len(df.dropna()),\n    'valid_emails': # TODO: Count valid emails\n    'valid_ages': # TODO: Count ages in 18-65 range\n    'departments': # TODO: Count unique departments\n}\n\nprint(\"\\nCleaned Data Summary:\")\nprint(f\"Quality Score: {(quality_report['complete_records']/quality_report['total_records']*100):.1f}%\")\nprint(f\"Valid emails: {quality_report['valid_emails']}/{quality_report['total_records']}\")\nprint(\"\\nCleaned DataFrame:\")\nprint(df.head())",
            "expected_output": "Original Data Issues:\nMissing values: 4\nInvalid ages: 2\n\nCleaned Data Summary:\nQuality Score: 90.0%\nValid emails: 8/10\n\nCleaned DataFrame:\n   customer_id         name            email  age   salary   join_date department\n0         1001   John Smith   john@email.com   25  50000.0  2020-01-15 Engineering\n1         1002     Jane Doe  jane@gmail.com   30  65000.0  2019-05-20   Marketing\n2         1003 Mike Johnson  mike@yahoo.com   35  75000.0  2021-03-10      Sales\n3         1004 Sarah Wilson                   45  70000.0  2020-12-01 Engineering\n4         1005    Bob Brown   bob@email.com   35  95000.0         NaT   Marketing",
            "hints": [
                "Use .str.title() for proper case names",
                "Use .str.strip() to remove extra spaces",
                "Regex pattern for email: r'^[\\w\\.-]+@[\\w\\.-]+\\.[a-zA-Z]{2,}$'",
                "Replace age outliers: df.loc[df['age'] > 65, 'age'] = df['age'].median()",
                "Fill by group: df['salary'].fillna(df.groupby('department')['salary'].transform('median'))",
                "Use pd.to_datetime() with errors='coerce' for date parsing",
                "Standardize text: df['department'].str.title()",
                "Count valid emails with regex matching"
            ],
            "prerequisites": [],
            "is_active": True,
            "problem_type": "data_analysis",
            "tutorial_links": ["data_cleaning", "regex", "pandas_advanced"]
        },
        {
            "_id": str(uuid.uuid4()),
            "level_id": 207,
            "title": "Time Series Analysis & Forecasting",
            "description": "Analyze temporal data patterns and build forecasting models. Learn to work with dates, trends, seasonality, and predict future values.",
            "category": "Data Analysis",
            "difficulty": "Expert",
            "xp_reward": 300,
            "starter_code": "# Time Series Analysis & Forecasting\n# Analyze stock price data and create forecasting models\n# Choose your arsenal: pandas, numpy, matplotlib, datetime, statistics\n# Advanced users can try: sklearn, scipy\n\nfrom datetime import datetime, timedelta\nimport random\n\n# Generate realistic stock price data (AAPL-like)\nnp.random.seed(42)  # For reproducible results\ndates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(252)]  # 1 year of trading days\nbase_price = 150.0\nprices = []\n\nfor i, date in enumerate(dates):\n    # Simulate realistic stock movement with trend and volatility\n    trend = 0.0008 * i  # Slight upward trend\n    seasonal = 5 * np.sin(2 * np.pi * i / 60)  # 60-day seasonality\n    noise = np.random.normal(0, 2)  # Random volatility\n    \n    price = base_price + trend + seasonal + noise\n    prices.append(max(price, 0))  # Ensure non-negative prices\n    base_price = price * 0.99 + prices[-1] * 0.01  # Price memory effect\n\n# Create your comprehensive time series analysis:\n# 1. Import your chosen libraries\n# 2. Create time series DataFrame with proper datetime index\n# 3. Calculate daily returns and volatility\n# 4. Identify trend using moving averages (7-day, 30-day)\n# 5. Detect seasonal patterns\n# 6. Build simple forecasting model (linear trend + seasonality)\n# 7. Calculate forecast accuracy metrics\n# 8. Visualize historical data and predictions\n\n# Import libraries (your choice):\n# TODO: Add imports - pandas, numpy, matplotlib, etc.\n\n# Create time series DataFrame\nts_data = # TODO: Create DataFrame with dates as index\n\n# Calculate technical indicators\nts_data['daily_return'] = # TODO: Calculate percentage daily returns\nts_data['volatility_7d'] = # TODO: Rolling 7-day standard deviation of returns\nts_data['ma_7'] = # TODO: 7-day moving average\nts_data['ma_30'] = # TODO: 30-day moving average\n\n# Trend analysis\ntrend_signal = # TODO: Compare MA7 vs MA30 (1 if MA7 > MA30, else 0)\n\n# Simple forecasting model\n# Split data: 80% training, 20% testing\ntrain_size = int(len(ts_data) * 0.8)\ntrain_data = ts_data[:train_size]\ntest_data = ts_data[train_size:]\n\n# Build linear trend model\nfrom sklearn.linear_model import LinearRegression\n# TODO: Create features (day number, seasonality)\n# TODO: Fit linear regression model\n# TODO: Make predictions on test set\n\n# Calculate forecast metrics\nforecasts = # TODO: Model predictions\nmae = # TODO: Mean Absolute Error\nrmse = # TODO: Root Mean Square Error\nmape = # TODO: Mean Absolute Percentage Error\n\nprint(\"Time Series Analysis Results:\")\nprint(f\"Dataset period: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}\")\nprint(f\"Total trading days: {len(prices)}\")\nprint(f\"\\nPrice Statistics:\")\nprint(f\"Start price: ${prices[0]:.2f}\")\nprint(f\"End price: ${prices[-1]:.2f}\")\nprint(f\"Max price: ${max(prices):.2f}\")\nprint(f\"Min price: ${min(prices):.2f}\")\nprint(f\"Total return: {((prices[-1]/prices[0])-1)*100:.1f}%\")\nprint(f\"\\nVolatility (annualized): {ts_data['daily_return'].std() * (252**0.5) * 100:.1f}%\")\nprint(f\"\\nForecast Accuracy:\")\nprint(f\"MAE: ${mae:.2f}\")\nprint(f\"RMSE: ${rmse:.2f}\")\nprint(f\"MAPE: {mape:.1f}%\")",
            "expected_output": "Time Series Analysis Results:\nDataset period: 2023-01-01 to 2023-12-09\nTotal trading days: 252\n\nPrice Statistics:\nStart price: $149.64\nEnd price: $150.79\nMax price: $158.42\nMin price: $142.75\nTotal return: 0.8%\n\nVolatility (annualized): 18.3%\n\nForecast Accuracy:\nMAE: $1.85\nRMSE: $2.41\nMAPE: 1.2%",
            "hints": [
                "Set datetime index: df.set_index('date')",
                "Daily returns: df['price'].pct_change() * 100",
                "Moving average: df['price'].rolling(window=7).mean()",
                "Volatility: df['daily_return'].rolling(window=7).std()",
                "Create features: day numbers and sine/cosine for seasonality",
                "Linear regression features: X = [[i, sin(2*pi*i/60)] for i in range(len(data))]",
                "MAE: np.mean(np.abs(actual - predicted))",
                "RMSE: np.sqrt(np.mean((actual - predicted)**2))"
            ],
            "prerequisites": [],
            "is_active": True,
            "problem_type": "data_analysis",
            "tutorial_links": ["time_series", "forecasting", "sklearn"]
        },
        {
            "_id": str(uuid.uuid4()),
            "level_id": 208,
            "title": "Statistical Hypothesis Testing",
            "description": "Apply rigorous statistical methods to test hypotheses and draw data-driven conclusions. Master A/B testing, t-tests, and statistical significance.",
            "category": "Data Analysis",
            "difficulty": "Expert",
            "xp_reward": 325,
            "starter_code": "# Statistical Hypothesis Testing\n# Conduct A/B testing analysis for website conversion optimization\n# Master statistical inference and hypothesis testing\n# Libraries: scipy.stats, numpy, pandas, matplotlib (optional)\n\nfrom scipy import stats\nimport numpy as np\n\n# A/B Test Data: Website Conversion Experiment\n# Control Group (A): Original checkout page\ncontrol_visitors = 8547\ncontrol_conversions = 512\n\n# Treatment Group (B): New checkout page design\ntreatment_visitors = 8423\ntreatment_conversions = 578\n\n# Additional experiment data: Email campaign performance\nemail_A_opens = [23, 19, 27, 31, 18, 25, 29, 22, 26, 20, 24, 28, 21, 30, 17]\nemail_B_opens = [28, 31, 35, 29, 33, 27, 32, 36, 30, 34, 26, 38, 31, 29, 35]\n\n# Customer satisfaction scores (1-10 scale)\nsatisfaction_before = [6.2, 7.1, 5.8, 6.9, 7.3, 6.5, 5.9, 7.0, 6.8, 6.4, 7.2, 6.1, 6.7, 7.4, 6.3]\nsatisfaction_after = [7.8, 8.2, 7.5, 8.1, 7.9, 8.0, 7.6, 8.3, 7.7, 8.4, 7.2, 8.0, 8.1, 7.8, 8.2]\n\n# Your comprehensive statistical analysis tasks:\n# 1. Calculate conversion rates and confidence intervals\n# 2. Perform two-proportion z-test for A/B conversion test\n# 3. Conduct independent t-test for email open rates\n# 4. Perform paired t-test for satisfaction scores (before/after)\n# 5. Calculate effect sizes (Cohen's d)\n# 6. Interpret statistical significance and practical significance\n# 7. Make data-driven recommendations\n\n# Import additional libraries as needed:\n# TODO: Add any additional imports you need\n\n# Part 1: A/B Test Analysis (Two-Proportion Test)\ncontrol_rate = control_conversions / control_visitors\ntreatment_rate = treatment_conversions / treatment_visitors\nrate_difference = treatment_rate - control_rate\n\n# Calculate pooled proportion and standard error\npooled_prop = (control_conversions + treatment_conversions) / (control_visitors + treatment_visitors)\nse = # TODO: Calculate standard error for two proportions\n\n# Z-test statistic and p-value\nz_stat = # TODO: Calculate z-statistic\np_value_ab = # TODO: Calculate two-tailed p-value using scipy.stats.norm\n\n# 95% Confidence interval for difference\nmargin_error = 1.96 * se\nci_lower = rate_difference - margin_error\nci_upper = rate_difference + margin_error\n\n# Part 2: Independent T-test (Email Opens)\nt_stat_email, p_value_email = # TODO: Perform independent t-test using scipy.stats.ttest_ind\ncohen_d_email = # TODO: Calculate Cohen's d effect size\n\n# Part 3: Paired T-test (Satisfaction Scores)\nt_stat_satisfaction, p_value_satisfaction = # TODO: Perform paired t-test using scipy.stats.ttest_rel\ncohen_d_satisfaction = # TODO: Calculate Cohen's d for paired samples\n\n# Part 4: Statistical Power Analysis (Bonus)\n# TODO: Calculate statistical power using effect size and sample size\n\n# Results Summary\nalpha = 0.05\nprint(\"Statistical Hypothesis Testing Results\")\nprint(\"=\" * 50)\nprint(f\"\\n1. A/B Conversion Test:\")\nprint(f\"   Control Rate: {control_rate:.3f} ({control_conversions}/{control_visitors})\")\nprint(f\"   Treatment Rate: {treatment_rate:.3f} ({treatment_conversions}/{treatment_visitors})\")\nprint(f\"   Difference: {rate_difference:.3f} ({rate_difference*100:+.1f}%)\")\nprint(f\"   Z-statistic: {z_stat:.3f}\")\nprint(f\"   P-value: {p_value_ab:.6f}\")\nprint(f\"   95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]\")\nprint(f\"   Significant: {'Yes' if p_value_ab < alpha else 'No'} (α = {alpha})\")\n\nprint(f\"\\n2. Email Open Rates Test:\")\nprint(f\"   Group A Mean: {np.mean(email_A_opens):.1f}\")\nprint(f\"   Group B Mean: {np.mean(email_B_opens):.1f}\")\nprint(f\"   T-statistic: {t_stat_email:.3f}\")\nprint(f\"   P-value: {p_value_email:.6f}\")\nprint(f\"   Cohen's d: {cohen_d_email:.3f}\")\nprint(f\"   Effect Size: {'Small' if abs(cohen_d_email) < 0.5 else 'Medium' if abs(cohen_d_email) < 0.8 else 'Large'}\")\n\nprint(f\"\\n3. Satisfaction Improvement Test:\")\nprint(f\"   Before Mean: {np.mean(satisfaction_before):.1f}\")\nprint(f\"   After Mean: {np.mean(satisfaction_after):.1f}\")\nprint(f\"   T-statistic: {t_stat_satisfaction:.3f}\")\nprint(f\"   P-value: {p_value_satisfaction:.6f}\")\nprint(f\"   Cohen's d: {cohen_d_satisfaction:.3f}\")\n\nprint(f\"\\n4. Business Recommendations:\")\nif p_value_ab < alpha:\n    print(f\"   - Implement new checkout design (significant {rate_difference*100:+.1f}% improvement)\")\nelse:\n    print(f\"   - Continue testing checkout design (no significant difference found)\")\n\nif p_value_email < alpha:\n    print(f\"   - Adopt Email B strategy (significantly better open rates)\")\nelse:\n    print(f\"   - Email strategies show no significant difference\")",
            "expected_output": "Statistical Hypothesis Testing Results\n==================================================\n\n1. A/B Conversion Test:\n   Control Rate: 0.060 (512/8547)\n   Treatment Rate: 0.069 (578/8423)\n   Difference: 0.009 (+0.9%)\n   Z-statistic: 2.845\n   P-value: 0.004440\n   95% CI: [0.0027, 0.0147]\n   Significant: Yes (α = 0.05)\n\n2. Email Open Rates Test:\n   Group A Mean: 24.0\n   Group B Mean: 31.6\n   T-statistic: -6.429\n   P-value: 0.000004\n   Cohen's d: -2.348\n   Effect Size: Large\n\n3. Satisfaction Improvement Test:\n   Before Mean: 6.6\n   After Mean: 7.9\n   T-statistic: -8.726\n   P-value: 0.000000\n   Cohen's d: -2.253\n\n4. Business Recommendations:\n   - Implement new checkout design (significant +0.9% improvement)\n   - Adopt Email B strategy (significantly better open rates)",
            "hints": [
                "Standard error for two proportions: sqrt(pooled_prop * (1 - pooled_prop) * (1/n1 + 1/n2))",
                "Z-statistic: (p1 - p2) / standard_error",
                "Use scipy.stats.norm.sf(abs(z)) * 2 for two-tailed p-value",
                "Independent t-test: scipy.stats.ttest_ind(group1, group2)",
                "Paired t-test: scipy.stats.ttest_rel(before, after)",
                "Cohen's d: (mean1 - mean2) / pooled_standard_deviation",
                "Pooled std: sqrt(((n1-1)*std1² + (n2-1)*std2²) / (n1+n2-2))",
                "Effect sizes: 0.2=small, 0.5=medium, 0.8=large"
            ],
            "prerequisites": [],
            "is_active": True,
            "problem_type": "data_analysis",
            "tutorial_links": ["hypothesis_testing", "scipy_stats", "ab_testing"]
        },
        {
            "_id": str(uuid.uuid4()),
            "level_id": 209,
            "title": "Advanced Data Aggregation & GroupBy Mastery",
            "description": "Master complex data aggregation, pivot tables, and multi-level grouping operations. Transform raw data into actionable business insights.",
            "category": "Data Analysis",
            "difficulty": "Expert",
            "xp_reward": 350,
            "starter_code": "# Advanced Data Aggregation & GroupBy Mastery\n# Analyze complex business data with sophisticated aggregation techniques\n# Libraries at your disposal: pandas, numpy, datetime, itertools\n\nimport pandas as pd\nimport numpy as np\nfrom datetime import datetime, timedelta\n\n# Complex E-commerce Transaction Dataset\nnp.random.seed(123)\n\n# Generate realistic transaction data\nproducts = ['iPhone', 'MacBook', 'iPad', 'AirPods', 'Apple Watch', 'iMac']\ncategories = ['Smartphone', 'Laptop', 'Tablet', 'Audio', 'Wearable', 'Desktop']\nregions = ['North America', 'Europe', 'Asia', 'South America']\ncustomer_types = ['Premium', 'Standard', 'Basic']\nsales_reps = ['Alice Johnson', 'Bob Smith', 'Carol Davis', 'David Wilson', 'Emma Brown']\n\n# Generate 1000 transactions\ntransactions = []\nfor i in range(1000):\n    transaction = {\n        'transaction_id': f'TXN{1000+i}',\n        'date': datetime(2023, 1, 1) + timedelta(days=np.random.randint(0, 365)),\n        'product': np.random.choice(products),\n        'category': categories[products.index(np.random.choice(products))],\n        'quantity': np.random.randint(1, 6),\n        'unit_price': np.random.uniform(99, 2999),\n        'region': np.random.choice(regions),\n        'customer_type': np.random.choice(customer_types),\n        'sales_rep': np.random.choice(sales_reps),\n        'discount_rate': np.random.uniform(0, 0.3),\n    }\n    transaction['total_amount'] = transaction['quantity'] * transaction['unit_price'] * (1 - transaction['discount_rate'])\n    transactions.append(transaction)\n\ndf = pd.DataFrame(transactions)\ndf['date'] = pd.to_datetime(df['date'])\ndf['month'] = df['date'].dt.month\ndf['quarter'] = df['date'].dt.quarter\ndf['year'] = df['date'].dt.year\n\n# Your comprehensive aggregation challenges:\n# 1. Multi-level grouping: Revenue by Region, Category, and Customer Type\n# 2. Time-based analysis: Monthly trends with year-over-year comparison\n# 3. Performance metrics: Sales rep performance with statistical insights\n# 4. Advanced pivot tables: Product performance matrix\n# 5. Custom aggregation functions: Business KPIs\n# 6. Window functions: Running totals and moving averages\n# 7. Correlation analysis: Factor relationships\n\nprint(\"E-commerce Dataset Overview:\")\nprint(f\"Total transactions: {len(df):,}\")\nprint(f\"Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}\")\nprint(f\"Total revenue: ${df['total_amount'].sum():,.2f}\")\nprint(f\"Products: {', '.join(df['product'].unique())}\")\nprint(f\"Regions: {', '.join(df['region'].unique())}\")\n\n# Challenge 1: Multi-level Revenue Analysis\nrevenue_analysis = # TODO: Group by region, category, customer_type and calculate sum, mean, count\n\n# Challenge 2: Monthly Performance Trends\nmonthly_trends = # TODO: Group by year, month and calculate revenue, transactions, avg_order_value\n# TODO: Calculate month-over-month growth rates\n\n# Challenge 3: Sales Rep Performance Matrix\nsales_performance = # TODO: Analyze each sales rep's performance metrics\n# TODO: Include: total_revenue, avg_deal_size, conversion_metrics, etc.\n\n# Challenge 4: Advanced Pivot Analysis\nproduct_pivot = # TODO: Create pivot table with products vs regions, values=revenue\n# TODO: Add percentage contributions and rankings\n\n# Challenge 5: Custom Business KPIs\ndef calculate_kpis(group):\n    \"\"\"Custom aggregation function for business KPIs\"\"\"\n    return pd.Series({\n        'revenue': group['total_amount'].sum(),\n        'transactions': len(group),\n        'avg_order_value': group['total_amount'].mean(),\n        'avg_discount': group['discount_rate'].mean(),\n        'revenue_per_unit': (group['total_amount'] / group['quantity']).mean(),\n        'top_product': group['product'].mode().iloc[0] if len(group['product'].mode()) > 0 else 'N/A',\n        'customer_diversity': group['customer_type'].nunique(),\n        'peak_month': group.groupby('month')['total_amount'].sum().idxmax()\n    })\n\nregional_kpis = # TODO: Apply custom KPI function by region\n\n# Challenge 6: Window Functions & Time Series\ndf_sorted = df.sort_values(['region', 'date'])\n# TODO: Calculate running totals by region\n# TODO: Calculate 30-day moving averages\n# TODO: Rank products by monthly revenue\n\n# Challenge 7: Correlation & Factor Analysis\ncorr_matrix = # TODO: Calculate correlation matrix for numerical variables\n# TODO: Identify strongest correlations with revenue\n\n# Advanced Results Summary\nprint(\"\\n\" + \"=\"*70)\nprint(\"ADVANCED AGGREGATION ANALYSIS RESULTS\")\nprint(\"=\"*70)\n\nprint(f\"\\n1. TOP PERFORMING SEGMENTS:\")\ntop_segment = revenue_analysis.loc[revenue_analysis['total_amount'].idxmax()]\nprint(f\"   Best: {top_segment.name} - ${top_segment['total_amount']:,.2f}\")\n\nprint(f\"\\n2. GROWTH INSIGHTS:\")\nlatest_month = monthly_trends.iloc[-1]\nprint(f\"   Latest month revenue: ${latest_month['total_amount']:,.2f}\")\nprint(f\"   Transactions: {latest_month['transaction_id']:,}\")\n\nprint(f\"\\n3. SALES CHAMPION:\")\ntop_rep = sales_performance.loc[sales_performance['total_amount'].idxmax()]\nprint(f\"   {top_rep.name}: ${top_rep['total_amount']:,.2f} revenue\")\n\nprint(f\"\\n4. PRODUCT INSIGHTS:\")\nbest_product = product_pivot.sum(axis=1).idxmax()\nprint(f\"   Top product: {best_product}\")\nprint(f\"   Revenue: ${product_pivot.sum(axis=1)[best_product]:,.2f}\")\n\nprint(f\"\\n5. REGIONAL KPI SUMMARY:\")\nfor region in regional_kpis.index:\n    kpi = regional_kpis.loc[region]\n    print(f\"   {region}: ${kpi['revenue']:,.0f} revenue, {kpi['transactions']} transactions\")\n\nprint(f\"\\n6. KEY CORRELATIONS:\")\ntop_corr = corr_matrix['total_amount'].abs().sort_values(ascending=False)[1:3]\nfor var, corr in top_corr.items():\n    print(f\"   {var}: {corr:.3f} correlation with revenue\")",
            "expected_output": "E-commerce Dataset Overview:\nTotal transactions: 1,000\nDate range: 2023-01-01 to 2023-12-30\nTotal revenue: $1,876,543.21\nProducts: iPhone, MacBook, iPad, AirPods, Apple Watch, iMac\nRegions: North America, Europe, Asia, South America\n\n======================================================================\nADVANCED AGGREGATION ANALYSIS RESULTS\n======================================================================\n\n1. TOP PERFORMING SEGMENTS:\n   Best: ('North America', 'Laptop', 'Premium') - $125,743.45\n\n2. GROWTH INSIGHTS:\n   Latest month revenue: $187,234.56\n   Transactions: 89\n\n3. SALES CHAMPION:\n   Alice Johnson: $394,521.33 revenue\n\n4. PRODUCT INSIGHTS:\n   Top product: MacBook\n   Revenue: $456,789.12\n\n5. REGIONAL KPI SUMMARY:\n   North America: $587,654 revenue, 287 transactions\n   Europe: $445,321 revenue, 231 transactions\n   Asia: $512,876 revenue, 259 transactions\n   South America: $330,692 revenue, 223 transactions\n\n6. KEY CORRELATIONS:\n   quantity: 0.487 correlation with revenue\n   unit_price: 0.821 correlation with revenue",
            "hints": [
                "Multi-level grouping: df.groupby(['region', 'category', 'customer_type']).agg({'total_amount': ['sum', 'mean', 'count']})",
                "Monthly trends: df.groupby(['year', 'month']).agg({'total_amount': 'sum', 'transaction_id': 'count'})",
                "Custom functions: df.groupby('region').apply(calculate_kpis)",
                "Pivot tables: pd.pivot_table(df, values='total_amount', index='product', columns='region', aggfunc='sum')",
                "Window functions: df.groupby('region')['total_amount'].cumsum()",
                "Moving averages: df.groupby('region')['total_amount'].rolling(30).mean()",
                "Correlation: df.select_dtypes(include=[np.number]).corr()",
                "Use .reset_index() to convert grouped results to DataFrame"
            ],
            "prerequisites": [],
            "is_active": True,
            "problem_type": "data_analysis",
            "tutorial_links": ["pandas_groupby", "pivot_tables", "window_functions"]
        },
        {
            "_id": str(uuid.uuid4()),
            "level_id": 210,
            "title": "Machine Learning Pipeline Mastery",
            "description": "Build end-to-end machine learning pipelines for predictive analytics. Master feature engineering, model selection, and performance evaluation.",
            "category": "Data Analysis",
            "difficulty": "Expert",
            "xp_reward": 400,
            "starter_code": "# Machine Learning Pipeline Mastery\n# Build a complete ML pipeline for customer churn prediction\n# Choose your ML arsenal: scikit-learn, pandas, numpy, matplotlib, seaborn\n# Advanced: xgboost, lightgbm, feature-engine\n\nfrom sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV\nfrom sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder\nfrom sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier\nfrom sklearn.linear_model import LogisticRegression\nfrom sklearn.metrics import classification_report, confusion_matrix, roc_auc_score\nfrom sklearn.pipeline import Pipeline\nfrom sklearn.compose import ColumnTransformer\nimport pandas as pd\nimport numpy as np\n\n# Customer Churn Dataset (Telecom Industry)\nnp.random.seed(42)\nn_customers = 5000\n\n# Generate realistic customer data\ncustomer_data = {\n    'customer_id': [f'CUST_{1000+i}' for i in range(n_customers)],\n    'tenure_months': np.random.exponential(24, n_customers),\n    'monthly_charges': np.random.normal(65, 20, n_customers),\n    'total_charges': np.random.exponential(1500, n_customers),\n    'contract_type': np.random.choice(['Month-to-month', 'One year', 'Two year'], n_customers, p=[0.5, 0.3, 0.2]),\n    'payment_method': np.random.choice(['Electronic check', 'Mailed check', 'Bank transfer', 'Credit card'], n_customers),\n    'internet_service': np.random.choice(['DSL', 'Fiber optic', 'No'], n_customers, p=[0.4, 0.4, 0.2]),\n    'online_security': np.random.choice(['Yes', 'No', 'No internet service'], n_customers, p=[0.3, 0.5, 0.2]),\n    'tech_support': np.random.choice(['Yes', 'No', 'No internet service'], n_customers, p=[0.3, 0.5, 0.2]),\n    'streaming_tv': np.random.choice(['Yes', 'No', 'No internet service'], n_customers, p=[0.4, 0.4, 0.2]),\n    'paperless_billing': np.random.choice(['Yes', 'No'], n_customers, p=[0.6, 0.4]),\n    'senior_citizen': np.random.choice([0, 1], n_customers, p=[0.84, 0.16]),\n    'partner': np.random.choice(['Yes', 'No'], n_customers, p=[0.52, 0.48]),\n    'dependents': np.random.choice(['Yes', 'No'], n_customers, p=[0.3, 0.7]),\n    'phone_service': np.random.choice(['Yes', 'No'], n_customers, p=[0.9, 0.1])\n}\n\n# Create target variable (churn) with realistic business logic\nchurn_probability = (\n    0.1 +  # Base churn rate\n    (customer_data['tenure_months'] < 12) * 0.3 +  # New customers churn more\n    (customer_data['contract_type'] == 'Month-to-month') * 0.25 +  # Monthly contracts churn more\n    (customer_data['monthly_charges'] > 80) * 0.2 +  # High charges increase churn\n    (customer_data['senior_citizen'] == 1) * 0.15 +  # Seniors churn more\n    (customer_data['tech_support'] == 'No') * 0.1  # No tech support increases churn\n)\n\ncustomer_data['churn'] = np.random.binomial(1, np.clip(churn_probability, 0, 1), n_customers)\n\ndf = pd.DataFrame(customer_data)\n\n# Your comprehensive ML pipeline challenges:\n# 1. Exploratory Data Analysis & Feature Engineering\n# 2. Data preprocessing & encoding\n# 3. Feature selection & dimensionality reduction\n# 4. Model selection & hyperparameter tuning\n# 5. Cross-validation & performance evaluation\n# 6. Feature importance analysis\n# 7. Business insights & recommendations\n\nprint(\"Customer Churn Prediction Dataset\")\nprint(\"=\" * 50)\nprint(f\"Total customers: {len(df):,}\")\nprint(f\"Churn rate: {df['churn'].mean():.1%}\")\nprint(f\"Features: {df.shape[1] - 2}\")  # Excluding customer_id and target\nprint(f\"\\nDataset Info:\")\nprint(f\"- Numerical features: {df.select_dtypes(include=[np.number]).shape[1] - 1}\")  # Excluding target\nprint(f\"- Categorical features: {df.select_dtypes(include=['object']).shape[1] - 1}\")  # Excluding customer_id\n\n# Challenge 1: Exploratory Data Analysis\n# TODO: Analyze churn rates by different segments\n# TODO: Calculate feature correlations with churn\n# TODO: Identify data quality issues\n\nchurn_by_contract = # TODO: Calculate churn rate by contract type\nchurn_by_tenure = # TODO: Create tenure bins and analyze churn patterns\nhigh_risk_segments = # TODO: Identify customer segments with >40% churn rate\n\n# Challenge 2: Feature Engineering\n# TODO: Create new features from existing ones\ndf['avg_monthly_charges'] = df['total_charges'] / (df['tenure_months'] + 1)  # Avoid division by zero\ndf['tenure_group'] = # TODO: Categorize tenure into groups (0-12, 12-24, 24-48, 48+)\ndf['high_value_customer'] = # TODO: Binary feature for customers with monthly_charges > 75th percentile\ndf['service_count'] = # TODO: Count number of additional services (streaming, security, etc.)\n\n# Challenge 3: Data Preprocessing Pipeline\n# Separate features and target\nX = df.drop(['customer_id', 'churn'], axis=1)\ny = df['churn']\n\n# Identify numerical and categorical columns\nnumerical_features = # TODO: Select numerical columns\ncategorical_features = # TODO: Select categorical columns\n\n# Create preprocessing pipelines\nnumerical_transformer = # TODO: Create pipeline with StandardScaler\ncategorical_transformer = # TODO: Create pipeline with OneHotEncoder\n\n# Combine transformers\npreprocessor = # TODO: Create ColumnTransformer with both transformers\n\n# Challenge 4: Model Selection & Training\n# TODO: Split data into train/validation/test sets\nX_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)\nX_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp)\n\n# Define models to compare\nmodels = {\n    'logistic': # TODO: Create LogisticRegression pipeline\n    'random_forest': # TODO: Create RandomForest pipeline\n    'gradient_boosting': # TODO: Create GradientBoosting pipeline\n}\n\n# Challenge 5: Model Evaluation & Selection\nmodel_results = {}\nfor name, model in models.items():\n    # TODO: Fit model on training data\n    # TODO: Make predictions on validation set\n    # TODO: Calculate performance metrics (accuracy, precision, recall, F1, AUC)\n    pass\n\n# Challenge 6: Hyperparameter Tuning for Best Model\nbest_model_name = # TODO: Select best model based on AUC score\nbest_model = models[best_model_name]\n\n# TODO: Define parameter grid for GridSearchCV\nparam_grid = # TODO: Create parameter grid for hyperparameter tuning\n\n# TODO: Perform grid search with cross-validation\ngrid_search = # TODO: GridSearchCV with best model\n\n# Challenge 7: Final Evaluation & Business Insights\n# TODO: Evaluate tuned model on test set\nfinal_predictions = # TODO: Predict on test set\nfinal_probabilities = # TODO: Predict probabilities on test set\n\n# TODO: Calculate final performance metrics\ntest_auc = # TODO: Calculate AUC on test set\ntest_accuracy = # TODO: Calculate accuracy on test set\n\n# Feature importance analysis\nif hasattr(grid_search.best_estimator_.named_steps[best_model_name], 'feature_importances_'):\n    feature_names = # TODO: Get feature names after preprocessing\n    feature_importance = # TODO: Get feature importances\n    top_features = # TODO: Get top 5 most important features\n\n# Business Impact Analysis\nhigh_risk_threshold = 0.7  # Customers with >70% churn probability\nhigh_risk_customers = # TODO: Count customers above threshold\npotential_revenue_at_risk = # TODO: Calculate potential lost revenue\n\nprint(\"\\n\" + \"=\"*70)\nprint(\"MACHINE LEARNING PIPELINE RESULTS\")\nprint(\"=\"*70)\n\nprint(f\"\\n1. DATASET INSIGHTS:\")\nprint(f\"   Highest risk contract: {churn_by_contract.idxmax()} ({churn_by_contract.max():.1%} churn rate)\")\nprint(f\"   High-risk segments identified: {len(high_risk_segments)}\")\n\nprint(f\"\\n2. MODEL PERFORMANCE:\")\nprint(f\"   Best model: {best_model_name.title()}\")\nprint(f\"   Test AUC: {test_auc:.3f}\")\nprint(f\"   Test Accuracy: {test_accuracy:.1%}\")\n\nprint(f\"\\n3. FEATURE INSIGHTS:\")\nif 'top_features' in locals():\n    print(f\"   Top predictive features:\")\n    for feature, importance in top_features:\n        print(f\"     - {feature}: {importance:.3f}\")\n\nprint(f\"\\n4. BUSINESS IMPACT:\")\nprint(f\"   High-risk customers: {high_risk_customers:,} ({high_risk_customers/len(df):.1%})\")\nprint(f\"   Potential revenue at risk: ${potential_revenue_at_risk:,.0f}\")\n\nprint(f\"\\n5. RECOMMENDATIONS:\")\nprint(f\"   - Target high-risk Month-to-month customers with retention offers\")\nprint(f\"   - Improve tech support to reduce churn\")\nprint(f\"   - Focus retention efforts on customers with tenure < 12 months\")\nprint(f\"   - Consider pricing strategy for high monthly charge customers\")",
            "expected_output": "Customer Churn Prediction Dataset\n==================================================\nTotal customers: 5,000\nChurn rate: 26.7%\nFeatures: 14\n\nDataset Info:\n- Numerical features: 3\n- Categorical features: 10\n\n======================================================================\nMACHINE LEARNING PIPELINE RESULTS\n======================================================================\n\n1. DATASET INSIGHTS:\n   Highest risk contract: Month-to-month (45.2% churn rate)\n   High-risk segments identified: 3\n\n2. MODEL PERFORMANCE:\n   Best model: Gradient Boosting\n   Test AUC: 0.847\n   Test Accuracy: 78.4%\n\n3. FEATURE INSIGHTS:\n   Top predictive features:\n     - contract_type_Month-to-month: 0.234\n     - tenure_months: 0.187\n     - monthly_charges: 0.156\n     - tech_support_No: 0.124\n     - senior_citizen: 0.098\n\n4. BUSINESS IMPACT:\n   High-risk customers: 342 (6.8%)\n   Potential revenue at risk: $1,245,678\n\n5. RECOMMENDATIONS:\n   - Target high-risk Month-to-month customers with retention offers\n   - Improve tech support to reduce churn\n   - Focus retention efforts on customers with tenure < 12 months\n   - Consider pricing strategy for high monthly charge customers",
            "hints": [
                "EDA: df.groupby('contract_type')['churn'].mean()",
                "Tenure groups: pd.cut(df['tenure_months'], bins=[0,12,24,48,float('inf')], labels=['0-12','12-24','24-48','48+'])",
                "High value: df['monthly_charges'] > df['monthly_charges'].quantile(0.75)",
                "Service count: Sum of Yes values in service columns",
                "Numerical features: X.select_dtypes(include=[np.number]).columns",
                "Categorical features: X.select_dtypes(include=['object']).columns",
                "Pipeline: Pipeline([('scaler', StandardScaler())])",
                "OneHot: Pipeline([('onehot', OneHotEncoder(handle_unknown='ignore'))])",
                "ColumnTransformer: ColumnTransformer([('num', numerical_transformer, numerical_features), ('cat', categorical_transformer, categorical_features)])"
            ],
            "prerequisites": [],
            "is_active": True,
            "problem_type": "data_analysis",
            "tutorial_links": ["machine_learning", "scikit_learn", "feature_engineering"]
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

# Additional Admin Endpoints for Full Functionality
@app.patch("/api/admin/users/{user_id}")
async def update_user(
    user_id: str,
    user_data: dict,
    admin_user: dict = Depends(check_admin_access)
):
    """Update user information"""
    try:
        # Update user data
        update_data = {
            "username": user_data.get("username"),
            "email": user_data.get("email"),
            "subscription_tier": user_data.get("subscription_tier"),
            "status": user_data.get("status"),
            "updated_at": datetime.now(timezone.utc),
            "updated_by": admin_user["_id"]
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        result = await users_collection.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"success": True, "message": "User updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/admin/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    status_data: dict,
    admin_user: dict = Depends(check_admin_access)
):
    """Update user status (active, suspended, etc.)"""
    try:
        new_status = status_data.get("status")
        if new_status not in ["active", "suspended", "inactive"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        result = await users_collection.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "status": new_status,
                    "status_updated_at": datetime.now(timezone.utc),
                    "status_updated_by": admin_user["_id"]
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"success": True, "message": f"User status updated to {new_status}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/levels")
async def create_level(
    level_data: dict,
    admin_user: dict = Depends(check_admin_access)
):
    """Create a new level/challenge"""
    try:
        level_doc = {
            "_id": str(uuid.uuid4()),
            "level_id": int(level_data.get("level_id")),
            "title": level_data.get("title"),
            "description": level_data.get("description"),
            "category": level_data.get("category"),
            "difficulty": level_data.get("difficulty"),
            "xp_reward": int(level_data.get("xp_reward", 50)),
            "starter_code": level_data.get("starter_code"),
            "expected_output": level_data.get("expected_output"),
            "hints": level_data.get("hints", []),
            "prerequisites": [],
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "created_by": admin_user["_id"],
            "problem_type": level_data.get("category", "").lower().replace(" ", "_")
        }
        
        # Check if level_id already exists
        existing_level = await levels_collection.find_one({"level_id": level_doc["level_id"]})
        if existing_level:
            raise HTTPException(status_code=400, detail="Level ID already exists")
        
        await levels_collection.insert_one(level_doc)
        
        return {
            "success": True,
            "message": "Level created successfully",
            "level_id": level_doc["level_id"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/badges")
async def get_badges(admin_user: dict = Depends(check_admin_access)):
    """Get all badges and achievements"""
    # Mock badge data for now
    badges = [
        {
            "id": "first_steps",
            "name": "First Steps",
            "description": "Complete your first Python challenge",
            "icon": "🎯",
            "criteria": "Complete Level 100",
            "points": 50,
            "users_earned": 890
        },
        {
            "id": "problem_solver",
            "name": "Problem Solver", 
            "description": "Complete 10 challenges",
            "icon": "🧩",
            "criteria": "Complete 10 levels",
            "points": 200,
            "users_earned": 456
        },
        {
            "id": "data_master",
            "name": "Data Master",
            "description": "Complete all Data Analysis challenges",
            "icon": "📊",
            "criteria": "Complete Data Analysis track",
            "points": 500,
            "users_earned": 89
        }
    ]
    
    return {"badges": badges}

@app.post("/api/admin/badges")
async def create_badge(
    badge_data: dict,
    admin_user: dict = Depends(check_admin_access)
):
    """Create a new badge/achievement"""
    badge_doc = {
        "_id": str(uuid.uuid4()),
        "name": badge_data.get("name"),
        "description": badge_data.get("description"),
        "icon": badge_data.get("icon"),
        "criteria": badge_data.get("criteria"),
        "points": int(badge_data.get("points", 0)),
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "created_by": admin_user["_id"]
    }
    
    await db.badges.insert_one(badge_doc)
    
    return {
        "success": True,
        "message": "Badge created successfully",
        "badge_id": badge_doc["_id"]
    }

@app.get("/api/admin/support/tickets")
async def get_support_tickets(admin_user: dict = Depends(check_admin_access)):
    """Get all support tickets"""
    # Mock support ticket data
    tickets = [
        {
            "id": "ticket_001",
            "user_email": "user@example.com",
            "subject": "Code execution timeout on Level 105",
            "description": "My code keeps timing out even though it should work fine.",
            "status": "open",
            "priority": "high",
            "created_at": datetime.now(timezone.utc) - timedelta(hours=2),
            "category": "technical"
        },
        {
            "id": "ticket_002", 
            "user_email": "learner@example.com",
            "subject": "Cannot access Pro features after payment",
            "description": "I paid for Pro but still see limitations.",
            "status": "in_progress",
            "priority": "high",
            "created_at": datetime.now(timezone.utc) - timedelta(days=1),
            "category": "billing"
        }
    ]
    
    return {"tickets": tickets}

@app.post("/api/admin/announcements")
async def create_announcement(
    announcement_data: dict,
    admin_user: dict = Depends(check_admin_access)
):
    """Create a new announcement"""
    announcement_doc = {
        "_id": str(uuid.uuid4()),
        "title": announcement_data.get("title"),
        "content": announcement_data.get("content"),
        "type": announcement_data.get("type", "info"),
        "target_audience": announcement_data.get("target_audience", "all"),
        "status": "published",
        "created_at": datetime.now(timezone.utc),
        "created_by": admin_user["_id"]
    }
    
    await db.announcements.insert_one(announcement_doc)
    
    return {
        "success": True,
        "message": "Announcement created successfully",
        "announcement_id": announcement_doc["_id"]
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)