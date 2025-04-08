import 'package:flutter/foundation.dart';
import 'package:intl/intl.dart';
import 'package:shared_preferences/shared_preferences.dart';
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
      // Get the access token
      final prefs = await SharedPreferences.getInstance();
      final accessToken = prefs.getString(AppConfig.tokenKey);
      
      if (accessToken == null) {
        _error = 'No authentication token found';
        _isLoading = false;
        notifyListeners();
        return;
      }
      
      // If account ID is provided or selected account exists, filter by account
      final selectedAccountId = accountId ?? _bankService.selectedAccount?.id;
      if (selectedAccountId == null) {
        _error = 'No account selected';
        _isLoading = false;
        notifyListeners();
        return;
      }
      
      // Format dates
      final fromDate = _startDate != null 
          ? DateFormat(AppConfig.apiDateFormat).format(_startDate!)
          : DateFormat(AppConfig.apiDateFormat).format(DateTime.now().subtract(Duration(days: 90)));
          
      final toDate = _endDate != null
          ? DateFormat(AppConfig.apiDateFormat).format(_endDate!)
          : DateFormat(AppConfig.apiDateFormat).format(DateTime.now());
      
      final endpoint = '${AppConfig.bankTransactionsEndpoint}?access_token=$accessToken&account_id=$selectedAccountId&from_date=$fromDate&to_date=$toDate';
      final response = await _apiService.get(endpoint);
      
      if (_apiService.isSuccessful(response)) {
        final data = _apiService.parseResponse(response);
        
        if (data['results'] != null) {
          _transactions = (data['results'] as List)
              .map((txJson) => Transaction(
                id: txJson['transaction_id'],
                accountId: selectedAccountId,
                transactionId: txJson['transaction_id'],
                timestamp: DateTime.parse(txJson['timestamp']),
                description: txJson['description'],
                amount: txJson['amount'],
                currency: txJson['currency'] ?? 'GBP',
                merchantName: txJson['merchant_name'],
                reference: txJson['meta']?['reference'],
                type: txJson['amount'] < 0 
                    ? TransactionType.expense 
                    : TransactionType.income,
                category: _categorizeTransaction(txJson['description']),
              ))
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
  
  // Simple categorization function for transactions
  String _categorizeTransaction(String description) {
    final lowerDesc = description.toLowerCase();
    
    if (lowerDesc.contains('salary') || lowerDesc.contains('wage') || lowerDesc.contains('income')) {
      return 'Income';
    } else if (lowerDesc.contains('sainsbury') || lowerDesc.contains('tesco') || 
               lowerDesc.contains('asda') || lowerDesc.contains('aldi') || 
               lowerDesc.contains('lidl') || lowerDesc.contains('morrisons') ||
               lowerDesc.contains('waitrose') || lowerDesc.contains('grocery')) {
      return 'Groceries';
    } else if (lowerDesc.contains('uber') || lowerDesc.contains('taxi') || 
               lowerDesc.contains('bus') || lowerDesc.contains('transport') || 
               lowerDesc.contains('train') || lowerDesc.contains('rail')) {
      return 'Transport';
    } else if (lowerDesc.contains('restaurant') || lowerDesc.contains('cafe') || 
               lowerDesc.contains('coffee') || lowerDesc.contains('pub') || 
               lowerDesc.contains('bar') || lowerDesc.contains('takeaway')) {
      return 'Dining';
    } else if (lowerDesc.contains('rent') || lowerDesc.contains('mortgage') || 
               lowerDesc.contains('council tax') || lowerDesc.contains('water') || 
               lowerDesc.contains('electric') || lowerDesc.contains('gas') ||
               lowerDesc.contains('energy')) {
      return 'Housing';
    } else if (lowerDesc.contains('amazon') || lowerDesc.contains('ebay') || 
               lowerDesc.contains('shops')) {
      return 'Shopping';
    } else if (lowerDesc.contains('netflix') || lowerDesc.contains('spotify') || 
               lowerDesc.contains('cinema') || lowerDesc.contains('entertainment')) {
      return 'Entertainment';
    } else if (lowerDesc.contains('gym') || lowerDesc.contains('fitness') || 
               lowerDesc.contains('health')) {
      return 'Health';
    } else if (lowerDesc.contains('doctor') || lowerDesc.contains('dentist') || 
               lowerDesc.contains('pharmacy') || lowerDesc.contains('medical')) {
      return 'Healthcare';
    } else if (lowerDesc.contains('phone') || lowerDesc.contains('mobile') || 
               lowerDesc.contains('broadband') || lowerDesc.contains('internet')) {
      return 'Utilities';
    } else if (lowerDesc.contains('insurance') || lowerDesc.contains('premium')) {
      return 'Insurance';
    } else if (lowerDesc.contains('transfer')) {
      return 'Transfer';
    }
    
    return 'Miscellaneous';
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