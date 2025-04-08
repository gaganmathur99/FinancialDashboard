class AppConfig {
  // App Information
  static const String appName = 'Personal Finance';
  static const String appVersion = '1.0.0';
  
  // API Configuration
  static const String apiBaseUrl = 'http://localhost:5000/api';
  
  // Auth endpoints
  static const String loginEndpoint = '/auth/login';
  static const String registerEndpoint = '/auth/register';
  static const String refreshTokenEndpoint = '/auth/refresh';
  
  // Bank endpoints
  static const String bankAuthLinkEndpoint = '/bank/auth-link';
  static const String bankCallbackEndpoint = '/bank/callback';
  static const String bankAccountsEndpoint = '/bank/accounts';
  static const String bankSyncEndpoint = '/bank/sync';
  
  // Transaction endpoints
  static const String transactionsEndpoint = '/transactions';
  
  // User endpoints
  static const String userProfileEndpoint = '/user/profile';
  
  // Storage keys
  static const String tokenKey = 'auth_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String userIdKey = 'user_id';
  
  // Timeouts
  static const int apiTimeoutSeconds = 30;
  
  // Session expiration (in minutes)
  static const int sessionExpiration = 60;
  
  // Date formats
  static const String displayDateFormat = 'MMM dd, yyyy';
  static const String apiDateFormat = 'yyyy-MM-dd';
  static const String displayTimeFormat = 'hh:mm a';
  
  // Animation durations
  static const int shortAnimationDuration = 200; // milliseconds
  static const int standardAnimationDuration = 300; // milliseconds
  static const int longAnimationDuration = 500; // milliseconds
  
  // Pagination
  static const int defaultPageSize = 20;
  
  // TrueLayer Configuration
  static const String trueLayerRedirectUri = 'https://console.truelayer.com/redirect-page';
}