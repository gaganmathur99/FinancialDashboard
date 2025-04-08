import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/models.dart';
import '../config/app_config.dart';
import 'api_service.dart';

class AuthService extends ChangeNotifier {
  final ApiService _apiService;
  User? _currentUser;
  bool _isLoading = false;
  String? _error;
  bool _isLoggedIn = false;

  AuthService(this._apiService) {
    _checkLoggedInStatus();
  }

  // Getters
  User? get currentUser => _currentUser;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isLoggedIn => _isLoggedIn;

  // Check if user is logged in
  Future<void> _checkLoggedInStatus() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(AppConfig.tokenKey);
    
    if (token != null) {
      _isLoggedIn = true;
      
      // Try to load user profile
      await _loadUserProfile();
      
      notifyListeners();
    }
  }

  // Login
  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      final response = await _apiService.post(
        AppConfig.loginEndpoint,
        body: {
          'email': email,
          'password': password,
        },
        requiresAuth: false,
      );
      
      if (_apiService.isSuccessful(response)) {
        final data = _apiService.parseResponse(response);
        
        // Save tokens
        await _apiService.saveTokens(
          data['access_token'],
          data['refresh_token'],
        );
        
        // Save user ID
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(AppConfig.userIdKey, data['user_id'].toString());
        
        _isLoggedIn = true;
        
        // Load user profile
        await _loadUserProfile();
        
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _error = _apiService.getErrorMessage(response);
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _error = 'Failed to login: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  // Register
  Future<bool> register(String email, String password, String fullName) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      final response = await _apiService.post(
        AppConfig.registerEndpoint,
        body: {
          'email': email,
          'password': password,
          'full_name': fullName,
        },
        requiresAuth: false,
      );
      
      if (_apiService.isSuccessful(response)) {
        final data = _apiService.parseResponse(response);
        
        // Save tokens
        await _apiService.saveTokens(
          data['access_token'],
          data['refresh_token'],
        );
        
        // Save user ID
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(AppConfig.userIdKey, data['user_id'].toString());
        
        _isLoggedIn = true;
        
        // Load user profile
        await _loadUserProfile();
        
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _error = _apiService.getErrorMessage(response);
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _error = 'Failed to register: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  // Logout
  Future<void> logout() async {
    try {
      await _apiService.clearTokens();
      
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(AppConfig.userIdKey);
      
      _currentUser = null;
      _isLoggedIn = false;
      notifyListeners();
    } catch (e) {
      _error = 'Failed to logout: ${e.toString()}';
      notifyListeners();
    }
  }

  // Load user profile
  Future<void> _loadUserProfile() async {
    try {
      final response = await _apiService.get(AppConfig.userProfileEndpoint);
      
      if (_apiService.isSuccessful(response)) {
        final data = _apiService.parseResponse(response);
        _currentUser = User.fromJson(data);
      } else {
        // If failed to load profile, user might be logged out
        if (response.statusCode == 401) {
          _isLoggedIn = false;
        }
      }
    } catch (e) {
      _error = 'Failed to load user profile: ${e.toString()}';
    }
  }

  // Update user profile
  Future<bool> updateProfile(String fullName, {String? avatarUrl}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      final response = await _apiService.put(
        AppConfig.userProfileEndpoint,
        body: {
          'full_name': fullName,
          if (avatarUrl != null) 'avatar_url': avatarUrl,
        },
      );
      
      if (_apiService.isSuccessful(response)) {
        final data = _apiService.parseResponse(response);
        _currentUser = User.fromJson(data);
        
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _error = _apiService.getErrorMessage(response);
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _error = 'Failed to update profile: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  // Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }
}