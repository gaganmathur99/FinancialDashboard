import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'models/models.dart';
import 'services/services.dart';
import 'screens/splash_screen.dart';
import 'screens/login_screen.dart';
import 'screens/register_screen.dart';
import 'screens/home_screen.dart';
import 'screens/connect_bank_screen.dart';
import 'theme.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // API Service
        Provider<ApiService>(
          create: (_) => ApiService(),
        ),
        
        // Auth Service
        ChangeNotifierProxyProvider<ApiService, AuthService>(
          create: (context) => AuthService(context.read<ApiService>()),
          update: (context, apiService, authService) => 
              authService ?? AuthService(apiService),
        ),
        
        // Bank Service
        ChangeNotifierProxyProvider<ApiService, BankService>(
          create: (context) => BankService(context.read<ApiService>()),
          update: (context, apiService, bankService) => 
              bankService ?? BankService(apiService),
        ),
        
        // Transaction Service
        ChangeNotifierProxyProvider2<ApiService, BankService, TransactionService>(
          create: (context) => TransactionService(
            context.read<ApiService>(), 
            context.read<BankService>(),
          ),
          update: (context, apiService, bankService, transactionService) => 
              transactionService ?? TransactionService(apiService, bankService),
        ),
      ],
      child: MaterialApp(
        title: 'Personal Finance',
        theme: AppTheme.lightTheme,
        debugShowCheckedModeBanner: false,
        initialRoute: '/',
        routes: {
          '/': (context) => SplashScreen(),
          '/login': (context) => LoginScreen(),
          '/register': (context) => RegisterScreen(),
          '/home': (context) => HomeScreen(),
          '/connect': (context) => ConnectBankScreen(),
        },
      ),
    );
  }
}