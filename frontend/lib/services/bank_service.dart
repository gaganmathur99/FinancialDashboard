import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/models.dart';
import '../config/app_config.dart';
import 'api_service.dart';

class BankService extends ChangeNotifier {
  final ApiService _apiService;
  List<BankAccount> _bankAccounts = [];
  BankAccount? _selectedAccount;
  bool _isLoading = false;
  String? _error;

  BankService(this._apiService);

  // Getters
  List<BankAccount> get bankAccounts => _bankAccounts;
  BankAccount? get selectedAccount => _selectedAccount;
  bool get isLoading => _isLoading;
  String? get error => _error;

  // Select an account
  void selectAccount(BankAccount? account) {
    _selectedAccount = account;
    notifyListeners();
  }

  // Reset selected account (to show all accounts)
  void resetSelectedAccount() {
    _selectedAccount = null;
    notifyListeners();
  }

  // Load bank accounts from API
  Future<void> loadBankAccounts() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      // Get the access token
      final prefs = await SharedPreferences.getInstance();
      final accessToken = prefs.getString(AppConfig.tokenKey);
      
      if (accessToken == null) {
        _error = 'No authentication token found';
        _isLoading = false;
        notifyListeners();
        return;
      }
      
      final response = await _apiService.get('${AppConfig.bankAccountsEndpoint}?access_token=$accessToken');
      
      if (_apiService.isSuccessful(response)) {
        final data = _apiService.parseResponse(response);
        
        if (data['results'] != null) {
          _bankAccounts = (data['results'] as List)
              .map((accountJson) => BankAccount(
                  id: accountJson['account_id'],
                  accountId: accountJson['account_id'],
                  accountName: accountJson['display_name'] ?? 'Account',
                  accountType: accountJson['account_type'] ?? 'Unknown',
                  accountNumber: accountJson['account_number']?['number'],
                  sortCode: accountJson['account_number']?['sort_code'],
                  balance: accountJson['balance'] != null ? double.parse(accountJson['balance'].toString()) : 0.0,
                  currency: accountJson['currency'] ?? 'GBP',
                  providerId: accountJson['provider']?['provider_id'],
                ))
              .toList();
        } else {
          _bankAccounts = [];
        }
        
        // Reset selected account if it no longer exists
        if (_selectedAccount != null) {
          final stillExists = _bankAccounts.any((account) => account.id == _selectedAccount!.id);
          if (!stillExists) {
            _selectedAccount = null;
          }
        }
        
        _isLoading = false;
        notifyListeners();
      } else {
        _error = _apiService.getErrorMessage(response);
        _isLoading = false;
        notifyListeners();
      }
    } catch (e) {
      _error = 'Failed to load bank accounts: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
    }
  }

  // Get TrueLayer authentication link
  Future<String> getAuthLink() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      // Our FastAPI endpoint redirects directly to TrueLayer
      // so we just return that URL
      final authUrl = '${AppConfig.apiBaseUrl}${AppConfig.bankAuthLinkEndpoint}';
      
      _isLoading = false;
      notifyListeners();
      return authUrl;
    } catch (e) {
      _error = 'Failed to get auth link: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
      throw Exception(_error);
    }
  }

  // Handle TrueLayer authentication callback
  Future<bool> handleCallback(String code) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      final response = await _apiService.get(
        '${AppConfig.callbackEndpoint}?code=$code',
        requiresAuth: false,
      );
      
      if (_apiService.isSuccessful(response)) {
        final data = _apiService.parseResponse(response);
        
        // Save tokens from response if available
        if (data['tokens'] != null) {
          await _apiService.saveTokens(
            data['tokens']['access_token'],
            data['tokens']['refresh_token'],
          );
        }
        
        // Refresh the list of accounts
        await loadBankAccounts();
        
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
      _error = 'Failed to handle callback: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  // Sync transactions for a specific account
  Future<bool> syncTransactions(String accountId) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      final response = await _apiService.post(
        '${AppConfig.bankSyncEndpoint}/$accountId',
      );
      
      if (_apiService.isSuccessful(response)) {
        // Refresh the list of accounts to get updated last sync time
        await loadBankAccounts();
        
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
      _error = 'Failed to sync transactions: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  // Disconnect a bank account
  Future<bool> disconnectAccount(String accountId) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      final response = await _apiService.delete(
        '${AppConfig.bankAccountsEndpoint}/$accountId',
      );
      
      if (_apiService.isSuccessful(response)) {
        // Remove the account from the list
        _bankAccounts.removeWhere((account) => account.id == accountId);
        
        // Reset selected account if it was the disconnected one
        if (_selectedAccount?.id == accountId) {
          _selectedAccount = null;
        }
        
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
      _error = 'Failed to disconnect account: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  // Helper to get account by ID
  BankAccount? getAccountById(String accountId) {
    return _bankAccounts.firstWhere(
      (account) => account.id == accountId,
      orElse: () => BankAccount(
        accountId: 'unknown',
        accountName: 'Unknown Account',
        accountType: 'Unknown',
      ),
    );
  }

  // Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }
}