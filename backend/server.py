from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import os
import jwt
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import logging

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
    rating: int  # 1-5 stars
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
            "starter_code": "# Welcome to Python! Type your code below\nprint(\"Hello, World!\")",
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
            "starter_code": "# Data Analysis with Lists\ndata = [85, 92, 78, 96, 85, 88, 79, 92, 88, 84]\n\n# Calculate mean\nmean = # Your code here\n\n# Find maximum and minimum\nmax_value = # Your code here\nmin_value = # Your code here\n\n# Print results\nprint(f\"Dataset: {data}\")\nprint(f\"Mean: {mean}\")\nprint(f\"Maximum: {max_value}\")\nprint(f\"Minimum: {min_value}\")",
            "expected_output": "Dataset: [85, 92, 78, 96, 85, 88, 79, 92, 88, 84]\nMean: 86.7\nMaximum: 96\nMinimum: 78",
            "hints": [
                "Use sum(data) to add all numbers in the list",
                "Use len(data) to get the count of items",
                "Mean = sum / count",
                "Use max(data) and min(data) for maximum and minimum",
                "Round the mean to 1 decimal place"
            ],
            "prerequisites": [104],
            "is_active": True,
            "problem_type": "data_analysis",
            "tutorial_links": ["lists", "functions", "statistics"]
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
    if current_user["username"] not in ["admin", "administrator"]:
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

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)