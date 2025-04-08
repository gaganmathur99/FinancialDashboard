import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config/app_config.dart';

class ApiService {
  static const String _baseUrl = AppConfig.apiBaseUrl;
  static const int _timeout = AppConfig.apiTimeoutSeconds;
  static const String _tokenKey = AppConfig.tokenKey;
  static const String _refreshTokenKey = AppConfig.refreshTokenKey;
  
  Future<http.Response> get(String endpoint, {Map<String, String>? headers, bool requiresAuth = true}) async {
    final requestHeaders = {
      'Content-Type': 'application/json',
      ...?headers,
    };
    
    if (requiresAuth) {
      final token = await _getToken();
      requestHeaders['Authorization'] = 'Bearer $token';
    }
    
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl$endpoint'),
        headers: requestHeaders,
      ).timeout(Duration(seconds: _timeout));
      
      if (response.statusCode == 401) {
        // Token expired, try to refresh
        final refreshed = await _refreshToken();
        if (refreshed) {
          // Retry with new token
          return get(endpoint, headers: headers);
        }
      }
      
      return response;
    } catch (e) {
      throw Exception('Failed to make GET request: $e');
    }
  }
  
  Future<http.Response> post(String endpoint, {
    Map<String, String>? headers, 
    Object? body, 
    bool requiresAuth = true,
  }) async {
    final requestHeaders = {
      'Content-Type': 'application/json',
      ...?headers,
    };
    
    if (requiresAuth) {
      final token = await _getToken();
      requestHeaders['Authorization'] = 'Bearer $token';
    }
    
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl$endpoint'),
        headers: requestHeaders,
        body: body != null ? jsonEncode(body) : null,
      ).timeout(Duration(seconds: _timeout));
      
      if (requiresAuth && response.statusCode == 401) {
        // Token expired, try to refresh
        final refreshed = await _refreshToken();
        if (refreshed) {
          // Retry with new token
          return post(endpoint, headers: headers, body: body);
        }
      }
      
      return response;
    } catch (e) {
      throw Exception('Failed to make POST request: $e');
    }
  }
  
  Future<http.Response> put(String endpoint, {
    Map<String, String>? headers, 
    Object? body,
    bool requiresAuth = true,
  }) async {
    final requestHeaders = {
      'Content-Type': 'application/json',
      ...?headers,
    };
    
    if (requiresAuth) {
      final token = await _getToken();
      requestHeaders['Authorization'] = 'Bearer $token';
    }
    
    try {
      final response = await http.put(
        Uri.parse('$_baseUrl$endpoint'),
        headers: requestHeaders,
        body: body != null ? jsonEncode(body) : null,
      ).timeout(Duration(seconds: _timeout));
      
      if (response.statusCode == 401) {
        // Token expired, try to refresh
        final refreshed = await _refreshToken();
        if (refreshed) {
          // Retry with new token
          return put(endpoint, headers: headers, body: body);
        }
      }
      
      return response;
    } catch (e) {
      throw Exception('Failed to make PUT request: $e');
    }
  }
  
  Future<http.Response> delete(String endpoint, {
    Map<String, String>? headers,
    bool requiresAuth = true,
  }) async {
    final requestHeaders = {
      'Content-Type': 'application/json',
      ...?headers,
    };
    
    if (requiresAuth) {
      final token = await _getToken();
      requestHeaders['Authorization'] = 'Bearer $token';
    }
    
    try {
      final response = await http.delete(
        Uri.parse('$_baseUrl$endpoint'),
        headers: requestHeaders,
      ).timeout(Duration(seconds: _timeout));
      
      if (response.statusCode == 401) {
        // Token expired, try to refresh
        final refreshed = await _refreshToken();
        if (refreshed) {
          // Retry with new token
          return delete(endpoint, headers: headers);
        }
      }
      
      return response;
    } catch (e) {
      throw Exception('Failed to make DELETE request: $e');
    }
  }
  
  // Token management methods
  Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }
  
  Future<void> saveTokens(String token, String refreshToken) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
    await prefs.setString(_refreshTokenKey, refreshToken);
  }
  
  Future<void> clearTokens() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_refreshTokenKey);
  }
  
  Future<bool> _refreshToken() async {
    final prefs = await SharedPreferences.getInstance();
    final refreshToken = prefs.getString(_refreshTokenKey);
    
    if (refreshToken == null) {
      return false;
    }
    
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl${AppConfig.refreshTokenEndpoint}'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh_token': refreshToken}),
      ).timeout(Duration(seconds: _timeout));
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        await saveTokens(data['access_token'], data['refresh_token']);
        return true;
      } else {
        // If refresh failed, clear tokens
        await clearTokens();
        return false;
      }
    } catch (e) {
      // If refresh failed with exception, clear tokens
      await clearTokens();
      return false;
    }
  }
  
  // Helper methods for API response handling
  Map<String, dynamic> parseResponse(http.Response response) {
    try {
      if (response.body.isEmpty) {
        return {};
      }
      return jsonDecode(response.body);
    } catch (e) {
      throw Exception('Failed to parse response: $e');
    }
  }
  
  bool isSuccessful(http.Response response) {
    return response.statusCode >= 200 && response.statusCode < 300;
  }
  
  String getErrorMessage(http.Response response) {
    try {
      if (response.body.isEmpty) {
        return 'An error occurred';
      }
      final data = jsonDecode(response.body);
      return data['detail'] ?? data['message'] ?? 'An error occurred';
    } catch (e) {
      return 'An error occurred';
    }
  }
}