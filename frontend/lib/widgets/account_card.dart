import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/models.dart';
import '../theme.dart';

class AccountCard extends StatelessWidget {
  final BankAccount account;
  final bool isSelected;
  final VoidCallback? onTap;
  final VoidCallback? onSync;

  const AccountCard({
    Key? key,
    required this.account,
    this.isSelected = false,
    this.onTap,
    this.onSync,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final currencyFormat = NumberFormat.currency(
      locale: 'en_US', 
      symbol: account.currency == 'GBP' ? '£' : '\$'
    );
    final dateFormat = DateFormat('MMM dd, yyyy • hh:mm a');
    
    // Get last sync time or placeholder
    final lastSyncText = account.lastSynced != null
        ? 'Last synced: ${dateFormat.format(account.lastSynced!)}'
        : 'Not synced yet';
    
    // Get account type icon
    final IconData accountIcon = _getAccountTypeIcon(account.accountType);
    
    return Card(
      margin: EdgeInsets.symmetric(vertical: 8),
      color: isSelected ? AppTheme.primaryColor.withOpacity(0.1) : null,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: isSelected
            ? BorderSide(color: AppTheme.primaryColor, width: 2)
            : BorderSide.none,
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Account name and icon
              Row(
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: AppTheme.primaryColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(24),
                    ),
                    child: Icon(
                      accountIcon,
                      color: AppTheme.primaryColor,
                      size: 24,
                    ),
                  ),
                  SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          account.accountName,
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 18,
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          account.accountType,
                          style: TextStyle(
                            color: Colors.grey.shade600,
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                  ),
                  if (onSync != null)
                    IconButton(
                      icon: Icon(Icons.sync),
                      onPressed: onSync,
                      tooltip: 'Sync transactions',
                    ),
                ],
              ),
              SizedBox(height: 16),
              
              // Account details
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // Account number/sort code
                  if (account.accountNumber != null || account.sortCode != null)
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          if (account.accountNumber != null) ...[
                            Text(
                              'Account Number',
                              style: TextStyle(
                                color: Colors.grey.shade600,
                                fontSize: 12,
                              ),
                            ),
                            SizedBox(height: 2),
                            Text(
                              '•••• ${account.accountNumber!.substring(account.accountNumber!.length - 4)}',
                              style: TextStyle(
                                fontWeight: FontWeight.w500,
                                fontSize: 14,
                              ),
                            ),
                          ],
                          if (account.sortCode != null) ...[
                            SizedBox(height: 8),
                            Text(
                              'Sort Code',
                              style: TextStyle(
                                color: Colors.grey.shade600,
                                fontSize: 12,
                              ),
                            ),
                            SizedBox(height: 2),
                            Text(
                              account.sortCode!,
                              style: TextStyle(
                                fontWeight: FontWeight.w500,
                                fontSize: 14,
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  
                  // Balance
                  if (account.balance != null)
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            'Balance',
                            style: TextStyle(
                              color: Colors.grey.shade600,
                              fontSize: 12,
                            ),
                          ),
                          SizedBox(height: 2),
                          Text(
                            currencyFormat.format(account.balance),
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 20,
                              color: account.balance! >= 0
                                  ? AppTheme.incomeColor
                                  : AppTheme.expenseColor,
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
              SizedBox(height: 16),
              
              // Last sync info
              Text(
                lastSyncText,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey.shade600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // Helper method to get icon based on account type
  IconData _getAccountTypeIcon(String accountType) {
    switch (accountType.toLowerCase()) {
      case 'checking':
      case 'current':
        return Icons.account_balance;
      case 'savings':
        return Icons.savings;
      case 'credit':
      case 'credit card':
        return Icons.credit_card;
      case 'loan':
      case 'mortgage':
        return Icons.home;
      case 'investment':
        return Icons.trending_up;
      case 'pension':
      case 'retirement':
        return Icons.monetization_on;
      default:
        return Icons.account_balance;
    }
  }
}