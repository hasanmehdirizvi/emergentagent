import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Checkbox } from '../components/ui/checkbox';
import { Label } from '../components/ui/label';
import { Code, Zap, Trophy, Users, ArrowRight, Play, CheckCircle, Star } from 'lucide-react';

const HomePage = () => {
  const navigate = useNavigate();
  
  const features = [
    {
      icon: <Zap className="h-8 w-8 text-orange-500" />,
      title: "Interactive Learning",
      description: "Learn Python through hands-on coding challenges with instant feedback and Monaco code editor."
    },
    {
      icon: <Trophy className="h-8 w-8 text-amber-500" />,
      title: "Gamified Progress",
      description: "Earn XP, unlock levels, collect badges, and compete with friends on the leaderboard."
    },
    {
      icon: <Users className="h-8 w-8 text-emerald-500" />,
      title: "Community Driven",
      description: "Join thousands of learners and track your progress from beginner to Python expert."
    }
  ];

  const allLevels = [
    { range: "100-149", title: "Python Basics", description: "Variables, data types, operators, input/output", difficulty: "Beginner", category: "programming" },
    { range: "150-199", title: "Control Flow", description: "Conditions, loops, functions, error handling", difficulty: "Beginner", category: "programming" },
    { range: "200-249", title: "Data Structures", description: "Lists, dictionaries, sets, tuples", difficulty: "Intermediate", category: "programming" },
    { range: "250-299", title: "Object-Oriented Programming", description: "Classes, inheritance, polymorphism", difficulty: "Intermediate", category: "programming" },
    { range: "300-349", title: "Libraries and APIs", description: "Working with external libraries and APIs", difficulty: "Advanced", category: "programming" },
    { range: "350-400", title: "Real-World Projects", description: "Build complete applications and projects", difficulty: "Expert", category: "programming" },
    
    // Data Analyst Track
    { range: "DA100-149", title: "Data Analysis Basics", description: "NumPy, Pandas fundamentals, data loading", difficulty: "Beginner", category: "data-analysis" },
    { range: "DA150-199", title: "Data Manipulation", description: "Data cleaning, filtering, grouping operations", difficulty: "Beginner", category: "data-analysis" },
    { range: "DA200-249", title: "Data Visualization", description: "Matplotlib, Seaborn, interactive plots", difficulty: "Intermediate", category: "data-analysis" },
    { range: "DA250-299", title: "Statistical Analysis", description: "Descriptive stats, hypothesis testing", difficulty: "Intermediate", category: "data-analysis" },
    { range: "DA300-349", title: "Machine Learning", description: "Scikit-learn, model building and evaluation", difficulty: "Advanced", category: "data-analysis" },
    { range: "DA350-400", title: "Advanced Analytics", description: "Time series, deep learning, big data tools", difficulty: "Expert", category: "data-analysis" }
  ];

  const [selectedDifficulties, setSelectedDifficulties] = useState(['Beginner', 'Intermediate', 'Advanced', 'Expert']);
  const [selectedCategories, setSelectedCategories] = useState(['programming', 'data-analysis']);
  
  const filteredLevels = allLevels.filter(level => 
    selectedDifficulties.includes(level.difficulty) && selectedCategories.includes(level.category)
  );

  const handleDifficultyChange = (difficulty) => {
    setSelectedDifficulties(prev => 
      prev.includes(difficulty) 
        ? prev.filter(d => d !== difficulty)
        : [...prev, difficulty]
    );
  };

  const handleCategoryChange = (category) => {
    setSelectedCategories(prev => 
      prev.includes(category) 
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'Beginner': return 'bg-green-100 text-green-800 border-green-200';
      case 'Intermediate': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'Advanced': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'Expert': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="min-h-screen">
      <section className="relative overflow-hidden py-20 px-4 sm:px-6 lg:px-8">
        <div className="absolute inset-0 bg-gradient-to-r from-orange-400/10 to-amber-400/10 backdrop-blur-3xl"></div>
        <div className="relative max-w-7xl mx-auto">
          <div className="text-center">
            <div className="flex justify-center mb-6">
              <Badge variant="secondary" className="text-orange-600 bg-orange-50 border-orange-200 px-4 py-2">
                Start Your Python Journey Today!
              </Badge>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold mb-6">
              Learn Python Through
              <span className="gradient-text block mt-2">Gamified Adventures</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
              Master Python programming from Level 100 to 400 through interactive challenges, 
              earn XP, collect badges, and compete with learners worldwide.
            </p>
            {/* Module Selection */}
            <div className="mb-8">
              <h3 className="text-xl font-semibold mb-6 text-gray-800">Choose Your Learning Path:</h3>
              <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto mb-8">
                <Card className="level-card border-2 border-orange-200 hover:border-orange-400 cursor-pointer" onClick={() => navigate('/auth?module=programming')}>
                  <CardContent className="pt-6 text-center">
                    <div className="text-4xl mb-4">🐍</div>
                    <h4 className="text-xl font-bold mb-2 text-gray-900">General Programming</h4>
                    <p className="text-gray-600 text-sm">
                      Learn Python fundamentals, control flow, OOP, and build real projects
                    </p>
                    <div className="mt-4">
                      <Badge variant="outline" className="mr-2">Levels 100-400</Badge>
                      <Badge className="bg-green-100 text-green-800">Beginner Friendly</Badge>
                    </div>
                  </CardContent>
                </Card>
                
                <Card className="level-card border-2 border-blue-200 hover:border-blue-400 cursor-pointer" onClick={() => navigate('/auth?module=data-analysis')}>
                  <CardContent className="pt-6 text-center">
                    <div className="text-4xl mb-4">📊</div>
                    <h4 className="text-xl font-bold mb-2 text-gray-900">Data Analysis & Science</h4>
                    <p className="text-gray-600 text-sm">
                      Master data manipulation, visualization, and machine learning with Python
                    </p>
                    <div className="mt-4">
                      <Badge variant="outline" className="mr-2">Levels DA100-400</Badge>
                      <Badge className="bg-blue-100 text-blue-800">Analytics Focused</Badge>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                asChild
                size="lg"
                className="bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-semibold px-8 py-6 text-lg glow-effect"
                data-testid="start-learning-btn"
              >
                <Link to="/auth">
                  <Play className="mr-2 h-5 w-5" />
                  Start Learning Free
                </Link>
              </Button>
              <Button
                asChild
                variant="outline"
                size="lg"
                className="border-2 border-orange-200 hover:border-orange-300 px-8 py-6 text-lg"
                data-testid="view-curriculum-btn"
              >
                <Link to="#curriculum">
                  View Curriculum
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Why Choose PythonQuest?</h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Our innovative approach combines the best of education and gaming to make learning Python engaging and effective.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="level-card border-0 text-center" data-testid={`feature-${index}`}>
                <CardHeader>
                  <div className="flex justify-center mb-4">
                    <div className="p-3 rounded-full bg-gradient-to-br from-orange-100 to-amber-100">
                      {feature.icon}
                    </div>
                  </div>
                  <CardTitle className="text-xl font-semibold mb-2">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-gray-600 leading-relaxed">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section id="curriculum" className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-orange-50 to-amber-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Complete Python Curriculum</h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Progress through 300+ levels designed to take you from Python newbie to coding expert.
            </p>
          </div>
          
          {/* Filter Controls */}
          <div className="mb-12 p-6 bg-white/80 backdrop-blur-md rounded-2xl border border-white/20">
            <h3 className="text-lg font-semibold mb-4">Filter Learning Paths</h3>
            
            <div className="grid md:grid-cols-2 gap-6">
              {/* Category Filter */}
              <div>
                <h4 className="text-sm font-medium mb-3 text-gray-700">Learning Tracks</h4>
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Checkbox 
                      id="programming"
                      checked={selectedCategories.includes('programming')}
                      onCheckedChange={() => handleCategoryChange('programming')}
                    />
                    <Label htmlFor="programming" className="text-sm">
                      🐍 General Programming
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox 
                      id="data-analysis"
                      checked={selectedCategories.includes('data-analysis')}
                      onCheckedChange={() => handleCategoryChange('data-analysis')}
                    />
                    <Label htmlFor="data-analysis" className="text-sm">
                      📊 Data Analysis & Science
                    </Label>
                  </div>
                </div>
              </div>
              
              {/* Difficulty Filter */}
              <div>
                <h4 className="text-sm font-medium mb-3 text-gray-700">Difficulty Levels</h4>
                <div className="grid grid-cols-2 gap-2">
                  {['Beginner', 'Intermediate', 'Advanced', 'Expert'].map(difficulty => (
                    <div key={difficulty} className="flex items-center space-x-2">
                      <Checkbox 
                        id={difficulty.toLowerCase()}
                        checked={selectedDifficulties.includes(difficulty)}
                        onCheckedChange={() => handleDifficultyChange(difficulty)}
                      />
                      <Label htmlFor={difficulty.toLowerCase()} className="text-sm">
                        {difficulty}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredLevels.map((level, index) => (
              <Card key={index} className="level-card border-0" data-testid={`curriculum-${index}`}>
                <CardHeader>
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant="outline" className="text-xs font-medium">
                      Levels {level.range}
                    </Badge>
                    <Badge className={`text-xs ${getDifficultyColor(level.difficulty)}`}>
                      {level.difficulty}
                    </Badge>
                  </div>
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-lg">
                      {level.category === 'data-analysis' ? '📊' : '🐍'}
                    </span>
                    <CardTitle className="text-lg font-semibold">{level.title}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-gray-600">
                    {level.description}
                  </CardDescription>
                  <div className="flex items-center mt-4 text-sm text-gray-500">
                    <CheckCircle className="h-4 w-4 mr-1" />
                    <span>Interactive Challenges</span>
                  </div>
                  <div className="flex items-center mt-2 text-sm text-gray-500">
                    <span className="mr-2">📝</span>
                    <span>Notes & Hints Available</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="glass-card rounded-3xl p-12 text-center">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              <div className="space-y-2">
                <div className="text-3xl font-bold gradient-text">300+</div>
                <div className="text-gray-600">Coding Challenges</div>
              </div>
              <div className="space-y-2">
                <div className="text-3xl font-bold gradient-text">50+</div>
                <div className="text-gray-600">Achievement Badges</div>
              </div>
              <div className="space-y-2">
                <div className="text-3xl font-bold gradient-text">10K+</div>
                <div className="text-gray-600">Active Learners</div>
              </div>
              <div className="space-y-2">
                <div className="text-3xl font-bold gradient-text">4.9</div>
                <div className="text-gray-600 flex items-center justify-center gap-1">
                  <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                  User Rating
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">
            Ready to Start Your Python Journey?
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Join thousands of learners and start coding today. It is free to get started!
          </p>
          <Button
            asChild
            size="lg"
            className="bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-semibold px-12 py-6 text-lg glow-effect"
            data-testid="cta-start-button"
          >
            <Link to="/auth">
              <Code className="mr-2 h-5 w-5" />
              Start Coding Now
            </Link>
          </Button>
        </div>
      </section>
    </div>
  );
};

export default HomePage;