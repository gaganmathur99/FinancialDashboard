import 'package:flutter/foundation.dart';
import 'package:intl/intl.dart';
import '../models/models.dart';
import '../config/app_config.dart';
import 'api_service.dart';
import 'bank_service.dart';

class TransactionService extends ChangeNotifier {
  final ApiService _apiService;
  final BankService _bankService;
  List<Transaction> _transactions = [];
  List<Transaction> _filteredTransactions = [];
  bool _isLoading = false;
  String? _error;
  
  // Filters
  DateTime? _startDate;
  DateTime? _endDate;
  List<String>? _categories;
  double? _minAmount;
  double? _maxAmount;

  TransactionService(this._apiService, this._bankService);

  // Getters
  List<Transaction> get transactions => _transactions;
  List<Transaction> get filteredTransactions => _filteredTransactions;
  bool get isLoading => _isLoading;
  String? get error => _error;
  
  // Filter getters
  DateTime? get startDate => _startDate;
  DateTime? get endDate => _endDate;
  List<String>? get categories => _categories;
  double? get minAmount => _minAmount;
  double? get maxAmount => _maxAmount;

  // Load transactions from API
  Future<void> loadTransactions({String? accountId}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      String endpoint = AppConfig.transactionsEndpoint;
      
      // If account ID is provided or selected account exists, filter by account
      final selectedAccountId = accountId ?? _bankService.selectedAccount?.id;
      if (selectedAccountId != null) {
        endpoint += '?account_id=$selectedAccountId';
      }
      
      // Add date filters if set
      if (_startDate != null) {
        final startDateStr = DateFormat(AppConfig.apiDateFormat).format(_startDate!);
        endpoint += endpoint.contains('?') ? '&' : '?';
        endpoint += 'from_date=$startDateStr';
      }
      
      if (_endDate != null) {
        final endDateStr = DateFormat(AppConfig.apiDateFormat).format(_endDate!);
        endpoint += endpoint.contains('?') ? '&' : '?';
        endpoint += 'to_date=$endDateStr';
      }
      
      final response = await _apiService.get(endpoint);
      
      if (_apiService.isSuccessful(response)) {
        final data = _apiService.parseResponse(response);
        
        if (data['transactions'] != null) {
          _transactions = (data['transactions'] as List)
              .map((txJson) => Transaction.fromJson(txJson))
              .toList();
          
          // Sort by date (newest first)
          _transactions.sort((a, b) => b.timestamp.compareTo(a.timestamp));
          
          // Apply other filters if set
          _applyFilters();
        } else {
          _transactions = [];
          _filteredTransactions = [];
        }
        
        _isLoading = false;
        notifyListeners();
      } else {
        _error = _apiService.getErrorMessage(response);
        _isLoading = false;
        notifyListeners();
      }
    } catch (e) {
      _error = 'Failed to load transactions: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
    }
  }

  // Set filters and apply them
  void setFilters({
    DateTime? startDate,
    DateTime? endDate,
    List<String>? categories,
    double? minAmount,
    double? maxAmount,
  }) {
    bool filtersChanged = false;
    
    if (startDate != _startDate) {
      _startDate = startDate;
      filtersChanged = true;
    }
    
    if (endDate != _endDate) {
      _endDate = endDate;
      filtersChanged = true;
    }
    
    if (categories != _categories) {
      _categories = categories;
      filtersChanged = true;
    }
    
    if (minAmount != _minAmount) {
      _minAmount = minAmount;
      filtersChanged = true;
    }
    
    if (maxAmount != _maxAmount) {
      _maxAmount = maxAmount;
      filtersChanged = true;
    }
    
    if (filtersChanged) {
      // If date filters changed, reload from API
      if (startDate != _startDate || endDate != _endDate) {
        loadTransactions();
      } else {
        // Otherwise, just apply filters locally
        _applyFilters();
        notifyListeners();
      }
    }
  }

  // Clear all filters
  void clearFilters() {
    _startDate = null;
    _endDate = null;
    _categories = null;
    _minAmount = null;
    _maxAmount = null;
    _filteredTransactions = [];
    loadTransactions();
  }

  // Apply filters to the transactions
  void _applyFilters() {
    if (_categories == null && _minAmount == null && _maxAmount == null) {
      _filteredTransactions = [];
      return;
    }
    
    _filteredTransactions = _transactions.where((tx) {
      bool match = true;
      
      // Filter by category
      if (_categories != null && _categories!.isNotEmpty) {
        match = match && (tx.category != null && _categories!.contains(tx.category));
      }
      
      // Filter by amount
      if (_minAmount != null) {
        match = match && tx.amount >= _minAmount!;
      }
      
      if (_maxAmount != null) {
        match = match && tx.amount <= _maxAmount!;
      }
      
      return match;
    }).toList();
  }

  // Get all unique categories
  List<String> getAllCategories() {
    final categories = <String>{};
    
    for (final tx in _transactions) {
      if (tx.category != null && tx.category!.isNotEmpty) {
        categories.add(tx.category!);
      }
    }
    
    return categories.toList()..sort();
  }

  // Get transactions grouped by day (date string -> list of transactions)
  Map<String, List<Transaction>> getTransactionsByDay() {
    final byDay = <String, List<Transaction>>{};
    
    final transactionsToUse = _filteredTransactions.isNotEmpty
        ? _filteredTransactions
        : _transactions;
    
    for (final tx in transactionsToUse) {
      final dateStr = tx.timestamp.toIso8601String().split('T')[0];
      
      if (!byDay.containsKey(dateStr)) {
        byDay[dateStr] = [];
      }
      
      byDay[dateStr]!.add(tx);
    }
    
    // Sort transactions within each day
    byDay.forEach((key, list) {
      list.sort((a, b) => b.timestamp.compareTo(a.timestamp));
    });
    
    return byDay;
  }

  // Get spending by category (category -> amount)
  Map<String, double> getSpendingByCategory() {
    final byCategory = <String, double>{};
    
    final transactionsToUse = _filteredTransactions.isNotEmpty
        ? _filteredTransactions
        : _transactions;
    
    for (final tx in transactionsToUse) {
      if (tx.isExpense) {
        final category = tx.category ?? 'Uncategorized';
        
        if (!byCategory.containsKey(category)) {
          byCategory[category] = 0;
        }
        
        byCategory[category] = byCategory[category]! + tx.amount;
      }
    }
    
    return byCategory;
  }

  // Get spending by day (date -> amount)
  Map<DateTime, double> getSpendingByDay() {
    final byDay = <DateTime, double>{};
    
    final transactionsToUse = _filteredTransactions.isNotEmpty
        ? _filteredTransactions
        : _transactions;
    
    for (final tx in transactionsToUse) {
      if (tx.isExpense) {
        final date = DateTime(
          tx.timestamp.year,
          tx.timestamp.month,
          tx.timestamp.day,
        );
        
        if (!byDay.containsKey(date)) {
          byDay[date] = 0;
        }
        
        byDay[date] = byDay[date]! + tx.amount;
      }
    }
    
    return byDay;
  }

  // Get total income
  double getTotalIncome() {
    final transactionsToUse = _filteredTransactions.isNotEmpty
        ? _filteredTransactions
        : _transactions;
    
    return transactionsToUse
        .where((tx) => tx.isIncome)
        .fold(0, (sum, tx) => sum + tx.amount);
  }

  // Get total expenses
  double getTotalExpenses() {
    final transactionsToUse = _filteredTransactions.isNotEmpty
        ? _filteredTransactions
        : _transactions;
    
    return transactionsToUse
        .where((tx) => tx.isExpense)
        .fold(0, (sum, tx) => sum + tx.amount);
  }

  // Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }
}