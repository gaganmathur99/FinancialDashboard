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

  // Helper Methods
  void _setLoading(bool value) {
    _isLoading = value;
    notifyListeners();
  }

  void _setError(String? error) {
    _error = error;
    notifyListeners();
  }

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
    _setLoading(true);
    _setError(null);

    try {
      final prefs = await SharedPreferences.getInstance();
      final accessToken = prefs.getString(AppConfig.tokenKey);

      if (accessToken == null) {
        _setError('No authentication token found');
        _setLoading(false);
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
      } else {
        _setError(_apiService.getErrorMessage(response));
      }
    } catch (e) {
      _setError('Failed to load bank accounts: ${e.toString()}');
    } finally {
      _setLoading(false);
    }
  }

  // Get TrueLayer authentication link
  Future<String> getAuthLink() async {
    _setLoading(true);
    _setError(null);

    try {
      final response = await _apiService.get('${AppConfig.bankAuthLinkEndpoint}');

      if (_apiService.isSuccessful(response)) {
        final data = _apiService.parseResponse(response);
        final authUrl = data['auth_url'];
        return authUrl;
      } else {
        throw Exception(_apiService.getErrorMessage(response));
      }
    } catch (e) {
      _setError('Failed to get auth link: ${e.toString()}');
      throw Exception(_error);
    } finally {
      _setLoading(false);
    }
  }

  // Handle TrueLayer authentication callback
  Future<bool> handleCallback(String code) async {
    _setLoading(true);
    _setError(null);

    try {
      final response = await _apiService.get(
        '${AppConfig.callbackEndpoint}?code=$code',
        requiresAuth: true,
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
        return true;
      } else {
        _setError(_apiService.getErrorMessage(response));
        return false;
      }
    } catch (e) {
      _setError('Failed to handle callback: ${e.toString()}');
      return false;
    } finally {
      _setLoading(false);
    }
  }

  // Sync transactions for a specific account
  Future<bool> syncTransactions(String accountId) async {
    _setLoading(true);
    _setError(null);

    try {
      final response = await _apiService.post('${AppConfig.bankSyncEndpoint}/$accountId');

      if (_apiService.isSuccessful(response)) {
        // Refresh the list of accounts to get updated last sync time
        await loadBankAccounts();
        return true;
      } else {
        _setError(_apiService.getErrorMessage(response));
        return false;
      }
    } catch (e) {
      _setError('Failed to sync transactions: ${e.toString()}');
      return false;
    } finally {
      _setLoading(false);
    }
  }

  // Disconnect a bank account
  Future<bool> disconnectAccount(String accountId) async {
    _setLoading(true);
    _setError(null);

    try {
      final response = await _apiService.delete('${AppConfig.bankAccountsEndpoint}/$accountId');

      if (_apiService.isSuccessful(response)) {
        // Remove the account from the list
        _bankAccounts.removeWhere((account) => account.id == accountId);

        // Reset selected account if it was the disconnected one
        if (_selectedAccount?.id == accountId) {
          _selectedAccount = null;
        }

        return true;
      } else {
        _setError(_apiService.getErrorMessage(response));
        return false;
      }
    } catch (e) {
      _setError('Failed to disconnect account: ${e.toString()}');
      return false;
    } finally {
      _setLoading(false);
    }
  }

  // Helper to get account by ID
  BankAccount? getAccountById(String accountId) {
    return _bankAccounts.firstWhere(
      (account) => account.id == accountId,
    );
  }

  // Clear error
  void clearError() {
    _setError(null);
  }
}