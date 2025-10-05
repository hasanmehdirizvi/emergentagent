import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import MonacoEditor from '@monaco-editor/react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Textarea } from '../components/ui/textarea';
import { Separator } from '../components/ui/separator';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import {
  Play,
  RotateCcw,
  CheckCircle,
  XCircle,
  Lightbulb,
  ArrowLeft,
  ArrowRight,
  Target,
  Code,
  Trophy,
  BookOpen,
  FileText,
  ExternalLink,
  Minus,
  MessageSquare,
  Send,
  Star,
  Mail,
  User,
  X,
  Brain,
  Sparkles,
  Crown,
  Lock
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const LevelPage = () => {
  const { levelId } = useParams();
  const navigate = useNavigate();
  const { currentUser, updateUserStats } = useAuth();
  const [level, setLevel] = useState(null);
  const [code, setCode] = useState('');
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [showHints, setShowHints] = useState(false);
  const [attempts, setAttempts] = useState(0);
  const [loading, setLoading] = useState(true);
  const [notes, setNotes] = useState('');
  const [hintsUsed, setHintsUsed] = useState(0);
  const [showTutorials, setShowTutorials] = useState(false);
  const [userPoints, setUserPoints] = useState(100); // Starting points
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState({ rating: 5, comment: '', category: 'general' });

  // AI Tutor State
  const [showAITutor, setShowAITutor] = useState(false);
  const [aiTutorLoading, setAiTutorLoading] = useState(false);
  const [aiExplanation, setAiExplanation] = useState('');
  const [userSubscription, setUserSubscription] = useState(null);
  const [aiTutorError, setAiTutorError] = useState(null);

  useEffect(() => {
    fetchLevel();
    fetchUserSubscription();
  }, [levelId]);

  const fetchUserSubscription = async () => {
    try {
      const response = await axios.get('/api/user/subscription');
      setUserSubscription(response.data);
    } catch (error) {
      console.error('Failed to fetch subscription:', error);
      // Set default free subscription
      setUserSubscription({
        tier: 'free',
        limitations: { ai_tutor_uses: 3, ai_tutor_remaining: 3 }
      });
    }
  };

  const fetchLevel = async () => {
    try {
      const response = await axios.get(`/api/levels/${levelId}`);
      setLevel(response.data);
      setCode(response.data.starter_code);
    } catch (error) {
      console.error('Failed to fetch level:', error);
      toast.error('Failed to load level');
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const runCode = async () => {
    setIsRunning(true);
    setOutput('');
    
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      const simulatedOutput = executeSimplePython(code);
      setOutput(simulatedOutput);
      toast.success('Code executed successfully!');
    } catch (error) {
      setOutput('Error: ' + error.message);
      toast.error('Execution error');
    } finally {
      setIsRunning(false);
    }
  };

  const executeSimplePython = (code) => {
    try {
      console.log('Executing Python code:', code);
      const lines = code.split('\n').filter(line => 
        line.trim() && !line.trim().startsWith('#')
      );
      
      console.log('Filtered lines:', lines);
      let output = [];
      let variables = {};
      let skipNextLine = false;
      
      for (let i = 0; i < lines.length; i++) {
        if (skipNextLine) {
          skipNextLine = false;
          continue;
        }
        
        let line = lines[i].trim();
        
        if (line.includes('print(')) {
          const printMatch = line.match(/print\s*\(([^)]*)\)/);
          if (printMatch) {
            let content = printMatch[1].trim();
            
            // Handle string literals with quotes
            if ((content.startsWith('"') && content.endsWith('"')) || 
                (content.startsWith("'") && content.endsWith("'"))) {
              content = content.slice(1, -1); // Remove quotes
              output.push(content);
            } else if (variables[content]) {
              output.push(variables[content].toString());
            } else {
              try {
                const result = evaluateExpression(content, variables);
                output.push(result.toString());
              } catch (e) {
                // If all else fails, just remove quotes and output as string
                const cleanContent = content.replace(/['"]/g, '');
                output.push(cleanContent);
              }
            }
          }
        } else if (line.includes('=') && !line.includes('==')) {
          const [varName, expression] = line.split('=').map(s => s.trim());
          
          if (expression.includes('"') || expression.includes("'")) {
            variables[varName] = expression.replace(/['"]/g, '');
          } else {
            try {
              variables[varName] = evaluateExpression(expression, variables);
            } catch (e) {
              variables[varName] = expression;
            }
          }
        } else if (line.includes('for') && line.includes('range(')) {
          const rangeMatch = line.match(/for\s+(\w+)\s+in\s+range\((.*)\):/);
          if (rangeMatch) {
            const [, varName, rangeParams] = rangeMatch;
            const params = rangeParams.split(',').map(p => parseInt(p.trim()));
            
            let start = 0, end = params[0], step = 1;
            if (params.length === 2) {
              [start, end] = params;
            } else if (params.length === 3) {
              [start, end, step] = params;
            }
            
            // Check if there's a next line (loop body)
            if (i + 1 < lines.length) {
              const nextLine = lines[i + 1];
              if (nextLine.includes('print(')) {
                // Execute the loop with the print statement
                for (let loopVar = start; loopVar < end; loopVar += step) {
                  variables[varName] = loopVar;
                  // Execute the print statement in the loop context
                  const printMatch = nextLine.match(/print\s*\(([^)]*)\)/);
                  if (printMatch) {
                    let content = printMatch[1].trim();
                    if (content === varName) {
                      output.push(loopVar.toString());
                    }
                  }
                }
                // Skip the next line since we processed it
                skipNextLine = true;
              }
            }
          }
        }
      }
      
      const finalOutput = output.join('\n') || 'No output';
      console.log('Final output:', finalOutput);
      return finalOutput;
    } catch (error) {
      console.error('Execution error:', error);
      throw new Error('Execution failed: ' + error.message);
    }
  };

  const evaluateExpression = (expr, variables) => {
    let processed = expr;
    for (let [varName, value] of Object.entries(variables)) {
      processed = processed.replace(new RegExp(`\\b${varName}\\b`, 'g'), value);
    }
    
    if (processed.includes('+') && (processed.includes('"') || processed.includes("'"))) {
      const parts = processed.split('+').map(p => p.trim().replace(/['"]/g, ''));
      return parts.join('');
    }
    
    try {
      return eval(processed);
    } catch (e) {
      return processed;
    }
  };

  const submitSolution = async () => {
    if (!output) {
      toast.error('Please run your code first!');
      return;
    }

    setIsSubmitting(true);
    setAttempts(prev => prev + 1);

    try {
      const response = await axios.post(`/api/levels/${levelId}/submit`, {
        code: code,
        output: output
      });

      setResult(response.data);
      
      if (response.data.success) {
        toast.success('Level Completed! +' + (response.data.xp_earned || 0) + ' XP earned');
        updateUserStats(response.data.stats);
      } else {
        toast.error('Keep trying! Check your output.');
      }
    } catch (error) {
      console.error('Failed to submit solution:', error);
      toast.error('Failed to submit solution');
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetCode = () => {
    setCode(level.starter_code);
    setOutput('');
    setResult(null);
    toast.info('Code reset to starting template');
  };

  const useHint = () => {
    if (hintsUsed < (level.hints?.length || 0)) {
      setHintsUsed(prev => prev + 1);
      setUserPoints(prev => Math.max(0, prev - 10)); // Deduct 10 points per hint
      setShowHints(true);
      toast.warning(`Hint revealed! -10 points (${userPoints - 10} remaining)`);
    }
  };

  const getTutorialLink = (topic) => {
    const tutorials = {
      'variables': 'https://docs.python.org/3/tutorial/introduction.html#using-python-as-a-calculator',
      'print': 'https://docs.python.org/3/tutorial/inputoutput.html#fancier-output-formatting',
      'strings': 'https://docs.python.org/3/tutorial/introduction.html#strings',
      'loops': 'https://docs.python.org/3/tutorial/controlflow.html#for-statements',
      'functions': 'https://docs.python.org/3/tutorial/controlflow.html#defining-functions'
    };
    return tutorials[topic] || 'https://docs.python.org/3/tutorial/';
  };

  const submitFeedback = async () => {
    try {
      await axios.post(`/api/levels/${levelId}/feedback`, {
        ...feedback,
        level_id: parseInt(levelId),
        user_id: currentUser?.id
      });
      toast.success('Thank you for your feedback! 🙏');
      setShowFeedback(false);
      setFeedback({ rating: 5, comment: '', category: 'general' });
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      toast.error('Failed to submit feedback. Please try again.');
    }
  };

  const handleAITutor = async () => {
    // Check subscription limits for free users
    if (userSubscription?.tier === 'free' && userSubscription?.ai_tutor_remaining <= 0) {
      toast.error('Daily AI tutor limit reached. Upgrade to Pro for unlimited access!');
      return;
    }

    setAiTutorLoading(true);
    setAiTutorError(null);
    setShowAITutor(true);

    try {
      const response = await axios.post(`/api/levels/${levelId}/ai-tutor`);
      
      if (response.data.success) {
        setAiExplanation(response.data.explanation);
        
        // Update subscription data if usage changed
        if (userSubscription?.tier === 'free') {
          setUserSubscription(prev => ({
            ...prev,
            ai_tutor_remaining: Math.max(0, (prev?.ai_tutor_remaining || 3) - 1)
          }));
        }
        
        toast.success('AI tutor explanation ready!');
      } else {
        setAiTutorError(response.data.error);
        setAiExplanation(response.data.fallback_explanation);
      }
    } catch (error) {
      console.error('AI Tutor error:', error);
      setAiTutorError('Failed to load AI tutor. Please try again.');
      setAiExplanation('AI tutor is temporarily unavailable. Try using the hints or check the challenge description for guidance.');
    } finally {
      setAiTutorLoading(false);
    }
  };

  const getAITutorButtonText = () => {
    if (!userSubscription) return 'AI Tutor';
    
    if (userSubscription.tier === 'free') {
      return `AI Tutor (${userSubscription.ai_tutor_remaining || 0}/3 left)`;
    }
    
    return 'AI Tutor';
  };

  const canUseAITutor = () => {
    if (!userSubscription) return false;
    if (userSubscription.tier === 'pro' || userSubscription.tier === 'enterprise') return true;
    return userSubscription.ai_tutor_remaining > 0;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  if (!level) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Level not found</h2>
          <Button onClick={() => navigate('/dashboard')}>Back to Dashboard</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-6 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <Button 
              variant="outline" 
              onClick={() => navigate('/dashboard')}
              data-testid="back-to-dashboard"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Dashboard
            </Button>
            <div>
              <h1 className="text-2xl font-bold" data-testid="level-title">
                Level {level.level_id}: {level.title}
              </h1>
              <div className="flex items-center space-x-2 mt-1">
                <Badge className="bg-blue-100 text-blue-800">
                  {level.difficulty}
                </Badge>
                <span className="text-sm text-gray-500">{level.category}</span>
                <span className="text-sm text-orange-600 font-medium">{level.xp_reward} XP</span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-2 px-3 py-1 bg-amber-100 rounded-full">
              <Trophy className="h-4 w-4 text-amber-600" />
              <span className="text-sm font-medium text-amber-800">{userPoints} points</span>
            </div>
            <Button 
              variant="outline" 
              onClick={useHint}
              disabled={hintsUsed >= (level?.hints?.length || 0)}
              data-testid="use-hint"
            >
              <Lightbulb className="mr-2 h-4 w-4" />
              Get Hint (-10 pts)
            </Button>
            <Button
              onClick={handleAITutor}
              disabled={!canUseAITutor() || aiTutorLoading}
              className={`flex items-center space-x-2 ${
                userSubscription?.tier === 'pro' || userSubscription?.tier === 'enterprise' 
                  ? 'bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600' 
                  : ''
              }`}
              variant={canUseAITutor() ? 'default' : 'outline'}
            >
              {aiTutorLoading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
              ) : (
                <>
                  <Brain className="h-4 w-4" />
                  {userSubscription?.tier === 'pro' || userSubscription?.tier === 'enterprise' ? (
                    <Sparkles className="h-3 w-3" />
                  ) : !canUseAITutor() ? (
                    <Lock className="h-3 w-3" />
                  ) : null}
                </>
              )}
              <span>{getAITutorButtonText()}</span>
              {userSubscription?.tier === 'pro' || userSubscription?.tier === 'enterprise' ? (
                <Crown className="h-3 w-3" />
              ) : null}
            </Button>
            <Button 
              variant="outline" 
              onClick={() => setShowTutorials(!showTutorials)}
              data-testid="toggle-tutorials"
            >
              <BookOpen className="mr-2 h-4 w-4" />
              Tutorials
            </Button>
            <Button 
              variant="outline" 
              onClick={() => setShowFeedback(!showFeedback)}
              data-testid="toggle-feedback"
            >
              <MessageSquare className="mr-2 h-4 w-4" />
              Feedback
            </Button>
            {parseInt(levelId) > 100 && (
              <Button 
                variant="outline" 
                onClick={() => navigate(`/level/${parseInt(levelId) - 1}`)}
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                Previous Level
              </Button>
            )}
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          <div className="space-y-6">
            <Card className="glass-card border-0">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Target className="h-5 w-5 text-orange-500" />
                  <span>Challenge</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700 leading-relaxed" data-testid="level-description">
                  {level.description}
                </p>
              </CardContent>
            </Card>

            {/* Progressive Hints */}
            {hintsUsed > 0 && level.hints && level.hints.length > 0 && (
              <Card className="glass-card border-0 border-l-4 border-l-amber-400">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2 text-amber-700">
                    <Lightbulb className="h-5 w-5" />
                    <span>Hints Used ({hintsUsed}/{level.hints.length})</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {level.hints.slice(0, hintsUsed).map((hint, index) => (
                    <div key={index} className="p-3 bg-amber-50 rounded-lg border border-amber-200">
                      <div className="flex items-start space-x-2">
                        <span className="inline-block w-6 h-6 rounded-full bg-amber-500 text-white text-xs font-bold flex items-center justify-center mt-0.5">
                          {index + 1}
                        </span>
                        <p className="text-amber-800 font-medium">{hint}</p>
                      </div>
                    </div>
                  ))}
                  {hintsUsed < level.hints.length && (
                    <div className="text-center pt-2">
                      <p className="text-sm text-amber-600">
                        {level.hints.length - hintsUsed} more hint(s) available
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Tutorials Section */}
            {showTutorials && (
              <Card className="glass-card border-0 border-l-4 border-l-blue-400">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2 text-blue-700">
                    <BookOpen className="h-5 w-5" />
                    <span>Learning Resources</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid gap-3">
                    <a 
                      href={getTutorialLink('print')}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center space-x-2 p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                    >
                      <ExternalLink className="h-4 w-4 text-blue-600" />
                      <span className="text-blue-800 font-medium">Python Print Functions</span>
                    </a>
                    <a 
                      href={getTutorialLink('variables')}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center space-x-2 p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                    >
                      <ExternalLink className="h-4 w-4 text-blue-600" />
                      <span className="text-blue-800 font-medium">Variables & Data Types</span>
                    </a>
                    <a 
                      href={getTutorialLink('strings')}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center space-x-2 p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                    >
                      <ExternalLink className="h-4 w-4 text-blue-600" />
                      <span className="text-blue-800 font-medium">Working with Strings</span>
                    </a>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Feedback Section */}
            {showFeedback && (
              <Card className="glass-card border-0 border-l-4 border-l-green-400">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2 text-green-700">
                    <MessageSquare className="h-5 w-5" />
                    <span>Level Feedback</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">
                      How would you rate this level?
                    </label>
                    <div className="flex items-center space-x-1">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <Star
                          key={star}
                          className={`h-6 w-6 cursor-pointer transition-colors ${
                            star <= feedback.rating
                              ? 'text-yellow-500 fill-current'
                              : 'text-gray-300'
                          }`}
                          onClick={() => setFeedback({ ...feedback, rating: star })}
                        />
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">
                      Feedback Category
                    </label>
                    <Select value={feedback.category} onValueChange={(value) => setFeedback({ ...feedback, category: value })}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="general">General Feedback</SelectItem>
                        <SelectItem value="difficulty">Difficulty Level</SelectItem>
                        <SelectItem value="instructions">Instructions Clarity</SelectItem>
                        <SelectItem value="bug">Bug Report</SelectItem>
                        <SelectItem value="suggestion">Suggestion</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">
                      Your Comments
                    </label>
                    <Textarea
                      placeholder="Tell us about your experience with this level..."
                      value={feedback.comment}
                      onChange={(e) => setFeedback({ ...feedback, comment: e.target.value })}
                      className="min-h-[80px]"
                    />
                  </div>

                  <Button 
                    onClick={submitFeedback}
                    className="w-full bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white"
                    data-testid="submit-feedback"
                  >
                    <Send className="mr-2 h-4 w-4" />
                    Submit Feedback
                  </Button>
                </CardContent>
              </Card>
            )}

            <Card className="glass-card border-0">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>Expected Output</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="bg-gray-50 p-3 rounded-lg text-sm font-mono border" data-testid="expected-output">
                  {level.expected_output}
                </pre>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            {/* Notes Section */}
            <Card className="glass-card border-0">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <FileText className="h-5 w-5 text-purple-500" />
                  <span>My Notes</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Textarea
                  placeholder="Write your notes about this level... (e.g., key concepts, reminders, solution approach)"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="min-h-[100px] resize-none"
                  data-testid="level-notes"
                />
                <div className="flex justify-between items-center mt-2">
                  <span className="text-xs text-gray-500">
                    Notes are saved automatically
                  </span>
                  <span className="text-xs text-gray-500">
                    {notes.length}/500 characters
                  </span>
                </div>
              </CardContent>
            </Card>
            
            <Card className="glass-card border-0">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center space-x-2">
                    <Code className="h-5 w-5 text-blue-500" />
                    <span>Python Code</span>
                  </CardTitle>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={resetCode}
                    data-testid="reset-code"
                  >
                    <RotateCcw className="mr-2 h-4 w-4" />
                    Reset
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="border rounded-lg overflow-hidden">
                  <MonacoEditor
                    height="400px"
                    language="python"
                    value={code}
                    onChange={setCode}
                    theme="light"
                    options={{
                      minimap: { enabled: false },
                      fontSize: 14,
                      lineNumbers: 'on',
                      scrollBeyondLastLine: false,
                      automaticLayout: true,
                      tabSize: 4
                    }}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Action Buttons */}
            {result && result.success ? (
              // Show success state with Next Level button
              <div className="space-y-3">
                <div className="flex space-x-3">
                  {parseInt(levelId) < 400 ? (
                    <Button
                      onClick={() => navigate(`/level/${parseInt(levelId) + 1}`)}
                      className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white flex-1"
                      data-testid="next-level"
                    >
                      <ArrowRight className="mr-2 h-4 w-4" />
                      Next Level ({parseInt(levelId) + 1})
                    </Button>
                  ) : (
                    <Button
                      onClick={() => navigate('/dashboard')}
                      className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white flex-1"
                      data-testid="course-complete"
                    >
                      <Trophy className="mr-2 h-4 w-4" />
                      Course Complete! 
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    onClick={() => navigate('/dashboard')}
                    data-testid="back-to-dashboard-success"
                  >
                    Dashboard
                  </Button>
                </div>
                <div className="flex space-x-3">
                  <Button
                    variant="outline"
                    onClick={runCode}
                    disabled={isRunning}
                    className="flex-1"
                  >
                    <Play className="mr-2 h-4 w-4" />
                    Run Again
                  </Button>
                  <Button
                    variant="outline"
                    onClick={resetCode}
                    className="flex-1"
                    data-testid="reset-and-retry"
                  >
                    <RotateCcw className="mr-2 h-4 w-4" />
                    Reset & Retry
                  </Button>
                </div>
              </div>
            ) : (
              // Show default run/submit buttons
              <div className="flex space-x-3">
                <Button
                  onClick={runCode}
                  disabled={isRunning}
                  className="bg-blue-500 hover:bg-blue-600 text-white flex-1"
                  data-testid="run-code"
                >
                  {isRunning ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
                      Running...
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4" />
                      Run Code
                    </>
                  )}
                </Button>
                <Button
                  onClick={submitSolution}
                  disabled={isSubmitting || !output}
                  className="bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white flex-1"
                  data-testid="submit-solution"
                >
                  {isSubmitting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="mr-2 h-4 w-4" />
                      Submit Solution
                    </>
                  )}
                </Button>
              </div>
            )}

            <Card className="glass-card border-0">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <div className="flex items-center space-x-2">
                    {result?.success ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : result && !result.success ? (
                      <XCircle className="h-5 w-5 text-red-500" />
                    ) : (
                      <Code className="h-5 w-5 text-gray-500" />
                    )}
                    <span>Output</span>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {result && (
                  <Alert className={`mb-4 ${
                    result.success 
                      ? 'border-green-200 bg-green-50' 
                      : 'border-orange-200 bg-orange-50'
                  }`}>
                    <AlertDescription className={result.success ? 'text-green-800' : 'text-orange-800'}>
                      {result.success ? (
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2">
                            <Trophy className="h-4 w-4 text-green-600" />
                            <span className="font-bold">🎉 Level Completed Successfully!</span>
                          </div>
                          <div className="text-sm">
                            You earned <span className="font-semibold text-green-700">+{result.xp_earned || 0} XP</span>
                            {parseInt(levelId) < 400 && (
                              <span> - Ready for Level {parseInt(levelId) + 1}?</span>
                            )}
                          </div>
                        </div>
                      ) : (
                        result.message
                      )}
                    </AlertDescription>
                  </Alert>
                )}
                <pre 
                  className="bg-gray-900 text-green-400 p-4 rounded-lg text-sm font-mono min-h-[100px] overflow-auto"
                  data-testid="code-output"
                >
                  {output || 'No output yet. Click "Run Code" to execute your program.'}
                </pre>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LevelPage;