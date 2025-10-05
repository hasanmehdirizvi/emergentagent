import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { 
  Code, 
  Trophy, 
  Target, 
  Zap, 
  BookOpen, 
  Star, 
  Play, 
  Lock, 
  CheckCircle,
  Filter,
  BarChart3
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const DashboardPage = () => {
  const { currentUser, userStats } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [levels, setLevels] = useState([]);
  const [userProgress, setUserProgress] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    // Check URL parameters for category selection
    const urlParams = new URLSearchParams(location.search);
    const categoryParam = urlParams.get('category');
    if (categoryParam) {
      setSelectedCategory(categoryParam);
    }
    fetchDashboardData();
  }, [location.search]);

  const fetchDashboardData = async () => {
    try {
      const [levelsResponse, progressResponse] = await Promise.all([
        axios.get('/api/levels?limit=50'), // Increase limit to get more levels
        axios.get('/api/user/progress')
      ]);
      
      setLevels(levelsResponse.data);
      setUserProgress(progressResponse.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'Easy': return 'bg-green-100 text-green-800';
      case 'Medium': return 'bg-yellow-100 text-yellow-800';
      case 'Hard': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getCurrentLevelProgress = () => {
    const currentLevel = userStats?.current_level || 100;
    const totalXP = userStats?.total_xp || 0;
    const baseXP = (currentLevel - 100) * 100;
    const currentLevelXP = totalXP - baseXP;
    return Math.min((currentLevelXP / 100) * 100, 100);
  };

  // Filter levels by category and accessibility
  const filteredLevels = levels.filter(level => {
    const categoryMatch = selectedCategory === 'all' || level.category === selectedCategory;
    return categoryMatch;
  });

  // Further filter for available levels (accessible to user)
  const availableLevels = filteredLevels.filter(level => 
    level.level_id <= (userStats?.current_level || 100)
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            <Avatar className="h-16 w-16">
              <AvatarFallback className="bg-gradient-to-br from-orange-400 to-amber-500 text-white text-xl font-bold">
                {currentUser?.username?.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div>
              <h1 className="text-3xl font-bold text-gray-900" data-testid="welcome-message">
                Welcome back, {currentUser?.username}!
              </h1>
              <p className="text-gray-600">Ready to continue your Python journey?</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="glass-card border-0">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Current Level</CardTitle>
              <Target className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold" data-testid="current-level">
                Level {userStats?.current_level || 100}
              </div>
              <Progress value={getCurrentLevelProgress()} className="mt-2" />
              <p className="text-xs text-muted-foreground mt-1">
                {Math.round(getCurrentLevelProgress())}% to next level
              </p>
            </CardContent>
          </Card>

          <Card className="glass-card border-0">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total XP</CardTitle>
              <Zap className="h-4 w-4 text-amber-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold gradient-text" data-testid="total-xp">
                {userStats?.total_xp || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                Keep learning to earn more!
              </p>
            </CardContent>
          </Card>

          <Card className="glass-card border-0">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed Levels</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold" data-testid="completed-levels">
                {userStats?.completed_levels || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                of 300+ available levels
              </p>
            </CardContent>
          </Card>

          <Card className="glass-card border-0">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Badges Earned</CardTitle>
              <Trophy className="h-4 w-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold" data-testid="badges-count">
                {userStats?.badges?.length || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                Unlock more with progress
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-4">
                <h2 className="text-2xl font-bold">Continue Learning</h2>
                <div className="flex items-center space-x-2">
                  <Filter className="h-4 w-4 text-gray-500" />
                  <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                    <SelectTrigger className="w-48">
                      <SelectValue placeholder="Select Category" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Categories</SelectItem>
                      <SelectItem value="Python Basics">🐍 Python Basics</SelectItem>
                      <SelectItem value="Control Flow">🔄 Control Flow</SelectItem>
                      <SelectItem value="Data Analysis">📊 Data Analysis</SelectItem>
                      <SelectItem value="Comprehensive Project">🚀 Projects</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <Link to={`/level/${userStats?.current_level || 100}`}>
                <Button className="bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600">
                  <Play className="mr-2 h-4 w-4" />
                  Start Next Level
                </Button>
              </Link>
            </div>

            {selectedCategory === 'Data Analysis' && (
              <Card className="glass-card border-0 bg-gradient-to-r from-blue-50 to-indigo-50 mb-4">
                <CardContent className="pt-4">
                  <div className="flex items-center space-x-3">
                    <BarChart3 className="h-8 w-8 text-blue-500" />
                    <div>
                      <h3 className="text-lg font-semibold text-blue-900">Data Analysis Track</h3>
                      <p className="text-blue-700 text-sm">
                        Master data manipulation, statistics, and analysis with Python. Start with Level 200!
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            <div className="space-y-4">
              {availableLevels.length === 0 ? (
                <Card className="glass-card border-0">
                  <CardContent className="pt-6 text-center">
                    <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">
                      {selectedCategory === 'Data Analysis' 
                        ? 'Data Analysis Levels Coming Soon!' 
                        : 'No levels available in this category'}
                    </h3>
                    <p className="text-gray-600 text-sm mb-4">
                      {selectedCategory === 'Data Analysis'
                        ? 'Complete the Python Basics levels first to unlock Data Analysis challenges.'
                        : 'Try selecting a different category or continue with your current progress.'}
                    </p>
                    <Button
                      onClick={() => setSelectedCategory('all')}
                      variant="outline"
                    >
                      View All Levels
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                availableLevels.map((level) => {
                const progress = userProgress[level.level_id];
                const isCompleted = progress?.is_completed;
                const isLocked = level.level_id > (userStats?.current_level || 100);

                return (
                  <Card 
                    key={level.id} 
                    className={`level-card border-0 ${isCompleted ? 'bg-green-50/50' : ''}`}
                    data-testid={`level-${level.level_id}`}
                  >
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className={`p-2 rounded-lg ${
                            isCompleted ? 'bg-green-100' : 
                            isLocked ? 'bg-gray-100' : 'bg-orange-100'
                          }`}>
                            {isCompleted ? (
                              <CheckCircle className="h-5 w-5 text-green-600" />
                            ) : isLocked ? (
                              <Lock className="h-5 w-5 text-gray-400" />
                            ) : (
                              <Code className="h-5 w-5 text-orange-600" />
                            )}
                          </div>
                          <div>
                            <CardTitle className="text-lg">
                              Level {level.level_id}: {level.title}
                              {isCompleted && <CheckCircle className="inline ml-2 h-4 w-4 text-green-500" />}
                            </CardTitle>
                            <p className="text-sm text-gray-600">
                              {level.category} - {level.xp_reward} XP
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge className={getDifficultyColor(level.difficulty)}>
                            {level.difficulty}
                          </Badge>
                          {progress?.stars > 0 && (
                            <div className="flex">
                              {[...Array(3)].map((_, i) => (
                                <Star
                                  key={i}
                                  className={`h-4 w-4 ${
                                    i < progress.stars
                                      ? 'text-amber-400 fill-current'
                                      : 'text-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-gray-600 mb-4">{level.description}</p>
                      <div className="flex items-center justify-between">
                        <div className="text-sm text-gray-500">
                          {progress?.attempts > 0 && (
                            <span>{progress.attempts} attempt{progress.attempts !== 1 ? 's' : ''}</span>
                          )}
                        </div>
                        <Link to={`/level/${level.level_id}`}>
                          <Button 
                            variant={isCompleted ? "outline" : "default"}
                            disabled={isLocked}
                            className={!isCompleted && !isLocked ? 'bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600' : ''}
                            data-testid={`start-level-${level.level_id}`}
                          >
                            {isLocked ? (
                              <>
                                <Lock className="mr-2 h-4 w-4" />
                                Locked
                              </>
                            ) : isCompleted ? (
                              <>
                                <BookOpen className="mr-2 h-4 w-4" />
                                Review
                              </>
                            ) : (
                              <>
                                <Play className="mr-2 h-4 w-4" />
                                Start
                              </>
                            )}
                          </Button>
                        </Link>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>

          <div className="space-y-6">
            {userStats?.badges && userStats.badges.length > 0 && (
              <Card className="glass-card border-0">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Trophy className="h-5 w-5 text-amber-500" />
                    <span>Recent Badges</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {userStats.badges.slice(0, 3).map((badge, index) => (
                    <div key={index} className="flex items-center space-x-3 p-2 rounded-lg bg-amber-50">
                      <div className="text-2xl">{badge.icon}</div>
                      <div>
                        <p className="font-medium">{badge.name}</p>
                        <p className="text-xs text-gray-500">Earned recently</p>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;