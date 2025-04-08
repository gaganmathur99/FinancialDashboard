class Transaction {
  final String? id;
  final String? userId;
  final String accountId;
  final String transactionId;
  final DateTime timestamp;
  final String description;
  final double amount;
  final String currency;
  final String? category;
  final String? merchantName;
  final String? merchantLogo;
  final String? reference;
  final TransactionType type;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  Transaction({
    this.id,
    this.userId,
    required this.accountId,
    required this.transactionId,
    required this.timestamp,
    required this.description,
    required this.amount,
    this.currency = 'GBP',
    this.category,
    this.merchantName,
    this.merchantLogo,
    this.reference,
    required this.type,
    this.createdAt,
    this.updatedAt,
  });

  factory Transaction.fromJson(Map<String, dynamic> json) {
    return Transaction(
      id: json['id']?.toString(),
      userId: json['user_id']?.toString(),
      accountId: json['account_id'],
      transactionId: json['transaction_id'],
      timestamp: DateTime.parse(json['timestamp']),
      description: json['description'],
      amount: double.parse(json['amount'].toString()),
      currency: json['currency'] ?? 'GBP',
      category: json['category'],
      merchantName: json['merchant_name'],
      merchantLogo: json['merchant_logo'],
      reference: json['reference'],
      type: _parseTransactionType(json['type']),
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : null,
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'])
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'account_id': accountId,
      'transaction_id': transactionId,
      'timestamp': timestamp.toIso8601String(),
      'description': description,
      'amount': amount,
      'currency': currency,
      'category': category,
      'merchant_name': merchantName,
      'merchant_logo': merchantLogo,
      'reference': reference,
      'type': type.toString().split('.').last,
      'created_at': createdAt?.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }

  Transaction copyWith({
    String? id,
    String? userId,
    String? accountId,
    String? transactionId,
    DateTime? timestamp,
    String? description,
    double? amount,
    String? currency,
    String? category,
    String? merchantName,
    String? merchantLogo,
    String? reference,
    TransactionType? type,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return Transaction(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      accountId: accountId ?? this.accountId,
      transactionId: transactionId ?? this.transactionId,
      timestamp: timestamp ?? this.timestamp,
      description: description ?? this.description,
      amount: amount ?? this.amount,
      currency: currency ?? this.currency,
      category: category ?? this.category,
      merchantName: merchantName ?? this.merchantName,
      merchantLogo: merchantLogo ?? this.merchantLogo,
      reference: reference ?? this.reference,
      type: type ?? this.type,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  // Helper method to determine if transaction is an expense
  bool get isExpense => type == TransactionType.expense;

  // Helper method to determine if transaction is income
  bool get isIncome => type == TransactionType.income;

  // Helper method to determine if transaction is a transfer
  bool get isTransfer => type == TransactionType.transfer;

  // Get formatted amount with sign
  String get signedAmount {
    if (isExpense) {
      return '-$amount';
    } else if (isIncome) {
      return '+$amount';
    }
    return amount.toString();
  }
}

enum TransactionType {
  income,
  expense,
  transfer,
}

// Helper to parse transaction type from string
TransactionType _parseTransactionType(String? typeStr) {
  switch (typeStr?.toLowerCase()) {
    case 'income':
      return TransactionType.income;
    case 'transfer':
      return TransactionType.transfer;
    case 'expense':
    default:
      return TransactionType.expense;
  }
}