import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Progress } from './ui/progress';
import { Code, Trophy, User, LogOut, Home, BookOpen, Settings } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';

const Navbar = () => {
  const { currentUser, userStats, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <nav className="glass-card border-0 border-b border-white/20 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link
            to={currentUser ? "/dashboard" : "/"}
            className="flex items-center space-x-2 text-xl font-bold gradient-text hover:scale-105 transition-transform"
          >
            <Code className="h-8 w-8" />
            <span className="font-extrabold">PythonQuest</span>
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center space-x-6">
            {currentUser ? (
              <>
                <Link
                  to="/dashboard"
                  className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-white/20 transition-colors"
                  data-testid="nav-dashboard"
                >
                  <Home className="h-4 w-4" />
                  <span>Dashboard</span>
                </Link>
                <Link
                  to="/leaderboard"
                  className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-white/20 transition-colors"
                  data-testid="nav-leaderboard"
                >
                  <Trophy className="h-4 w-4" />
                  <span>Leaderboard</span>
                </Link>
              </>
            ) : (
              <Link
                to="/"
                className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-white/20 transition-colors"
                data-testid="nav-home"
              >
                <BookOpen className="h-4 w-4" />
                <span>Home</span>
              </Link>
            )}
          </div>

          {/* User Section */}
          <div className="flex items-center space-x-4">
            {currentUser ? (
              <>
                {/* XP Display */}
                <div className="hidden sm:flex flex-col items-end space-y-1">
                  <div className="text-sm font-medium" data-testid="user-xp">
                    Level {userStats?.current_level || 100} - {userStats?.total_xp || 0} XP
                  </div>
                  <div className="w-20">
                    <Progress 
                      value={((userStats?.total_xp || 0) % 100)} 
                      className="h-2"
                      data-testid="xp-progress"
                    />
                  </div>
                </div>

                {/* User Menu */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="p-0 h-10 w-10">
                      <Avatar className="h-10 w-10">
                        <AvatarFallback className="bg-gradient-to-br from-orange-400 to-amber-500 text-white font-bold">
                          {currentUser.username?.charAt(0).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent className="w-56" align="end">
                    <DropdownMenuLabel>
                      <div className="flex flex-col space-y-1">
                        <p className="text-sm font-medium leading-none" data-testid="user-name">
                          {currentUser.username}
                        </p>
                        <p className="text-xs leading-none text-muted-foreground">
                          {currentUser.email}
                        </p>
                      </div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => navigate('/profile')} data-testid="nav-profile">
                      <User className="mr-2 h-4 w-4" />
                      <span>Profile</span>
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate('/dashboard')}>
                      <Home className="mr-2 h-4 w-4" />
                      <span>Dashboard</span>
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate('/leaderboard')}>
                      <Trophy className="mr-2 h-4 w-4" />
                      <span>Leaderboard</span>
                    </DropdownMenuItem>
                    {currentUser?.username?.toLowerCase().includes('admin') && (
                      <DropdownMenuItem onClick={() => navigate('/admin')}>
                        <Settings className="mr-2 h-4 w-4" />
                        <span>Admin Panel</span>
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={handleLogout} data-testid="logout-button">
                      <LogOut className="mr-2 h-4 w-4" />
                      <span>Log out</span>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            ) : (
              <div className="flex items-center space-x-3">
                <Button 
                  variant="ghost" 
                  onClick={() => navigate('/auth')}
                  className="hover:bg-white/20"
                  data-testid="login-button"
                >
                  Login
                </Button>
                <Button
                  onClick={() => navigate('/auth')}
                  className="bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-medium px-6 glow-effect"
                  data-testid="signup-button"
                >
                  Get Started
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;