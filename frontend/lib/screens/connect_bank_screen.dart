import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:webview_flutter/webview_flutter.dart';
import '../services/services.dart';
import '../widgets/widgets.dart';

class ConnectBankScreen extends StatefulWidget {
  @override
  _ConnectBankScreenState createState() => _ConnectBankScreenState();
}

class _ConnectBankScreenState extends State<ConnectBankScreen> {
  bool _isLoading = true;
  bool _hasError = false;
  String _authUrl = '';
  WebViewController? _webViewController;

  @override
  void initState() {
    super.initState();
    _getAuthLink();
  }

  Future<void> _getAuthLink() async {
    setState(() {
      _isLoading = true;
      _hasError = false;
    });

    try {
      final bankService = Provider.of<BankService>(context, listen: false);
      final url = await bankService.getAuthLink();
      
      if (mounted) {
        setState(() {
          _authUrl = url;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _hasError = true;
          _isLoading = false;
        });
      }
    }
  }

  void _handleRedirect(String url) async {
    // Check if URL contains the code parameter
    if (url.contains('code=')) {
      // Extract the code
      final uri = Uri.parse(url);
      final code = uri.queryParameters['code'];

      if (code != null) {
        setState(() {
          _isLoading = true;
        });

        try {
          final bankService = Provider.of<BankService>(context, listen: false);
          final success = await bankService.handleCallback(code);

          if (success && mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Bank account connected successfully!')),
            );
            Navigator.of(context).pushReplacementNamed('/home');
          }
        } catch (e) {
          if (mounted) {
            setState(() {
              _hasError = true;
              _isLoading = false;
            });
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Failed to connect bank account')),
            );
          }
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Connect Your Bank'),
      ),
      body: _isLoading
          ? AppLoadingIndicator()
          : _hasError
              ? _buildErrorView()
              : _buildWebView(),
    );
  }

  Widget _buildErrorView() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.error_outline,
            size: 64,
            color: Colors.red,
          ),
          SizedBox(height: 16),
          Text(
            'Failed to load bank connection',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'There was an error connecting to the bank service',
            textAlign: TextAlign.center,
          ),
          SizedBox(height: 24),
          ElevatedButton(
            onPressed: _getAuthLink,
            child: Text('Try Again'),
          ),
        ],
      ),
    );
  }

  Widget _buildWebView() {
    final controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(Colors.white)
      ..setNavigationDelegate(
        NavigationDelegate(
          onProgress: (int progress) {
            // Update loading bar
          },
          onPageStarted: (String url) {
            // Page started loading
          },
          onPageFinished: (String url) {
            setState(() {
              _isLoading = false;
            });
          },
          onWebResourceError: (WebResourceError error) {
            setState(() {
              _hasError = true;
              _isLoading = false;
            });
          },
          onNavigationRequest: (NavigationRequest request) {
            // Check for redirect URL with code
            if (request.url.contains('redirect-page') || request.url.contains('callback')) {
              _handleRedirect(request.url);
            }
            return NavigationDecision.navigate;
          },
        ),
      )
      ..loadRequest(Uri.parse(_authUrl));
    
    _webViewController = controller;
    
    return Stack(
      children: [
        WebViewWidget(controller: controller),
        if (_isLoading)
          Container(
            color: Colors.white,
            child: AppLoadingIndicator(),
          ),
      ],
    );
  }
}