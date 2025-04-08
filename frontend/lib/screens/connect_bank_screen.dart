import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:flutter/foundation.dart'; // For kIsWeb
import 'package:url_launcher/url_launcher.dart';
import 'dart:html' as html;
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
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _getAuthLink();
      if (kIsWeb) {
        _handleRedirectForWeb();
      }
    });
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
    if (url.contains('code=')) {
      final uri = Uri.parse(url);
      final code = uri.queryParameters['code'];

      if (code != null) {
        Future.microtask(() {
          setState(() {
            _isLoading = true;
          });
        });

        try {
          final bankService = Provider.of<BankService>(context, listen: false);
          final success = await bankService.handleCallback(code);

          if (success && mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Bank account connected successfully!')),
            );
            Navigator.of(context).pushReplacementNamed('/home');
          } else if (mounted) {
            Future.microtask(() {
              setState(() {
                _hasError = true;
                _isLoading = false;
              });
            });

            final error = bankService.error;
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Error: ${error ?? "Failed to connect bank account"}')),
            );
          }
        } catch (e) {
          if (mounted) {
            Future.microtask(() {
              setState(() {
                _hasError = true;
                _isLoading = false;
              });
            });
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Error: ${e.toString()}')),
            );
          }
        }
      }
    } else if (url.contains('error=')) {
      final uri = Uri.parse(url);
      final errorDescription = uri.queryParameters['error_description'];

      Future.microtask(() {
        setState(() {
          _hasError = true;
          _isLoading = false;
        });
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: ${errorDescription ?? "Unknown error"}')),
      );
    }
  }

  void _handleRedirectForWeb() {
    html.window.onHashChange.listen((event) {
      final url = html.window.location.href;
      if (url.contains('code=')) {
        _handleRedirect(url);
      } else if (url.contains('error=')) {
        _handleRedirect(url);
      }
    });
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
    if (kIsWeb) {
      // For Flutter Web, open the URL in a new browser tab
      return Center(
        child: ElevatedButton(
          onPressed: () async {
            if (await canLaunchUrl(Uri.parse(_authUrl))) {
              await launchUrl(Uri.parse(_authUrl), mode: LaunchMode.externalApplication);
            } else {
              setState(() {
                _hasError = true;
              });
            }
          },
          child: Text('Open Bank Connection'),
        ),
      );
    } else {
      // For Android/iOS, use WebView
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
              Future.microtask(() {
                setState(() {
                  _isLoading = false;
                });
              });
            },
            onWebResourceError: (WebResourceError error) {
              Future.microtask(() {
                setState(() {
                  _hasError = true;
                  _isLoading = false;
                });
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

}