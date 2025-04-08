import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';

import '../models/models.dart';
import '../services/services.dart';
import '../widgets/widgets.dart';
import '../theme.dart';

class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;
  final currencyFormat = NumberFormat.currency(locale: 'en_US', symbol: '\$');

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    // Load bank accounts
    await Provider.of<BankService>(context, listen: false).loadBankAccounts();
    
    // Load transactions
    await Provider.of<TransactionService>(context, listen: false).loadTransactions();
  }

  // Navigation
  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    final authService = Provider.of<AuthService>(context);
    final bankService = Provider.of<BankService>(context);
    final transactionService = Provider.of<TransactionService>(context);
    
    // Get selected account name or "All Accounts"
    final selectedAccountName = bankService.selectedAccount?.accountName ?? 'All Accounts';
    
    // Main content based on selected tab
    Widget _buildBody() {
      switch (_selectedIndex) {
        case 0:
          return _buildDashboard();
        case 1:
          return _buildTransactions();
        case 2:
          return _buildAccounts();
        case 3:
          return _buildAnalytics();
        default:
          return _buildDashboard();
      }
    }
    
    return Scaffold(
      appBar: AppBar(
        title: Text(selectedAccountName),
        actions: [
          // Profile menu
          PopupMenuButton<String>(
            icon: CircleAvatar(
              backgroundColor: Theme.of(context).primaryColor.withOpacity(0.2),
              child: Text(
                authService.currentUser?.fullName?.substring(0, 1).toUpperCase() ?? 'U',
                style: TextStyle(
                  color: Theme.of(context).primaryColor,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            onSelected: (value) {
              if (value == 'logout') {
                authService.logout();
                Navigator.of(context).pushReplacementNamed('/login');
              } else if (value == 'settings') {
                Navigator.of(context).pushNamed('/settings');
              }
            },
            itemBuilder: (context) => [
              PopupMenuItem(
                value: 'profile',
                child: Row(
                  children: [
                    Icon(Icons.person),
                    SizedBox(width: 8),
                    Text('Profile'),
                  ],
                ),
              ),
              PopupMenuItem(
                value: 'settings',
                child: Row(
                  children: [
                    Icon(Icons.settings),
                    SizedBox(width: 8),
                    Text('Settings'),
                  ],
                ),
              ),
              PopupMenuItem(
                value: 'logout',
                child: Row(
                  children: [
                    Icon(Icons.logout),
                    SizedBox(width: 8),
                    Text('Logout'),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        child: bankService.isLoading || transactionService.isLoading
            ? AppLoadingIndicator()
            : _buildBody(),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: _onItemTapped,
        items: [
          BottomNavigationBarItem(
            icon: Icon(Icons.dashboard),
            label: 'Dashboard',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.receipt_long),
            label: 'Transactions',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.account_balance),
            label: 'Accounts',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.analytics),
            label: 'Analytics',
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.of(context).pushNamed('/connect');
        },
        child: Icon(Icons.add),
        tooltip: 'Connect Bank',
      ),
    );
  }

  // Dashboard Tab
  Widget _buildDashboard() {
    final bankService = Provider.of<BankService>(context);
    final transactionService = Provider.of<TransactionService>(context);
    
    // Calculate total balance across all accounts
    final totalBalance = bankService.bankAccounts.fold(
      0.0,
      (sum, account) => sum + (account.balance ?? 0),
    );
    
    // Get income and expenses
    final totalIncome = transactionService.getTotalIncome();
    final totalExpenses = transactionService.getTotalExpenses();
    
    return SingleChildScrollView(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Balance summary
          Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Total Balance',
                    style: TextStyle(
                      fontSize: 16,
                      color: AppTheme.secondaryTextColor,
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    currencyFormat.format(totalBalance),
                    style: TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.textColor,
                    ),
                  ),
                  SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Income',
                              style: TextStyle(
                                fontSize: 14,
                                color: AppTheme.secondaryTextColor,
                              ),
                            ),
                            SizedBox(height: 4),
                            Text(
                              currencyFormat.format(totalIncome),
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: AppTheme.incomeColor,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Expenses',
                              style: TextStyle(
                                fontSize: 14,
                                color: AppTheme.secondaryTextColor,
                              ),
                            ),
                            SizedBox(height: 4),
                            Text(
                              currencyFormat.format(totalExpenses),
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: AppTheme.expenseColor,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          SizedBox(height: 24),
          
          // Stats and quick insights
          Text(
            'Key Metrics',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          SizedBox(height: 8),
          StatCardRow(
            cards: [
              StatCard(
                title: 'Connected Banks',
                value: bankService.bankAccounts.length.toString(),
                icon: Icons.account_balance,
                color: Colors.blue,
                onTap: () {
                  setState(() {
                    _selectedIndex = 2;
                  });
                },
              ),
              StatCard(
                title: 'This Month',
                value: currencyFormat.format(totalIncome - totalExpenses),
                icon: Icons.trending_up,
                color: (totalIncome - totalExpenses) >= 0
                    ? AppTheme.incomeColor
                    : AppTheme.expenseColor,
              ),
              StatCard(
                title: 'Transactions',
                value: transactionService.transactions.length.toString(),
                icon: Icons.receipt_long,
                color: Colors.purple,
                onTap: () {
                  setState(() {
                    _selectedIndex = 1;
                  });
                },
              ),
            ],
          ),
          SizedBox(height: 24),
          
          // Recent transactions
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Recent Transactions',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              TextButton(
                onPressed: () {
                  setState(() {
                    _selectedIndex = 1;
                  });
                },
                child: Text('See All'),
              ),
            ],
          ),
          SizedBox(height: 8),
          _buildRecentTransactions(),
          
          SizedBox(height: 24),
          
          // Spending by category
          Text(
            'Spending by Category',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          SizedBox(height: 8),
          _buildSpendingCategoryChart(),
        ],
      ),
    );
  }

  // Recent transactions widget
  Widget _buildRecentTransactions() {
    final transactionService = Provider.of<TransactionService>(context);
    final transactions = transactionService.transactions;
    
    if (transactions.isEmpty) {
      return Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Center(
            child: Column(
              children: [
                Icon(
                  Icons.receipt_long,
                  size: 48,
                  color: Colors.grey.shade400,
                ),
                SizedBox(height: 16),
                Text(
                  'No transactions yet',
                  style: TextStyle(
                    fontSize: 16,
                    color: AppTheme.secondaryTextColor,
                  ),
                ),
                SizedBox(height: 8),
                Text(
                  'Connect a bank account to see your transactions',
                  style: TextStyle(
                    fontSize: 14,
                    color: AppTheme.secondaryTextColor,
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      );
    }
    
    // Show only the 5 most recent transactions
    final recentTransactions = transactions.length > 5
        ? transactions.sublist(0, 5)
        : transactions;
    
    return Column(
      children: recentTransactions.map((transaction) {
        return TransactionCard(
          transaction: transaction,
          onTap: () {
            // Open transaction details
          },
        );
      }).toList(),
    );
  }

  // Spending by category chart
  Widget _buildSpendingCategoryChart() {
    final transactionService = Provider.of<TransactionService>(context);
    final categorySpending = transactionService.getSpendingByCategory();
    
    if (categorySpending.isEmpty) {
      return Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Center(
            child: Column(
              children: [
                Icon(
                  Icons.pie_chart,
                  size: 48,
                  color: Colors.grey.shade400,
                ),
                SizedBox(height: 16),
                Text(
                  'No spending data yet',
                  style: TextStyle(
                    fontSize: 16,
                    color: AppTheme.secondaryTextColor,
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }
    
    // Create a list of pie chart sections and legend items
    final List<PieChartSectionData> sections = [];
    final List<ChartLegendItem> legendItems = [];
    
    final colors = [
      Colors.blue,
      Colors.green,
      Colors.red,
      Colors.orange,
      Colors.purple,
      Colors.teal,
      Colors.pink,
      Colors.amber,
      Colors.indigo,
      Colors.lime,
    ];
    
    int colorIndex = 0;
    categorySpending.forEach((category, amount) {
      final color = colors[colorIndex % colors.length];
      colorIndex++;
      
      sections.add(PieChartSectionData(
        value: amount,
        title: '',
        color: color,
        radius: 60,
      ));
      
      legendItems.add(ChartLegendItem(
        label: '$category: ${currencyFormat.format(amount)}',
        color: color,
      ));
    });
    
    return ChartCard(
      title: 'Spending by Category',
      chartType: ChartType.pie,
      chart: PieChartSample(sections: sections),
      legendItems: legendItems,
    );
  }

  // Transactions Tab
  Widget _buildTransactions() {
    final transactionService = Provider.of<TransactionService>(context);
    final transactions = transactionService.filteredTransactions.isEmpty
        ? transactionService.transactions
        : transactionService.filteredTransactions;
    
    if (transactions.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.receipt_long,
              size: 64,
              color: Colors.grey.shade400,
            ),
            SizedBox(height: 16),
            Text(
              'No transactions yet',
              style: TextStyle(
                fontSize: 18,
                color: AppTheme.secondaryTextColor,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Connect a bank account to see your transactions',
              style: TextStyle(
                fontSize: 14,
                color: AppTheme.secondaryTextColor,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }
    
    // Group by days
    final groupedTransactions = transactionService.getTransactionsByDay();
    final sortedDays = groupedTransactions.keys.toList()..sort((a, b) => b.compareTo(a));
    
    return SingleChildScrollView(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Filters row
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () {
                    // Show date range picker
                  },
                  icon: Icon(Icons.date_range),
                  label: Text('Filter Dates'),
                ),
              ),
              SizedBox(width: 8),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () {
                    // Show category filter
                  },
                  icon: Icon(Icons.category),
                  label: Text('Categories'),
                ),
              ),
            ],
          ),
          SizedBox(height: 16),
          
          // Transactions by day
          ...sortedDays.map((day) {
            final dayTransactions = groupedTransactions[day]!;
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: Text(
                    DateFormat('EEEE, MMMM d, yyyy').format(DateTime.parse(day)),
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.secondaryTextColor,
                    ),
                  ),
                ),
                ...dayTransactions.map((transaction) {
                  return TransactionCard(
                    transaction: transaction,
                    onTap: () {
                      // Open transaction details
                    },
                  );
                }).toList(),
                Divider(),
              ],
            );
          }).toList(),
        ],
      ),
    );
  }

  // Accounts Tab
  Widget _buildAccounts() {
    final bankService = Provider.of<BankService>(context);
    final accounts = bankService.bankAccounts;
    
    if (accounts.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.account_balance,
              size: 64,
              color: Colors.grey.shade400,
            ),
            SizedBox(height: 16),
            Text(
              'No accounts connected',
              style: TextStyle(
                fontSize: 18,
                color: AppTheme.secondaryTextColor,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Connect a bank account to get started',
              style: TextStyle(
                fontSize: 14,
                color: AppTheme.secondaryTextColor,
              ),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () {
                Navigator.of(context).pushNamed('/connect');
              },
              icon: Icon(Icons.add),
              label: Text('Connect Bank'),
            ),
          ],
        ),
      );
    }
    
    return SingleChildScrollView(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Your Accounts',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          SizedBox(height: 16),
          ...accounts.map((account) {
            return AccountCard(
              account: account,
              isSelected: bankService.selectedAccount?.id == account.id,
              onTap: () {
                bankService.selectAccount(account);
              },
              onSync: () async {
                await bankService.syncTransactions(account.id);
                // Refresh transactions
                Provider.of<TransactionService>(context, listen: false)
                    .loadTransactions(accountId: account.id);
              },
            );
          }).toList(),
          SizedBox(height: 16),
          Center(
            child: OutlinedButton.icon(
              onPressed: () {
                Navigator.of(context).pushNamed('/connect');
              },
              icon: Icon(Icons.add),
              label: Text('Connect Another Bank'),
            ),
          ),
        ],
      ),
    );
  }

  // Analytics Tab
  Widget _buildAnalytics() {
    final transactionService = Provider.of<TransactionService>(context);
    final categorySpending = transactionService.getSpendingByCategory();
    final spendingByDay = transactionService.getSpendingByDay();
    
    // Sort by date
    final days = spendingByDay.keys.toList()..sort();
    
    if (categorySpending.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.analytics,
              size: 64,
              color: Colors.grey.shade400,
            ),
            SizedBox(height: 16),
            Text(
              'No data for analytics',
              style: TextStyle(
                fontSize: 18,
                color: AppTheme.secondaryTextColor,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Connect an account and add some transactions',
              style: TextStyle(
                fontSize: 14,
                color: AppTheme.secondaryTextColor,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }
    
    // Prepare data for spending by day chart
    final List<FlSpot> spots = [];
    final List<String> labels = [];
    double maxY = 0;
    
    for (int i = 0; i < days.length; i++) {
      final day = days[i];
      final amount = spendingByDay[day]!;
      spots.add(FlSpot(i.toDouble(), amount));
      labels.add(DateFormat('MM/dd').format(day));
      if (amount > maxY) maxY = amount;
    }
    
    final line = LineChartBarData(
      spots: spots,
      isCurved: true,
      color: AppTheme.primaryColor,
      barWidth: 3,
      dotData: FlDotData(show: true),
      belowBarData: BarAreaData(
        show: true,
        color: AppTheme.primaryColor.withOpacity(0.2),
      ),
    );
    
    return SingleChildScrollView(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Spending over time
          ChartCard(
            title: 'Daily Spending',
            subtitle: 'Last ${days.length} days',
            chartType: ChartType.line,
            chart: LineChartSample(
              lines: [line],
              xLabels: labels,
              maxY: maxY * 1.2,
              leftTitle: 'Amount',
              bottomTitle: 'Date',
              showDots: true,
            ),
          ),
          SizedBox(height: 24),
          
          // Spending by category
          ChartCard(
            title: 'Spending by Category',
            chartType: ChartType.pie,
            chart: _buildCategoryPieChart(categorySpending),
            legendItems: _buildCategoryLegendItems(categorySpending),
          ),
          SizedBox(height: 24),
          
          // Income vs Expenses
          ChartCard(
            title: 'Income vs Expenses',
            chartType: ChartType.bar,
            chart: _buildIncomeExpensesBarChart(),
          ),
        ],
      ),
    );
  }

  // Category pie chart
  Widget _buildCategoryPieChart(Map<String, double> categorySpending) {
    final List<PieChartSectionData> sections = [];
    
    final colors = [
      Colors.blue,
      Colors.green,
      Colors.red,
      Colors.orange,
      Colors.purple,
      Colors.teal,
      Colors.pink,
      Colors.amber,
      Colors.indigo,
      Colors.lime,
    ];
    
    int colorIndex = 0;
    categorySpending.forEach((category, amount) {
      final color = colors[colorIndex % colors.length];
      colorIndex++;
      
      sections.add(PieChartSectionData(
        value: amount,
        title: '',
        color: color,
        radius: 60,
      ));
    });
    
    return PieChartSample(sections: sections);
  }

  // Category legend items
  List<ChartLegendItem> _buildCategoryLegendItems(Map<String, double> categorySpending) {
    final List<ChartLegendItem> legendItems = [];
    
    final colors = [
      Colors.blue,
      Colors.green,
      Colors.red,
      Colors.orange,
      Colors.purple,
      Colors.teal,
      Colors.pink,
      Colors.amber,
      Colors.indigo,
      Colors.lime,
    ];
    
    int colorIndex = 0;
    categorySpending.forEach((category, amount) {
      final color = colors[colorIndex % colors.length];
      colorIndex++;
      
      legendItems.add(ChartLegendItem(
        label: '$category: ${currencyFormat.format(amount)}',
        color: color,
      ));
    });
    
    return legendItems;
  }

  // Income vs Expenses bar chart
  Widget _buildIncomeExpensesBarChart() {
    final transactionService = Provider.of<TransactionService>(context);
    final income = transactionService.getTotalIncome();
    final expenses = transactionService.getTotalExpenses();
    
    final barGroups = [
      BarChartGroupData(
        x: 0,
        barRods: [
          BarChartRodData(
            toY: income,
            color: AppTheme.incomeColor,
            width: 20,
            borderRadius: BorderRadius.vertical(top: Radius.circular(4)),
          ),
        ],
      ),
      BarChartGroupData(
        x: 1,
        barRods: [
          BarChartRodData(
            toY: expenses,
            color: AppTheme.expenseColor,
            width: 20,
            borderRadius: BorderRadius.vertical(top: Radius.circular(4)),
          ),
        ],
      ),
    ];
    
    final titles = ['Income', 'Expenses'];
    
    return BarChartSample(
      barGroups: barGroups,
      titles: titles,
      maxY: income > expenses ? income * 1.2 : expenses * 1.2,
    );
  }
}