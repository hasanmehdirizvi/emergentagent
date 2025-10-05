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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Users,
  MessageSquare,
  BarChart3,
  Filter,
  Search,
  Star,
  Calendar,
  CheckCircle,
  Clock,
  XCircle,
  Eye,
  RefreshCw,
  ArrowLeft,
  Settings,
  Bug,
  Mail,
  Key,
  PlayCircle,
  UserPlus,
  UserX,
  Edit,
  AlertTriangle,
  FileText,
  Code,
  TestTube,
  ShieldCheck,
  Unlock
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const AdminPageEnhanced = () => {
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  
  // Main state
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  
  // Overview State
  const [overviewStats, setOverviewStats] = useState(null);
  
  // Feedback Management State (existing)
  const [feedbackList, setFeedbackList] = useState([]);
  const [feedbackStats, setFeedbackStats] = useState(null);
  const [selectedFeedback, setSelectedFeedback] = useState(null);
  const [showFeedbackDetails, setShowFeedbackDetails] = useState(false);
  
  // User Management State
  const [usersList, setUsersList] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showUserDetails, setShowUserDetails] = useState(false);
  const [showPasswordReset, setShowPasswordReset] = useState(false);
  const [showProgressManagement, setShowProgressManagement] = useState(false);
  const [progressAction, setProgressAction] = useState('');
  const [targetLevelId, setTargetLevelId] = useState('');
  
  // Issue Tracking State
  const [issues, setIssues] = useState([]);
  const [showCreateIssue, setShowCreateIssue] = useState(false);
  const [issueForm, setIssueForm] = useState({
    title: '',
    description: '',
    priority: 'medium',
    type: 'bug',
    affectedUser: '',
    codeFile: '',
    codeError: ''
  });
  
  // Module Testing State
  const [testModules, setTestModules] = useState([]);
  const [selectedModule, setSelectedModule] = useState('');
  const [testResults, setTestResults] = useState(null);
  const [testingInProgress, setTestingInProgress] = useState(false);

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
      
      // Load overview statistics
      const [feedbackStatsRes, usersRes, modulesRes] = await Promise.all([
        axios.get('/api/admin/feedback/statistics'),
        axios.get('/api/admin/users?limit=10'),
        axios.get('/api/admin/test-modules')
      ]);
      
      setFeedbackStats(feedbackStatsRes.data);
      setUsersList(usersRes.data.users);
      setTestModules(modulesRes.data.modules);
      
      // Prepare overview stats
      setOverviewStats({
        totalFeedback: feedbackStatsRes.data.total_feedback,
        pendingFeedback: feedbackStatsRes.data.status_breakdown.pending || 0,
        totalUsers: usersRes.data.total,
        activeUsers: usersRes.data.users.filter(u => u.last_activity).length
      });
      
    } catch (error) {
      console.error('Failed to load admin data:', error);
      if (error.response?.status === 403) {
        toast.error('Admin access required');
        navigate('/dashboard');
      } else {
        toast.error('Failed to load admin data');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUserProgressUpdate = async () => {
    try {
      const payload = {
        action: progressAction,
        level_id: parseInt(targetLevelId)
      };
      
      await axios.patch(`/api/admin/users/${selectedUser._id}/progress`, payload);
      
      toast.success(`User progress updated successfully`);
      setShowProgressManagement(false);
      setProgressAction('');
      setTargetLevelId('');
      
      // Refresh user data
      const response = await axios.get('/api/admin/users');
      setUsersList(response.data.users);
    } catch (error) {
      console.error('Failed to update user progress:', error);
      toast.error('Failed to update user progress');
    }
  };

  const handlePasswordReset = async () => {
    try {
      const response = await axios.post(`/api/admin/users/${selectedUser._id}/password-reset`);
      
      toast.success('Password reset initiated successfully');
      
      // Show reset link to admin
      navigator.clipboard.writeText(response.data.reset_link);
      toast.info('Reset link copied to clipboard');
      
      setShowPasswordReset(false);
    } catch (error) {
      console.error('Failed to initiate password reset:', error);
      toast.error('Failed to initiate password reset');
    }
  };

  const handleCreateIssue = async () => {
    try {
      await axios.post('/api/admin/issues', issueForm);
      
      toast.success('Issue created successfully');
      setShowCreateIssue(false);
      setIssueForm({
        title: '',
        description: '',
        priority: 'medium',
        type: 'bug',
        affectedUser: '',
        codeFile: '',
        codeError: ''
      });
    } catch (error) {
      console.error('Failed to create issue:', error);
      toast.error('Failed to create issue');
    }
  };

  const handleModuleTest = async () => {
    if (!selectedModule) return;
    
    try {
      setTestingInProgress(true);
      const response = await axios.post(`/api/admin/test-module/${selectedModule}`, {});
      
      setTestResults(response.data.test_results);
      toast.success(`Module ${selectedModule} tested successfully`);
    } catch (error) {
      console.error('Failed to test module:', error);
      toast.error('Failed to test module');
    } finally {
      setTestingInProgress(false);
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
    <div className="min-h-screen py-6 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <Button 
              variant="outline" 
              onClick={() => navigate('/dashboard')}
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Dashboard
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Enhanced Admin Panel</h1>
              <p className="text-gray-600 mt-1">Comprehensive system administration and user support</p>
            </div>
          </div>
          <Button onClick={initializeAdminData}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh All
          </Button>
        </div>

        {/* Admin Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid grid-cols-5 w-full mb-8">
            <TabsTrigger value="overview" className="flex items-center space-x-2">
              <BarChart3 className="h-4 w-4" />
              <span>Overview</span>
            </TabsTrigger>
            <TabsTrigger value="users" className="flex items-center space-x-2">
              <Users className="h-4 w-4" />
              <span>Users</span>
            </TabsTrigger>
            <TabsTrigger value="feedback" className="flex items-center space-x-2">
              <MessageSquare className="h-4 w-4" />
              <span>Feedback</span>
            </TabsTrigger>
            <TabsTrigger value="issues" className="flex items-center space-x-2">
              <Bug className="h-4 w-4" />
              <span>Issues</span>
            </TabsTrigger>
            <TabsTrigger value="testing" className="flex items-center space-x-2">
              <TestTube className="h-4 w-4" />
              <span>Testing</span>
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600">Total Users</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center space-x-2">
                    <Users className="h-5 w-5 text-blue-500" />
                    <span className="text-2xl font-bold">{overviewStats?.totalUsers || 0}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600">Active Users</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span className="text-2xl font-bold">{overviewStats?.activeUsers || 0}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600">Total Feedback</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center space-x-2">
                    <MessageSquare className="h-5 w-5 text-purple-500" />
                    <span className="text-2xl font-bold">{overviewStats?.totalFeedback || 0}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600">Pending Reviews</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center space-x-2">
                    <Clock className="h-5 w-5 text-yellow-500" />
                    <span className="text-2xl font-bold">{overviewStats?.pendingFeedback || 0}</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Quick Actions */}
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Button onClick={() => setActiveTab('users')} variant="outline" className="h-16 flex-col">
                    <UserPlus className="h-6 w-6 mb-1" />
                    Manage Users
                  </Button>
                  <Button onClick={() => setShowCreateIssue(true)} variant="outline" className="h-16 flex-col">
                    <Bug className="h-6 w-6 mb-1" />
                    Create Issue
                  </Button>
                  <Button onClick={() => setActiveTab('testing')} variant="outline" className="h-16 flex-col">
                    <TestTube className="h-6 w-6 mb-1" />
                    Test Module
                  </Button>
                  <Button onClick={() => setActiveTab('feedback')} variant="outline" className="h-16 flex-col">
                    <MessageSquare className="h-6 w-6 mb-1" />
                    Review Feedback
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Users Management Tab */}
          <TabsContent value="users">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Users className="h-5 w-5" />
                  <span>User Management</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {usersList.map((user) => (
                    <div
                      key={user._id}
                      className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <Badge variant="outline">{user.username}</Badge>
                            <span className="text-sm text-gray-500">{user.email}</span>
                            <Badge className="bg-blue-100 text-blue-800">
                              Level {user.current_level}
                            </Badge>
                            <Badge variant="outline">
                              {user.total_xp} XP
                            </Badge>
                          </div>
                          <div className="text-sm text-gray-600">
                            <span>Completed: {user.total_levels_completed} levels</span>
                            {user.last_activity && (
                              <span className="ml-4">
                                Last active: {new Date(user.last_activity).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedUser(user);
                              setShowProgressManagement(true);
                            }}
                          >
                            <Unlock className="h-4 w-4 mr-1" />
                            Manage Progress
                          </Button>
                          
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedUser(user);
                              setShowPasswordReset(true);
                            }}
                          >
                            <Key className="h-4 w-4 mr-1" />
                            Reset Password
                          </Button>
                          
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedUser(user);
                              setShowUserDetails(true);
                            }}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Feedback Tab (Existing functionality) */}
          <TabsContent value="feedback">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <MessageSquare className="h-5 w-5" />
                  <span>Feedback Management</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Advanced feedback management system with filtering and status updates.
                  <Button 
                    className="ml-4" 
                    onClick={() => navigate('/admin')}
                    variant="outline"
                  >
                    Open Full Feedback Manager
                  </Button>
                </p>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Issues Tab */}
          <TabsContent value="issues">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Bug className="h-5 w-5" />
                  <span>Issue Tracking</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex justify-between items-center mb-4">
                  <p className="text-gray-600">
                    Track and manage user issues with provision for Jira integration
                  </p>
                  <Button onClick={() => setShowCreateIssue(true)}>
                    <Bug className="mr-2 h-4 w-4" />
                    Create Issue
                  </Button>
                </div>
                
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-blue-900 mb-2">Future Integration Ready:</h3>
                  <ul className="text-blue-700 text-sm space-y-1">
                    <li>• Automatic Jira ticket creation</li>
                    <li>• Code error linking and file references</li>
                    <li>• User issue escalation workflow</li>
                    <li>• Integration with development workflow</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Testing Tab */}
          <TabsContent value="testing">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <TestTube className="h-5 w-5" />
                  <span>Module Testing</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center space-x-4">
                    <Select value={selectedModule} onValueChange={setSelectedModule}>
                      <SelectTrigger className="w-64">
                        <SelectValue placeholder="Select module to test" />
                      </SelectTrigger>
                      <SelectContent>
                        {testModules.map((module) => (
                          <SelectItem key={module.id} value={module.id}>
                            {module.name} {module.levels && `(${module.levels})`}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    
                    <Button 
                      onClick={handleModuleTest}
                      disabled={!selectedModule || testingInProgress}
                    >
                      {testingInProgress ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
                          Testing...
                        </>
                      ) : (
                        <>
                          <PlayCircle className="mr-2 h-4 w-4" />
                          Run Test
                        </>
                      )}
                    </Button>
                  </div>
                  
                  {testResults && (
                    <Card className="bg-green-50 border-green-200">
                      <CardHeader>
                        <CardTitle className="text-green-800">Test Results</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <pre className="text-sm text-green-700">
                          {JSON.stringify(testResults, null, 2)}
                        </pre>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Dialogs */}
        
        {/* Progress Management Dialog */}
        {showProgressManagement && selectedUser && (
          <Dialog open={showProgressManagement} onOpenChange={setShowProgressManagement}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Manage User Progress - {selectedUser.username}</DialogTitle>
              </DialogHeader>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    Action
                  </label>
                  <Select value={progressAction} onValueChange={setProgressAction}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select action" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="unlock_level">Unlock Level</SelectItem>
                      <SelectItem value="complete_level">Complete Level</SelectItem>
                      <SelectItem value="reset_progress">Reset All Progress</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                {(progressAction === 'unlock_level' || progressAction === 'complete_level') && (
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">
                      Level ID
                    </label>
                    <Input
                      type="number"
                      placeholder="e.g., 105"
                      value={targetLevelId}
                      onChange={(e) => setTargetLevelId(e.target.value)}
                    />
                  </div>
                )}
                
                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setShowProgressManagement(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleUserProgressUpdate}>
                    Apply Changes
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}

        {/* Password Reset Dialog */}
        {showPasswordReset && selectedUser && (
          <Dialog open={showPasswordReset} onOpenChange={setShowPasswordReset}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Reset Password - {selectedUser.username}</DialogTitle>
              </DialogHeader>
              
              <div className="space-y-4">
                <p className="text-gray-600">
                  This will generate a password reset link for {selectedUser.email}. 
                  The link will be copied to your clipboard for you to share with the user.
                </p>
                
                <div className="bg-yellow-50 p-3 rounded-lg">
                  <p className="text-yellow-800 text-sm">
                    <strong>Future Enhancement:</strong> This will automatically send an email to the user with the reset link.
                  </p>
                </div>
                
                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setShowPasswordReset(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handlePasswordReset}>
                    <Mail className="mr-2 h-4 w-4" />
                    Generate Reset Link
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}

        {/* Create Issue Dialog */}
        {showCreateIssue && (
          <Dialog open={showCreateIssue} onOpenChange={setShowCreateIssue}>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create Issue Ticket</DialogTitle>
              </DialogHeader>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">
                      Issue Type
                    </label>
                    <Select 
                      value={issueForm.type} 
                      onValueChange={(value) => setIssueForm({...issueForm, type: value})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="bug">Bug</SelectItem>
                        <SelectItem value="feature">Feature Request</SelectItem>
                        <SelectItem value="support">Support</SelectItem>
                        <SelectItem value="enhancement">Enhancement</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">
                      Priority
                    </label>
                    <Select 
                      value={issueForm.priority} 
                      onValueChange={(value) => setIssueForm({...issueForm, priority: value})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="critical">Critical</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    Issue Title
                  </label>
                  <Input
                    placeholder="Brief description of the issue"
                    value={issueForm.title}
                    onChange={(e) => setIssueForm({...issueForm, title: e.target.value})}
                  />
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    Description
                  </label>
                  <Textarea
                    placeholder="Detailed description of the issue"
                    value={issueForm.description}
                    onChange={(e) => setIssueForm({...issueForm, description: e.target.value})}
                    className="min-h-[100px]"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">
                      Affected User ID
                    </label>
                    <Input
                      placeholder="User ID (optional)"
                      value={issueForm.affectedUser}
                      onChange={(e) => setIssueForm({...issueForm, affectedUser: e.target.value})}
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">
                      Code File Reference
                    </label>
                    <Input
                      placeholder="e.g., /app/frontend/src/pages/LevelPage.js"
                      value={issueForm.codeFile}
                      onChange={(e) => setIssueForm({...issueForm, codeFile: e.target.value})}
                    />
                  </div>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    Code Error/Stack Trace
                  </label>
                  <Textarea
                    placeholder="Paste error message or stack trace here"
                    value={issueForm.codeError}
                    onChange={(e) => setIssueForm({...issueForm, codeError: e.target.value})}
                    className="min-h-[80px] font-mono text-sm"
                  />
                </div>
                
                <div className="bg-blue-50 p-3 rounded-lg">
                  <p className="text-blue-800 text-sm">
                    <strong>Jira Integration Ready:</strong> This issue will be prepared for automatic Jira sync when integration is configured.
                  </p>
                </div>
                
                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setShowCreateIssue(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreateIssue}>
                    <Bug className="mr-2 h-4 w-4" />
                    Create Issue
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>
    </div>
  );
};

export default AdminPageEnhanced;