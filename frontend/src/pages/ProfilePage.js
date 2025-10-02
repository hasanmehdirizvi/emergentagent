import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { Badge } from '../components/ui/badge';
import {
  User,
  Mail,
  Calendar,
  Trophy,
  Target,
  Zap,
  Award,
  Clock,
  Code,
  CheckCircle
} from 'lucide-react';
import axios from 'axios';

const ProfilePage = () => {
  const { currentUser, userStats } = useAuth();
  const [userProgress, setUserProgress] = useState({});
  const [loading, setLoading] = useState(true);

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

  const getMemberSince = () => {
    if (!currentUser?.created_at) return 'Recently';
    const date = new Date(currentUser.created_at);
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  const categories = [
    { name: 'Python Basics', color: 'bg-green-500', levels: '100-149' },
    { name: 'Control Flow', color: 'bg-blue-500', levels: '150-199' },
    { name: 'Data Structures', color: 'bg-purple-500', levels: '200-249' },
    { name: 'Object-Oriented', color: 'bg-orange-500', levels: '250-299' },
    { name: 'Libraries and APIs', color: 'bg-red-500', levels: '300-349' },
    { name: 'Projects', color: 'bg-indigo-500', levels: '350-400' }
  ];

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        <Card className="glass-card border-0 mb-8">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row items-start md:items-center space-y-4 md:space-y-0 md:space-x-6">
              <Avatar className="h-24 w-24">
                <AvatarFallback className="bg-gradient-to-br from-orange-400 to-amber-500 text-white text-3xl font-bold">
                  {currentUser?.username?.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              
              <div className="flex-1">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                  <div>
                    <h1 className="text-3xl font-bold text-gray-900 mb-1" data-testid="profile-username">
                      {currentUser?.username}
                    </h1>
                    <div className="flex items-center space-x-4 text-sm text-gray-600 mb-4">
                      <div className="flex items-center space-x-1">
                        <Mail className="h-4 w-4" />
                        <span>{currentUser?.email}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Calendar className="h-4 w-4" />
                        <span>Member since {getMemberSince()}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-2xl font-bold gradient-text" data-testid="profile-level">
                      Level {userStats?.current_level || 100}
                    </div>
                    <div className="text-sm text-gray-600 mb-2">
                      {userStats?.total_xp || 0} XP Total
                    </div>
                    <Progress value={getCurrentLevelProgress()} className="w-32" />
                    <div className="text-xs text-gray-500 mt-1">
                      {Math.round(getCurrentLevelProgress())}% to next level
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="glass-card border-0 text-center">
                <CardContent className="pt-4">
                  <div className="flex justify-center mb-2">
                    <Target className="h-8 w-8 text-orange-500" />
                  </div>
                  <div className="text-2xl font-bold text-gray-900" data-testid="stats-completed">
                    {userStats?.completed_levels || 0}
                  </div>
                  <div className="text-sm text-gray-600">Completed</div>
                </CardContent>
              </Card>

              <Card className="glass-card border-0 text-center">
                <CardContent className="pt-4">
                  <div className="flex justify-center mb-2">
                    <Zap className="h-8 w-8 text-amber-500" />
                  </div>
                  <div className="text-2xl font-bold text-gray-900" data-testid="stats-xp">
                    {userStats?.total_xp || 0}
                  </div>
                  <div className="text-sm text-gray-600">Total XP</div>
                </CardContent>
              </Card>

              <Card className="glass-card border-0 text-center">
                <CardContent className="pt-4">
                  <div className="flex justify-center mb-2">
                    <Clock className="h-8 w-8 text-red-500" />
                  </div>
                  <div className="text-2xl font-bold text-gray-900">
                    {userStats?.streak || 0}
                  </div>
                  <div className="text-sm text-gray-600">Day Streak</div>
                </CardContent>
              </Card>

              <Card className="glass-card border-0 text-center">
                <CardContent className="pt-4">
                  <div className="flex justify-center mb-2">
                    <Award className="h-8 w-8 text-purple-500" />
                  </div>
                  <div className="text-2xl font-bold text-gray-900" data-testid="stats-badges">
                    {userStats?.badges?.length || 0}
                  </div>
                  <div className="text-sm text-gray-600">Badges</div>
                </CardContent>
              </Card>
            </div>

            <Card className="glass-card border-0">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Code className="h-5 w-5 text-blue-500" />
                  <span>Learning Progress</span>
                </CardTitle>
                <CardDescription>
                  Track your progress across different Python topics
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {categories.map((category) => {
                  const percentage = Math.random() * 100; // Mock progress
                  
                  return (
                    <div key={category.name} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className={`w-3 h-3 rounded-full ${category.color}`}></div>
                          <span className="font-medium">{category.name}</span>
                          <Badge variant="outline" className="text-xs">
                            Levels {category.levels}
                          </Badge>
                        </div>
                        <span className="text-sm text-gray-600">
                          {Math.round(percentage)}%
                        </span>
                      </div>
                      <Progress value={percentage} className="h-2" />
                    </div>
                  );
                })}
              </CardContent>
            </Card>

            {userStats?.badges && userStats.badges.length > 0 && (
              <Card className="glass-card border-0">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Trophy className="h-5 w-5 text-amber-500" />
                    <span>Recent Achievements</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {userStats.badges.map((badge, index) => (
                    <div key={index} className="flex items-center space-x-4 p-3 rounded-lg bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-100">
                      <div className="text-3xl">{badge.icon}</div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900">{badge.name}</h4>
                        <p className="text-sm text-gray-600">Earned recently</p>
                      </div>
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>

          <div className="space-y-6">
            <Card className="glass-card border-0">
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button variant="outline" className="w-full justify-start">
                  <Code className="mr-2 h-4 w-4" />
                  Continue Learning
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <Trophy className="mr-2 h-4 w-4" />
                  View Leaderboard
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;