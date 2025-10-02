import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import MonacoEditor from '@monaco-editor/react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import {
  Play,
  RotateCcw,
  CheckCircle,
  XCircle,
  Lightbulb,
  ArrowLeft,
  Target,
  Code
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const LevelPage = () => {
  const { levelId } = useParams();
  const navigate = useNavigate();
  const { updateUserStats } = useAuth();
  const [level, setLevel] = useState(null);
  const [code, setCode] = useState('');
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [showHints, setShowHints] = useState(false);
  const [attempts, setAttempts] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLevel();
  }, [levelId]);

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
      
      for (let line of lines) {
        line = line.trim();
        
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
          const rangeMatch = line.match(/for\s+(\w+)\s+in\s+range\((.*)\)/);
          if (rangeMatch) {
            const [, varName, rangeParams] = rangeMatch;
            const params = rangeParams.split(',').map(p => parseInt(p.trim()));
            
            let start = 0, end = params[0], step = 1;
            if (params.length === 2) {
              [start, end] = params;
            } else if (params.length === 3) {
              [start, end, step] = params;
            }
            
            for (let i = start; i < end; i += step) {
              variables[varName] = i;
              output.push(i.toString());
            }
          }
        }
      }
      
      return output.join('\n') || 'No output';
    } catch (error) {
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
          
          <Button 
            variant="outline" 
            onClick={() => setShowHints(!showHints)}
            data-testid="toggle-hints"
          >
            <Lightbulb className="mr-2 h-4 w-4" />
            {showHints ? 'Hide' : 'Show'} Hints
          </Button>
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

            {showHints && level.hints && level.hints.length > 0 && (
              <Card className="glass-card border-0 border-l-4 border-l-amber-400">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2 text-amber-700">
                    <Lightbulb className="h-5 w-5" />
                    <span>Hints</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {level.hints.map((hint, index) => (
                    <div key={index} className="flex items-start space-x-2">
                      <span className="inline-block w-5 h-5 rounded-full bg-amber-100 text-amber-700 text-xs font-bold flex items-center justify-center mt-0.5">
                        {index + 1}
                      </span>
                      <p className="text-amber-700">{hint}</p>
                    </div>
                  ))}
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
                      {result.message}
                      {result.success && result.xp_earned > 0 && (
                        <span className="ml-2 font-semibold">+{result.xp_earned} XP</span>
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