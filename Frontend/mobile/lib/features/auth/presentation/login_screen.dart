import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/network/dio_client.dart';
import '../../../core/network/api_endpoints.dart';
import '../../../core/storage/secure_storage.dart';
import '../../../core/constants/app_constants.dart';
import '../../../models/models.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});
  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailCtrl = TextEditingController(text: 'driver@urbansense.in');
  final _passCtrl  = TextEditingController(text: 'password123');
  bool _obscure  = true;
  bool _loading  = false;
  String? _error;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() { _loading = true; _error = null; });

    try {
      if (AppConfig.mockMode) {
        // Mock login — simulate network delay
        await Future.delayed(const Duration(milliseconds: 800));
        final storage = ref.read(secureStorageProvider);
        await storage.saveTokens(
          accessToken: 'mock-access-token',
          refreshToken: 'mock-refresh-token',
        );
        await storage.saveUserInfo(userId: 'mock-user-id', role: 'DRIVER');
        if (mounted) context.go('/dashboard');
        return;
      }

      final client = ref.read(dioClientProvider);
      final tokenData = await client.post<Map<String, dynamic>>(
        ApiEndpoints.login,
        data: {'email': _emailCtrl.text.trim(), 'password': _passCtrl.text},
      );
      final tokens = TokenOut.fromJson(tokenData);

      // Save token then fetch user info
      final storage = ref.read(secureStorageProvider);
      await storage.saveTokens(
        accessToken: tokens.accessToken,
        refreshToken: tokens.refreshToken,
      );

      // Verify role
      final userData = await client.get<Map<String, dynamic>>(ApiEndpoints.me);
      final user = User.fromJson(userData);
      if (user.role != UserRole.DRIVER) {
        await storage.clearAll();
        setState(() { _error = 'Access denied. Driver role required.'; _loading = false; });
        return;
      }

      await storage.saveUserInfo(userId: user.id, role: user.role.name);
      if (mounted) context.go('/dashboard');
    } catch (e) {
      setState(() {
        _error = e.toString().contains('401')
            ? 'Invalid email or password.'
            : 'Connection error. Please try again.';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0F1E),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Logo
                Container(
                  width: 72,
                  height: 72,
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [Color(0xFF3B82F6), Color(0xFF8B5CF6)],
                    ),
                    borderRadius: BorderRadius.circular(18),
                    boxShadow: [BoxShadow(color: const Color(0xFF3B82F6).withOpacity(0.3), blurRadius: 24)],
                  ),
                  child: const Icon(Icons.shield_rounded, color: Colors.white, size: 40),
                ),
                const SizedBox(height: 20),
                const Text('AI UrbanSense', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: Color(0xFFE8EDF5))),
                const SizedBox(height: 6),
                const Text('Driver Mobile Application', style: TextStyle(fontSize: 13, color: Color(0xFF8FA3C0))),
                const SizedBox(height: 32),

                // Form card
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: const Color(0xFF111827),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFF1E2D45)),
                  ),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        if (_error != null)
                          Container(
                            padding: const EdgeInsets.all(12),
                            margin: const EdgeInsets.only(bottom: 16),
                            decoration: BoxDecoration(
                              color: const Color(0xFFEF4444).withOpacity(0.1),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: const Color(0xFFEF4444).withOpacity(0.3)),
                            ),
                            child: Row(children: [
                              const Icon(Icons.error_outline, color: Color(0xFFEF4444), size: 16),
                              const SizedBox(width: 8),
                              Expanded(child: Text(_error!, style: const TextStyle(color: Color(0xFFFCA5A5), fontSize: 13))),
                            ]),
                          ),

                        // Email field
                        TextFormField(
                          controller: _emailCtrl,
                          keyboardType: TextInputType.emailAddress,
                          style: const TextStyle(color: Color(0xFFE8EDF5)),
                          decoration: const InputDecoration(
                            labelText: 'Email / Mobile',
                            prefixIcon: Icon(Icons.person_outline, color: Color(0xFF8FA3C0), size: 20),
                          ),
                          validator: (v) => v == null || v.isEmpty ? 'Email required' : null,
                        ),
                        const SizedBox(height: 16),

                        // Password field
                        TextFormField(
                          controller: _passCtrl,
                          obscureText: _obscure,
                          style: const TextStyle(color: Color(0xFFE8EDF5)),
                          decoration: InputDecoration(
                            labelText: 'Password',
                            prefixIcon: const Icon(Icons.lock_outline, color: Color(0xFF8FA3C0), size: 20),
                            suffixIcon: IconButton(
                              icon: Icon(_obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined, color: const Color(0xFF8FA3C0), size: 20),
                              onPressed: () => setState(() => _obscure = !_obscure),
                            ),
                          ),
                          validator: (v) => v == null || v.isEmpty ? 'Password required' : null,
                        ),

                        Align(
                          alignment: Alignment.centerRight,
                          child: TextButton(
                            onPressed: () {},
                            child: const Text('Forgot Password?', style: TextStyle(color: Color(0xFF3B82F6), fontSize: 13)),
                          ),
                        ),

                        // Login button
                        SizedBox(
                          height: 52,
                          child: ElevatedButton(
                            onPressed: _loading ? null : _login,
                            child: _loading
                                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                                : const Text('LOGIN', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, letterSpacing: 1)),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 16),
                const Text(
                  'AI UrbanSense v1.0 · Access restricted to drivers',
                  style: TextStyle(fontSize: 11, color: Color(0xFF4D6180)),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
