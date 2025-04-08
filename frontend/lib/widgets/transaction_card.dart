import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/models.dart';
import '../theme.dart';

class TransactionCard extends StatelessWidget {
  final Transaction transaction;
  final VoidCallback? onTap;
  final bool showAccount;

  const TransactionCard({
    Key? key,
    required this.transaction,
    this.onTap,
    this.showAccount = false,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final currencyFormat = NumberFormat.currency(locale: 'en_US', symbol: transaction.currency == 'GBP' ? '£' : '\$');
    final dateFormat = DateFormat('dd MMM, hh:mm a');
    
    // Color for the amount
    final amountColor = transaction.isIncome
        ? AppTheme.incomeColor
        : transaction.isExpense
            ? AppTheme.expenseColor
            : Colors.grey;
    
    // Get the category icon
    IconData categoryIcon = _getCategoryIcon(transaction.category);
    
    return Card(
      margin: EdgeInsets.symmetric(vertical: 4),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: EdgeInsets.all(12),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // Category/merchant icon
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(24),
                ),
                child: transaction.merchantLogo != null
                    ? ClipRRect(
                        borderRadius: BorderRadius.circular(24),
                        child: Image.network(
                          transaction.merchantLogo!,
                          fit: BoxFit.cover,
                          errorBuilder: (context, error, stackTrace) {
                            return Icon(
                              categoryIcon,
                              color: Colors.grey.shade600,
                              size: 24,
                            );
                          },
                        ),
                      )
                    : Icon(
                        categoryIcon,
                        color: Colors.grey.shade600,
                        size: 24,
                      ),
              ),
              SizedBox(width: 12),
              
              // Description and date
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      transaction.merchantName ?? transaction.description,
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 16,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    SizedBox(height: 4),
                    Text(
                      dateFormat.format(transaction.timestamp),
                      style: TextStyle(
                        color: Colors.grey.shade600,
                        fontSize: 12,
                      ),
                    ),
                    if (showAccount && transaction.accountId.isNotEmpty) ...[
                      SizedBox(height: 4),
                      Text(
                        'Account: ${transaction.accountId}',
                        style: TextStyle(
                          color: Colors.grey.shade500,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              
              // Amount
              Text(
                transaction.isExpense
                    ? '-${currencyFormat.format(transaction.amount)}'
                    : '+${currencyFormat.format(transaction.amount)}',
                style: TextStyle(
                  color: amountColor,
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // Helper method to get icon based on category
  IconData _getCategoryIcon(String? category) {
    if (category == null) {
      return Icons.receipt_long;
    }
    
    switch (category.toLowerCase()) {
      case 'food':
      case 'groceries':
      case 'dining':
      case 'restaurant':
        return Icons.restaurant;
      case 'transport':
      case 'transportation':
      case 'travel':
        return Icons.directions_car;
      case 'shopping':
      case 'retail':
        return Icons.shopping_bag;
      case 'entertainment':
      case 'recreation':
        return Icons.movie;
      case 'utilities':
      case 'bills':
        return Icons.receipt;
      case 'health':
      case 'medical':
      case 'healthcare':
        return Icons.local_hospital;
      case 'education':
        return Icons.school;
      case 'housing':
      case 'rent':
      case 'mortgage':
        return Icons.home;
      case 'income':
      case 'salary':
      case 'wages':
        return Icons.payments;
      case 'transfer':
        return Icons.swap_horiz;
      default:
        return Icons.receipt_long;
    }
  }
}