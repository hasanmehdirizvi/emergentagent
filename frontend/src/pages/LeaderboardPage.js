import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { Progress } from '../components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Trophy,
  Medal,
  Crown,
  Star,
  TrendingUp,
  Users,
  Zap,
  Target,
  Award,
  Calendar,
  Flame
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const LeaderboardPage = () => {
  const { currentUser, userStats } = useAuth();
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState('all-time');
  
  // Mock data for weekly and monthly leaderboards
  const [weeklyLeaders] = useState([
    { rank: 1, username: 'PythonMaster', total_xp: 2450, completed_levels: 45, current_level: 145, weekly_xp: 850 },
    { rank: 2, username: 'CodeNinja', total_xp: 2200, completed_levels: 38, current_level: 138, weekly_xp: 720 },
    { rank: 3, username: 'DevQueen', total_xp: 1980, completed_levels: 35, current_level: 135, weekly_xp: 680 },
    { rank: 4, username: 'ByteWizard', total_xp: 1750, completed_levels: 32, current_level: 132, weekly_xp: 620 },
    { rank: 5, username: 'AlgoExpert', total_xp: 1600, completed_levels: 28, current_level: 128, weekly_xp: 580 }
  ]);

  const [monthlyLeaders] = useState([
    { rank: 1, username: 'CodeMaster', total_xp: 3200, completed_levels: 58, current_level: 158, monthly_xp: 1200 },
    { rank: 2, username: 'PythonGuru', total_xp: 2980, completed_levels: 52, current_level: 152, monthly_xp: 1150 },
    { rank: 3, username: 'DevLegend', total_xp: 2750, completed_levels: 48, current_level: 148, monthly_xp: 1080 },
    { rank: 4, username: 'ByteMaster', total_xp: 2500, completed_levels: 44, current_level: 144, monthly_xp: 980 },
    { rank: 5, username: 'CodeCrusher', total_xp: 2300, completed_levels: 41, current_level: 141, monthly_xp: 920 }
  ]);

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const fetchLeaderboard = async () => {
    try {
      const response = await axios.get('/api/leaderboard?limit=50');
      setLeaderboard(response.data);
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
      toast.error('Failed to load leaderboard');
      // Use mock data as fallback
      setLeaderboard([
        { rank: 1, username: 'PythonPro', total_xp: 3500, completed_levels: 62, current_level: 162 },
        { rank: 2, username: 'CodeChamp', total_xp: 3200, completed_levels: 58, current_level: 158 },
        { rank: 3, username: 'DevExpert', total_xp: 2950, completed_levels: 54, current_level: 154 },
        { rank: 4, username: 'ByteHero', total_xp: 2750, completed_levels: 50, current_level: 150 },
        { rank: 5, username: 'AlgoWiz', total_xp: 2500, completed_levels: 46, current_level: 146 }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getCurrentUserRank = () => {
    const userEntry = leaderboard.find(entry => entry.username === currentUser?.username);
    return userEntry?.rank || leaderboard.length + 1;
  };

  const getRankIcon = (rank) => {
    switch (rank) {
      case 1:
        return <Crown className=\"h-6 w-6 text-yellow-500\" />;
      case 2:
        return <Medal className=\"h-6 w-6 text-gray-400\" />;
      case 3:
        return <Medal className=\"h-6 w-6 text-amber-600\" />;
      default:
        return (
          <div className=\"h-6 w-6 rounded-full bg-gray-200 flex items-center justify-center text-sm font-bold text-gray-600\">
            {rank}
          </div>
        );
    }
  };

  const getRankBadge = (rank) => {
    if (rank <= 3) {
      return (
        <Badge className={`${
          rank === 1 ? 'bg-gradient-to-r from-yellow-400 to-yellow-600 text-yellow-900' :
          rank === 2 ? 'bg-gradient-to-r from-gray-300 to-gray-500 text-gray-900' :
          'bg-gradient-to-r from-amber-400 to-amber-600 text-amber-900'
        } font-bold`}>
          #{rank}
        </Badge>
      );
    }
    return <Badge variant=\"outline\">#{rank}</Badge>;
  };

  const getLeaderboardData = () => {
    switch (timeframe) {
      case 'weekly':
        return weeklyLeaders;
      case 'monthly':
        return monthlyLeaders;
      default:
        return leaderboard;
    }
  };

  const getXPLabel = () => {
    switch (timeframe) {
      case 'weekly':
        return 'Weekly XP';
      case 'monthly':
        return 'Monthly XP';
      default:
        return 'Total XP';
    }
  };

  const getXPValue = (entry) => {
    switch (timeframe) {
      case 'weekly':
        return entry.weekly_xp || entry.total_xp;
      case 'monthly':
        return entry.monthly_xp || entry.total_xp;
      default:
        return entry.total_xp;
    }
  };

  if (loading) {
    return (
      <div className=\"min-h-screen flex items-center justify-center\">
        <div className=\"animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500\"></div>
      </div>
    );
  }

  const data = getLeaderboardData();

  return (
    <div className=\"min-h-screen py-8 px-4 sm:px-6 lg:px-8\">
      <div className=\"max-w-6xl mx-auto\">
        {/* Header */}
        <div className=\"text-center mb-8\">
          <div className=\"flex justify-center mb-4\">
            <div className=\"p-3 rounded-full bg-gradient-to-br from-amber-400 to-yellow-500\">
              <Trophy className=\"h-8 w-8 text-white\" />
            </div>
          </div>
          <h1 className=\"text-4xl font-bold gradient-text mb-2\">Leaderboard</h1>
          <p className=\"text-gray-600 max-w-2xl mx-auto\">
            Compete with fellow Python learners and climb your way to the top!
          </p>
        </div>

        <div className=\"grid lg:grid-cols-4 gap-8\">
          {/* Main Leaderboard */}
          <div className=\"lg:col-span-3\">
            {/* Timeframe Selector */}
            <Tabs value={timeframe} onValueChange={setTimeframe} className=\"mb-6\">
              <TabsList className=\"grid w-full grid-cols-3\">
                <TabsTrigger value=\"all-time\" data-testid=\"tab-all-time\">
                  <Trophy className=\"mr-2 h-4 w-4\" />
                  All Time
                </TabsTrigger>
                <TabsTrigger value=\"monthly\" data-testid=\"tab-monthly\">
                  <Calendar className=\"mr-2 h-4 w-4\" />
                  This Month
                </TabsTrigger>
                <TabsTrigger value=\"weekly\" data-testid=\"tab-weekly\">
                  <Flame className=\"mr-2 h-4 w-4\" />
                  This Week
                </TabsTrigger>
              </TabsList>
            </Tabs>

            {/* Top 3 Podium */}
            <div className=\"grid md:grid-cols-3 gap-4 mb-8\">
              {data.slice(0, 3).map((entry, index) => {
                const actualRank = entry.rank || index + 1;
                return (
                  <Card 
                    key={entry.username} 
                    className={`glass-card border-0 text-center relative overflow-hidden ${
                      actualRank === 1 ? 'ring-2 ring-yellow-400 bg-gradient-to-br from-yellow-50 to-amber-50' :
                      actualRank === 2 ? 'ring-2 ring-gray-400 bg-gradient-to-br from-gray-50 to-slate-50' :
                      'ring-2 ring-amber-400 bg-gradient-to-br from-amber-50 to-orange-50'
                    }`}
                    data-testid={`podium-${actualRank}`}
                  >
                    {/* Crown/Medal decoration */}
                    <div className=\"absolute top-2 right-2\">
                      {getRankIcon(actualRank)}
                    </div>
                    
                    <CardContent className=\"pt-6 pb-4\">
                      <div className=\"mb-4\">
                        <Avatar className=\"h-16 w-16 mx-auto mb-3\">
                          <AvatarFallback className={`text-white text-xl font-bold ${
                            actualRank === 1 ? 'bg-gradient-to-br from-yellow-400 to-yellow-600' :
                            actualRank === 2 ? 'bg-gradient-to-br from-gray-400 to-gray-600' :
                            'bg-gradient-to-br from-amber-400 to-amber-600'
                          }`}>
                            {entry.username.charAt(0).toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <h3 className=\"font-bold text-lg mb-1\">{entry.username}</h3>
                        <p className=\"text-sm text-gray-600\">Level {entry.current_level}</p>
                      </div>
                      
                      <div className=\"space-y-2\">
                        <div className=\"text-2xl font-bold gradient-text\">
                          {getXPValue(entry).toLocaleString()}
                        </div>
                        <div className=\"text-xs text-gray-500\">{getXPLabel()}</div>
                        <div className=\"text-sm text-gray-600\">
                          {entry.completed_levels} levels completed
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {/* Full Leaderboard */}
            <Card className=\"glass-card border-0\">
              <CardHeader>
                <CardTitle className=\"flex items-center space-x-2\">
                  <Users className=\"h-5 w-5 text-blue-500\" />
                  <span>Full Rankings</span>
                </CardTitle>
                <CardDescription>
                  Complete leaderboard for {timeframe.replace('-', ' ')} performance
                </CardDescription>
              </CardHeader>
              <CardContent className=\"p-0\">
                <div className=\"divide-y divide-gray-100\">
                  {data.map((entry, index) => {
                    const actualRank = entry.rank || index + 1;
                    const isCurrentUser = entry.username === currentUser?.username;
                    
                    return (
                      <div
                        key={entry.username}
                        className={`flex items-center justify-between p-4 hover:bg-gray-50 transition-colors ${
                          isCurrentUser ? 'bg-orange-50 border-l-4 border-orange-400' : ''
                        }`}
                        data-testid={`leaderboard-entry-${actualRank}`}
                      >
                        <div className=\"flex items-center space-x-4\">
                          <div className=\"flex items-center space-x-3\">
                            {getRankBadge(actualRank)}
                            <Avatar className=\"h-10 w-10\">
                              <AvatarFallback className=\"bg-gradient-to-br from-gray-400 to-gray-600 text-white font-bold\">
                                {entry.username.charAt(0).toUpperCase()}
                              </AvatarFallback>
                            </Avatar>
                          </div>
                          <div>
                            <div className=\"flex items-center space-x-2\">
                              <span className=\"font-semibold text-gray-900\">
                                {entry.username}
                              </span>
                              {isCurrentUser && (
                                <Badge variant=\"outline\" className=\"text-xs\">
                                  You
                                </Badge>
                              )}
                            </div>
                            <div className=\"text-sm text-gray-600\">
                              Level {entry.current_level} • {entry.completed_levels} completed
                            </div>
                          </div>
                        </div>
                        
                        <div className=\"text-right\">
                          <div className=\"font-bold text-gray-900\">
                            {getXPValue(entry).toLocaleString()} XP
                          </div>
                          <div className=\"text-xs text-gray-500\">
                            {getXPLabel()}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className=\"space-y-6\">
            {/* User Position */}
            <Card className=\"glass-card border-0\">
              <CardHeader>
                <CardTitle className=\"flex items-center space-x-2\">
                  <Target className=\"h-5 w-5 text-orange-500\" />
                  <span>Your Position</span>
                </CardTitle>
              </CardHeader>
              <CardContent className=\"text-center\">
                <div className=\"mb-4\">
                  <Avatar className=\"h-16 w-16 mx-auto mb-3\">
                    <AvatarFallback className=\"bg-gradient-to-br from-orange-400 to-amber-500 text-white text-2xl font-bold\">
                      {currentUser?.username?.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <h3 className=\"font-bold text-lg\">{currentUser?.username}</h3>
                </div>
                
                <div className=\"space-y-3\">
                  <div>
                    <div className=\"text-3xl font-bold gradient-text\" data-testid=\"user-rank\">
                      #{getCurrentUserRank()}
                    </div>
                    <div className=\"text-sm text-gray-600\">Current Rank</div>
                  </div>
                  
                  <div className=\"grid grid-cols-2 gap-3 text-center\">
                    <div>
                      <div className=\"font-bold text-gray-900\">{userStats?.total_xp || 0}</div>
                      <div className=\"text-xs text-gray-500\">Total XP</div>
                    </div>
                    <div>
                      <div className=\"font-bold text-gray-900\">{userStats?.completed_levels || 0}</div>
                      <div className=\"text-xs text-gray-500\">Completed</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Achievements */}
            <Card className=\"glass-card border-0\">
              <CardHeader>
                <CardTitle className=\"flex items-center space-x-2\">
                  <Award className=\"h-5 w-5 text-purple-500\" />
                  <span>Top Achievements</span>
                </CardTitle>
              </CardHeader>
              <CardContent className=\"space-y-3\">
                {userStats?.badges && userStats.badges.length > 0 ? (
                  userStats.badges.slice(0, 3).map((badge, index) => (
                    <div key={index} className=\"flex items-center space-x-3 p-2 rounded-lg bg-purple-50\">
                      <div className=\"text-xl\">{badge.icon}</div>
                      <div>
                        <p className=\"font-medium text-sm\">{badge.name}</p>
                        <p className=\"text-xs text-gray-500\">Recently earned</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className=\"text-center text-gray-500 py-4\">
                    <Award className=\"h-8 w-8 mx-auto mb-2 opacity-50\" />
                    <p className=\"text-sm\">Complete levels to earn badges!</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Leaderboard Stats */}
            <Card className=\"glass-card border-0\">
              <CardHeader>
                <CardTitle className=\"flex items-center space-x-2\">
                  <TrendingUp className=\"h-5 w-5 text-green-500\" />
                  <span>Community Stats</span>
                </CardTitle>
              </CardHeader>
              <CardContent className=\"space-y-4\">
                <div className=\"text-center\">
                  <div className=\"text-2xl font-bold text-gray-900\">{data.length}</div>
                  <div className=\"text-sm text-gray-600\">Active Learners</div>
                </div>
                
                <div className=\"space-y-3\">
                  <div className=\"flex justify-between items-center\">
                    <span className=\"text-sm text-gray-600\">Avg Level:</span>
                    <span className=\"font-medium\">
                      {Math.round(data.reduce((acc, entry) => acc + entry.current_level, 0) / data.length) || 100}
                    </span>
                  </div>
                  <div className=\"flex justify-between items-center\">
                    <span className=\"text-sm text-gray-600\">Top XP:</span>
                    <span className=\"font-medium\">
                      {data[0]?.total_xp?.toLocaleString() || '0'}
                    </span>
                  </div>
                  <div className=\"flex justify-between items-center\">
                    <span className=\"text-sm text-gray-600\">Total Completions:</span>
                    <span className=\"font-medium\">
                      {data.reduce((acc, entry) => acc + entry.completed_levels, 0).toLocaleString()}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeaderboardPage;"