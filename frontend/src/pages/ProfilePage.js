import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import {
  User,
  Mail,
  Calendar,
  Trophy,
  Target,
  Zap,
  Award,
  TrendingUp,
  Clock,
  Code,
  Star,
  CheckCircle,
  Flame
} from 'lucide-react';
import axios from 'axios';

const ProfilePage = () => {
  const { currentUser, userStats } = useAuth();
  const [userProgress, setUserProgress] = useState({});
  const [loading, setLoading] = useState(true);
  const [achievements] = useState([
    { id: 1, name: 'First Steps', icon: '🎯', description: 'Complete your first level', earned: true, earnedAt: '2024-01-15' },
    { id: 2, name: 'Quick Learner', icon: '⚡', description: 'Complete 5 levels in one day', earned: false },
    { id: 3, name: 'Dedication', icon: '📚', description: 'Complete 10 levels', earned: userStats?.completed_levels >= 10 },
    { id: 4, name: 'Code Master', icon: '💻', description: 'Complete 25 levels', earned: userStats?.completed_levels >= 25 },
    { id: 5, name: 'Python Expert', icon: '🐍', description: 'Complete 50 levels', earned: userStats?.completed_levels >= 50 },
    { id: 6, name: 'Perfectionist', icon: '⭐', description: 'Get 3 stars on 10 levels', earned: false },
    { id: 7, name: 'Speed Runner', icon: '🏃', description: 'Complete a level in under 5 minutes', earned: false },
    { id: 8, name: 'Problem Solver', icon: '🧩', description: 'Complete all Easy levels', earned: false },
  ]);

  useEffect(() => {
    fetchUserProgress();
  }, []);

  const fetchUserProgress = async () => {
    try {
      const response = await axios.get('/api/user/progress');
      setUserProgress(response.data);
    } catch (error) {
      console.error('Failed to fetch user progress:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCurrentLevelProgress = () => {
    const currentLevel = userStats?.current_level || 100;
    const totalXP = userStats?.total_xp || 0;
    const baseXP = (currentLevel - 100) * 100;
    const currentLevelXP = totalXP - baseXP;
    return Math.min((currentLevelXP / 100) * 100, 100);
  };

  const getCompletedLevelsInCategory = (category) => {
    const categoryLevels = {
      'Python Basics': { start: 100, end: 149 },
      'Control Flow': { start: 150, end: 199 },
      'Data Structures': { start: 200, end: 249 },
      'Object-Oriented': { start: 250, end: 299 },
      'Libraries & APIs': { start: 300, end: 349 },
      'Projects': { start: 350, end: 400 }
    };

    const range = categoryLevels[category];
    if (!range) return { completed: 0, total: 0 };

    let completed = 0;
    const total = range.end - range.start + 1;

    for (let level = range.start; level <= range.end; level++) {
      if (userProgress[level]?.is_completed) {
        completed++;
      }
    }

    return { completed, total };
  };

  const getMemberSince = () => {
    if (!currentUser?.created_at) return 'Recently';
    const date = new Date(currentUser.created_at);
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  const getLastActive = () => {
    if (!currentUser?.last_login) return 'Recently';
    const date = new Date(currentUser.last_login);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Today';
    if (diffDays <= 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  const categories = [
    { name: 'Python Basics', color: 'bg-green-500', levels: '100-149' },
    { name: 'Control Flow', color: 'bg-blue-500', levels: '150-199' },
    { name: 'Data Structures', color: 'bg-purple-500', levels: '200-249' },
    { name: 'Object-Oriented', color: 'bg-orange-500', levels: '250-299' },
    { name: 'Libraries & APIs', color: 'bg-red-500', levels: '300-349' },
    { name: 'Projects', color: 'bg-indigo-500', levels: '350-400' }
  ];

  if (loading) {
    return (
      <div className=\"min-h-screen flex items-center justify-center\">
        <div className=\"animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500\"></div>
      </div>
    );
  }

  return (
    <div className=\"min-h-screen py-8 px-4 sm:px-6 lg:px-8\">
      <div className=\"max-w-6xl mx-auto\">
        {/* Profile Header */}
        <Card className=\"glass-card border-0 mb-8\">
          <CardContent className=\"pt-6\">
            <div className=\"flex flex-col md:flex-row items-start md:items-center space-y-4 md:space-y-0 md:space-x-6\">
              <Avatar className=\"h-24 w-24\">
                <AvatarFallback className=\"bg-gradient-to-br from-orange-400 to-amber-500 text-white text-3xl font-bold\">
                  {currentUser?.username?.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              
              <div className=\"flex-1\">
                <div className=\"flex flex-col md:flex-row md:items-center md:justify-between\">
                  <div>
                    <h1 className=\"text-3xl font-bold text-gray-900 mb-1\" data-testid=\"profile-username\">
                      {currentUser?.username}
                    </h1>
                    <div className=\"flex items-center space-x-4 text-sm text-gray-600 mb-4\">
                      <div className=\"flex items-center space-x-1\">
                        <Mail className=\"h-4 w-4\" />
                        <span>{currentUser?.email}</span>
                      </div>
                      <div className=\"flex items-center space-x-1\">
                        <Calendar className=\"h-4 w-4\" />
                        <span>Member since {getMemberSince()}</span>
                      </div>
                      <div className=\"flex items-center space-x-1\">
                        <Clock className=\"h-4 w-4\" />
                        <span>Last active {getLastActive()}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className=\"text-right\">
                    <div className=\"text-2xl font-bold gradient-text\" data-testid=\"profile-level\">
                      Level {userStats?.current_level || 100}
                    </div>
                    <div className=\"text-sm text-gray-600 mb-2\">
                      {userStats?.total_xp || 0} XP Total
                    </div>
                    <Progress value={getCurrentLevelProgress()} className=\"w-32\" />
                    <div className=\"text-xs text-gray-500 mt-1\">
                      {Math.round(getCurrentLevelProgress())}% to next level
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className=\"grid lg:grid-cols-3 gap-8\">
          {/* Stats Overview */}
          <div className=\"lg:col-span-2 space-y-6\">
            {/* Quick Stats */}
            <div className=\"grid grid-cols-2 md:grid-cols-4 gap-4\">
              <Card className=\"glass-card border-0 text-center\">
                <CardContent className=\"pt-4\">
                  <div className=\"flex justify-center mb-2\">
                    <Target className=\"h-8 w-8 text-orange-500\" />
                  </div>
                  <div className=\"text-2xl font-bold text-gray-900\" data-testid=\"stats-completed\">
                    {userStats?.completed_levels || 0}
                  </div>
                  <div className=\"text-sm text-gray-600\">Completed</div>
                </CardContent>
              </Card>

              <Card className=\"glass-card border-0 text-center\">
                <CardContent className=\"pt-4\">
                  <div className=\"flex justify-center mb-2\">
                    <Zap className=\"h-8 w-8 text-amber-500\" />
                  </div>
                  <div className=\"text-2xl font-bold text-gray-900\" data-testid=\"stats-xp\">
                    {userStats?.total_xp || 0}
                  </div>
                  <div className=\"text-sm text-gray-600\">Total XP</div>
                </CardContent>
              </Card>

              <Card className=\"glass-card border-0 text-center\">
                <CardContent className=\"pt-4\">
                  <div className=\"flex justify-center mb-2\">
                    <Flame className=\"h-8 w-8 text-red-500\" />
                  </div>
                  <div className=\"text-2xl font-bold text-gray-900\">
                    {userStats?.streak || 0}
                  </div>
                  <div className=\"text-sm text-gray-600\">Day Streak</div>
                </CardContent>
              </Card>

              <Card className=\"glass-card border-0 text-center\">
                <CardContent className=\"pt-4\">
                  <div className=\"flex justify-center mb-2\">
                    <Award className=\"h-8 w-8 text-purple-500\" />
                  </div>
                  <div className=\"text-2xl font-bold text-gray-900\" data-testid=\"stats-badges\">
                    {userStats?.badges?.length || 0}
                  </div>
                  <div className=\"text-sm text-gray-600\">Badges</div>
                </CardContent>
              </Card>
            </div>

            {/* Learning Progress */}
            <Card className=\"glass-card border-0\">
              <CardHeader>
                <CardTitle className=\"flex items-center space-x-2\">
                  <TrendingUp className=\"h-5 w-5 text-blue-500\" />
                  <span>Learning Progress</span>
                </CardTitle>
                <CardDescription>
                  Track your progress across different Python topics
                </CardDescription>
              </CardHeader>
              <CardContent className=\"space-y-4\">
                {categories.map((category) => {
                  const progress = getCompletedLevelsInCategory(category.name);
                  const percentage = progress.total > 0 ? (progress.completed / progress.total) * 100 : 0;
                  
                  return (
                    <div key={category.name} className=\"space-y-2\">
                      <div className=\"flex items-center justify-between\">
                        <div className=\"flex items-center space-x-3\">
                          <div className={`w-3 h-3 rounded-full ${category.color}`}></div>
                          <span className=\"font-medium\">{category.name}</span>
                          <Badge variant=\"outline\" className=\"text-xs\">
                            Levels {category.levels}
                          </Badge>
                        </div>
                        <span className=\"text-sm text-gray-600\">
                          {progress.completed}/{progress.total}
                        </span>
                      </div>
                      <Progress value={percentage} className=\"h-2\" />
                    </div>
                  );
                })}
              </CardContent>
            </Card>

            {/* Recent Achievements */}
            {userStats?.badges && userStats.badges.length > 0 && (
              <Card className=\"glass-card border-0\">
                <CardHeader>
                  <CardTitle className=\"flex items-center space-x-2\">
                    <Trophy className=\"h-5 w-5 text-amber-500\" />
                    <span>Recent Achievements</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className=\"space-y-3\">
                  {userStats.badges.map((badge, index) => (
                    <div key={index} className=\"flex items-center space-x-4 p-3 rounded-lg bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-100\">
                      <div className=\"text-3xl\">{badge.icon}</div>
                      <div className=\"flex-1\">
                        <h4 className=\"font-semibold text-gray-900\">{badge.name}</h4>
                        <p className=\"text-sm text-gray-600\">Earned recently</p>
                      </div>
                      <CheckCircle className=\"h-5 w-5 text-green-500\" />
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className=\"space-y-6\">
            {/* All Achievements */}
            <Card className=\"glass-card border-0\">
              <CardHeader>
                <CardTitle className=\"flex items-center space-x-2\">
                  <Award className=\"h-5 w-5 text-purple-500\" />
                  <span>All Achievements</span>
                </CardTitle>
                <CardDescription>
                  {achievements.filter(a => a.earned).length} of {achievements.length} unlocked
                </CardDescription>
              </CardHeader>
              <CardContent className=\"space-y-3\">
                {achievements.map((achievement) => (
                  <div 
                    key={achievement.id} 
                    className={`flex items-center space-x-3 p-3 rounded-lg border transition-all ${
                      achievement.earned 
                        ? 'bg-green-50 border-green-200' 
                        : 'bg-gray-50 border-gray-200 opacity-60'
                    }`}
                  >
                    <div className=\"text-2xl\">{achievement.icon}</div>
                    <div className=\"flex-1\">
                      <h4 className={`font-medium ${
                        achievement.earned ? 'text-gray-900' : 'text-gray-500'
                      }`}>
                        {achievement.name}
                      </h4>
                      <p className={`text-xs ${
                        achievement.earned ? 'text-gray-600' : 'text-gray-400'
                      }`}>
                        {achievement.description}
                      </p>
                    </div>
                    {achievement.earned && (
                      <CheckCircle className=\"h-4 w-4 text-green-500 flex-shrink-0\" />
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card className=\"glass-card border-0\">
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className=\"space-y-3\">
                <Button variant=\"outline\" className=\"w-full justify-start\">
                  <Code className=\"mr-2 h-4 w-4\" />
                  Continue Learning
                </Button>
                <Button variant=\"outline\" className=\"w-full justify-start\">
                  <Trophy className=\"mr-2 h-4 w-4\" />
                  View Leaderboard
                </Button>
                <Separator />
                <Button variant=\"outline\" className=\"w-full justify-start text-gray-500\" disabled>
                  <User className=\"mr-2 h-4 w-4\" />
                  Edit Profile (Coming Soon)
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;"