class BankAccount {
  final String? id;
  final String? userId;
  final String accountId;
  final String? providerId;
  final String accountName;
  final String accountType;
  final String? accountNumber;
  final String? sortCode;
  final double? balance;
  final String? currency;
  final String? accessToken;
  final String? refreshToken;
  final DateTime? tokenExpiryDate;
  final DateTime? lastSynced;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  BankAccount({
    this.id,
    this.userId,
    required this.accountId,
    this.providerId,
    required this.accountName,
    required this.accountType,
    this.accountNumber,
    this.sortCode,
    this.balance,
    this.currency = 'GBP',
    this.accessToken,
    this.refreshToken,
    this.tokenExpiryDate,
    this.lastSynced,
    this.createdAt,
    this.updatedAt,
  });

  factory BankAccount.fromJson(Map<String, dynamic> json) {
    return BankAccount(
      id: json['id']?.toString(),
      userId: json['user_id']?.toString(),
      accountId: json['account_id'].toString(),
      providerId: json['provider_id']?.toString(),
      accountName: json['account_name'],
      accountType: json['account_type'],
      accountNumber: json['account_number'],
      sortCode: json['sort_code'],
      balance: json['balance'] != null ? double.parse(json['balance'].toString()) : null,
      currency: json['currency'] ?? 'GBP',
      accessToken: json['access_token'],
      refreshToken: json['refresh_token'],
      tokenExpiryDate: json['token_expiry_date'] != null
          ? DateTime.parse(json['token_expiry_date'])
          : null,
      lastSynced: json['last_synced'] != null
          ? DateTime.parse(json['last_synced'])
          : null,
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
      'provider_id': providerId,
      'account_name': accountName,
      'account_type': accountType,
      'account_number': accountNumber,
      'sort_code': sortCode,
      'balance': balance,
      'currency': currency,
      'access_token': accessToken,
      'refresh_token': refreshToken,
      'token_expiry_date': tokenExpiryDate?.toIso8601String(),
      'last_synced': lastSynced?.toIso8601String(),
      'created_at': createdAt?.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }

  BankAccount copyWith({
    String? id,
    String? userId,
    String? accountId,
    String? providerId,
    String? accountName,
    String? accountType,
    String? accountNumber,
    String? sortCode,
    double? balance,
    String? currency,
    String? accessToken,
    String? refreshToken,
    DateTime? tokenExpiryDate,
    DateTime? lastSynced,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return BankAccount(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      accountId: accountId ?? this.accountId,
      providerId: providerId ?? this.providerId,
      accountName: accountName ?? this.accountName,
      accountType: accountType ?? this.accountType,
      accountNumber: accountNumber ?? this.accountNumber,
      sortCode: sortCode ?? this.sortCode,
      balance: balance ?? this.balance,
      currency: currency ?? this.currency,
      accessToken: accessToken ?? this.accessToken,
      refreshToken: refreshToken ?? this.refreshToken,
      tokenExpiryDate: tokenExpiryDate ?? this.tokenExpiryDate,
      lastSynced: lastSynced ?? this.lastSynced,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}