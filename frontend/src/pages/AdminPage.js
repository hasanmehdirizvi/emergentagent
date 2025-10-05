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
  TestTube
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const AdminPage = () => {
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const [feedbackList, setFeedbackList] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedFeedback, setSelectedFeedback] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  
  // Filters
  const [filters, setFilters] = useState({
    status: '',
    category: '',
    level_id: '',
    user_id: ''
  });
  
  // Pagination
  const [pagination, setPagination] = useState({
    skip: 0,
    limit: 20,
    hasMore: false
  });

  useEffect(() => {
    // Check admin access
    if (!currentUser || !currentUser.username?.toLowerCase().includes('admin')) {
      toast.error('Admin access required');
      navigate('/dashboard');
      return;
    }
    
    fetchFeedback();
    fetchStatistics();
  }, [currentUser, filters, pagination.skip]);

  const fetchFeedback = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.append('skip', pagination.skip);
      params.append('limit', pagination.limit);
      
      // Add filters if they exist
      if (filters.status) params.append('status', filters.status);
      if (filters.category) params.append('category', filters.category);
      if (filters.level_id) params.append('level_id', filters.level_id);
      if (filters.user_id) params.append('user_id', filters.user_id);

      const response = await axios.get(`/api/admin/feedback?${params.toString()}`);
      
      if (pagination.skip === 0) {
        setFeedbackList(response.data.feedback);
      } else {
        setFeedbackList(prev => [...prev, ...response.data.feedback]);
      }
      
      setPagination(prev => ({
        ...prev,
        hasMore: response.data.pagination.has_more
      }));
    } catch (error) {
      console.error('Failed to fetch feedback:', error);
      if (error.response?.status === 403) {
        toast.error('Admin access required');
        navigate('/dashboard');
      } else {
        toast.error('Failed to load feedback');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await axios.get('/api/admin/feedback/statistics');
      setStatistics(response.data);
    } catch (error) {
      console.error('Failed to fetch statistics:', error);
    }
  };

  const updateFeedbackStatus = async (feedbackId, newStatus) => {
    try {
      await axios.patch(`/api/admin/feedback/${feedbackId}/status`, {
        status: newStatus
      });
      
      // Update the feedback in the list
      setFeedbackList(prev => 
        prev.map(feedback => 
          feedback._id === feedbackId 
            ? { ...feedback, status: newStatus }
            : feedback
        )
      );
      
      toast.success(`Feedback marked as ${newStatus}`);
      fetchStatistics(); // Refresh statistics
    } catch (error) {
      console.error('Failed to update feedback status:', error);
      toast.error('Failed to update status');
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, skip: 0 })); // Reset pagination
  };

  const clearFilters = () => {
    setFilters({
      status: '',
      category: '',
      level_id: '',
      user_id: ''
    });
    setPagination(prev => ({ ...prev, skip: 0 }));
  };

  const loadMore = () => {
    setPagination(prev => ({
      ...prev,
      skip: prev.skip + prev.limit
    }));
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'reviewed':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'resolved':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4" />;
      case 'reviewed':
        return <Eye className="h-4 w-4" />;
      case 'resolved':
        return <CheckCircle className="h-4 w-4" />;
      default:
        return <XCircle className="h-4 w-4" />;
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

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
              <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>
              <p className="text-gray-600 mt-1">Manage feedback and system administration</p>
            </div>
          </div>
          <Button onClick={() => window.location.reload()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>

        {/* Statistics Cards */}
        {statistics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Total Feedback
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center space-x-2">
                  <MessageSquare className="h-5 w-5 text-blue-500" />
                  <span className="text-2xl font-bold">{statistics.total_feedback}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Pending Review
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center space-x-2">
                  <Clock className="h-5 w-5 text-yellow-500" />
                  <span className="text-2xl font-bold">{statistics.status_breakdown.pending || 0}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Recent (7 days)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center space-x-2">
                  <Calendar className="h-5 w-5 text-green-500" />
                  <span className="text-2xl font-bold">{statistics.recent_feedback}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Avg Rating
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center space-x-2">
                  <Star className="h-5 w-5 text-orange-500" />
                  <span className="text-2xl font-bold">
                    {statistics.rating_distribution ? 
                      (Object.entries(statistics.rating_distribution).reduce((acc, [rating, count]) => acc + (parseInt(rating) * count), 0) / 
                       Object.values(statistics.rating_distribution).reduce((a, b) => a + b, 0)).toFixed(1)
                      : '0.0'
                    }
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Filters */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Filter className="h-5 w-5" />
              <span>Filters</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              <Select value={filters.status} onValueChange={(value) => handleFilterChange('status', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Status</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="reviewed">Reviewed</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                </SelectContent>
              </Select>

              <Select value={filters.category} onValueChange={(value) => handleFilterChange('category', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Categories</SelectItem>
                  <SelectItem value="general">General</SelectItem>
                  <SelectItem value="difficulty">Difficulty</SelectItem>
                  <SelectItem value="instructions">Instructions</SelectItem>
                  <SelectItem value="bug">Bug Report</SelectItem>
                  <SelectItem value="suggestion">Suggestion</SelectItem>
                </SelectContent>
              </Select>

              <Input
                placeholder="Level ID"
                value={filters.level_id}
                onChange={(e) => handleFilterChange('level_id', e.target.value)}
              />

              <Input
                placeholder="User ID"
                value={filters.user_id}
                onChange={(e) => handleFilterChange('user_id', e.target.value)}
              />

              <Button variant="outline" onClick={clearFilters}>
                Clear Filters
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Feedback List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <MessageSquare className="h-5 w-5" />
              <span>Feedback Management</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading && feedbackList.length === 0 ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto"></div>
                <p className="text-gray-500 mt-2">Loading feedback...</p>
              </div>
            ) : feedbackList.length === 0 ? (
              <div className="text-center py-8">
                <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No feedback found</p>
              </div>
            ) : (
              <div className="space-y-4">
                {feedbackList.map((feedback) => (
                  <div
                    key={feedback._id}
                    className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <Badge className={getStatusColor(feedback.status)}>
                            {getStatusIcon(feedback.status)}
                            <span className="ml-1 capitalize">{feedback.status}</span>
                          </Badge>
                          <Badge variant="outline" className="capitalize">
                            {feedback.category}
                          </Badge>
                          <span className="text-sm text-gray-500">
                            Level {feedback.level_id}
                          </span>
                          <div className="flex items-center space-x-1">
                            {[1, 2, 3, 4, 5].map((star) => (
                              <Star
                                key={star}
                                className={`h-4 w-4 ${
                                  star <= feedback.rating
                                    ? 'text-yellow-500 fill-current'
                                    : 'text-gray-300'
                                }`}
                              />
                            ))}
                          </div>
                        </div>
                        
                        <div className="mb-2">
                          <p className="text-gray-700 font-medium">
                            From: {feedback.username}
                          </p>
                          <p className="text-sm text-gray-500">
                            {formatDate(feedback.submitted_at)}
                          </p>
                        </div>
                        
                        <p className="text-gray-800 mb-3">
                          {feedback.comment.length > 200
                            ? `${feedback.comment.substring(0, 200)}...`
                            : feedback.comment
                          }
                        </p>
                      </div>
                      
                      <div className="flex items-center space-x-2 ml-4">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedFeedback(feedback);
                            setShowDetails(true);
                          }}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        
                        {feedback.status === 'pending' && (
                          <Button
                            size="sm"
                            onClick={() => updateFeedbackStatus(feedback._id, 'reviewed')}
                          >
                            Mark Reviewed
                          </Button>
                        )}
                        
                        {feedback.status === 'reviewed' && (
                          <Button
                            size="sm"
                            onClick={() => updateFeedbackStatus(feedback._id, 'resolved')}
                            className="bg-green-500 hover:bg-green-600"
                          >
                            Mark Resolved
                          </Button>
                        )}
                        
                        {feedback.status === 'resolved' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => updateFeedbackStatus(feedback._id, 'pending')}
                          >
                            Reopen
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                
                {pagination.hasMore && (
                  <div className="text-center pt-4">
                    <Button onClick={loadMore} disabled={loading}>
                      {loading ? 'Loading...' : 'Load More'}
                    </Button>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Feedback Details Dialog */}
        {selectedFeedback && (
          <Dialog open={showDetails} onOpenChange={setShowDetails}>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>
                  Feedback Details - Level {selectedFeedback.level_id}
                </DialogTitle>
              </DialogHeader>
              
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <Badge className={getStatusColor(selectedFeedback.status)}>
                    {getStatusIcon(selectedFeedback.status)}
                    <span className="ml-1 capitalize">{selectedFeedback.status}</span>
                  </Badge>
                  <Badge variant="outline" className="capitalize">
                    {selectedFeedback.category}
                  </Badge>
                  <div className="flex items-center space-x-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Star
                        key={star}
                        className={`h-4 w-4 ${
                          star <= selectedFeedback.rating
                            ? 'text-yellow-500 fill-current'
                            : 'text-gray-300'
                        }`}
                      />
                    ))}
                    <span className="text-sm text-gray-600 ml-2">
                      ({selectedFeedback.rating}/5)
                    </span>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <strong>Submitted by:</strong> {selectedFeedback.username}
                  </div>
                  <div>
                    <strong>User ID:</strong> {selectedFeedback.user_id}
                  </div>
                  <div>
                    <strong>Level ID:</strong> {selectedFeedback.level_id}
                  </div>
                  <div>
                    <strong>Date:</strong> {formatDate(selectedFeedback.submitted_at)}
                  </div>
                </div>
                
                <div>
                  <strong>Comment:</strong>
                  <div className="mt-2 p-3 bg-gray-50 rounded-lg">
                    <p className="text-gray-800 whitespace-pre-wrap">
                      {selectedFeedback.comment}
                    </p>
                  </div>
                </div>
                
                <div className="flex justify-end space-x-2 pt-4">
                  <Button variant="outline" onClick={() => setShowDetails(false)}>
                    Close
                  </Button>
                  {selectedFeedback.status !== 'resolved' && (
                    <Button 
                      onClick={() => {
                        updateFeedbackStatus(selectedFeedback._id, 'resolved');
                        setShowDetails(false);
                      }}
                      className="bg-green-500 hover:bg-green-600"
                    >
                      Mark as Resolved
                    </Button>
                  )}
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>
    </div>
  );
};

export default AdminPage;