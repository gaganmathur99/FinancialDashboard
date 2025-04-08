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
      final response = await _apiService.get(AppConfig.bankAccountsEndpoint);
      
      if (_apiService.isSuccessful(response)) {
        final data = _apiService.parseResponse(response);
        
        if (data['accounts'] != null) {
          _bankAccounts = (data['accounts'] as List)
              .map((accountJson) => BankAccount.fromJson(accountJson))
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
      final response = await _apiService.get(AppConfig.bankAuthLinkEndpoint);
      
      if (_apiService.isSuccessful(response)) {
        final data = _apiService.parseResponse(response);
        
        _isLoading = false;
        notifyListeners();
        return data['auth_url'] ?? '';
      } else {
        _error = _apiService.getErrorMessage(response);
        _isLoading = false;
        notifyListeners();
        throw Exception(_error);
      }
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
      final response = await _apiService.post(
        AppConfig.bankCallbackEndpoint,
        body: {
          'code': code,
          'redirect_uri': AppConfig.trueLayerRedirectUri,
        },
      );
      
      if (_apiService.isSuccessful(response)) {
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