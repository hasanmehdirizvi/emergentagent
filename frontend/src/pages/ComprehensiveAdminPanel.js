import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import {
  LayoutDashboard,
  Users,
  BookOpen,
  Trophy,
  CreditCard,
  BarChart3,
  HeadphonesIcon,
  Settings,
  Search,
  Filter,
  Plus,
  Edit,
  Trash2,
  Eye,
  Ban,
  RefreshCw,
  Download,
  Mail,
  Bell,
  Shield,
  Award,
  Target,
  Zap,
  Crown,
  DollarSign,
  TrendingUp,
  Calendar,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Star,
  MessageSquare,
  Code,
  Play,
  Pause,
  RotateCcw,
  FileText,
  PieChart,
  Activity,
  UserCheck,
  UserX,
  Gift,
  Coins,
  Medal
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const ComprehensiveAdminPanel = () => {
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  
  // Navigation State
  const [activeSection, setActiveSection] = useState('dashboard');
  const [activeSubSection, setActiveSubSection] = useState('');
  const [loading, setLoading] = useState(true);

  // Dashboard State
  const [dashboardStats, setDashboardStats] = useState({
    totalUsers: 0,
    activeUsers: 0,
    totalRevenue: 0,
    challengesCompleted: 0,
    freeUsers: 0,
    proUsers: 0,
    enterpriseUsers: 0
  });

  // User Management State
  const [usersList, setUsersList] = useState([]);
  const [userFilters, setUserFilters] = useState({
    search: '',
    subscription: 'all',
    status: 'all',
    level: 'all'
  });
  const [selectedUsers, setSelectedUsers] = useState([]);

  // Subscription Management State
  const [subscriptionPlans, setSubscriptionPlans] = useState([
    { id: 'free', name: 'Free Plan', price: 0, features: ['Basic Challenges', 'Community Access'], users: 0 },
    { id: 'pro', name: 'Pro Plan', price: 9.99, features: ['All Challenges', 'Priority Support', 'Certificates'], users: 0 },
    { id: 'enterprise', name: 'Enterprise', price: 49.99, features: ['Custom Tracks', 'Team Management', 'API Access'], users: 0 }
  ]);
  const [transactions, setTransactions] = useState([]);
  const [revenueData, setRevenueData] = useState({});

  // Content Management State
  const [challenges, setChallenges] = useState([]);
  const [tracks, setTracks] = useState([]);
  const [showCreateChallenge, setShowCreateChallenge] = useState(false);
  const [challengeForm, setChallengeForm] = useState({
    title: '',
    description: '',
    difficulty: 'Easy',
    category: 'Python Basics',
    xp_reward: 50,
    starter_code: '',
    expected_output: '',
    hints: [''],
    test_cases: [{ input: '', expected_output: '' }]
  });

  // Analytics State
  const [analytics, setAnalytics] = useState({
    dailyActiveUsers: [],
    completionRates: {},
    popularChallenges: [],
    dropOffPoints: [],
    engagementMetrics: {}
  });

  // Support State
  const [supportTickets, setSupportTickets] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [showCreateAnnouncement, setShowCreateAnnouncement] = useState(false);

  // Admin Roles State
  const [adminUsers, setAdminUsers] = useState([]);
  const [showCreateAdmin, setShowCreateAdmin] = useState(false);

  useEffect(() => {
    // Check admin access
    if (!currentUser || !currentUser.username?.toLowerCase().includes('admin')) {
      toast.error('Admin access required');
      navigate('/dashboard');
      return;
    }
    
    initializeAdminData();
  }, [currentUser]);

  const initializeAdminData = async () => {
    try {
      setLoading(true);
      
      // Load dashboard data
      await loadDashboardStats();
      await loadUserData();
      await loadSubscriptionData();
      await loadContentData();
      await loadAnalyticsData();
      await loadSupportData();
      
    } catch (error) {
      console.error('Failed to load admin data:', error);
      toast.error('Failed to load admin data');
    } finally {
      setLoading(false);
    }
  };

  const loadDashboardStats = async () => {
    try {
      // Mock data - replace with actual API calls
      setDashboardStats({
        totalUsers: 1250,
        activeUsers: 950,
        totalRevenue: 5700,
        challengesCompleted: 3200,
        freeUsers: 800,
        proUsers: 400,
        enterpriseUsers: 50
      });
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
    }
  };

  const loadUserData = async () => {
    try {
      const response = await axios.get('/api/admin/users?limit=100');
      setUsersList(response.data.users || []);
    } catch (error) {
      console.error('Failed to load user data:', error);
      // Mock data for demonstration
      setUsersList([
        {
          _id: '1',
          username: 'john_doe',
          email: 'john@example.com',
          subscription: 'pro',
          status: 'active',
          current_level: 105,
          total_xp: 1250,
          created_at: new Date().toISOString(),
          last_login: new Date().toISOString()
        }
      ]);
    }
  };

  const loadSubscriptionData = async () => {
    try {
      // Mock subscription data
      setTransactions([
        {
          id: 'txn_001',
          user: 'john@example.com',
          plan: 'Pro Plan',
          amount: 9.99,
          status: 'completed',
          date: new Date().toISOString()
        }
      ]);

      setRevenueData({
        mrr: 4500,
        arr: 54000,
        churnRate: 5.2,
        trialConversion: 68.5
      });
    } catch (error) {
      console.error('Failed to load subscription data:', error);
    }
  };

  const loadContentData = async () => {
    try {
      const response = await axios.get('/api/levels?limit=50');
      setChallenges(response.data || []);
      
      // Mock tracks data
      setTracks([
        { id: 'python-basics', name: 'Python Basics', challenges: 10, difficulty: 'Beginner' },
        { id: 'data-analysis', name: 'Data Analysis', challenges: 8, difficulty: 'Intermediate' }
      ]);
    } catch (error) {
      console.error('Failed to load content data:', error);
    }
  };

  const loadAnalyticsData = async () => {
    try {
      // Mock analytics data
      setAnalytics({
        dailyActiveUsers: [120, 135, 142, 128, 156, 143, 167],
        completionRates: {
          'python-basics': 78.5,
          'data-analysis': 65.2
        },
        popularChallenges: [
          { id: 100, title: 'Hello World', completions: 890 },
          { id: 101, title: 'Variables', completions: 756 }
        ],
        dropOffPoints: [
          { level: 103, dropRate: 15.2 },
          { level: 200, dropRate: 23.1 }
        ]
      });
    } catch (error) {
      console.error('Failed to load analytics data:', error);
    }
  };

  const loadSupportData = async () => {
    try {
      // Mock support data
      setSupportTickets([
        {
          id: 'ticket_001',
          user: 'user@example.com',
          subject: 'Code execution timeout',
          status: 'open',
          priority: 'high',
          created_at: new Date().toISOString()
        }
      ]);

      setAnnouncements([
        {
          id: 'ann_001',
          title: 'New Data Analysis Track Released!',
          content: 'We\'ve added 10 new challenges focused on data analysis.',
          status: 'published',
          created_at: new Date().toISOString()
        }
      ]);
    } catch (error) {
      console.error('Failed to load support data:', error);
    }
  };

  // Navigation items
  const navigationItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      subsections: []
    },
    {
      id: 'users',
      label: 'Users',
      icon: Users,
      subsections: [
        { id: 'all-users', label: 'All Users' },
        { id: 'achievements', label: 'Achievements' },
        { id: 'cohorts', label: 'Cohorts' }
      ]
    },
    {
      id: 'content',
      label: 'Content',
      icon: BookOpen,
      subsections: [
        { id: 'challenges', label: 'Challenges' },
        { id: 'tracks', label: 'Tracks' },
        { id: 'quizzes', label: 'Quizzes' }
      ]
    },
    {
      id: 'gamification',
      label: 'Gamification',
      icon: Trophy,
      subsections: [
        { id: 'points-xp', label: 'Points & XP' },
        { id: 'badges', label: 'Badges' },
        { id: 'leaderboards', label: 'Leaderboards' },
        { id: 'tournaments', label: 'Tournaments' }
      ]
    },
    {
      id: 'payments',
      label: 'Payments',
      icon: CreditCard,
      subsections: [
        { id: 'plans', label: 'Plans' },
        { id: 'transactions', label: 'Transactions' },
        { id: 'reports', label: 'Reports' }
      ]
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: BarChart3,
      subsections: [
        { id: 'learning-progress', label: 'Learning Progress' },
        { id: 'engagement', label: 'Engagement' },
        { id: 'system-usage', label: 'System Usage' }
      ]
    },
    {
      id: 'support',
      label: 'Support',
      icon: HeadphonesIcon,
      subsections: [
        { id: 'tickets', label: 'Tickets' },
        { id: 'community', label: 'Community' },
        { id: 'announcements', label: 'Announcements' }
      ]
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: Settings,
      subsections: [
        { id: 'admin-roles', label: 'Admin Roles' },
        { id: 'app-settings', label: 'App Settings' },
        { id: 'certificates', label: 'Certificates' }
      ]
    }
  ];

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <Users className="h-5 w-5 text-blue-500" />
              <span className="text-2xl font-bold">{dashboardStats.totalUsers.toLocaleString()}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Active Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <UserCheck className="h-5 w-5 text-green-500" />
              <span className="text-2xl font-bold">{dashboardStats.activeUsers.toLocaleString()}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Revenue</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <DollarSign className="h-5 w-5 text-green-600" />
              <span className="text-2xl font-bold">${dashboardStats.totalRevenue.toLocaleString()}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Challenges Completed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <Trophy className="h-5 w-5 text-yellow-500" />
              <span className="text-2xl font-bold">{dashboardStats.challengesCompleted.toLocaleString()}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Subscription Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Users className="h-5 w-5" />
              <span>Free Users</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-600">{dashboardStats.freeUsers}</div>
            <Badge className="mt-2">64% of total</Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Crown className="h-5 w-5 text-blue-500" />
              <span>Pro Users</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">{dashboardStats.proUsers}</div>
            <Badge className="mt-2 bg-blue-100 text-blue-800">32% of total</Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Medal className="h-5 w-5 text-purple-500" />
              <span>Enterprise Users</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-600">{dashboardStats.enterpriseUsers}</div>
            <Badge className="mt-2 bg-purple-100 text-purple-800">4% of total</Badge>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm">New Signup - user@example.com</span>
              <span className="text-xs text-gray-500 ml-auto">2 minutes ago</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="text-sm">Payment Received - Pro Plan $9.99</span>
              <span className="text-xs text-gray-500 ml-auto">1 hour ago</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
              <span className="text-sm">Reported Issue - Code execution timeout</span>
              <span className="text-xs text-gray-500 ml-auto">5 hours ago</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderUserManagement = () => (
    <div className="space-y-6">
      {activeSubSection === 'all-users' || activeSubSection === '' ? (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center space-x-2">
                <Users className="h-5 w-5" />
                <span>All Users</span>
              </CardTitle>
              <div className="flex items-center space-x-2">
                <div className="relative">
                  <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
                  <Input 
                    placeholder="Search users..." 
                    className="pl-10 w-64"
                    value={userFilters.search}
                    onChange={(e) => setUserFilters({...userFilters, search: e.target.value})}
                  />
                </div>
                <Select value={userFilters.subscription} onValueChange={(value) => setUserFilters({...userFilters, subscription: value})}>
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Plans</SelectItem>
                    <SelectItem value="free">Free</SelectItem>
                    <SelectItem value="pro">Pro</SelectItem>
                    <SelectItem value="enterprise">Enterprise</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {usersList.map((user) => (
                <div key={user._id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold">
                        {user.username?.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-semibold">{user.username}</span>
                          <Badge className={
                            user.subscription === 'pro' ? 'bg-blue-100 text-blue-800' :
                            user.subscription === 'enterprise' ? 'bg-purple-100 text-purple-800' :
                            'bg-gray-100 text-gray-800'
                          }>
                            {user.subscription || 'Free'}
                          </Badge>
                          <Badge variant={user.status === 'active' ? 'default' : 'destructive'}>
                            {user.status || 'Active'}
                          </Badge>
                        </div>
                        <div className="text-sm text-gray-600">
                          {user.email} • Level {user.current_level} • {user.total_xp} XP
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button size="sm" variant="outline">
                        <Eye className="h-4 w-4 mr-1" />
                        View
                      </Button>
                      <Button size="sm" variant="outline">
                        <Edit className="h-4 w-4 mr-1" />
                        Edit
                      </Button>
                      <Button size="sm" variant="outline">
                        <Ban className="h-4 w-4 mr-1" />
                        Suspend
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : activeSubSection === 'achievements' ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Award className="h-5 w-5" />
              <span>Achievements Management</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">Manage badges, achievements, and XP rewards for users.</p>
            {/* Achievement management UI would go here */}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Users className="h-5 w-5" />
              <span>User Cohorts</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">Segment and manage user groups for targeted campaigns.</p>
            {/* Cohorts management UI would go here */}
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderPaymentManagement = () => (
    <div className="space-y-6">
      {activeSubSection === 'plans' || activeSubSection === '' ? (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center space-x-2">
                <CreditCard className="h-5 w-5" />
                <span>Subscription Plans</span>
              </CardTitle>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Create Plan
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {subscriptionPlans.map((plan) => (
                <Card key={plan.id} className="border-2">
                  <CardHeader>
                    <CardTitle className="text-center">{plan.name}</CardTitle>
                    <div className="text-center">
                      <span className="text-3xl font-bold">${plan.price}</span>
                      <span className="text-gray-600">/month</span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2 mb-4">
                      {plan.features.map((feature, index) => (
                        <li key={index} className="flex items-center space-x-2">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          <span className="text-sm">{feature}</span>
                        </li>
                      ))}
                    </ul>
                    <div className="text-center text-sm text-gray-600 mb-4">
                      {plan.users} active users
                    </div>
                    <div className="flex space-x-2">
                      <Button size="sm" variant="outline" className="flex-1">
                        <Edit className="h-4 w-4 mr-1" />
                        Edit
                      </Button>
                      <Button size="sm" variant="outline" className="flex-1">
                        <BarChart3 className="h-4 w-4 mr-1" />
                        Analytics
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : activeSubSection === 'transactions' ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <DollarSign className="h-5 w-5" />
              <span>Recent Transactions</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {transactions.map((transaction) => (
                <div key={transaction.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-semibold">{transaction.user}</div>
                      <div className="text-sm text-gray-600">{transaction.plan} • ${transaction.amount}</div>
                    </div>
                    <div className="text-right">
                      <Badge className={transaction.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}>
                        {transaction.status}
                      </Badge>
                      <div className="text-sm text-gray-600 mt-1">
                        {new Date(transaction.date).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5" />
              <span>Revenue Reports</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center space-x-2">
                    <DollarSign className="h-5 w-5 text-green-500" />
                    <div>
                      <div className="text-sm text-gray-600">MRR</div>
                      <div className="text-2xl font-bold">${revenueData.mrr?.toLocaleString()}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center space-x-2">
                    <TrendingUp className="h-5 w-5 text-blue-500" />
                    <div>
                      <div className="text-sm text-gray-600">ARR</div>
                      <div className="text-2xl font-bold">${revenueData.arr?.toLocaleString()}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center space-x-2">
                    <XCircle className="h-5 w-5 text-red-500" />
                    <div>
                      <div className="text-sm text-gray-600">Churn Rate</div>
                      <div className="text-2xl font-bold">{revenueData.churnRate}%</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <div>
                      <div className="text-sm text-gray-600">Trial Conversion</div>
                      <div className="text-2xl font-bold">{revenueData.trialConversion}%</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  // Render different sections based on active selection
  const renderContent = () => {
    switch (activeSection) {
      case 'dashboard':
        return renderDashboard();
      case 'users':
        return renderUserManagement();
      case 'payments':
        return renderPaymentManagement();
      case 'content':
        return (
          <Card>
            <CardHeader>
              <CardTitle>Content Management</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Challenge creation, tracks, and quiz management coming soon...</p>
            </CardContent>
          </Card>
        );
      case 'gamification':
        return (
          <Card>
            <CardHeader>
              <CardTitle>Gamification Controls</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Points, badges, leaderboards, and tournaments management coming soon...</p>
            </CardContent>
          </Card>
        );
      case 'analytics':
        return (
          <Card>
            <CardHeader>
              <CardTitle>Analytics & Reports</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Comprehensive analytics dashboard coming soon...</p>
            </CardContent>
          </Card>
        );
      case 'support':
        return (
          <Card>
            <CardHeader>
              <CardTitle>Support & Communication</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Support tickets, community moderation, and announcements coming soon...</p>
            </CardContent>
          </Card>
        );
      case 'settings':
        return (
          <Card>
            <CardHeader>
              <CardTitle>Admin Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Admin roles, app settings, and certificates management coming soon...</p>
            </CardContent>
          </Card>
        );
      default:
        return renderDashboard();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex">
        {/* Sidebar Navigation */}
        <div className="w-64 bg-white shadow-lg border-r border-gray-200 min-h-screen">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-800">Admin Dashboard</h2>
          </div>
          
          <nav className="mt-6">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeSection === item.id;
              
              return (
                <div key={item.id}>
                  <button
                    onClick={() => {
                      setActiveSection(item.id);
                      setActiveSubSection('');
                    }}
                    className={`w-full flex items-center space-x-3 px-6 py-3 text-left hover:bg-blue-50 transition-colors ${
                      isActive ? 'bg-blue-50 border-r-2 border-blue-500 text-blue-700' : 'text-gray-700'
                    }`}
                  >
                    <Icon className={`h-5 w-5 ${isActive ? 'text-blue-500' : 'text-gray-500'}`} />
                    <span className="font-medium">{item.label}</span>
                  </button>
                  
                  {/* Subsections */}
                  {isActive && item.subsections.length > 0 && (
                    <div className="ml-6 border-l border-gray-200">
                      {item.subsections.map((subsection) => (
                        <button
                          key={subsection.id}
                          onClick={() => setActiveSubSection(subsection.id)}
                          className={`w-full flex items-center space-x-3 px-6 py-2 text-left text-sm hover:bg-gray-50 transition-colors ${
                            activeSubSection === subsection.id ? 'text-blue-600 bg-blue-50' : 'text-gray-600'
                          }`}
                        >
                          <span>{subsection.label}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </nav>
        </div>

        {/* Main Content */}
        <div className="flex-1">
          {/* Header */}
          <div className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 capitalize">
                  {activeSection} {activeSubSection && `- ${activeSubSection.replace('-', ' ')}`}
                </h1>
                <p className="text-gray-600 mt-1">Comprehensive system administration</p>
              </div>
              <div className="flex items-center space-x-4">
                <Button variant="outline" onClick={() => navigate('/dashboard')}>
                  Dashboard
                </Button>
                <Button onClick={initializeAdminData}>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Refresh
                </Button>
              </div>
            </div>
          </div>

          {/* Content Area */}
          <div className="p-6">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComprehensiveAdminPanel;